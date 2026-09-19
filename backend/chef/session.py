"""Server-side kitchen state that both the chef's tool calls and the
headset's Back/Timer/Next buttons mutate. Keeping this on the server
(not just in the frontend) is what lets voice commands and button
presses stay in sync.
"""
import re
import time
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional

from backend.models import Recipe

_QUANTITY_RE = re.compile(r"(\d+\s*\d*/\d+|\d+\.\d+|\d+)")
_DURATION_RE = re.compile(r"(\d+)\s*(?:-|to)?\s*(\d+)?\s*(minute|min|hour|hr)s?", re.I)


@dataclass
class Timer:
    label: str
    duration_seconds: int
    started_at: float = field(default_factory=time.time)

    @property
    def remaining_seconds(self) -> int:
        elapsed = time.time() - self.started_at
        return max(0, int(self.duration_seconds - elapsed))

    @property
    def done(self) -> bool:
        return self.remaining_seconds <= 0


class KitchenSession:
    """One cook's in-progress recipe: current step, servings, timers."""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.step_index = 0
        self.servings_multiplier = Fraction(1)
        self.checked_ingredients: set[int] = set()
        self.timers: List[Timer] = []

    # --- navigation -----------------------------------------------------
    def next_step(self) -> str:
        if self.step_index < len(self.recipe.steps) - 1:
            self.step_index += 1
        return self.current_step()

    def back_step(self) -> str:
        if self.step_index > 0:
            self.step_index -= 1
        return self.current_step()

    def current_step(self) -> str:
        return self.recipe.steps[self.step_index]

    def repeat_step(self) -> str:
        return self.current_step()

    # --- ingredients ------------------------------------------------------
    def toggle_ingredient(self, index: int) -> None:
        if index in self.checked_ingredients:
            self.checked_ingredients.remove(index)
        else:
            self.checked_ingredients.add(index)

    def read_ingredients(self) -> List[str]:
        return self.scaled_ingredients()

    def scaled_ingredients(self) -> List[str]:
        if self.servings_multiplier == 1:
            return self.recipe.ingredients
        return [_scale_ingredient_line(line, self.servings_multiplier) for line in self.recipe.ingredients]

    # --- edits by voice ---------------------------------------------------
    def scale_servings(self, multiplier: float) -> None:
        self.servings_multiplier = Fraction(multiplier).limit_denominator(8)

    def swap_ingredient(self, original: str, replacement: str) -> None:
        pattern = re.compile(re.escape(original), re.I)
        for i, line in enumerate(self.recipe.ingredients):
            if pattern.search(line):
                self.recipe.ingredients[i] = pattern.sub(replacement, line, count=1)
                return

    # --- timers -------------------------------------------------------------
    def start_timer(self, label: Optional[str] = None, duration_seconds: Optional[int] = None) -> Timer:
        if duration_seconds is None:
            duration_seconds = detect_duration_seconds(self.current_step()) or 300
        timer = Timer(label=label or f"Step {self.step_index + 1}", duration_seconds=duration_seconds)
        self.timers.append(timer)
        return timer

    def active_timers(self) -> List[Timer]:
        return [t for t in self.timers if not t.done]

    def to_state_dict(self) -> Dict:
        return {
            "title": self.recipe.title,
            "step_index": self.step_index,
            "total_steps": len(self.recipe.steps),
            "current_step": self.current_step(),
            "ingredients": self.scaled_ingredients(),
            "checked_ingredients": sorted(self.checked_ingredients),
            "servings_multiplier": float(self.servings_multiplier),
            "timers": [
                {"label": t.label, "remaining_seconds": t.remaining_seconds} for t in self.active_timers()
            ],
        }


def detect_duration_seconds(step_text: str) -> Optional[int]:
    """Auto-detect a duration in a step like 'simmer for 10 minutes'."""
    match = _DURATION_RE.search(step_text)
    if not match:
        return None
    low, high, unit = match.groups()
    value = int(high) if high else int(low)
    if unit.lower().startswith("h"):
        return value * 3600
    return value * 60


def _scale_ingredient_line(line: str, multiplier: Fraction) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(1).strip()
        if "/" in raw and " " in raw:
            whole, frac = raw.split(" ", 1)
            qty = Fraction(int(whole)) + Fraction(frac)
        elif "/" in raw:
            qty = Fraction(raw)
        else:
            qty = Fraction(raw)
        scaled = qty * multiplier
        return _format_fraction(scaled)

    return _QUANTITY_RE.sub(repl, line, count=1)


def _format_fraction(value: Fraction) -> str:
    whole, remainder = divmod(value.numerator, value.denominator)
    if remainder == 0:
        return str(whole)
    frac_part = Fraction(remainder, value.denominator)
    return f"{whole} {frac_part}" if whole else str(frac_part)
