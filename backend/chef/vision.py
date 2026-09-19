"""Photo -> semantic answer, for the Unity client's on-headset camera
(UXR.QuestCamera) and the phone-photo fallback alike. Same shape as
fridge.py's suggest_dishes_from_photo (same VisionClient, same fenced-JSON
parsing with a non-JSON fallback) - Unity/the phone just POST a photo,
the Python backend does the only "looking" that happens.

Everything here is pure and stateless: photo in, structured result out,
no session mutation. The WATCHING/CORRECTING state machine that decides
what to DO with a CookingCheck lives in cooking_monitor.py, not here -
keeps this module trivially unit-testable with FakeVisionClient (see
docs/vision.md's "Where the orchestration lives").
"""
import json
import re
from typing import Any, Dict, List, Optional, Protocol

from backend.models import CookingCheck, HazardCheck, KitchenSetup, SpotIdentification, StationCheck

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

SPOT_LABELS = ("Stove", "Counter", "Sink", "Microwave", "Fridge", "Other")
DONENESS_LEVELS = ("not started", "in progress", "done", "overcooked", "burnt")
HAZARD_TYPES = ("none", "smoke", "fire", "boil-over", "other")

SPOT_PROMPT = (
    "You're looking through a cook's headset camera at a spot in their kitchen "
    f"they just pointed at to pin it. Pick the single best label from this exact "
    f'list: {list(SPOT_LABELS)}. Respond with ONLY JSON, no other text, in this '
    'exact shape: {"label": "...", "confidence": "high"|"medium"|"low"}'
)

HAZARD_PROMPT = (
    "You're looking through a cook's headset camera. Check ONLY for an active safety "
    "hazard - visible smoke, flame outside a burner or where it shouldn't be, or a pot "
    'boiling over. If none of those are visible, hazard is "none" - do not invent one. '
    "Respond with ONLY JSON, no other text, in this exact shape: "
    '{"hazard": "none"|"smoke"|"fire"|"boil-over"|"other", "severity": "low"|"high", "note": "..."}'
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


def _cooking_prompt(dish: str, current_step: str, pending_issue: Optional[str] = None) -> str:
    context = (
        f"You're looking through a cook's headset camera while they make '{dish}'. "
        f"The current recipe step is: '{current_step}'."
    )
    if pending_issue:
        context += (
            f" On the last check, this issue was flagged: '{pending_issue}'. Pay "
            "particular attention to whether THIS SPECIFIC issue has been resolved."
        )
    return (
        f"{context} Identify every distinct cooking vessel actually in use in frame "
        "(pots, pans, trays, cutting boards - whatever's really there, don't force it "
        "into a fixed list; skip empty/idle items) and report its contents and how "
        "done it looks. Also list any other loose objects in frame not tied to a "
        "specific vessel (tools, trays, ingredients laid out). Respond with ONLY "
        'JSON, no other text, in this exact shape: {"objects": ["..."], "stations": '
        '[{"vessel": "...", "contents": ["..."], "doneness": "not started"|'
        '"in progress"|"done"|"overcooked"|"burnt", "matches_expected_step": '
        'true|false|null, "note": "..."}]}'
    )


async def check_cooking(
    client: VisionClient,
    image_bytes: bytes,
    filename: str,
    dish: str,
    current_step: str,
    pending_issue: Optional[str] = None,
) -> CookingCheck:
    response = await client.analyze_image(image_bytes, filename, _cooking_prompt(dish, current_step, pending_issue))
    data = _parse_json(response.get("content", ""))
    objects = [str(o) for o in data.get("objects", []) if str(o).strip()]
    stations: List[StationCheck] = []
    for raw in data.get("stations", []):
        if not isinstance(raw, dict):
            continue
        doneness = str(raw.get("doneness", "not started"))
        if doneness not in DONENESS_LEVELS:
            doneness = "not started"
        matches = raw.get("matches_expected_step")
        if not isinstance(matches, bool):
            matches = None
        stations.append(
            StationCheck(
                vessel=str(raw.get("vessel", "unknown")),
                contents=[str(c) for c in raw.get("contents", [])],
                doneness=doneness,
                matches_expected_step=matches,
                note=str(raw.get("note", "")),
            )
        )
    return CookingCheck(objects=objects, stations=stations)


async def check_hazard(client: VisionClient, image_bytes: bytes, filename: str) -> HazardCheck:
    response = await client.analyze_image(image_bytes, filename, HAZARD_PROMPT)
    data = _parse_json(response.get("content", ""))
    hazard = str(data.get("hazard", "none"))
    if hazard not in HAZARD_TYPES:
        hazard = "none"
    severity = str(data.get("severity", "low"))
    if severity not in ("low", "high"):
        severity = "low"
    return HazardCheck(hazard=hazard, severity=severity, note=str(data.get("note", "")))


def _kitchen_setup_prompt(dish: str, ingredients: List[str]) -> str:
    return (
        f"You're looking through a cook's headset camera at their kitchen before they "
        f"start making '{dish}'. The recipe needs these ingredients: "
        f'{", ".join(ingredients) or "unspecified"}. List the cooking equipment you can '
        "actually see (pots, pans, trays, cutting boards, utensils - open-ended, "
        "describe what's there), any of the recipe's ingredients you can see out and "
        "ready, and - only if you're confident something the recipe will need is "
        "visibly absent - what's missing. Don't guess at what might be in a cabinet; "
        "only report what's actually visible. Respond with ONLY JSON, no other text, "
        'in this exact shape: {"available_equipment": ["..."], "available_ingredients": '
        '["..."], "missing_for_recipe": ["..."], "note": "..."}'
    )


async def check_kitchen_setup(
    client: VisionClient, image_bytes: bytes, filename: str, dish: str, ingredients: List[str]
) -> KitchenSetup:
    response = await client.analyze_image(image_bytes, filename, _kitchen_setup_prompt(dish, ingredients))
    data = _parse_json(response.get("content", ""))
    return KitchenSetup(
        available_equipment=[str(e) for e in data.get("available_equipment", [])],
        available_ingredients=[str(i) for i in data.get("available_ingredients", [])],
        missing_for_recipe=[str(m) for m in data.get("missing_for_recipe", [])],
        note=str(data.get("note", "")),
    )


def _parse_json(text: str) -> Dict[str, Any]:
    if not isinstance(text, str):
        return {}
    cleaned = _CODE_FENCE_RE.sub("", text).strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
