"""Fake chat client shaped like BackboardClient, for testing the chef's
tool-call loop without hitting a live model.
"""
from typing import Any, Dict, List, Optional


class FakeBackboardClient:
    """Plays back a fixed script of responses, one per call to send_message."""

    def __init__(self, script: List[Dict[str, Any]]):
        self.script = script
        self.calls: List[List[Dict[str, str]]] = []

    async def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, str]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        self.calls.append(messages)
        index = len(self.calls) - 1
        if index >= len(self.script):
            return {"text": "", "tool_calls": [], "audio": None}
        return self.script[index]
