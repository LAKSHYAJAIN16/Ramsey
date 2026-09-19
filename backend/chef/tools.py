"""Tool definitions the chef can call, and the dispatcher that executes
them against a KitchenSession + CookMemory.

Schema shape follows the common OpenAI-style function-calling format,
since that's what most model gateways (Backboard included, presumably)
accept. Confirm the exact shape Backboard wants during Tier 0/3.
"""
from typing import Any, Dict

from backend.chef.memory import CookMemory
from backend.chef.session import KitchenSession

TOOL_SCHEMAS = [
    {
        "name": "next_step",
        "description": "Advance to the next step of the recipe.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "back_step",
        "description": "Go back to the previous step of the recipe.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "repeat_step",
        "description": "Repeat the current step out loud.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "start_timer",
        "description": "Start a timer, auto-detecting duration from the current step if not given.",
        "parameters": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "duration_seconds": {"type": "integer"},
            },
        },
    },
    {
        "name": "read_ingredients",
        "description": "Read out the full (scaled) ingredient list.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "scale_servings",
        "description": "Scale the recipe to a serving multiplier, e.g. 2 for 'double it'.",
        "parameters": {
            "type": "object",
            "properties": {"multiplier": {"type": "number"}},
            "required": ["multiplier"],
        },
    },
    {
        "name": "swap_ingredient",
        "description": "Swap one ingredient for another substitute.",
        "parameters": {
            "type": "object",
            "properties": {
                "original": {"type": "string"},
                "replacement": {"type": "string"},
            },
            "required": ["original", "replacement"],
        },
    },
    {
        "name": "remember_allergy",
        "description": "Remember that the cook is allergic to something, across sessions.",
        "parameters": {
            "type": "object",
            "properties": {"item": {"type": "string"}},
            "required": ["item"],
        },
    },
    {
        "name": "remember_dislike",
        "description": "Remember that the cook dislikes something, across sessions.",
        "parameters": {
            "type": "object",
            "properties": {"item": {"type": "string"}},
            "required": ["item"],
        },
    },
]


def dispatch(name: str, args: Dict[str, Any], session: KitchenSession, memory: CookMemory) -> Dict[str, Any]:
    if name == "next_step":
        return {"current_step": session.next_step()}
    if name == "back_step":
        return {"current_step": session.back_step()}
    if name == "repeat_step":
        return {"current_step": session.repeat_step()}
    if name == "start_timer":
        timer = session.start_timer(args.get("label"), args.get("duration_seconds"))
        return {"label": timer.label, "duration_seconds": timer.duration_seconds}
    if name == "read_ingredients":
        return {"ingredients": session.read_ingredients()}
    if name == "scale_servings":
        session.scale_servings(args["multiplier"])
        return {"ingredients": session.scaled_ingredients()}
    if name == "swap_ingredient":
        session.swap_ingredient(args["original"], args["replacement"])
        return {"ingredients": session.scaled_ingredients()}
    if name == "remember_allergy":
        memory.remember_allergy(args["item"])
        return {"allergies": memory.allergies}
    if name == "remember_dislike":
        memory.remember_dislike(args["item"])
        return {"dislikes": memory.dislikes}
    raise ValueError(f"Unknown tool: {name}")
