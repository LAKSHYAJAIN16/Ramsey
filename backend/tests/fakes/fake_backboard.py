"""Fake Backboard client, shaped like the real thread/run API: a
send_message call either COMPLETEs with text or REQUIRES_ACTION with
tool_calls, and submit_tool_outputs continues the same run.
"""
from typing import Any, Dict, List, Optional


class FakeBackboardClient:
    """Plays back a fixed script of responses, one per call (send_message
    or submit_tool_outputs, in the order they'd naturally occur).
    """

    def __init__(self, script: List[Dict[str, Any]]):
        self.script = script
        self.calls: List[Dict[str, Any]] = []

    async def send_message(
        self,
        content: str,
        thread_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, Any]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        self.calls.append({"type": "send_message", "content": content, "thread_id": thread_id})
        return self._next_response()

    async def submit_tool_outputs(self, thread_id: str, tool_outputs: List[Dict[str, str]]) -> Dict[str, Any]:
        self.calls.append({"type": "submit_tool_outputs", "thread_id": thread_id, "tool_outputs": tool_outputs})
        return self._next_response()

    def _next_response(self) -> Dict[str, Any]:
        index = len(self.calls) - 1
        if index >= len(self.script):
            return {"thread_id": "fake-thread", "status": "COMPLETED", "content": "", "tool_calls": [], "audio_url": None}
        response = dict(self.script[index])
        response.setdefault("thread_id", "fake-thread")
        response.setdefault("tool_calls", [])
        response.setdefault("audio_url", None)
        return response
