"""Photo -> semantic answer, for the Unity client's on-headset camera
(UXR.QuestCamera) and the phone-photo fallback alike. Same shape as
fridge.py's suggest_dishes_from_photo (same VisionClient, same fenced-JSON
parsing with a non-JSON fallback) - Unity/the phone just POST a photo,
the Python backend does the only "looking" that happens.
"""
import json
import re
from typing import Any, Dict, Protocol

from backend.models import DonenessCheck, SpotIdentification

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

SPOT_LABELS = ("Stove", "Counter", "Sink", "Microwave", "Fridge", "Other")

SPOT_PROMPT = (
    "You're looking through a cook's headset camera at a spot in their kitchen "
    f"they just pointed at to pin it. Pick the single best label from this exact "
    f'list: {list(SPOT_LABELS)}. Respond with ONLY JSON, no other text, in this '
    'exact shape: {"label": "...", "confidence": "high"|"medium"|"low"}'
)


class VisionClient(Protocol):
    async def analyze_image(self, image_bytes: bytes, filename: str, prompt: str) -> Dict[str, Any]: ...


async def identify_spot(client: VisionClient, image_bytes: bytes, filename: str) -> SpotIdentification:
    response = await client.analyze_image(image_bytes, filename, SPOT_PROMPT)
    data = _parse_json(response.get("content", ""))
    label = str(data.get("label", "Other"))
    if label not in SPOT_LABELS:
        label = "Other"
    confidence = str(data.get("confidence", "low"))
    return SpotIdentification(label=label, confidence=confidence if confidence in ("high", "medium", "low") else "low")


def _doneness_prompt(dish: str, current_step: str) -> str:
    return (
        f"You're looking through a cook's headset camera at their '{dish}', mid-recipe. "
        f"The current step is: '{current_step}'. Judge whether the food looks done for "
        "this stage - not necessarily the whole dish finished, just whether it looks "
        "right for where they are in the recipe. Be specific and brief (one sentence): "
        "what to look for or do next if it's not there yet. Respond with ONLY JSON, no "
        'other text, in this exact shape: {"looks_done": true|false, '
        '"confidence": "high"|"medium"|"low", "feedback": "..."}'
    )


async def check_doneness(client: VisionClient, image_bytes: bytes, filename: str, dish: str, current_step: str) -> DonenessCheck:
    response = await client.analyze_image(image_bytes, filename, _doneness_prompt(dish, current_step))
    data = _parse_json(response.get("content", ""))
    confidence = str(data.get("confidence", "low"))
    return DonenessCheck(
        looks_done=bool(data.get("looks_done", False)),
        confidence=confidence if confidence in ("high", "medium", "low") else "low",
        feedback=str(data.get("feedback", "")) or "Couldn't get a clear read on that - try a closer, better-lit shot.",
    )


def _parse_json(text: str) -> Dict[str, Any]:
    cleaned = _CODE_FENCE_RE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return {}
