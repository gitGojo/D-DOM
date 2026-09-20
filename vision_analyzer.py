from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from ddom_schema import fact, now_iso

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^\)]+\)|hsla?\([^\)]+\)")
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.I)
FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;}{]+)", re.I)
LINE_HEIGHT_RE = re.compile(r"line-height\s*:\s*([^;}{]+)", re.I)
SPACING_RE = re.compile(r"(?:margin|padding|gap|column-gap|row-gap)\s*:\s*([^;}{]+)", re.I)
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;}{]+)", re.I)
MEDIA_RE = re.compile(r"@media\s*([^\{]+)\{", re.I)
TRANSITION_RE = re.compile(r"(?:transition|animation)\s*:\s*([^;}{]+)", re.I)

COMMON_REGIONS = {"header", "nav", "main", "section", "article", "aside", "footer"}
ICON_CLASS_HINTS = ("icon", "fa", "material-icons", "mdi")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tag_counts: Counter[str] = Counter()
        self.class_counts: Counter[str] = Counter()
        self.inline_styles: List[str] = []
        self.stylesheets: List[str] = []
        self.style_blocks: List[str] = []
        self._in_style = False
        self._style_parts: List[str] = []
        self.interaction_counts: Counter[str] = Counter()
        self.svg_count = 0
        self.icon_class_hits: Counter[str] = Counter()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        t = tag.lower()
        self.tag_counts[t] += 1
        attrs_map = {k.lower(): (v or "") for k, v in attrs}

        if t == "style":
            self._in_style = True
            self._style_parts = []

        class_attr = attrs_map.get("class", "")
        if class_attr:
            for cls in class_attr.split():
                clean = cls.strip().lower()
                if clean:
                    self.class_counts[clean] += 1
                    if any(h in clean for h in ICON_CLASS_HINTS):
                        self.icon_class_hits[clean] += 1

        style_attr = attrs_map.get("style", "")
        if style_attr:
            self.inline_styles.append(style_attr)

        if t == "link":
            rel = attrs_map.get("rel", "").lower()
            href = attrs_map.get("href", "")
            if "stylesheet" in rel and href:
                self.stylesheets.append(href)

        if t == "svg":
            self.svg_count += 1

        if t in {"a", "button", "input", "select", "textarea"}:
            self.interaction_counts[t] += 1
        if attrs_map.get("onclick"):
            self.interaction_counts["onclick"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style" and self._in_style:
            self._in_style = False
            block = "".join(self._style_parts).strip()
            if block:
                self.style_blocks.append(block)
            self._style_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_parts.append(data)


def _fetch_text(url: str, timeout: int = 12) -> str:
    req = Request(url, headers={"User-Agent": "D-DOM-MVP/0.1"})
    with urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        if "text" not in content_type and "json" not in content_type and content_type:
            raise ValueError(f"Unsupported content type for extraction: {content_type}")
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def _normalize_css_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip('"\''))


def _top_counter_items(counter: Counter[str], limit: int = 12) -> List[Tuple[str, int]]:
    return [(k, v) for k, v in counter.most_common(limit) if k]


def _make_count_facts(items: List[Tuple[str, int]], key: str, origin: str, evidence: str = "SOURCE") -> List[Dict[str, Any]]:
    return [fact({key: value, "count": count}, evidence=evidence, origin=origin) for value, count in items]


def _fetch_stylesheet_texts(base_url: str, hrefs: List[str], warnings: List[str]) -> List[str]:
    texts: List[str] = []
    parsed_base = urlparse(base_url)

    for href in hrefs[:8]:
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc and parsed_base.netloc and parsed.netloc != parsed_base.netloc:
            continue
        try:
            texts.append(_fetch_text(full))
        except Exception as exc:  # pragma: no cover - network variability
            warnings.append(f"Could not fetch stylesheet {full}: {exc}")
    return texts


