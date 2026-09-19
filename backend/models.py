from typing import List, Optional

from pydantic import BaseModel


class Recipe(BaseModel):
    title: str
    source_url: str
    servings: Optional[int] = None
    ingredients: List[str]
    steps: List[str]
    method: str = "unknown"  # "fast" | "browser" | "demo"


class ChatMessage(BaseModel):
    session_id: str
    text: str


class ChatReply(BaseModel):
    reply: str
    tool_calls: List[dict] = []
    recipe: Optional[Recipe] = None


class FridgeSuggestions(BaseModel):
    ingredients: List[str] = []
    suggestions: List[str] = []


class SpotIdentification(BaseModel):
    label: str = "Unknown"
    confidence: str = "low"  # "high" | "medium" | "low"


class StationCheck(BaseModel):
    vessel: str = "unknown"
    contents: List[str] = []
    doneness: str = "not started"  # "not started" | "in progress" | "done" | "overcooked" | "burnt"
    matches_expected_step: Optional[bool] = None
    note: str = ""


class CookingCheck(BaseModel):
    objects: List[str] = []  # loose items in frame, not tied to a specific vessel
    stations: List[StationCheck] = []


class HazardCheck(BaseModel):
    hazard: str = "none"  # "none" | "smoke" | "fire" | "boil-over" | "other"
    severity: str = "low"  # "low" | "high"
    note: str = ""


class KitchenSetup(BaseModel):
    available_equipment: List[str] = []
    available_ingredients: List[str] = []
    missing_for_recipe: List[str] = []
    note: str = ""


class ProgressUpdate(BaseModel):
    calories: int = 0


class SafetyCommand(BaseModel):
    phrase: str
