"""Fridge photo -> dish suggestions (Tier 8's "what can I make with this?").

Take a photo on a phone (headset camera access is unconfirmed - see the
brief's known unknowns), send it here for a list of dish ideas, then feed
whichever one the cook picks into the normal Browserbase recipe race
(`recipe_engine.service.get_recipe`) exactly like a typed dish name.
"""
import json
import re
from typing import Any, Dict, Protocol

from backend.models import FridgeSuggestions

PROMPT = (
    "You're looking at a photo of a fridge or pantry. Identify the edible "
    "ingredients you can see, then suggest 3 dish names that could mostly be "
    "made from them. Respond with ONLY JSON, no other text, in this exact "
    'shape: {"ingredients": ["...", ...], "suggestions": ["...", "...", "..."]}'
)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class VisionClient(Protocol):
    async def analyze_image(self, image_bytes: bytes, filename: str, prompt: str) -> Dict[str, Any]: ...


async def suggest_dishes_from_photo(client: VisionClient, image_bytes: bytes, filename: str) -> FridgeSuggestions:
    response = await client.analyze_image(image_bytes, filename, PROMPT)
    return _parse_response(response.get("content", ""))


def _parse_response(text: str) -> FridgeSuggestions:
    cleaned = _CODE_FENCE_RE.sub("", text).strip()
    try:
        data = json.loads(cleaned)
        return FridgeSuggestions(
            ingredients=[str(i) for i in data.get("ingredients", [])],
            suggestions=[str(s) for s in data.get("suggestions", [])],
        )
    except (json.JSONDecodeError, AttributeError, TypeError):
        # Model didn't return clean JSON - fall back to non-empty lines so
        # the UI still has something to show instead of a blank screen.
        lines = [line.strip("-*• \t") for line in cleaned.splitlines() if line.strip()]
        return FridgeSuggestions(ingredients=[], suggestions=lines[:3])
