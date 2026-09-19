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


def tool_call(call_id: str, name: str, arguments: dict) -> dict:
    return {"id": call_id, "function": {"name": name, "parsed_arguments": arguments}}


async def test_direct_reply_with_no_tool_calls():
    client = FakeBackboardClient(script=[{"status": "COMPLETED", "content": "Right, get chopping."}])
    result = await handle_message(client, make_session(), CookMemory(), "what do I do first?")
    assert result["text"] == "Right, get chopping."
    assert result["tool_calls"] == []


async def test_tool_call_advances_step_and_loops_for_final_text():
    client = FakeBackboardClient(
        script=[
            {"status": "REQUIRES_ACTION", "tool_calls": [tool_call("call_1", "next_step", {})]},
            {"status": "COMPLETED", "content": "Done, onions are chopped, now simmer."},
        ]
    )
    session = make_session()
    result = await handle_message(client, session, CookMemory(), "next")
    assert session.step_index == 1
    assert "simmer" in result["text"].lower()
    assert result["tool_calls"][0]["name"] == "next_step"
    # second call must be submit_tool_outputs against the thread from the first response
    assert client.calls[1]["type"] == "submit_tool_outputs"


async def test_allergy_tool_call_persists_to_memory():
    client = FakeBackboardClient(
        script=[
            {"status": "REQUIRES_ACTION", "tool_calls": [tool_call("call_1", "remember_allergy", {"item": "peanuts"})]},
            {"status": "COMPLETED", "content": "Noted, no peanuts."},
        ]
    )
    memory = CookMemory()
    await handle_message(client, make_session(), memory, "I'm allergic to peanuts")
    assert "peanuts" in memory.allergies


async def test_scale_servings_tool_call():
    client = FakeBackboardClient(
        script=[
            {"status": "REQUIRES_ACTION", "tool_calls": [tool_call("call_1", "scale_servings", {"multiplier": 2})]},
            {"status": "COMPLETED", "content": "Doubled it."},
        ]
    )
    session = make_session()
    await handle_message(client, session, CookMemory(), "double it")
    assert "4 cups broth" in session.scaled_ingredients()[0]


async def test_thread_id_carries_across_the_conversation():
    client = FakeBackboardClient(script=[{"thread_id": "thread-abc", "status": "COMPLETED", "content": "Sure."}])
    session = make_session()
    await handle_message(client, session, CookMemory(), "hi")
    assert session.backboard_thread_id == "thread-abc"


async def test_stops_after_max_tool_rounds_to_avoid_infinite_loop():
    endless_call = {"status": "REQUIRES_ACTION", "tool_calls": [tool_call("call_x", "repeat_step", {})]}
    client = FakeBackboardClient(script=[endless_call] * 10)
    result = await handle_message(client, make_session(), CookMemory(), "repeat")
    # 1 send_message + MAX_TOOL_ROUNDS submit_tool_outputs calls
    assert len(client.calls) == 5
    assert result["text"]
