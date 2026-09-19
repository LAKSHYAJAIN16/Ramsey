"""Real Backboard client.

Verified against https://docs.backboard.io (Sept 2026):
  - base URL:      https://app.backboard.io/api
  - auth header:   X-API-Key
  - send message:  POST /threads/messages           (or /threads/{id}/messages)
  - tool outputs:  POST /threads/tool-outputs
  - voice:         same send-message call, multipart/form-data, with an
                    `audio_file` binary and a `voice` field (JSON-encoded
                    {"stt": {...}, "tts": {...}})

Backboard is an Assistants-style thread/run API, not a stateless chat
completion: it remembers the conversation server-side against a
`thread_id`, and when the model wants to call a tool it returns
status="REQUIRES_ACTION" with `tool_calls` instead of text - you execute
them locally and POST the results to /threads/tool-outputs to get the
next turn. That flow (not a client-side messages list) is what
`chef/brain.py`'s loop is built around.

Still unverified: exact behavior once a real key is live (Tier 0). The
response field spelling (camelCase vs snake_case) has been inconsistent
across the docs mirrors this was checked against - `_get` below reads
both spellings defensively.
"""
import json
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = "https://app.backboard.io/api"


def _get(data: Dict[str, Any], *keys: str, default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


class BackboardClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key}

    async def send_message(
        self,
        content: str,
        thread_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, Any]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """One turn of the conversation. Pass the `thread_id` from a prior
        response to continue it; omit it to start a new thread.
        """
        fields: Dict[str, Any] = {
            "content": content,
            "model_name": self.model,
            "memory": "Auto",
        }
        if thread_id:
            fields["thread_id"] = thread_id
        if system_prompt:
            fields["system_prompt"] = system_prompt
        if tools:
            fields["tools"] = tools if audio_input is None else json.dumps(tools)
        if voice:
            fields["voice"] = voice if audio_input is None else json.dumps(voice)

        async with httpx.AsyncClient(timeout=30) as client:
            if audio_input is not None:
                # multipart/form-data is required to attach a binary audio file
                resp = await client.post(
                    f"{BASE_URL}/threads/messages",
                    headers=self._headers(),
                    data=fields,
                    files={"audio_file": ("utterance.webm", audio_input, "audio/webm")},
                )
            else:
                resp = await client.post(
                    f"{BASE_URL}/threads/messages",
                    headers=self._headers(),
                    json=fields,
                )
        resp.raise_for_status()
        return self._normalize(resp.json())

    async def analyze_image(self, image_bytes: bytes, filename: str, prompt: str) -> Dict[str, Any]:
        """Send a photo + a text prompt, asking for a JSON reply.

        UNVERIFIED (not confirmed by docs): whether Backboard's `files`
        multipart field is read by a vision-capable model for an arbitrary
        photo, or is scoped to document/RAG attachments only. If this
        doesn't pan out live, swap this call for a direct Gemini vision
        call instead - the brief already flags Gemini as the fallback for
        image understanding (see Tier 8's "Is it done?" vision idea).
        """
        fields = {
            "content": prompt,
            "model_name": self.model,
            "json_output": "true",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BASE_URL}/threads/messages",
                headers=self._headers(),
                data=fields,
                files={"files": (filename, image_bytes, "image/jpeg")},
            )
        resp.raise_for_status()
        return self._normalize(resp.json())

    async def submit_tool_outputs(self, thread_id: str, tool_outputs: List[Dict[str, str]]) -> Dict[str, Any]:
        """`tool_outputs`: [{"tool_call_id": ..., "output": <stringified result>}]."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BASE_URL}/threads/tool-outputs",
                headers=self._headers(),
                json={"thread_id": thread_id, "tool_outputs": tool_outputs},
            )
        resp.raise_for_status()
        return self._normalize(resp.json())

    @staticmethod
    def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        voice_records = _get(data, "voice_records", "voiceRecords", default={}) or {}
        tts = voice_records.get("tts") if isinstance(voice_records, dict) else None
        return {
            "thread_id": _get(data, "thread_id", "threadId"),
            "status": _get(data, "status", default="COMPLETED"),
            "content": _get(data, "content", "message", default=""),
            "tool_calls": _get(data, "tool_calls", "toolCalls", default=[]) or [],
            "audio_url": tts.get("audio_url") if isinstance(tts, dict) else None,
        }
