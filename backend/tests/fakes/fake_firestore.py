"""In-memory fake shaped like a Firestore client: just enough surface for
ProfileStore (.collection(name).document(id).get()/.set()/.update()), so
tests never need a real Firebase project or service account key.
"""
from typing import Any, Dict, Optional


class _FakeSnapshot:
    def __init__(self, data: Optional[Dict[str, Any]]):
        self._data = data

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return dict(self._data) if self._data is not None else None


class _FakeDocument:
    def __init__(self, store: Dict[str, Dict[str, Any]], doc_id: str):
        self._store = store
        self._id = doc_id

    def get(self) -> _FakeSnapshot:
        return _FakeSnapshot(self._store.get(self._id))

    def set(self, data: Dict[str, Any]) -> None:
        self._store[self._id] = dict(data)

    def update(self, data: Dict[str, Any]) -> None:
        self._store.setdefault(self._id, {}).update(data)


class _FakeCollection:
    def __init__(self, store: Dict[str, Dict[str, Any]]):
        self._store = store

    def document(self, doc_id: str) -> _FakeDocument:
        return _FakeDocument(self._store, doc_id)


class FakeFirestoreClient:
    """One in-memory dict per collection name; documents are plain dicts."""

    def __init__(self):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self._collections.setdefault(name, {}))
