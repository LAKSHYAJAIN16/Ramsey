"""Firestore-backed Ramsey profiles and progression.

Firebase identity is deliberately separate from cooking sessions: a visitor
can use Ramsey as a guest, while a signed-in cook gets durable, cross-device
progression stored in Firestore. ProfileStore only relies on the small
collection().document().get()/.set()/.update() surface, so tests inject
FakeFirestoreClient instead of touching a real project (same pattern as the
Browserbase/Backboard fakes).
"""
from datetime import datetime, timezone
from typing import Dict, Optional

COLLECTION = "profiles"

RANKS = (
    (0, "Prep Cook"),
    (100, "Line Cook"),
    (300, "Sous Chef"),
    (700, "Chef de Partie"),
    (1400, "Head Chef"),
    (2500, "Kitchen Legend"),
)


def rank_for_xp(xp: int) -> str:
    return next(name for threshold, name in reversed(RANKS) if xp >= threshold)


class ProfileStore:
    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is None:
            from backend.firebase_client import get_firestore_client
            self._client = get_firestore_client()
        return self._client

    def _doc(self, uid: str):
        return self.client.collection(COLLECTION).document(uid)

    def upsert_firebase_user(self, uid: str, email: str, display_name: str, avatar_url: Optional[str]) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        doc = self._doc(uid)
        existing = doc.get().to_dict()
        data = existing or {"xp": 0, "calories": 0, "meals": 0, "streak": 0, "last_cooked_on": None, "created_at": now}
        data.update(email=email, display_name=display_name, avatar_url=avatar_url, updated_at=now)
        doc.set(data)
        return self._serialize(data)

    def get(self, uid: str) -> Optional[Dict]:
        data = self._doc(uid).get().to_dict()
        return self._serialize(data) if data else None

    def add_completed_meal(self, uid: str, calories: int, completion_id: Optional[str] = None, dish: Optional[str] = None) -> Optional[Dict]:
        doc = self._doc(uid)
        existing = doc.get().to_dict()
        if not existing:
            return None
        completions = existing.get("completed_sessions", [])
        if completion_id and completion_id in completions:
            return self._serialize(existing)
        today = datetime.now(timezone.utc).date().isoformat()
        last = existing.get("last_cooked_on")
        if last == today:
            streak = existing["streak"]
        else:
            yesterday = datetime.fromordinal(datetime.now(timezone.utc).date().toordinal() - 1).date().isoformat()
            streak = existing["streak"] + 1 if last == yesterday else 1
        updates = {
            "xp": existing["xp"] + 20,
            "calories": existing["calories"] + max(0, calories),
            "meals": existing["meals"] + 1,
            "streak": streak,
            "last_cooked_on": today,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if completion_id:
            updates["completed_sessions"] = [*completions, completion_id]
        if dish:
            completed_dishes = existing.get("completed_dishes", [])
            if dish.casefold() not in {name.casefold() for name in completed_dishes}:
                updates["completed_dishes"] = [*completed_dishes, dish]
        doc.update(updates)
        existing.update(updates)
        return self._serialize(existing)

    @staticmethod
    def _serialize(data: Dict) -> Dict:
        profile = dict(data)
        profile["rank"] = rank_for_xp(profile["xp"])
        profile["level"] = profile["xp"] // 100 + 1
        today = datetime.now(timezone.utc).date()
        last = profile.get("last_cooked_on")
        yesterday = datetime.fromordinal(today.toordinal() - 1).date().isoformat()
        if last not in {today.isoformat(), yesterday}:
            profile["streak"] = 0
        profile["daily_goal_complete"] = last == today.isoformat()
        profile["completed_dishes"] = profile.get("completed_dishes", [])
        profile["next_rank"] = next(({"name": name, "xp": xp} for xp, name in RANKS if xp > profile["xp"]), None)
        return profile
