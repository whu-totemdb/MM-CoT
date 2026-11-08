"""Shared chat client for controllers, retrieval baselines, and evaluation."""

from .config import LLMConfig


class ChatModel:
    def __init__(self, config: LLMConfig):
        from openai import OpenAI

        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url,
                             timeout=config.timeout, max_retries=config.max_retries)

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model, temperature=self.config.temperature,
            messages=[{"role": "system", "content": "You are a helpful AI bot."},
                      {"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("The model returned an empty response")
        return content.strip()

    def close(self):
        self.client.close()
