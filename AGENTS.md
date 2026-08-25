# AGENTS.md

AgriAgent is an autonomous SCADA system that computes biopesticide recipes from live environmental telemetry and dispatches them over MQTT to a digital twin (optionally a physical ESP32 dosing rig). Four-agent pipeline: Perception → Formulation → Safety → Actuator.

## Demo north star

The hackathon pitch is one decision, not a platform. Four beats, in order:

1. **One Decision** — the dynamic formulation ratio (biopesticide / UV stabilizer / surfactant mix). Pest detection and yield prediction are out of scope.
2. **Minimum Data** — UV index, ambient temperature, relative humidity. The Perception Agent pulls these from a local weather API or simulated field telemetry; farmers never hand-enter data.
3. **Actionable Prototype** — the output is the MQTT payload. Formulation computes the recipe, Safety validates it, SCADA dispatches a strict JSON command, and the digital twin simulates the pump dispensing the exact volume.
4. **Validate Savings** — kinetics models prove dynamic encapsulation extends biopesticide half-life; tie to the 90% synthetic-volume-reduction target and the per-acre input cost saving.

## Constitution

- Chemistry is deterministic, never LLM-guessed. The LLM agents are thin parsers over `@function_tool`-wrapped Python math on the OpenAI Agents SDK (`Agent`, `Runner`, `handoffs`).
- Strict Pydantic validation on every tool contract.
- Spec-driven: specs are the source of truth. Change `specs/` first, then re-derive code. Every feature spec follows the six-section anatomy and discipline of the `/create-spec` skill (Spec-Driven Development contract).
- Start each session by loading the wayfinder map (GitHub issue #1) for live decisions and open tickets.

## Key files

- @src/mcp_server_scada.py — MCP SCADA tool server: `compute_degradation_kinetics`, `generate_chemical_recipe`, `dispatch_scada_dosing`; run `--selftest` / `--demo`.
- @src/agents/tools.py — deterministic `@function_tool` surface (kinetics, recipe, dispatch) used by the SDK agents.
- @src/agents/pipeline.py — OpenAI Agents SDK pipeline: Perception → Formulation → SCADA agents with handoffs; run `python -m src.agents.pipeline`.
- @src/twin/contracts.py — shared SCADA contract (`SCADAPayload`, `PumpCommand`); single source of truth for payload schemas.
- @src/twin/twin.py — digital twin; subscribes to `agri/actuator/+/dosing_dispatch`, recomputes runtimes from its own flow table, publishes tank status.
- @scripts/test_publish.py — MQTT dispatcher smoke test for the contract payload.
- @dashboard/app.py — Streamlit SCADA dashboard: live twin tank levels over MQTT plus computed recipe/dispatch preview; run `streamlit run dashboard/app.py`.
- @tests/test_agents.py — end-to-end agent pipeline tests (ScriptedModel, no API key needed).
- @specs/mvp-build-spec.md — the buildable MVP spec: locked decisions as acceptance criteria (the one to build against).
- @specs/scope/hackthon-scope.md — MVP scope and acceptance boundaries (the what).
- @specs/design/design-and-implementation.md — system architecture and hardware design (the how).
- @specs/data/Biopesticide-Kinetics-&-Telemetry-Pipeline.md and @specs/data/SCADA-Dosing-&-Execution-Trajectories.md — dataset specs.
- @specs/code/kinetics_pipeline.py and @specs/code/scada_trajectory_pipeline.py — dataset generators (Kaggle-ready CSVs into `data/`).
- @README.md — setup and one-command run.

## Canonical MQTT topics

- Telemetry in: `agri/telemetry/{zone_id}/environment`
- Actuate: `agri/actuator/{zone_id}/dosing_dispatch` (QoS 1)
- State feedback: `agri/digital_twin/{zone_id}/tank_status`
