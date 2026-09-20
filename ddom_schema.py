from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

EVIDENCE_CONFIDENCE = {
    "SOURCE": 0.95,
    "RUNTIME": 0.9,
    "VISUAL": 0.85,
    "INFERRED": 0.6,
}

REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "source",
    "tokens",
    "structure",
    "motion",
    "interactions",
    "responsive",
    "icons",
    "quality",
    "warnings",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fact(value: Any, evidence: str, origin: str | None = None) -> Dict[str, Any]:
    if evidence not in EVIDENCE_CONFIDENCE:
        raise ValueError(f"Unsupported evidence source: {evidence}")
    out: Dict[str, Any] = {
        "value": value,
        "evidence": evidence,
        "confidence": EVIDENCE_CONFIDENCE[evidence],
    }
    if origin:
        out["origin"] = origin
    return out


def _validate_fact(item: Any, path: str) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"{path} must be an object")
    for key in ("value", "evidence", "confidence"):
        if key not in item:
            raise ValueError(f"{path} missing '{key}'")
    if item["evidence"] not in EVIDENCE_CONFIDENCE:
        raise ValueError(f"{path}.evidence invalid")
    conf = item["confidence"]
    if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
        raise ValueError(f"{path}.confidence must be 0..1")


def validate_ddom(ddom: Dict[str, Any]) -> None:
    if not isinstance(ddom, dict):
        raise ValueError("D-DOM must be an object")
    missing = REQUIRED_TOP_LEVEL - set(ddom.keys())
    if missing:
        raise ValueError(f"D-DOM missing keys: {sorted(missing)}")

    if ddom["schemaVersion"] != "0.1":
        raise ValueError("schemaVersion must be '0.1'")

    source = ddom["source"]
    if not isinstance(source, dict) or source.get("kind") != "website" or "url" not in source:
        raise ValueError("source must contain kind=website and url")

    tokens = ddom["tokens"]
    if not isinstance(tokens, dict):
        raise ValueError("tokens must be an object")
    for key in ("colors", "typography", "spacing", "radii", "shadows"):
        arr = tokens.get(key)
        if not isinstance(arr, list):
            raise ValueError(f"tokens.{key} must be a list")
        for i, item in enumerate(arr):
            _validate_fact(item, f"tokens.{key}[{i}]")

    structure = ddom["structure"]
    if not isinstance(structure, dict):
        raise ValueError("structure must be an object")
    for key in ("regions", "components"):
        arr = structure.get(key)
        if not isinstance(arr, list):
            raise ValueError(f"structure.{key} must be a list")
        for i, item in enumerate(arr):
            _validate_fact(item, f"structure.{key}[{i}]")

    for key in ("motion", "interactions", "responsive", "icons"):
        arr = ddom[key]
        if not isinstance(arr, list):
            raise ValueError(f"{key} must be a list")
        for i, item in enumerate(arr):
            _validate_fact(item, f"{key}[{i}]")

    if not isinstance(ddom["quality"], dict):
        raise ValueError("quality must be an object")
    if not isinstance(ddom["warnings"], list):
        raise ValueError("warnings must be a list")


def save_ddom(path: str | Path, ddom: Dict[str, Any]) -> None:
    validate_ddom(ddom)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ddom, indent=2), encoding="utf-8")


def _token_rows(facts: Iterable[Dict[str, Any]], key: str = "token") -> List[str]:
    rows: List[str] = []
    for item in facts:
        value = item.get("value")
        if isinstance(value, dict):
            label = value.get(key, value)
            usage = value.get("count")
            rows.append(f"- {label} (count: {usage}, {item['evidence']}, conf {item['confidence']})")
        else:
            rows.append(f"- {value} ({item['evidence']}, conf {item['confidence']})")
    return rows


