from backend.chef.vision import check_cooking, identify_spot


class FakeVisionClient:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    async def analyze_image(self, image_bytes, filename, prompt):
        self.calls.append((image_bytes, filename, prompt))
        return {"content": self.content}


async def test_identify_spot_parses_clean_json():
    client = FakeVisionClient('{"label": "Stove", "confidence": "high"}')
    result = await identify_spot(client, b"fake-jpeg", "spot.jpg")
    assert result.label == "Stove"
    assert result.confidence == "high"


async def test_identify_spot_strips_markdown_fence():
    client = FakeVisionClient('```json\n{"label": "Sink", "confidence": "medium"}\n```')
    result = await identify_spot(client, b"bytes", "spot.jpg")
    assert result.label == "Sink"


async def test_identify_spot_falls_back_to_other_on_unknown_label():
    client = FakeVisionClient('{"label": "Toaster Oven", "confidence": "high"}')
    result = await identify_spot(client, b"bytes", "spot.jpg")
    assert result.label == "Other"


async def test_identify_spot_falls_back_to_low_confidence_on_bad_value():
    client = FakeVisionClient('{"label": "Stove", "confidence": "extremely sure"}')
    result = await identify_spot(client, b"bytes", "spot.jpg")
    assert result.confidence == "low"


async def test_identify_spot_handles_non_json_response():
    client = FakeVisionClient("that's clearly a stove")
    result = await identify_spot(client, b"bytes", "spot.jpg")
    assert result.label == "Other"
    assert result.confidence == "low"


async def test_check_cooking_parses_clean_json():
    client = FakeVisionClient('{"objects": ["spatula"], "stations": [{"vessel": "pan", "contents": ["eggs"], "doneness": "done", "matches_expected_step": true, "note": "Eggs are set, plate it up."}]}')
    result = await check_cooking(client, b"bytes", "dish.jpg", "shakshuka", "Cover and cook until eggs are set.")
    assert result.stations[0].doneness == "done"
    assert result.stations[0].matches_expected_step is True
    assert result.stations[0].note == "Eggs are set, plate it up."


async def test_check_cooking_prompt_includes_dish_and_step():
    client = FakeVisionClient('{"stations": []}')
    await check_cooking(client, b"bytes", "dish.jpg", "shakshuka", "Cover and cook until eggs are set.")
    prompt = client.calls[0][2]
    assert "shakshuka" in prompt
    assert "Cover and cook until eggs are set." in prompt


async def test_check_cooking_handles_non_json_response():
    client = FakeVisionClient("looks pretty done to me")
    result = await check_cooking(client, b"bytes", "dish.jpg", "shakshuka", "some step")
    assert result.stations == []
    assert result.objects == []
