from backend.chef.brain import handle_message
from backend.chef.memory import CookMemory
from backend.chef.session import KitchenSession
from backend.models import Recipe
from backend.tests.fakes.fake_backboard import FakeBackboardClient


def make_session():
    recipe = Recipe(
        title="Test Soup",
        source_url="https://example.com",
        servings=4,
        ingredients=["2 cups broth", "1 onion", "3 carrots"],
        steps=["Chop the onion.", "Simmer for 10 minutes.", "Serve hot."],
    )
    return KitchenSession(recipe)


async def test_direct_reply_with_no_tool_calls():
    client = FakeBackboardClient(script=[{"text": "Right, get chopping.", "tool_calls": []}])
    result = await handle_message(client, make_session(), CookMemory(), "what do I do first?")
    assert result["text"] == "Right, get chopping."
    assert result["tool_calls"] == []


async def test_tool_call_advances_step_and_loops_for_final_text():
    client = FakeBackboardClient(
        script=[
            {"text": "", "tool_calls": [{"name": "next_step", "arguments": {}}]},
            {"text": "Done, onions are chopped, now simmer.", "tool_calls": []},
        ]
    )
    session = make_session()
    result = await handle_message(client, session, CookMemory(), "next")
    assert session.step_index == 1
    assert "simmer" in result["text"].lower()
    assert result["tool_calls"][0]["name"] == "next_step"


async def test_allergy_tool_call_persists_to_memory():
    client = FakeBackboardClient(
        script=[
            {"text": "", "tool_calls": [{"name": "remember_allergy", "arguments": {"item": "peanuts"}}]},
            {"text": "Noted, no peanuts.", "tool_calls": []},
        ]
    )
    memory = CookMemory()
    await handle_message(client, make_session(), memory, "I'm allergic to peanuts")
    assert "peanuts" in memory.allergies


async def test_scale_servings_tool_call():
    client = FakeBackboardClient(
        script=[
            {"text": "", "tool_calls": [{"name": "scale_servings", "arguments": {"multiplier": 2}}]},
            {"text": "Doubled it.", "tool_calls": []},
        ]
    )
    session = make_session()
    await handle_message(client, session, CookMemory(), "double it")
    assert "4 cups broth" in session.scaled_ingredients()[0]


async def test_stops_after_max_tool_rounds_to_avoid_infinite_loop():
    endless_call = {"text": "", "tool_calls": [{"name": "repeat_step", "arguments": {}}]}
    client = FakeBackboardClient(script=[endless_call] * 10)
    result = await handle_message(client, make_session(), CookMemory(), "repeat")
    assert len(client.calls) == 4  # MAX_TOOL_ROUNDS
    assert result["text"]