def generate_design_markdown(ddom: Dict[str, Any]) -> str:
    validate_ddom(ddom)

    colors = _token_rows(ddom["tokens"]["colors"])
    typography = _token_rows(ddom["tokens"]["typography"], key="name")
    spacing = _token_rows(ddom["tokens"]["spacing"])
    radii = _token_rows(ddom["tokens"]["radii"])
    shadows = _token_rows(ddom["tokens"]["shadows"])

    sections = [
        "# DESIGN.md",
        "",
        "## Design System",
        f"- Source URL: {ddom['source']['url']}",
        f"- Captured At: {ddom['source']['capturedAt']}",
        f"- Viewport: {ddom['source']['viewport']['width']}x{ddom['source']['viewport']['height']}",
        "",
        "## Evidence",
        "- SOURCE: parsed from HTML/CSS/source metadata.",
        "- RUNTIME: measured from runtime/browser behavior.",
        "- VISUAL: measured from visual rendering or screenshots.",
        "- INFERRED: deterministic fallback inference when direct evidence is unavailable.",
        "",
        "## Colors",
        *(colors or ["- None detected"]),
        "",
        "## Typography",
        *(typography or ["- None detected"]),
        "",
        "## Spacing",
        *(spacing or ["- None detected"]),
        "",
        "## Radius",
        *(radii or ["- None detected"]),
        "",
        "## Shadows",
        *(shadows or ["- None detected"]),
        "",
        "## Structure",
        "### Regions",
        *(_token_rows(ddom["structure"]["regions"]) or ["- None detected"]),
        "### Components",
        *(_token_rows(ddom["structure"]["components"], key="name") or ["- None detected"]),
        "",
        "## Motion & Interactions",
        "### Motion",
        *(_token_rows(ddom["motion"]) or ["- None detected"]),
        "### Interactions",
        *(_token_rows(ddom["interactions"]) or ["- None detected"]),
        "",
        "## Responsive",
        *(_token_rows(ddom["responsive"]) or ["- None detected"]),
        "",
        "## Icons",
        *(_token_rows(ddom["icons"]) or ["- None detected"]),
        "",
        "## Warnings",
        *([f"- {w}" for w in ddom["warnings"]] or ["- None"]),
    ]
    return "\n".join(sections) + "\n"


def _values_set(items: Iterable[Dict[str, Any]], key: str) -> set[str]:
    values: set[str] = set()
    for item in items:
        v = item.get("value")
        if isinstance(v, dict):
            v = v.get(key)
        if isinstance(v, str):
            values.add(v.strip().lower())
    return values


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def compare_ddom(source: Dict[str, Any], clone: Dict[str, Any]) -> Dict[str, Any]:
    validate_ddom(source)
    validate_ddom(clone)

    source_colors = _values_set(source["tokens"]["colors"], "token")
    clone_colors = _values_set(clone["tokens"]["colors"], "token")

    source_fonts = _values_set(source["tokens"]["typography"], "name")
    clone_fonts = _values_set(clone["tokens"]["typography"], "name")

    source_components = _values_set(source["structure"]["components"], "name")
    clone_components = _values_set(clone["structure"]["components"], "name")

    color_score = _jaccard(source_colors, clone_colors)
    font_score = _jaccard(source_fonts, clone_fonts)
    component_score = _jaccard(source_components, clone_components)

    weighted = (color_score * 0.5) + (font_score * 0.2) + (component_score * 0.3)
    score = round(weighted * 100, 2)

    mismatches: List[str] = []
    if color_score < 1.0:
        missing = sorted(source_colors - clone_colors)
        extra = sorted(clone_colors - source_colors)
        if missing:
            mismatches.append(f"Missing colors in clone: {missing[:8]}")
        if extra:
            mismatches.append(f"Extra colors in clone: {extra[:8]}")

    if font_score < 1.0:
        missing = sorted(source_fonts - clone_fonts)
        if missing:
            mismatches.append(f"Missing font families in clone: {missing[:8]}")

    if component_score < 1.0:
        missing = sorted(source_components - clone_components)
        if missing:
            mismatches.append(f"Missing repeated component classes in clone: {missing[:8]}")

    return {
        "score": score,
        "mismatches": mismatches,
        "detail": {
            "color_similarity": round(color_score, 4),
            "font_similarity": round(font_score, 4),
            "component_similarity": round(component_score, 4),
        },
        "capturedAt": now_iso(),
    }
