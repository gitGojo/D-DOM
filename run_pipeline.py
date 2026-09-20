from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any, Dict, Optional

from ddom_schema import compare_ddom, generate_design_markdown, save_ddom, validate_ddom
from vision_analyzer import analyze_url_to_ddom


def _render_list(items: list[Dict[str, Any]], key: str = "token") -> str:
    rows = []
    for item in items[:12]:
        value = item.get("value")
        if isinstance(value, dict):
            label = value.get(key) or value.get("name") or value
            count = value.get("count", "")
            rows.append(f"<li><code>{escape(str(label))}</code> <small>count: {escape(str(count))}</small></li>")
        else:
            rows.append(f"<li><code>{escape(str(value))}</code></li>")
    return "".join(rows) or "<li>None</li>"


def build_ui_html(source_ddom: Dict[str, Any], fidelity: Optional[Dict[str, Any]] = None, clone_url: Optional[str] = None) -> str:
    source_url = source_ddom["source"]["url"]
    score_html = ""
    mismatch_html = ""
    clone_frame = ""

    if fidelity:
        score_html = f"<h2>Fidelity Score: {fidelity['score']}</h2>"
        mismatch_items = "".join(f"<li>{escape(m)}</li>" for m in fidelity["mismatches"]) or "<li>No mismatches</li>"
        mismatch_html = f"<h3>Mismatches</h3><ul>{mismatch_items}</ul>"
    if clone_url:
        clone_frame = (
            "<div><h3>Clone URL</h3>"
            f"<iframe src='{escape(clone_url)}' title='clone-url'></iframe></div>"
        )

    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width,initial-scale=1' />
  <title>D-DOM MVP Result</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #1f2937; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    iframe {{ width: 100%; min-height: 420px; border: 1px solid #ddd; border-radius: 8px; }}
    section {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px 14px; margin: 10px 0; }}
    h1,h2,h3 {{ margin: 8px 0; }}
    code {{ background:#f3f4f6; padding:1px 4px; border-radius:4px; }}
    pre {{ max-height: 320px; overflow: auto; background:#111827; color:#e5e7eb; padding:10px; border-radius:8px; }}
  </style>
</head>
<body>
  <h1>D-DOM MVP</h1>
  <p>Source: <a href='{escape(source_url)}' target='_blank' rel='noreferrer'>{escape(source_url)}</a></p>
  {score_html}
  {mismatch_html}
  <div class='row'>
    <div><h3>Source URL</h3><iframe src='{escape(source_url)}' title='source-url'></iframe></div>
    {clone_frame}
  </div>
  <section>
    <h3>Colors</h3>
    <ul>{_render_list(source_ddom['tokens']['colors'])}</ul>
  </section>
  <section>
    <h3>Typography</h3>
    <ul>{_render_list(source_ddom['tokens']['typography'], 'name')}</ul>
  </section>
  <section>
    <h3>Structure Regions</h3>
    <ul>{_render_list(source_ddom['structure']['regions'], 'name')}</ul>
  </section>
  <section>
    <h3>Repeated Components</h3>
    <ul>{_render_list(source_ddom['structure']['components'], 'name')}</ul>
  </section>
  <section>
    <h3>D-DOM JSON</h3>
    <pre>{escape(json.dumps(source_ddom, indent=2))}</pre>
  </section>
</body>
</html>
"""


def run_pipeline(url: str, output_dir: Path, clone_url: Optional[str] = None) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_ddom = analyze_url_to_ddom(url)
    validate_ddom(source_ddom)

    ddom_path = output_dir / "ddom.json"
    save_ddom(ddom_path, source_ddom)

    design_md = generate_design_markdown(source_ddom)
    design_path = output_dir / "DESIGN.md"
    design_path.write_text(design_md, encoding="utf-8")

    result: Dict[str, Any] = {
        "source_ddom": source_ddom,
        "ddom_json": str(ddom_path),
        "design_md": str(design_path),
    }

    fidelity = None
    if clone_url:
        clone_ddom = analyze_url_to_ddom(clone_url)
        validate_ddom(clone_ddom)
        clone_ddom_path = output_dir / "clone_ddom.json"
        save_ddom(clone_ddom_path, clone_ddom)
        fidelity = compare_ddom(source_ddom, clone_ddom)
        fidelity_path = output_dir / "fidelity.json"
        fidelity_path.write_text(json.dumps(fidelity, indent=2), encoding="utf-8")
        result.update(
            {
                "clone_ddom": str(clone_ddom_path),
                "fidelity": str(fidelity_path),
            }
        )

    ui_path = output_dir / "ui.html"
    ui_path.write_text(build_ui_html(source_ddom, fidelity=fidelity, clone_url=clone_url), encoding="utf-8")
    result["ui_html"] = str(ui_path)

    return {k: str(v) for k, v in result.items() if k != "source_ddom"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="URL -> D-DOM MVP pipeline")
    parser.add_argument("url", help="Public website URL to analyze")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--clone-url", default=None, help="Optional clone URL for fidelity comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output).resolve()

    result = run_pipeline(args.url, output_dir, clone_url=args.clone_url)
    print("Done")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
