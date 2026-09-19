from backend.chef.brain import handle_message
from backend.chef.memory import CookMemory
from backend.tests.test_chef_brain import make_session, tool_call
from backend.tests.fakes.fake_backboard import FakeBackboardClient


async def test_transcript_survives_tool_round():
    client = FakeBackboardClient([
        {'status': 'REQUIRES_ACTION', 'transcript': 'next step', 'tool_calls': [tool_call('1', 'next_step', {})]},
        {'status': 'COMPLETED', 'content': 'Now simmer.', 'audio_url': 'https://example.com/reply.mp3'},
    ])
    result = await handle_message(client, make_session(), CookMemory(), '', audio_input=b'fake')
    assert result['transcript'] == 'next step'
    assert result['audio_url'].endswith('.mp3')
