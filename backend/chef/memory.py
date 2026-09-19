"""What Ramsey remembers about a cook across sessions.

Backed by a plain JSON file per hackathon scope (swap for MongoDB Atlas
under Tier 6 if there's time). Exposed separately from KitchenSession
because memory outlives any one recipe.
"""
import json
from pathlib import Path
from typing import Dict, List

from backend import config

MEMORY_PATH = config.BASE_DIR / "backend" / "data" / "memory.json"


class CookMemory:
    def __init__(self, allergies=None, dislikes=None, equipment=None, skill_level="unknown", past_mistakes=None):
        self.allergies: List[str] = allergies or []
        self.dislikes: List[str] = dislikes or []
        self.equipment: List[str] = equipment or []
        self.skill_level: str = skill_level
        self.past_mistakes: List[str] = past_mistakes or []

    def remember_allergy(self, item: str) -> None:
        if item.lower() not in [a.lower() for a in self.allergies]:
            self.allergies.append(item)

    def remember_dislike(self, item: str) -> None:
        if item.lower() not in [d.lower() for d in self.dislikes]:
            self.dislikes.append(item)

    def remember_mistake(self, note: str) -> None:
        self.past_mistakes.append(note)

    def to_dict(self) -> Dict:
        return {
            "allergies": self.allergies,
            "dislikes": self.dislikes,
            "equipment": self.equipment,
            "skill_level": self.skill_level,
            "past_mistakes": self.past_mistakes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CookMemory":
        return cls(**data)


class MemoryStore:
    """Keyed by cook/session id. In-process + JSON-file persisted."""

    def __init__(self, path: Path = MEMORY_PATH):
        self.path = path
        self._memories: Dict[str, CookMemory] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._memories = {k: CookMemory.from_dict(v) for k, v in raw.items()}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: v.to_dict() for k, v in self._memories.items()}
        self.path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    def get(self, cook_id: str) -> CookMemory:
        if cook_id not in self._memories:
            self._memories[cook_id] = CookMemory()
        return self._memories[cook_id]
