# MVP Build Spec — Runnable Demoable AgriAgent

The single buildable feature spec for the hackathon MVP. It fixes the locked decisions from the wayfinder map into acceptance criteria an agent can verify against. Derived from `specs/scope/hackthon-scope.md` (the what) and `specs/design/design-and-implementation.md` (the how), per the `/create-spec` discipline.

All volumes are SI litres (L); pump flows are L/s.

## Goal

Build a runnable, demoable AgriAgent MVP for the hackathon: the four-agent pipeline (Perception → Formulation → Safety → Actuator) computes a deterministic biopesticide recipe from live environmental telemetry (UV index, temperature, relative humidity), dispatches it as a strict JSON payload over a local Mosquitto MQTT broker, and the digital twin simulates the pump dispensing the exact volume — with a Streamlit dashboard showing the live state. Reproducible from a single README and one-command setup.

## User scenarios

- **An operator starts the system** and sees the Perception Agent pull live telemetry (UV 9.2, temp 38°C, RH 32%) for a zone, computing the degradation half-life.
- **The Formulation Agent** turns the telemetry into a 0.5 L recipe: biopesticide 0.04 L, UV stabilizer 0.01275 L, surfactant ~0.0005 L, carrier water balancing to 0.5 L.
- **The Safety Agent** validates the recipe (surfactant ≤ 0.20%, lignin ≤ 3.00%, volumes sum to batch) and either approves or rejects it with a machine-readable violation.
- **The SCADA Agent** maps the approved recipe to pump runtimes (0.01/0.01/0.01/0.05 L/s) and publishes the payload to `agri/actuator/{zone}/dosing_dispatch` at QoS 1.
- **The digital twin** subscribes, validates the payload against the contract, simulates the pumps dispensing, and publishes tank status to `agri/digital_twin/{zone}/tank_status`.
- **An operator on the dashboard** watches the live state: telemetry in, recipe computed, pumps actuating, tank levels falling.
- **A judge on stage** sees the SDK agent trace: telemetry enters the prompt, the JSON payload exits to MQTT, every deterministic step visible.

## Functional requirements

### FR-1 — Deterministic kinetics engine
Given UV index, temperature (°C), and RH (%), compute the degradation rate constant and half-life using the confirmed formulas:
- `k_baseline = ln(2) / 48` per hour
- `k_dynamic = k_baseline * (1 + 0.18·UV) * exp(-(42500/8.314)·(1/T_K − 1/298.15))`
- `t_1/2 = ln(2) / k_dynamic`
The engine must be pure math, zero third-party deps, and unit-testable (the `--selftest` gate).

### FR-2 — Deterministic formulation
Given batch volume (L), UV, temp, RH, compute the recipe (all volumes in SI litres):
- biopesticide = 8% v/v of batch (fixed)
- lignin % = min(3.00, 0.25 + 0.25·UV) % w/v
- surfactant % = min(0.20, 0.05·(1 + 1.2·(1 − RH/100))·(T_K/293.15)^1.5) % v/v
- carrier water = batch − (bio + lignin + surfactant), must be ≥ 0

### FR-3 — Safety guardrail
Reject any recipe where surfactant % > 0.20% (phytotoxicity), lignin % > 3.00% (solubility), any component < 0, or volumes don't sum to batch. Rejection returns a machine-readable `safety_violations` list with rule names.

### FR-4 — SCADA dispatch payload
Build the canonical `SCADAPayload` from `src/twin/contracts.py`: `timestamp`, `zone_id`, `safety_validated`, `sim_speed` (default 10), `recipe` (the 5 litre fields), `commands` (pump_id 1–4, chemical_name, volume_l, duration_sec). Duration is computed as volume ÷ flow (0.01/0.01/0.01/0.05 L/s); the twin recomputes it from its own flow table. Publish to `agri/actuator/{zone_id}/dosing_dispatch` at QoS 1. Never accept duration from a caller.

### FR-5 — OpenAI Agents SDK tool-calling backbone
The demo backbone is the official OpenAI Agents SDK (`Agent`, `Runner`, `@function_tool`). The pipeline splits into named agents (Perception → Formulation → SCADA) wired with native `handoffs=[...]`; the LLM agents are thin parsers that read telemetry and trigger the deterministic Python tools. Each step is logged (prompt sent, tool invoked, structured output returned, handoff taken) so the trace is judge-visible.

