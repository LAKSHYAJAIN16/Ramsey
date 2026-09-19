from backend.chef.session import KitchenSession, detect_duration_seconds
from backend.models import Recipe


def make_recipe():
    return Recipe(
        title="Test Soup",
        source_url="https://example.com",
        servings=4,
        ingredients=["2 cups broth", "1 onion", "3 carrots"],
        steps=["Chop the onion.", "Simmer for 10 minutes.", "Serve hot."],
    )


def test_step_navigation_bounds():
    session = KitchenSession(make_recipe())
    assert session.current_step() == "Chop the onion."
    session.next_step()
    assert session.current_step() == "Simmer for 10 minutes."
    session.next_step()
    session.next_step()  # should not overflow past the last step
    assert session.current_step() == "Serve hot."
    session.back_step()
    assert session.current_step() == "Simmer for 10 minutes."


def test_duration_auto_detection():
    assert detect_duration_seconds("Simmer for 10 minutes.") == 600
    assert detect_duration_seconds("Bake for 1 hour.") == 3600
    assert detect_duration_seconds("Chop the onion.") is None


def test_start_timer_uses_detected_duration():
    session = KitchenSession(make_recipe())
    session.next_step()  # "Simmer for 10 minutes."
    timer = session.start_timer()
    assert timer.duration_seconds == 600
    assert timer in session.active_timers()


def test_scale_servings_scales_quantities():
    session = KitchenSession(make_recipe())
    session.scale_servings(2)
    scaled = session.scaled_ingredients()
    assert "4 cups broth" in scaled[0]
    assert "2 onion" in scaled[1]
    assert "6 carrots" in scaled[2]


def test_swap_ingredient():
    session = KitchenSession(make_recipe())
    session.swap_ingredient("broth", "water")
    assert any("water" in line for line in session.recipe.ingredients)
