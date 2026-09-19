from backend.chef.kitchen_spots import KitchenSpotStore


def test_add_and_list_round_trip():
    store = KitchenSpotStore()
    spot = store.add("kitchen-1", "Stove")
    assert spot["label"] == "Stove"
    assert store.list("kitchen-1") == [spot]


def test_kitchens_are_isolated():
    store = KitchenSpotStore()
    store.add("kitchen-1", "Stove")
    store.add("kitchen-2", "Counter")
    assert [s["label"] for s in store.list("kitchen-1")] == ["Stove"]
    assert [s["label"] for s in store.list("kitchen-2")] == ["Counter"]


def test_unknown_kitchen_returns_empty_list():
    store = KitchenSpotStore()
    assert store.list("never-seen") == []


def test_remove_deletes_only_that_spot():
    store = KitchenSpotStore()
    stove = store.add("kitchen-1", "Stove")
    counter = store.add("kitchen-1", "Counter")
    store.remove("kitchen-1", stove["id"])
    assert store.list("kitchen-1") == [counter]


def test_remove_on_missing_spot_or_kitchen_is_a_no_op():
    store = KitchenSpotStore()
    store.remove("never-seen", "also-never-seen")  # must not raise
