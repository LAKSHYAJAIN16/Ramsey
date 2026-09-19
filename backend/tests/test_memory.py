import json

from backend.chef.memory import MemoryStore


def test_memory_persists_across_store_instances(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path=path)
    mem = store.get("cook-1")
    mem.remember_allergy("shellfish")
    mem.remember_dislike("cilantro")
    store.save()

    reloaded = MemoryStore(path=path)
    reloaded_mem = reloaded.get("cook-1")
    assert reloaded_mem.allergies == ["shellfish"]
    assert reloaded_mem.dislikes == ["cilantro"]


def test_remember_allergy_is_idempotent():
    from backend.chef.memory import CookMemory

    mem = CookMemory()
    mem.remember_allergy("nuts")
    mem.remember_allergy("Nuts")
    assert mem.allergies == ["nuts"]


def test_new_cook_gets_empty_memory(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    mem = store.get("new-cook")
    assert mem.allergies == []
    assert mem.skill_level == "unknown"
