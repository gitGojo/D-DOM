from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_SPEC: Dict[str, Any] = {
    "scene": {
        "type": "unknown",
        "background": {"color": "#808080"},
        "camera": {
            "projection": "perspective",
            "position": [0.0, -6.0, 2.5],
            "rotation": [1.1, 0.0, 0.0],
            "fov_degrees": 50.0,
        },
        "lighting": {
            "key": {"position": [4.0, -4.0, 6.0], "energy": 700.0},
            "fill": {"position": [-4.0, -2.0, 3.0], "energy": 250.0},
            "back": {"position": [0.0, 4.0, 4.0], "energy": 200.0},
            "ambient_strength": 0.25,
        },
    },
    "objects": [],
    "relationships": [],
    "meta": {},
}


def _is_rgb_hex(value: str) -> bool:
    return isinstance(value, str) and len(value) == 7 and value.startswith("#") and all(
        c in "0123456789abcdefABCDEF" for c in value[1:]
    )


def _validate_object(obj: Dict[str, Any], idx: int) -> None:
    required = [
        "id",
        "class",
        "primitive",
        "bbox_2d",
        "position",
        "rotation",
        "scale",
        "material",
        "confidence",
        "evidence",
    ]
    for key in required:
        if key not in obj:
            raise ValueError(f"objects[{idx}] missing required field '{key}'")

    for key in ("bbox_2d", "position", "rotation", "scale"):
        if not isinstance(obj[key], list) or len(obj[key]) != (4 if key == "bbox_2d" else 3):
            raise ValueError(f"objects[{idx}].{key} must be a list of numeric values")

    material = obj["material"]
    if not isinstance(material, dict):
        raise ValueError(f"objects[{idx}].material must be an object")
    if "color" not in material or not _is_rgb_hex(material["color"]):
        raise ValueError(f"objects[{idx}].material.color must be #RRGGBB")

    confidence = obj["confidence"]
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        raise ValueError(f"objects[{idx}].confidence must be between 0 and 1")

    if obj["evidence"] not in {"VISUAL", "INFERRED"}:
        raise ValueError(f"objects[{idx}].evidence must be VISUAL or INFERRED")


def validate_scene_spec(spec: Dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise ValueError("scene spec must be an object")
    if "scene" not in spec or "objects" not in spec:
        raise ValueError("scene spec requires scene and objects fields")
    if not isinstance(spec["scene"], dict):
        raise ValueError("scene must be an object")
    if not isinstance(spec["objects"], list):
        raise ValueError("objects must be a list")

    for i, obj in enumerate(spec["objects"]):
        if not isinstance(obj, dict):
            raise ValueError(f"objects[{i}] must be an object")
        _validate_object(obj, i)


def load_scene_spec(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        spec = json.load(f)
    validate_scene_spec(spec)
    return spec


def save_scene_spec(path: str | Path, spec: Dict[str, Any]) -> None:
    validate_scene_spec(spec)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
