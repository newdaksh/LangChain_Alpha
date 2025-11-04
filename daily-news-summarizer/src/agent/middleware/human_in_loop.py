"""
Human-in-the-loop middleware.

Provides a simple sync approval hook before tool calls that are marked sensitive.
In production this would be replaced with a UI/webhook; here it does a console prompt.
"""
from typing import Tuple, Any, List


class HumanInTheLoopMiddleware:
    def __init__(self, sensitive_tools=None):
        self.sensitive_tools = set(sensitive_tools or ["save_summary", "save_raw_data"]) 

    def before_tool_call(self, messages: List[Any], state: dict, tool_name: str) -> Tuple[List[Any], dict]:
        """Ask human to approve calls to sensitive tools.

        For CLI runs this prompts the console. For automated runs, you can set
        state['human_approval'] = True to bypass.
        """
        if state.get("bypass_human", False):
            return messages, state

        if tool_name in self.sensitive_tools:
            # Simple CLI approval
            try:
                ans = input(f"Approve tool call '{tool_name}'? (y/n): ").strip().lower()
            except Exception:
                ans = "n"
            if ans != "y":
                raise RuntimeError(f"Tool call '{tool_name}' denied by human-in-loop.")

        return messages, state

    def after_llm(self, messages: List[Any], state: dict) -> Tuple[List[Any], dict]:
        return messages, state
