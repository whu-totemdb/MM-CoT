"""Environment configuration without connecting to external services at import."""

import os
from dataclasses import dataclass

DOMAINS = ("Biology", "Chemistry", "ComputerScience", "MaterialsScience", "Medicine")
TABLES = ("Paper", "Author", "Affiliation", "PaperAuthor", "PaperAffiliation",
          "AuthorAffiliation", "Reference", "Collab")


def domain_suffix(domain: str) -> str:
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain {domain!r}; choose one of {DOMAINS}")
    return domain.lower()


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str
    base_url: str | None = None
    temperature: float = 0.0
    timeout: float = 120.0
    max_retries: int = 2

    @classmethod
    def from_env(cls, judge: bool = False):
        def value(name, default=""):
            return (os.getenv(f"JUDGE_{name}") if judge else None) or os.getenv(f"LLM_{name}", default)

        key = value("API_KEY")
        model = value("MODEL")
        if not key or not model:
            raise ValueError("Set LLM_API_KEY and LLM_MODEL in your environment or .env file")
        return cls(key, model, value("BASE_URL") or None,
                   float(os.getenv("LLM_TEMPERATURE", "0")),
                   float(os.getenv("LLM_TIMEOUT", "120")),
                   int(os.getenv("LLM_MAX_RETRIES", "2")))

    def public_metadata(self):
        # Credentials and endpoint URLs are intentionally absent from result files.
        return {"model": self.model, "temperature": self.temperature,
                "timeout": self.timeout, "max_retries": self.max_retries}


def connect_database():
    import psycopg2

    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"), port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "mmcot"), user=os.getenv("PGUSER", "mmcot"),
        password=os.getenv("PGPASSWORD", ""), sslmode=os.getenv("PGSSLMODE", "prefer"),
        connect_timeout=int(os.getenv("PGCONNECT_TIMEOUT", "10")),
    )
    # Each operation is independent; one failed query must not poison later steps.
    conn.autocommit = True
    conn.set_session(readonly=True)
    return conn
