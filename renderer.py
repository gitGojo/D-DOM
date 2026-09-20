from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def generate_blender_runner_script(output_script_path: Path) -> None:
    script = """\
import os
import sys

argv = sys.argv
if '--' in argv:
    argv = argv[argv.index('--') + 1:]

if len(argv) < 3:
    raise SystemExit('Usage: blender -b -P generated_scene.py -- <spec> <blend> <render> [width] [height]')

spec, blend, render = argv[0], argv[1], argv[2]
width = int(argv[3]) if len(argv) > 3 else 1024
height = int(argv[4]) if len(argv) > 4 else 768

repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from blender_generator import generate_scene

generate_scene(Path(spec), Path(blend), Path(render), width, height)
"""
    # Avoid importing pathlib in blender preamble repeatedly.
    script = "from pathlib import Path\n" + script
    output_script_path.write_text(script, encoding="utf-8")


def run_blender(
    blender_script_path: Path,
    spec_path: Path,
    blend_path: Path,
    render_path: Path,
    width: int = 1024,
    height: int = 768,
) -> bool:
    blender_bin = shutil.which("blender")
    if not blender_bin:
        return False

    cmd = [
        blender_bin,
        "-b",
        "-P",
        str(blender_script_path),
        "--",
        str(spec_path),
        str(blend_path),
        str(render_path),
        str(width),
        str(height),
    ]
    subprocess.run(cmd, check=True)
    return True


def run_or_prepare(
    output_dir: Path,
    spec_path: Path,
    width: int = 1024,
    height: int = 768,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    blend_path = output_dir / "scene.blend"
    render_path = output_dir / "render.png"
    blender_script_path = output_dir / "generated_scene.py"

    generate_blender_runner_script(blender_script_path)

    blender_executed = run_blender(blender_script_path, spec_path, blend_path, render_path, width, height)
    return {
        "blender_executed": blender_executed,
        "blender_script": str(blender_script_path),
        "blend_file": str(blend_path),
        "render_file": str(render_path),
    }
