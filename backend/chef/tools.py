"""Tool definitions the chef can call, and the dispatcher that executes
them against a KitchenSession + CookMemory.

Schema shape is Backboard's confirmed format (docs.backboard.io/sdk/tool-calls):
a list of {"type": "function", "function": {name, description, parameters}},
same wrapper OpenAI uses.
"""
from typing import Any, Dict

from backend.chef.memory import CookMemory
from backend.chef.session import KitchenSession


def _tool(name: str, description: str, properties: Dict[str, Any] = None, required=None) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                **({"required": required} if required else {}),
            },
        },
    }


TOOL_SCHEMAS = [
    _tool("next_step", "Advance to the next step of the recipe."),
    _tool("back_step", "Go back to the previous step of the recipe."),
    _tool("repeat_step", "Repeat the current step out loud."),
    _tool(
        "start_timer",
        "Start a timer, auto-detecting duration from the current step if not given.",
        {"label": {"type": "string"}, "duration_seconds": {"type": "integer"}},
    ),
    _tool("read_ingredients", "Read out the full (scaled) ingredient list."),
    _tool(
        "scale_servings",
        "Scale the recipe to a serving multiplier, e.g. 2 for 'double it'.",
        {"multiplier": {"type": "number"}},
        required=["multiplier"],
    ),
    _tool(
        "swap_ingredient",
        "Swap one ingredient for another substitute.",
        {"original": {"type": "string"}, "replacement": {"type": "string"}},
        required=["original", "replacement"],
    ),
    _tool(
        "remember_allergy",
        "Remember that the cook is allergic to something, across sessions.",
        {"item": {"type": "string"}},
        required=["item"],
    ),
    _tool(
        "remember_dislike",
        "Remember that the cook dislikes something, across sessions.",
        {"item": {"type": "string"}},
        required=["item"],
    ),
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
