# D-DOM MVP (Emergency Hackathon)

Public website URL -> deterministic extraction -> D-DOM JSON -> DESIGN.md -> visual HTML UI.

## Run

```bash
python run_pipeline.py https://example.com
```

Optional fidelity loop:

```bash
python run_pipeline.py https://example.com --clone-url https://example.org/clone
```

Optional output dir:

```bash
python run_pipeline.py https://example.com --output output
```

## Output

`output/` contains:

- `ddom.json` - source D-DOM schema v0.1
- `DESIGN.md` - concise human-readable design summary
- `ui.html` - visual result UI (open in browser)
- `clone_ddom.json` - only when `--clone-url` is passed
- `fidelity.json` - only when `--clone-url` is passed (score + mismatches)

## Notes

- No Blender dependency in this MVP flow.
- Extraction is deterministic and evidence-tagged.
- Raw website HTML is not sent to LLMs.
