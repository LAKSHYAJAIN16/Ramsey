from backend.chef.fridge import suggest_dishes_from_photo


class FakeVisionClient:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    async def analyze_image(self, image_bytes, filename, prompt):
        self.calls.append((image_bytes, filename, prompt))
        return {"content": self.content}


async def test_parses_clean_json_response():
    client = FakeVisionClient('{"ingredients": ["eggs", "spinach", "feta"], "suggestions": ["Spinach frittata", "Greek scramble", "Spanakopita"]}')
    result = await suggest_dishes_from_photo(client, b"fake-jpeg-bytes", "fridge.jpg")
    assert result.ingredients == ["eggs", "spinach", "feta"]
    assert len(result.suggestions) == 3


async def test_strips_markdown_code_fence():
    client = FakeVisionClient('```json\n{"ingredients": ["milk"], "suggestions": ["Pancakes"]}\n```')
    result = await suggest_dishes_from_photo(client, b"bytes", "fridge.jpg")
    assert result.ingredients == ["milk"]
    assert result.suggestions == ["Pancakes"]


async def test_falls_back_to_line_split_on_bad_json():
    client = FakeVisionClient("- Spinach frittata\n- Greek scramble\n- Spanakopita\n")
    result = await suggest_dishes_from_photo(client, b"bytes", "fridge.jpg")
    assert result.ingredients == []
    assert result.suggestions == ["Spinach frittata", "Greek scramble", "Spanakopita"]


async def test_passes_image_bytes_and_filename_through():
    client = FakeVisionClient('{"ingredients": [], "suggestions": []}')
    await suggest_dishes_from_photo(client, b"raw-bytes", "myfridge.png")
    assert client.calls[0][0] == b"raw-bytes"
    assert client.calls[0][1] == "myfridge.png"


async def test_empty_response_yields_empty_suggestions_not_a_crash():
    client = FakeVisionClient("")
    result = await suggest_dishes_from_photo(client, b"bytes", "fridge.jpg")
    assert result.suggestions == []