def analyze_url_to_ddom(url: str, viewport: Tuple[int, int] = (1440, 900)) -> Dict[str, Any]:
    warnings: List[str] = []
    try:
        html = _fetch_text(url)
    except Exception as exc:  # pragma: no cover - network variability
        warnings.append(f"Primary fetch failed for {url}: {exc}")
        html = ""

    parser = _PageParser()
    parser.feed(html)

    stylesheet_texts = _fetch_stylesheet_texts(url, parser.stylesheets, warnings)
    css_text = "\n".join(parser.style_blocks + stylesheet_texts + parser.inline_styles)

    color_counts = Counter(_normalize_css_value(x.lower()) for x in COLOR_RE.findall(css_text))

    typography_counter: Counter[str] = Counter()
    for pattern, name in (
        (FONT_FAMILY_RE, "font-family"),
        (FONT_SIZE_RE, "font-size"),
        (FONT_WEIGHT_RE, "font-weight"),
        (LINE_HEIGHT_RE, "line-height"),
    ):
        for match in pattern.findall(css_text):
            typography_counter[f"{name}: {_normalize_css_value(match)}"] += 1

    spacing_counts = Counter(_normalize_css_value(x) for x in SPACING_RE.findall(css_text))
    radius_counts = Counter(_normalize_css_value(x) for x in RADIUS_RE.findall(css_text))
    shadow_counts = Counter(_normalize_css_value(x) for x in SHADOW_RE.findall(css_text))

    media_counts = Counter(_normalize_css_value(x) for x in MEDIA_RE.findall(css_text))
    motion_counts = Counter(_normalize_css_value(x) for x in TRANSITION_RE.findall(css_text))

    regions = [(tag, parser.tag_counts[tag]) for tag in COMMON_REGIONS if parser.tag_counts[tag] > 0]
    regions.sort(key=lambda x: (-x[1], x[0]))

    repeated_components = [(cls, cnt) for cls, cnt in parser.class_counts.items() if cnt >= 2]
    repeated_components.sort(key=lambda x: (-x[1], x[0]))

    interactions = list(parser.interaction_counts.items())
    interactions.sort(key=lambda x: (-x[1], x[0]))

    icon_items: List[Tuple[str, int]] = []
    if parser.svg_count:
        icon_items.append(("svg-elements", parser.svg_count))
    icon_items.extend(parser.icon_class_hits.most_common(8))

    ddom = {
        "schemaVersion": "0.1",
        "source": {
            "kind": "website",
            "url": url,
            "capturedAt": now_iso(),
            "viewport": {"width": viewport[0], "height": viewport[1]},
        },
        "tokens": {
            "colors": _make_count_facts(_top_counter_items(color_counts), "token", "css"),
            "typography": _make_count_facts(_top_counter_items(typography_counter), "name", "css"),
            "spacing": _make_count_facts(_top_counter_items(spacing_counts), "token", "css"),
            "radii": _make_count_facts(_top_counter_items(radius_counts), "token", "css"),
            "shadows": _make_count_facts(_top_counter_items(shadow_counts), "token", "css"),
        },
        "structure": {
            "regions": _make_count_facts(regions[:12], "name", "html"),
            "components": _make_count_facts(repeated_components[:20], "name", "html-classes"),
        },
        "motion": _make_count_facts(_top_counter_items(motion_counts), "token", "css"),
        "interactions": _make_count_facts(interactions[:12], "name", "html"),
        "responsive": _make_count_facts(_top_counter_items(media_counts), "query", "css"),
        "icons": _make_count_facts(icon_items[:12], "name", "html"),
        "quality": {
            "extractor": "deterministic-source-parser",
            "htmlLength": len(html),
            "styleBlocks": len(parser.style_blocks),
            "stylesheetsFetched": len(stylesheet_texts),
            "classCount": sum(parser.class_counts.values()),
        },
        "warnings": warnings,
    }
    return ddom
