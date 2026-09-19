import httpx
import pytest

from backend.chef import backboard_client


def test_nested_voice_records_preserve_transcript_and_reply_audio():
    normalized = backboard_client.BackboardClient._normalize({'messages': [
        {'role': 'user', 'voice_records': {'stt': {'transcript': 'What comes next?'}}},
        {'role': 'assistant', 'content': 'Add the cheese.', 'voice_records': {'tts': {'audio_url': 'https://example.com/reply.mp3'}}},
    ]})
    assert normalized['transcript'] == 'What comes next?'
    assert normalized['content'] == 'Add the cheese.'
    assert normalized['audio_url'].endswith('reply.mp3')


@pytest.mark.parametrize("audio,filename,mime", [
    (b"RIFF\x10\x00\x00\x00WAVEfmt sample", "utterance.wav", "audio/wav"),
    (b"\x1a\x45\xdf\xa3webm sample", "utterance.webm", "audio/webm"),
])
async def test_voice_upload_preserves_quest_and_browser_audio_formats(monkeypatch, audio, filename, mime):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"content": "Hello", "status": "COMPLETED"})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(backboard_client.httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    client = backboard_client.BackboardClient("fake-key", "test-model")
    reply = await client.send_message("", audio_input=audio)
    assert reply["content"] == "Hello"
    body = requests[0].content
    assert f'filename="{filename}"'.encode() in body
    assert f"Content-Type: {mime}".encode() in body
    assert audio in body
