"""Validated image locations. Depth and world coordinates are measured on Quest."""
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class EquipmentDetection(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', allow_inf_nan=False)
    label: str = Field(min_length=1, max_length=48)
    confidence: float = Field(ge=0, le=1)
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)

    @model_validator(mode='after')
    def valid_box(self):
        self.label = self.label.strip().lower()
        if not self.label or any(c in self.label for c in '<>\n\r'):
            raise ValueError('Plain-text label required')
        if self.x + self.width > 1.000001 or self.y + self.height > 1.000001:
            raise ValueError('Box outside image')
        return self


SPATIAL_PROMPT = (
    ' Also return equipment as an array of at most 12 visible cooking objects: bowls, pans, '
    'plates, cutting boards, presses and appliances. Each entry has ONLY label (short plain noun), '
    'confidence (0..1), x,y,width,height. Boxes are normalized to the full supplied image, '
    'origin TOP LEFT, x rightward and y downward. Bound the visible object tightly; do not '
    'label people, hands, drawings or reflections. Omit occluded or uncertain objects. '
    'Do not infer depth, metres or world coordinates. Return equipment:[] if none are clear.'
)


def parse_equipment(raw):
    if not isinstance(raw, list):
        return []
    result = []
    for entry in raw[:12]:
        try:
            item = EquipmentDetection.model_validate(entry)
        except (ValidationError, TypeError):
            continue
        if item.confidence >= .8:
            result.append(item.model_dump())
    return result
