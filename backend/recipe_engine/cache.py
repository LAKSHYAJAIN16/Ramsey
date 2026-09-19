import json
from typing import Dict, Optional

from backend import config
from backend.models import Recipe


class RecipeCache:
    """In-memory result cache, keyed by lowercased dish name.

    Kept dead simple on purpose: a hackathon demo needs the same three
    dishes to resolve instantly on repeat, not a persistence layer.
    """

    def __init__(self):
        self._store: Dict[str, Recipe] = {}

    def get(self, dish_name: str) -> Optional[Recipe]:
        return self._store.get(dish_name.strip().lower())

    def set(self, dish_name: str, recipe: Recipe) -> None:
        self._store[dish_name.strip().lower()] = recipe

    def __len__(self) -> int:
        return len(self._store)


def load_demo_recipe() -> Recipe:
    """The offline recipe that always works, even with no network at all."""
    with open(config.DEMO_RECIPE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Recipe(**data, method="demo")
