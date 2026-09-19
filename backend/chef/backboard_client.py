"""Thin wrapper over Backboard: chat completion with tool calls, plus
optional server-side speech-to-text / text-to-speech so the headset never
depends on browser Web Speech support.

UNVERIFIED (Tier 0 item): confirm the request/response shape against a
live Backboard key and that your model names exist in the catalog.
"""
from typing import Any, Dict, List, Optional

import httpx

BACKBOARD_API_URL = "https://api.backboard.io/v1/chat"


class BackboardClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, str]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """One round-trip to Backboard.

        `voice={"stt": "...", "tts": "..."}` asks Backboard to transcribe
        `audio_input` before the model call and synthesize the reply
        after, per the brief. Returns:
            {"text": str, "tool_calls": [{"name", "arguments"}], "audio": bytes | None}
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
        if voice:
            payload["voice"] = voice
        if audio_input is not None:
            payload["audio_input"] = audio_input

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                BACKBOARD_API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        return {
            "text": data.get("text", ""),
            "tool_calls": data.get("tool_calls", []),
            "audio": data.get("audio"),
        }
