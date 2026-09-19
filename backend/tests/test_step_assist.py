import json
import pytest
from backend.chef import step_assist
from backend.chef.session import KitchenSession
from backend.models import Recipe


def session(steps=None):
    return KitchenSession(Recipe(title='Sandwich', source_url='', ingredients=['bread', 'cheese'], steps=steps or ['Spread bread', 'Add cheese']))


class Camera:
    def __init__(self, **changes):
        self.data = dict(visible=True, step_complete=True, confidence=.96, evidence='Spread covers the bread.', requires_confirmation=False, hazard='none', help='', plating_tips=['Wipe the plate rim.'])
        self.data.update(changes)
    async def analyze_image(self, image, filename, prompt):
        return {'content': json.dumps(self.data)}


async def test_two_fresh_observations_advance_once(monkeypatch):
    clock = [10.0]; monkeypatch.setattr(step_assist.time, 'monotonic', lambda: clock[0])
    cook = session()
    assert not (await step_assist.assess_frame(Camera(), cook, b'frame1', 'f.jpg'))['advanced']
    clock[0] += 4
    assert not (await step_assist.assess_frame(Camera(), cook, b'frame1', 'f.jpg'))['advanced']
    assert (await step_assist.assess_frame(Camera(), cook, b'frame2', 'f.jpg'))['advanced']
    assert cook.step_index == 1 and cook.completion_votes == 0


@pytest.mark.parametrize('changes', [dict(visible=False), dict(confidence=.5), dict(hazard='burning'), dict(requires_confirmation=True), dict(step_complete=False), dict(evidence='')])
async def test_ambiguous_or_unsafe_frames_never_advance(monkeypatch, changes):
    clock = [10.0]; monkeypatch.setattr(step_assist.time, 'monotonic', lambda: clock[0])
    cook = session()
    await step_assist.assess_frame(Camera(**changes), cook, b'1', 'f.jpg')
    clock[0] += 4
    result = await step_assist.assess_frame(Camera(**changes), cook, b'2', 'f.jpg')
    assert not result['advanced'] and cook.step_index == 0


async def test_late_frame_does_not_apply_after_navigation():
    cook = session()
    class LateCamera(Camera):
        async def analyze_image(self, *args):
            cook.next_step(); cook.back_step()
            return await super().analyze_image(*args)
    result = await step_assist.assess_frame(LateCamera(), cook, b'1', 'f.jpg')
    assert not result['advanced'] and cook.completion_votes == 0


async def test_plating_feedback_and_final_points_are_idempotent(monkeypatch):
    clock = [10.0]; monkeypatch.setattr(step_assist.time, 'monotonic', lambda: clock[0])
    cook = session(['Arrange the sandwich on the plate'])
    result = await step_assist.assess_frame(Camera(), cook, b'1', 'f.jpg', True)
    assert result['observation']['plating_tips'] == ['Wipe the plate rim.']
    clock[0] += 4
    await step_assist.assess_frame(Camera(), cook, b'2', 'f.jpg', True)
    assert cook.completed and cook.points == 20
    cook.complete(); assert cook.points == 20


@pytest.mark.parametrize('step', ['Wait for 10 minutes', 'Check internal temperature', 'Taste the sauce'])
async def test_nonvisual_steps_require_manual_confirmation(step):
    cook = session([step, 'Serve'])
    await step_assist.assess_frame(Camera(), cook, b'1', 'f.jpg')
    assert cook.completion_votes == 0
