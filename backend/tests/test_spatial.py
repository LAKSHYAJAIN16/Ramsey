import pytest
from backend.chef.spatial import parse_equipment


def box(**updates):
    return dict(label='Bowl', confidence=.95, x=.1, y=.2, width=.3, height=.4, **updates)


def test_valid_image_box_has_no_invented_world_coordinates():
    result = parse_equipment([box()])
    assert result[0]['label'] == 'bowl'
    assert set(result[0]) == {'label', 'confidence', 'x', 'y', 'width', 'height'}


@pytest.mark.parametrize('update', [dict(x=.9), dict(y=-.1), dict(width=0.),
    dict(confidence=.7), dict(label='<b>bowl</b>'), dict(x=float('nan')), dict(depth=2.), dict(x='0.1')])
def test_unusable_detections_are_dropped(update):
    item = box()
    item.update(update)
    assert parse_equipment([item]) == []


def test_malformed_or_excess_detections():
    assert parse_equipment(None) == []
    assert parse_equipment({'label': 'bowl'}) == []
    assert len(parse_equipment([None, box(), 'bad'])) == 1
    assert len(parse_equipment([box()] * 30)) == 12


async def test_assistance_returns_boxes_without_requiring_them():
    from backend.tests.test_step_assist import Camera, session
    from backend.chef.step_assist import assess_frame
    result = await assess_frame(Camera(equipment=[box(), {'bad': 'box'}]), session(), b'frame', 'f.jpg')
    assert len(result['equipment']) == 1
    assert not result['advanced']
    legacy = await assess_frame(Camera(), session(), b'other', 'f.jpg')
    assert legacy['equipment'] == []
