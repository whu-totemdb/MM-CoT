"""L2 nearest-neighbor retrieval with the original MPNet encoder and pgvector."""

import os
from functools import lru_cache

from .database import rows


@lru_cache(maxsize=1)
def load_encoder(model_name):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class NodeRetriever:
    def __init__(self, conn, graph, encoder=None):
        self.conn = conn
        self.graph = graph
        self.encoder = encoder

    def retrieve_node(self, keyword, top_k=1, node_type=None):
        if not keyword.strip() or top_k < 1:
            raise ValueError("Provide a nonempty keyword and positive top_k")
        if node_type is not None and node_type not in ("Paper", "Author", "Affiliation"):
            raise ValueError("node_type must be Paper, Author, or Affiliation")
        if self.encoder is None:
            self.encoder = load_encoder(os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"))
        vector = self.encoder.encode(keyword.strip(), convert_to_numpy=True).tolist()
        vector_text = "[" + ",".join(map(str, vector)) + "]"
        where = " WHERE nodetype = %s" if node_type else ""
        params = ((node_type,) if node_type else ()) + (vector_text, int(top_k))
        matches = rows(self.conn,
            f"SELECT id, nodetype FROM vectors_{self.graph.suffix}{where} "
            "ORDER BY embedding <-> %s::vector LIMIT %s", params)
        return [(str(row["id"]), row["nodetype"]) for row in matches]

    def get_best_match(self, keyword):
        matches = self.retrieve_node(keyword)
        return matches[0] if matches else None
