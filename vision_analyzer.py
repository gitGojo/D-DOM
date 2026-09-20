from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

from scene_spec import DEFAULT_SPEC


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _dominant_color(image: Image.Image) -> tuple[int, int, int]:
    reduced = image.convert("RGB").resize((64, 64))
    palette = reduced.convert("P", palette=Image.Palette.ADAPTIVE, colors=5)
    palette_colors = palette.getpalette()
    color_counts = sorted(palette.getcolors(), reverse=True)
    if not color_counts:
        return (128, 128, 128)
    _, palette_index = color_counts[0]
    base = palette_index * 3
    return tuple(palette_colors[base : base + 3])  # type: ignore[return-value]


def _estimate_scene_type(width: int, height: int) -> str:
    ratio = width / max(height, 1)
    if 1.2 <= ratio <= 2.2:
        return "room"
    if 0.85 <= ratio <= 1.15:
        return "product"
    return "object"


def _build_fallback_spec(image_path: Path) -> Dict[str, Any]:
    with Image.open(image_path) as img:
        width, height = img.size
        dom = _dominant_color(img)

    object_color = _rgb_to_hex(tuple(max(20, c - 35) for c in dom))
    background_color = _rgb_to_hex(tuple(min(240, c + 25) for c in dom))

    spec = {
        **DEFAULT_SPEC,
        "scene": {
            **DEFAULT_SPEC["scene"],
            "type": _estimate_scene_type(width, height),
            "background": {
                "mode": "solid",
                "color": background_color,
                "image_dimensions": [width, height],
            },
        },
        "objects": [
            {
                "id": "object_01",
                "class": "subject",
                "primitive": "cube",
                "bbox_2d": [0.30, 0.20, 0.40, 0.65],
                "position": [0.0, 0.0, 0.55],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.2, 0.8, 1.1],
                "material": {"color": object_color, "roughness": 0.6, "metallic": 0.0},
                "confidence": 0.55,
                "evidence": "INFERRED",
            }
        ],
        "relationships": [],
        "meta": {
            "analyzer": "deterministic-fallback",
            "single_call_budget": 1,
            "reference_image": str(image_path),
        },
    }
    return spec


def analyze_image_to_scene_spec(
    image_path: str | Path,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Uses one structured analysis path (deterministic fallback by default).
    If OPENAI_API_KEY + OPENAI_VISION_MODEL are present, this module can be extended
    to call a remote vision model once and return the same schema.
    """
    _ = model or os.getenv("OPENAI_VISION_MODEL")
    return _build_fallback_spec(Path(image_path))
