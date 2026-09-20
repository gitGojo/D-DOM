from __future__ import annotations

import argparse
from pathlib import Path

from renderer import run_or_prepare
from scene_spec import save_scene_spec, validate_scene_spec
from vision_analyzer import analyze_image_to_scene_spec


def run_pipeline(reference_image: Path, output_dir: Path, width: int = 1024, height: int = 768) -> dict:
    print("Analyzing scene...")
    spec = analyze_image_to_scene_spec(reference_image)
    validate_scene_spec(spec)

    output_dir.mkdir(parents=True, exist_ok=True)
    spec_path = output_dir / "scene_spec.json"
    save_scene_spec(spec_path, spec)

    print("Generating Blender scene...")
    render_info = run_or_prepare(output_dir, spec_path, width=width, height=height)

    if render_info["blender_executed"]:
        print("Blender scene created and render completed.")
    else:
        print("Blender not found. Generated script and spec are ready for manual Blender execution.")

    return {
        "scene_spec": str(spec_path),
        **render_info,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Screenshot -> Blender MVP pipeline")
    parser.add_argument("reference_image", help="Path to reference image")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reference_image = Path(args.reference_image).resolve()
    if not reference_image.exists():
        raise SystemExit(f"Reference image not found: {reference_image}")

    output_dir = Path(args.output).resolve()
    result = run_pipeline(reference_image, output_dir, width=args.width, height=args.height)

    print("Done")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
