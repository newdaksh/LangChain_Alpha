"""
Conversation summarization middleware.

If the conversation/messages grow beyond a threshold, this middleware
creates a condensed summary and replaces the long history with the summary
to keep prompts compact and reduce token usage.
"""
from typing import Tuple, Any, List
import os
import requests


class SummarizationMiddleware:
    def __init__(self, ollama_url: str = None, model: str = None, max_messages: int = 15):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.max_messages = max_messages

    def before_prompt(self, messages: List[Any], state: dict) -> Tuple[List[Any], dict]:
        # If too many messages, summarize and inject a short history note
        if len(messages) <= self.max_messages:
            return messages, state

        # Combine message texts
        combined = []
        for m in messages:
            try:
                text = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else "")
            except Exception:
                text = ""
            if text:
                combined.append(text)

        text_blob = "\n".join(combined[- self.max_messages :])

        summary = self._summarize_text(text_blob)

        # Replace messages with a short summary block followed by the last few messages
        new_msgs = []
        # insert a system-like summary message
        new_msgs.append({"role": "system", "content": f"[Conversation summary]\n{summary}"})
        # keep last few messages
        for m in messages[-5:]:
            new_msgs.append(m)

        return new_msgs, state

    def _summarize_text(self, text: str) -> str:
        try:
            payload = {
                "model": self.model,
                "prompt": f"Summarize the following conversation in 6 concise bullet points:\n\n{text}\n\nSummary:",
                "max_tokens": 512
            }
            resp = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "[summary-unavailable]").strip()
        except Exception:
            return "[summary-unavailable]"

    def after_llm(self, messages: List[Any], state: dict) -> Tuple[List[Any], dict]:
        return messages, state
