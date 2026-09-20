# Screenshot → Blender MVP

End-to-end prototype pipeline:

1. Analyze reference image into structured `scene_spec.json`
2. Generate deterministic Blender scene instructions
3. Run Blender render automatically (if Blender is installed)
4. Save reusable outputs in `output/`

## Run

```bash
python run_pipeline.py /absolute/path/to/reference.png
```

Optional flags:

```bash
python run_pipeline.py /absolute/path/to/reference.png --output output --width 1280 --height 720
```

## Output

`output/` contains:

- `scene_spec.json`
- `generated_scene.py`
- `scene.blend` (when Blender is available)
- `render.png` (when Blender is available)

If Blender is not installed, the pipeline still writes `scene_spec.json` and `generated_scene.py`.
You can then run Blender manually:

```bash
blender -b -P output/generated_scene.py -- output/scene_spec.json output/scene.blend output/render.png
```

## Notes

- Uses one structured scene-analysis path with deterministic fallback.
- Scene/object data is machine-readable and validated before generation.
- Object generation is deterministic and defaults to safe primitives when uncertain.
