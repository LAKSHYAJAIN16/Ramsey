"""Deterministic recipe extraction from raw page HTML.

No AI involved: this is the fast path. It looks for schema.org Recipe
JSON-LD, which the overwhelming majority of recipe sites embed for SEO,
and falls back to nothing (the caller decides whether to try the
Stagehand browser path instead).
"""
import json
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from backend import config
from backend.models import Recipe

_JSON_LD_TYPE = re.compile(r"application/ld\+json", re.I)


def _iter_ld_json_blocks(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", attrs={"type": _JSON_LD_TYPE}):
        if not tag.string:
            continue
        try:
            yield json.loads(tag.string)
        except json.JSONDecodeError:
            continue


def _flatten_candidates(blob):
    """JSON-LD can be a dict, a list of dicts, or a dict with @graph."""
    if isinstance(blob, list):
        for item in blob:
            yield from _flatten_candidates(item)
    elif isinstance(blob, dict):
        if "@graph" in blob:
            yield from _flatten_candidates(blob["@graph"])
        else:
            yield blob


def _is_recipe_node(node: dict) -> bool:
    t = node.get("@type")
    if isinstance(t, list):
        return "Recipe" in t
    return t == "Recipe"


def _text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return _text(value.get("text", ""))
    return ""


def _normalize_instructions(raw) -> List[str]:
    steps: List[str] = []
    if raw is None:
        return steps
    if isinstance(raw, str):
        # Some sites just dump one big string; split on sentence-ish breaks.
        parts = [p.strip() for p in re.split(r"\n+", raw) if p.strip()]
        return parts or [raw.strip()]
    if isinstance(raw, dict):
        raw = [raw]
    for item in raw:
        if isinstance(item, str):
            text = item.strip()
            if text:
                steps.append(text)
        elif isinstance(item, dict):
            item_type = item.get("@type")
            if item_type == "HowToSection" and "itemListElement" in item:
                steps.extend(_normalize_instructions(item["itemListElement"]))
            else:
                text = _text(item)
                if text:
                    steps.append(text)
    return steps


def _normalize_servings(raw) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if raw is None:
        return None
    match = re.search(r"\d+", str(raw))
    return int(match.group()) if match else None


def parse_recipe_from_html(html: str, source_url: str) -> Optional[Recipe]:
    """Extract a Recipe from raw HTML, or None if nothing usable is found.

    Junk extractions (too few ingredients/steps) are rejected here so the
    caller can fall through to the browser path without extra checks.
    """
    for blob in _iter_ld_json_blocks(html):
        for node in _flatten_candidates(blob):
            if not _is_recipe_node(node):
                continue

            title = _text(node.get("name", "")) or "Untitled recipe"
            ingredients = [
                _text(i).strip() for i in node.get("recipeIngredient", []) if _text(i).strip()
            ]
            steps = _normalize_instructions(node.get("recipeInstructions"))
            servings = _normalize_servings(node.get("recipeYield"))

            if len(ingredients) < config.MIN_INGREDIENTS or len(steps) < config.MIN_STEPS:
                continue

            return Recipe(
                title=title,
                source_url=source_url,
                servings=servings,
                ingredients=ingredients,
                steps=steps,
                method="fast",
            )
    return None
