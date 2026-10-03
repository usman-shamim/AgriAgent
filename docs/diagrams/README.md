# AgriAgent Diagrams

Mermaid sources plus everything derived from them: rendered SVG/PNG, and an interactive
zoom-and-pan gallery.

**`.mmd` is the source of truth.** `*.svg`, `*.png`, and `interactive.html` are generated —
edit the `.mmd` and re-run `./render.sh`. Never hand-edit a generated file.

## How to view

The fastest path is to **open the rendered `.svg`** — it scales without blurring, and GitHub
renders SVG files inline in its file viewer.

| Want | Do this |
| --- | --- |
| **Zoom and pan** | Open `interactive.html` in a browser. Scroll to zoom, drag to pan, double-click to zoom in, `+`/`-`/`0` on the keyboard. Fully offline — no CDN, no server. |
| See it in your IDE | Open the `.svg` (or `.png`). A `.mmd` file shows as plain text because it is source, not a rendering. |
| Live preview while editing | Paste the source into https://mermaid.live, or install a Mermaid preview extension for your IDE. |
| See it on GitHub | Open the `.svg` — GitHub renders it inline. A standalone `.mmd` does **not** render on GitHub. |
| Put it in the slide deck | Use the `.svg`. Fall back to `.png` only if the deck tool cannot take vector. |
| Edit and regenerate | Edit the `.mmd`, then run `./render.sh` |

All diagrams are also embedded as fenced ` ```mermaid ` blocks in the repository
[`README.md`](../../README.md), which is what GitHub and IDE Markdown previews render. The
build fails if any `.mmd` is not embedded there verbatim, so the two cannot drift apart.

Two caveats found the hard way:

- The `erDiagram` parser rejects `%%` comment lines, so `contract-erd` carries its notes here instead.
- The IDE registers each `.mmd` as a Mermaid diagram and writes a YAML frontmatter block holding only an `id:`. The build strips it before comparing against the README, so IDE metadata never breaks the sync check.

## The set

| File | Diagram | Shows |
| --- | --- | --- |
| `overview` | flowchart LR | The whole idea in one line: weather in, recipe computed, safety-gated, dispensed. This is the diagram for the top of the README. |
| `system-architecture` | flowchart TB | The system in layers: presentation → agent core → deterministic core → contract → MQTT → actuation. Red dashed = not built. |
| `agent-runtime` | sequenceDiagram | **How the agent works.** The full Runner loop, all three turns, every tool call, the conditional handoff, and the safety branch. Detailed — 9 lifelines. |
| `agent-runtime-slides` | sequenceDiagram | The same story compressed to 5 lifelines for stage readability. Use this one on the projector. |
| `agent-composition` | flowchart TB | Structure instead of sequence: agents → `@function_tool` wrappers → `_invoke_shared` → `TOOLS` registry → engines, with the MCP client and dashboard hanging off the same registry. Yellow = LLM, green = deterministic. |
| `dispatch-lifecycle` | sequenceDiagram | Data flow of one dispatch: request → safety gate → MQTT QoS 1 → twin validation → per-pump `tank_status` → events → dashboard. |
| `contract-erd` | erDiagram | The data model. |
| `safety-gate` | flowchart TD | The guardrail decision tree: envelope checks, the four recipe rules, the 30 s pump-cycle cap, and where each verdict exits. |

### Why the gallery uses Shadow DOM

mermaid-cli emits `id="my-svg"` and `color-N` ids in **every** file. Inlining all eight SVGs
into one page in the light DOM would make those ids collide, and one diagram's styles would
leak into another. `build.py` therefore hydrates each SVG inside its own Shadow DOM, which
scopes both ids and styles per diagram. Verified: all 8 sections render their SVG, each still
carrying its own `my-svg` id.

### Note on `contract-erd`

AgriAgent has **no database**, so this is not an ERD over tables. It is the data model of the
MQTT contract plus the engine outputs — the payloads every layer shares.

| Entity | Where it lives |
| --- | --- |
| `RecipeResult` | `src/mcp_server_scada.py` — frozen dataclass, engine output |
| `ChemicalRecipe`, `PumpCommand`, `SCADAPayload` | `src/twin/contracts.py` — the shared contract |
| `TwinState`, `DispatchEvent` | `src/twin/twin.py` — twin feedback and events |

Constraints the diagram cannot express:

- `PumpCommand.chemical_name` is one of `biopesticide` / `uv_stabilizer` / `surfactant` / `carrier_water`
- `PumpCommand.pump_id` is 1–4
- `DispatchEvent.code` is one of `SAFETY_REJECTED` / `INVALID_PAYLOAD` / `LOW_TANK` / `DISPATCH_COMPLETE`
- `PumpCommand` carries **no** `flow_rate_l_per_sec` — the twin is authoritative for runtimes and recomputes them from its own calibrated table

## Regenerating

```bash
./render.sh              # render SVG + PNG, rebuild interactive.html, verify the README embeds
./render.sh --no-render  # rebuild the gallery and the README check only (fast)
```

`render.sh` is a thin wrapper over `build.py`, which does three things:

1. Renders every `*.mmd` to `*.svg` and `*.png` via `@mermaid-js/mermaid-cli`.
2. Builds `interactive.html` from the rendered SVGs, each isolated in a Shadow DOM.
3. Verifies every `.mmd` is embedded verbatim in `README.md` and **exits non-zero if not**.

Requires Chromium on PATH, or set `PUPPETEER_EXECUTABLE_PATH`.

## Honest caveats

- The 9-lifeline `agent-runtime` diagram renders text small; it is the reference version, not the stage version.
- `system-architecture` marks the ESP32 rig as **not built** — the digital twin is the demo target and the firmware inherits the same contract later. Do not present the rig as existing.
- The physics in the twin is timed pump actuation plus tank depletion. It is not hydraulic simulation; do not describe it as fluid mechanics.
- `interactive.html` is ~1.7 MB because it inlines all eight SVGs. That is the price of being fully offline; it is not committed to the README's critical path.
