"""
PII Redaction middleware for LangChain v1-style agents.

Provides a before_prompt hook that redacts common PII patterns
from outgoing prompts so the LLM and tools do not receive sensitive data.
"""
import re
from typing import Tuple, Any, List


class PIIMiddleware:
    """Middleware to redact simple PII (emails, phone numbers) from agent messages."""

    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_REGEX = re.compile(r"\b\+?\d[\d\s\-()]{6,}\d\b")

    def before_prompt(self, messages: List[Any], state: dict) -> Tuple[List[Any], dict]:
        """Called before the prompt is sent to the model.

        messages: list of message objects or dicts that have a `content` attribute/key.
        state: agent state dict (passed-through)
        Returns the (messages, state) pair possibly modified.
        """
        redacted = []
        for m in messages:
            try:
                content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
            except Exception:
                content = None

            if content is None:
                redacted.append(m)
                continue

            txt = self.EMAIL_REGEX.sub("[REDACTED_EMAIL]", content)
            txt = self.PHONE_REGEX.sub("[REDACTED_PHONE]", txt)

            # Try to set back content in same shape
            if hasattr(m, "content"):
                m.content = txt
                redacted.append(m)
            elif isinstance(m, dict):
                nm = dict(m)
                nm["content"] = txt
                redacted.append(nm)
            else:
                redacted.append(m)

        return redacted, state

    def after_llm(self, messages: List[Any], state: dict) -> Tuple[List[Any], dict]:
        """No-op after LLM by default."""
        return messages, state
