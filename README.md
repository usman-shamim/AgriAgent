# AgriAgent

**Autonomous SCADA system for on-demand biopesticide formulation.**

AgriAgent replaces blanket synthetic pesticide spraying with an agentic AI system that mixes biopesticides *dynamically* — reading live environmental telemetry (UV index, temperature, humidity), calculating how fast the active ingredient is degrading, then computing and physically dispensing the optimal recipe to keep it alive on the leaf.

The problem it solves: biopesticides are safe but fragile. Solar UV and heat destroy them in hours. AgriAgent's AI agents compensate in real time — boosting UV stabilizers on bright days, adjusting surfactants in dry heat — and dispatch the exact volumetric recipe over MQTT to a dosing rig or its digital twin.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                            │
│            Streamlit / Next.js SCADA dashboard                    │
└───────────────────────────────┬──────────────────────────────────┘
                                │ WebSockets / State Sync
                                v
┌──────────────────────────────────────────────────────────────────┐
│                   AI AGENT REASONING CORE                         │
│  [Perception] → [Formulation] → [Safety] → [Actuator/SCADA]      │
└───────────────────────────────┬──────────────────────────────────┘
                                │ Tool Invocation (MCP / JSON-RPC)
                                v
┌──────────────────────────────────────────────────────────────────┐
│                  MIDDLEWARE & PROTOCOL HIGHWAY                    │
│                MQTT Broker (Eclipse Mosquitto)                    │
└───────────────┬───────────────────────────────┬──────────────────┘
                │ agri/actuator/+/dosing_dispatch│ telemetry
                v                               v
┌──────────────────────────────┐  ┌──────────────────────────────┐
│      DIGITAL TWIN (Sim)      │  │     PHYSICAL RIG (Optional)   │
│  Fluid mechanics, tank levels│  │  ESP32, relays, peristaltic   │
└──────────────────────────────┘  └──────────────────────────────┘
```

### The four agents

1. **Perception Agent** — ingests weather API + soil sensor telemetry, validates ranges, computes degradation half-life.
2. **Stoichiometry & Formulation Agent** — calculates exact mL setpoints for biopesticide, UV stabilizer (sodium lignosulfonate), surfactant, and carrier water.
3. **Safety & Compliance Agent** — a guardrail that rejects phytotoxic recipes (surfactant cap, solubility cap, tank levels).
4. **SCADA / Actuator Agent** — converts volumes to pump runtimes and publishes deterministic JSON payloads over MQTT.

### The science (deterministic, not LLM-guessed)

- **Kinetics**: `C(t) = C₀·e^(−k·t)` with `k = k₀·(1+α·UV)·e^(−(Ea/R)(1/T−1/T₀))` — Arrhenius thermal + UV photolysis scaling, per-hour units.
- **UV stabilizer**: `C_lignin = min(3.0%, 0.25% + 0.25%·UV)` — more sun, more lignosulfonate, capped at solubility limit.
- **Surfactant**: evaporative compensation against relative humidity and heat, capped at 0.20% to prevent phytotoxicity.
- **Active concentrate**: fixed 8% v/v of batch; carrier water balances to 100%.
- **Pump calibration**: 10 mL/s (pumps 1–3), 50 mL/s (carrier water); durations computed from volume ÷ flow.

## What's built

- **`src/mcp_server_scada.py`** — the MCP SCADA tool server. Three tools (`compute_degradation_kinetics`, `generate_chemical_recipe`, `dispatch_scada_dosing`) with Pydantic-validated schemas, the confirmed formulas, and a safety guardrail. Run `--selftest` or `--demo`; serves over MCP stdio.
- **`specs/kinetics_pipeline.py`** — fetches real hourly weather for Multan (Open-Meteo) and exports a Kaggle-ready degradation dataset.
- **`specs/scada_trajectory_pipeline.py`** — generates 500 synthetic agent-formulation + MQTT-actuation traces (the SCADA trajectories dataset).
- **Two Kaggle datasets** — `data/synthetic_biopesticide_telemetry.csv` (kinetics) and `data/agriagent_scada_dosing_trajectories.csv` (dosing decisions).

## Repository layout

```
src/            MCP SCADA server + agent pipeline (agents/, twin/)
dashboard/      Streamlit / Next.js SCADA interface
specs/          Technical specs, design docs, and data pipeline scripts
data/           Generated datasets (kinetics + SCADA trajectories)
docs/           Wayfinding map, ADRs, domain docs
scripts/        Utility scripts (telemetry sim, demo helpers)
```

## Getting started

```bash
# Install dependencies (MCP SDK, paho-mqtt, pydantic)
python3 -m venv .venv && .venv/bin/pip install -r specs/requirements.txt

# MCP SCADA server self-test (pure math, no broker needed)
.venv/bin/python src/mcp_server_scada.py --selftest

# Generate the kinetics benchmark dataset (real Multan weather)
.venv/bin/python specs/kinetics_pipeline.py --days 7 --output data/synthetic_biopesticide_telemetry.csv

# Generate the SCADA trajectories dataset (500 runs)
.venv/bin/python specs/scada_trajectory_pipeline.py --runs 500 --output data/agriagent_scada_dosing_trajectories.csv

# Offline kinetics mode (no network) — deterministic synthetic telemetry
.venv/bin/python specs/kinetics_pipeline.py --offline --days 2
```

## Roadmap

The build is charted on the wayfinder map (GitHub Issues #1) — decision tickets covering the digital twin contract, the agent runtime (OpenAI Agent SDK vs function-calling), and the demo dashboard. Broker choice, pump calibration, formulation policy, and the kinetics constants are settled. See the open tickets for what's next.

## License

MIT (pending — see tickets).