### FR-6 — Digital twin actuation
The twin subscribes to `agri/actuator/+/dosing_dispatch`, validates payloads through `SCADAPayload`, and rejects `safety_validated: false`. It simulates each pump for `volume ÷ flow / sim_speed` seconds and tracks tank depletion, publishing `TwinState` to `agri/digital_twin/{zone_id}/tank_status` **after every pump command** — not only once at the end of a dispatch — so tank levels are observable as they fall. Operational alarms and rejections are published to `agri/digital_twin/{zone_id}/events`.

`TwinState` fields: `timestamp`, `zone_id`, `tanks_l`, `current_batch_l` (litres of the dispatch in progress — reset per dispatch), `total_dispensed_l` (cumulative litres since twin start), `alarms`, `last_dispatch_id`.

Event fields: `timestamp`, `zone_id`, `code`, `detail`. Codes: `SAFETY_REJECTED`, `INVALID_PAYLOAD`, `LOW_TANK`, `DISPATCH_COMPLETE`. Events are transient (not retained); `tank_status` is retained so late-joining subscribers see current levels.

### FR-7 — Dashboard
A Streamlit dashboard shows live state: telemetry in, computed recipe, dispatch status, twin tank levels, and recent twin events. It exposes an explicit dispatch control that calls the shared SCADA tool and is disabled while the recipe fails safety validation. (Dashboard is the presentation layer; the MCP server and twin must run without it.)

### FR-8 — One-command reproducibility
A single README `Getting started` sequence installs deps from `specs/code/requirements.txt` and runs: MCP server selftest, kinetics pipeline, SCADA trajectories pipeline, twin, and dashboard.

## Edge cases & rules

- **UV out of range (>16 or <0)** → clamp to the Pydantic field bounds (0–16); reject beyond.
- **RH out of range (<0 or >100)** → the dispatch schema rejects with a validation error (`relative_humidity_pct must be in [0, 100]`).
- **Temperature extreme (−10 to 55 °C bounds)** → reject outside; `f_temp` guards `T_K ≤ 0` by returning 1.0 (thermal-only).
- **Low tank** → the twin raises a machine-readable `LOW_TANK <chem>` alarm in the published state and publishes a `LOW_TANK` event, never silently skips.
- **Broker down** → dispatch returns a machine-readable `{"published": false, "error": ...}`; the twin reconnect is handled by the MQTT client loop.
- **Safety-rejected recipe** → no dispatch occurs; the tool returns `safety_validated: false` with `safety_violations`, and the message reads "DISPATCH REJECTED by safety guardrail."
- **Zero-volume component** → skipped in `commands` (a pump command with volume ≤ 0 is omitted).
- **Pump runtime > 30s** → rejected by `validate_dispatch` (thermal threshold), blocking the whole dispatch.

## Out of scope

- Visual pest detection and yield prediction (the demo north star: one decision).
- Physical ESP32 rig firmware — inherits the same contract later; the twin is the demo target.
- Custom PCB manufacturing, closed-loop chemical titration probes, three-phase motor control.
- Farmer manual data entry — telemetry comes from weather API or simulated field data only.
- A hand-rolled plain chat-completions loop — the OpenAI Agents SDK (`Runner`, handoffs) is the locked demo backbone.

## Acceptance criteria

- [ ] `python src/mcp_server_scada.py --selftest` passes: kinetics doc scenario (k_deg ≈ 0.082/hr, t_1/2 ≈ 8.5h), recipe (bio 0.04 L, lignin 2.55%, surfactant ≈ 0.099%), safety rejects over-cap surfactant, pump runtimes under 30s, extreme UV caps lignin at 3.00%.
- [ ] The three MCP tools are callable over stdio with Pydantic-validated schemas (fallback JSON surface when pydantic absent).
- [ ] A recipe dispatched with `dispatch: true` publishes a `SCADAPayload` to `agri/actuator/{zone_id}/dosing_dispatch` at QoS 1, and a broker subscriber receives it.
- [ ] The digital twin, given that payload, dispenses the exact volumes (tank levels drop by the command volumes), publishes `tank_status`, and raises LOW_TANK alarms when a tank is short.
- [ ] A safety-violating recipe (surfactant > 0.20%) never dispatches — the tool returns the guardrail rejection.
- [ ] The OpenAI Agents SDK pipeline is wired to the MCP server: an agent session can trigger the recipe → safety → dispatch chain with only the deterministic tools exposed.
- [ ] The dashboard renders live state from the MCP server / twin topics.
- [ ] A fresh clone follows the README one-command setup and the whole chain runs against a local Mosquitto broker.
