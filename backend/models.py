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
