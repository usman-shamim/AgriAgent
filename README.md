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
│                MQTT Broker (Eclipse Mosquitto / EMQX)             │
└───────────────┬───────────────────────────────┬──────────────────┘
                │ agri/actuator/+/setpoint      │ telemetry
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

- **Kinetics**: `C(t) = C₀·e^(−k·t)` with `k = k₀·(1+α·UV)·e^(−(Ea/R)(1/T−1/T₀))` — Arrhenius thermal + UV photolysis scaling.
- **UV stabilizer**: `C_lignin = min(3.0%, 0.25% + 0.25%·UV)` — more sun, more lignosulfonate, capped at solubility limit.
- **Surfactant**: evaporative compensation against relative humidity and heat, capped at 0.20% to prevent phytotoxicity.
- **Kinetics pipeline**: fetches real hourly weather for Multan (Open-Meteo) and exports a Kaggle-ready degradation dataset.

## Repository layout

```
src/agents/     Agent pipeline (Perception → Formulation → Safety → Actuator)
src/twin/       Digital twin simulation engine (virtual SCADA rig)
dashboard/      Streamlit / Next.js SCADA interface
specs/          Technical specifications & design docs
data/           Generated datasets (e.g. synthetic_biopesticide_telemetry.csv)
docs/           Wayfinding map, ADRs, domain docs
scripts/        Utility scripts (telemetry sim, demo helpers)
```

## Getting started

```bash
# Generate the kinetics benchmark dataset (real Multan weather)
python3 specs/kinetics_pipeline.py --days 7 --output data/synthetic_biopesticide_telemetry.csv

# Offline mode (no network) — deterministic synthetic telemetry
python3 specs/kinetics_pipeline.py --offline --days 2
```

The pipeline is pure standard library — no install needed. MQTT broker, agent runtime, and dashboard dependencies are listed in `specs/requirements.txt` and will land as those layers are built.

## Roadmap

The build is charted on the [wayfinder map](docs/wayfinder/map.md) — a set of decision tickets on GitHub Issues covering broker choice (Mosquitto vs EMQX), pump flow-rate calibration, the digital twin contract, and demo strategy. See the open tickets for what's next.

## License

MIT (pending — see tickets).
