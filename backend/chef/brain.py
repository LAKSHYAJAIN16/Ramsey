"""The tool-call loop: user text/audio in, Ramsey's reply (and any
kitchen-state changes) out.
"""
from typing import Any, Dict, List, Optional, Protocol

from backend.chef.memory import CookMemory
from backend.chef.session import KitchenSession
from backend.chef.tools import TOOL_SCHEMAS, dispatch

SYSTEM_PROMPT = """You are Ramsey, a voice-driven cooking assistant on a mixed-reality \
headset. Persona: blunt but encouraging - push the cook to do better, never \
put them down, and never claim to be or imitate the real Gordon Ramsay's \
voice or likeness. Keep replies short; they're spoken aloud mid-cook. Use \
the provided tools to act on the kitchen (advance steps, start timers, \
scale the recipe, remember allergies/dislikes) instead of just describing \
what should happen."""

MAX_TOOL_ROUNDS = 4


class ChatClient(Protocol):
    async def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, str]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]: ...


def _memory_context(memory: CookMemory) -> str:
    parts = []
    if memory.allergies:
        parts.append(f"Allergic to: {', '.join(memory.allergies)}.")
    if memory.dislikes:
        parts.append(f"Dislikes: {', '.join(memory.dislikes)}.")
    if memory.skill_level != "unknown":
        parts.append(f"Skill level: {memory.skill_level}.")
    return " ".join(parts)


async def handle_message(
    client: ChatClient,
    session: KitchenSession,
    memory: CookMemory,
    user_text: str,
    audio_input: Optional[bytes] = None,
    voice: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run the tool-call loop and return {"text", "tool_calls", "audio", "state"}."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + " " + _memory_context(memory)},
        {"role": "system", "content": f"Kitchen state: {session.to_state_dict()}"},
        {"role": "user", "content": user_text},
    ]

    all_tool_calls: List[Dict[str, Any]] = []
    audio: Optional[bytes] = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.send_message(
            messages,
            tools=TOOL_SCHEMAS,
            voice=voice,
            audio_input=audio_input,
        )
        audio_input = None  # only send audio on the first round
        audio = response.get("audio") or audio
        tool_calls = response.get("tool_calls") or []

        if not tool_calls:
            return {
                "text": response.get("text", ""),
                "tool_calls": all_tool_calls,
                "audio": audio,
                "state": session.to_state_dict(),
            }

        messages.append({"role": "assistant", "content": response.get("text", "")})
        for call in tool_calls:
            result = dispatch(call["name"], call.get("arguments", {}), session, memory)
            all_tool_calls.append(call)
            messages.append({"role": "tool", "content": f"{call['name']} -> {result}"})

    return {
        "text": "Kept myself busy in there - what do you need?",
        "tool_calls": all_tool_calls,
        "audio": audio,
        "state": session.to_state_dict(),
    }
