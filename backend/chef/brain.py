"""The tool-call loop: user text/audio in, Ramsey's reply (and any
kitchen-state changes) out.

Backboard is a thread/run API: a turn either finishes with
status="COMPLETED" (plain text reply) or status="REQUIRES_ACTION" (it
wants tools run). On REQUIRES_ACTION we dispatch the requested tools
locally and POST the results to /threads/tool-outputs, which returns the
next turn - repeat until COMPLETED or MAX_TOOL_ROUNDS is hit.
"""
import json
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
        content: str,
        thread_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: Optional[Dict[str, Any]] = None,
        audio_input: Optional[bytes] = None,
    ) -> Dict[str, Any]: ...

    async def submit_tool_outputs(self, thread_id: str, tool_outputs: List[Dict[str, str]]) -> Dict[str, Any]: ...


def _memory_context(memory: CookMemory) -> str:
    parts = []
    if memory.allergies:
        parts.append(f"Allergic to: {', '.join(memory.allergies)}.")
    if memory.dislikes:
        parts.append(f"Dislikes: {', '.join(memory.dislikes)}.")
    if memory.skill_level != "unknown":
        parts.append(f"Skill level: {memory.skill_level}.")
    return " ".join(parts)


def _tool_call_name(call: Dict[str, Any]) -> str:
    return call.get("function", {}).get("name") or call.get("name")


def _tool_call_arguments(call: Dict[str, Any]) -> Dict[str, Any]:
    fn = call.get("function", {})
    args = fn.get("parsed_arguments")
    if args is not None:
        return args
    raw = fn.get("arguments") or call.get("arguments") or "{}"
    return json.loads(raw) if isinstance(raw, str) else raw


def _tool_call_id(call: Dict[str, Any]) -> str:
    return call.get("id") or call.get("tool_call_id")


async def handle_message(
    client: ChatClient,
    session: KitchenSession,
    memory: CookMemory,
    user_text: str,
    audio_input: Optional[bytes] = None,
    voice: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the tool-call loop and return {"text", "tool_calls", "audio_url", "state"}."""
    system_prompt = (
        f"{SYSTEM_PROMPT} {_memory_context(memory)} Kitchen state: {session.to_state_dict()}"
    )

    response = await client.send_message(
        content=user_text,
        thread_id=session.backboard_thread_id,
        system_prompt=system_prompt,
        tools=TOOL_SCHEMAS,
        voice=voice,
        audio_input=audio_input,
    )
    session.backboard_thread_id = response.get("thread_id") or session.backboard_thread_id

    all_tool_calls: List[Dict[str, Any]] = []
    rounds = 0

    while response.get("status") == "REQUIRES_ACTION" and rounds < MAX_TOOL_ROUNDS:
        tool_outputs = []
        for call in response.get("tool_calls", []):
            name = _tool_call_name(call)
            args = _tool_call_arguments(call)
            result = dispatch(name, args, session, memory)
            all_tool_calls.append({"name": name, "arguments": args})
            tool_outputs.append({"tool_call_id": _tool_call_id(call), "output": json.dumps(result)})

        response = await client.submit_tool_outputs(session.backboard_thread_id, tool_outputs)
        rounds += 1

    text = response.get("content") or "Kept myself busy in there - what do you need?"
    return {
        "text": text,
        "tool_calls": all_tool_calls,
        "audio_url": response.get("audio_url"),
        "state": session.to_state_dict(),
    }
