"""In-memory store for labeled spatial anchors ("Stove", "Counter", ...)
the Unity client places and confirms. Keyed by a kitchen_id the Unity
client generates and persists locally (same client-owned-ID pattern as
the web frontend's session_id/getSessionId()) - no auth required, this
is just a durable-enough-for-a-demo home for the labels themselves, not
the anchor geometry (Unity/Meta's native Spatial Anchors API owns that).
"""
import uuid
from typing import Dict, List


class KitchenSpotStore:
    def __init__(self):
        self._by_kitchen: Dict[str, Dict[str, str]] = {}  # kitchen_id -> {spot_id: label}

    def add(self, kitchen_id: str, label: str) -> Dict[str, str]:
        spot_id = uuid.uuid4().hex[:12]
        self._by_kitchen.setdefault(kitchen_id, {})[spot_id] = label
        return {"id": spot_id, "label": label}

    def list(self, kitchen_id: str) -> List[Dict[str, str]]:
        return [{"id": spot_id, "label": label} for spot_id, label in self._by_kitchen.get(kitchen_id, {}).items()]

    def remove(self, kitchen_id: str, spot_id: str) -> None:
        self._by_kitchen.get(kitchen_id, {}).pop(spot_id, None)
