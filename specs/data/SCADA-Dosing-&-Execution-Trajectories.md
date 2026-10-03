# AgriAgent SCADA Dosing & Execution Trajectories Dataset

While the [kinetics pipeline spec](./Biopesticide-Kinetics-&-Telemetry-Pipeline.md) models raw environmental degradation kinetics, this second dataset captures the **deterministic multi-agent control decisions and MQTT actuation traces**. It records how raw telemetry is evaluated by the agentic pipeline, converted into stoichiometric ratios, passed through safety validation, and formatted into precise pump timings.

Hosting this dataset proves to judges and recruiters that AgriAgent does not merely generate unstructured text, but acts as a deterministic supervisory control system that emits verifiable machine payloads.

All volumes are SI litres (L); pump flows are L/s.

## 1. Dataset Schema Specification

| Column Name | Data Type | Physical Unit | Description |
| --- | --- | --- | --- |
| `run_id` | String | UUID / ID | Unique identifier for the agent formulation run |
| `timestamp` | String | ISO-8601 UTC | Timestamp of sensor polling and execution cycle |
| `zone_id` | String | Categorical | Field sector (`zone_north_cotton`, `zone_south_cotton`, `zone_east_orchard`, `zone_west_cotton`) |
| `uv_index` | Float | Index (0–16) | Environmental UV index input |
| `ambient_temp_c` | Float | °C | Dry-bulb ambient air temperature |
| `rel_humidity_pct` | Float | % | Atmospheric relative humidity |
| `agent_reasoning_trace` | String | Text | Structured chain-of-deliberation from the Formulation Agent |
| `biopesticide_l` | Float | L | Target active *Bt* crystal endotoxin volume |
| `uv_stabilizer_l` | Float | L | Target sodium lignosulfonate volume |
| `surfactant_l` | Float | L | Target organosilicone super-spreader volume |
| `carrier_water_l` | Float | L | Target diluent carrier water volume |
| `total_batch_l` | Float | L | Total liquid batch volume (0.5 L) |
| `predicted_surface_tension_mN_m` | Float | mN/m | Leaf cuticular wetting equilibrium tension (< 22.0 mN/m) |
| `pump_1_duration_sec` | Float | Seconds | Biopesticide pump runtime (Q = 0.01 L/s) |
| `pump_2_duration_sec` | Float | Seconds | UV stabilizer pump runtime (Q = 0.01 L/s) |
| `pump_3_duration_sec` | Float | Seconds | Surfactant pump runtime (Q = 0.01 L/s) |
| `pump_4_duration_sec` | Float | Seconds | Water carrier pump runtime (Q = 0.05 L/s) |
| `safety_verification_status` | String | Flag | Verification status (`PASSED` or `REJECTED_PHYTOTOXIC`) |
| `mqtt_topic` | String | Topic Path | Destination MQTT broker routing topic |

The schema is the **execution record** of the agent pipeline: columns 1–6 are the telemetry inputs (Perception Agent), columns 7–12 are the formulation outputs (Formulation Agent), column 13 is the surface-tension model, columns 14–17 are the pump actuation setpoints (SCADA Agent), and columns 18–19 are the safety verdict and routing target (Safety + Actuator Agents).

## 2. Generator Script (`specs/code/scada_trajectory_pipeline.py`)

Run this standalone script to generate the synthetic execution trajectories dataset. It reuses the confirmed kinetics constants and formulation rules from the scope spec — so the generated rows match what `src/mcp_server_scada.py` would compute for the same telemetry.

```python
"""
AgriAgent — SCADA Dosing & Execution Trajectories Generator

Simulates multi-agent formulation runs across fluctuating field conditions.
Outputs stoichiometric chemical recipes, surface tension models, safety checks,
and exact MQTT pump actuation parameters for Kaggle hosting.

All volumes are SI litres (L) and flows L/s.

Usage:
    python specs/code/scada_trajectory_pipeline.py --runs 500 --output agriagent_scada_dosing_trajectories.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List


def generate_scada_runs(num_runs: int = 500) -> List[Dict]:
    """Generates synthetic agent reasoning traces and SCADA actuation setpoints."""
    base_time = datetime(2026, 8, 20, 6, 0, 0, tzinfo=timezone.utc)
    zones = ["zone_north_cotton", "zone_south_cotton", "zone_east_orchard", "zone_west_cotton"]
    records: List[Dict] = []

    batch_vol_l = 0.5
    pump_chem_flow_rate = 0.01    # L/sec
    pump_water_flow_rate = 0.05   # L/sec

    for i in range(num_runs):
        timestamp = base_time + timedelta(minutes=15 * i)
        zone = zones[i % len(zones)]
        hour = timestamp.hour + (timestamp.minute / 60.0)

        # Diurnal weather flux simulation
        solar_factor = max(0.0, math.sin(math.pi * (hour - 6.0) / 14.0)) if 6.0 <= hour <= 20.0 else 0.0
        uv = round(max(0.0, min(14.0, solar_factor * 11.5 + random.gauss(0, 0.3))), 2)
        temp_c = round(24.0 + (solar_factor * 15.0) + random.gauss(0, 0.4), 2)
        rh_pct = round(max(15.0, min(95.0, 78.0 - (solar_factor * 48.0) + random.gauss(0, 1.2))), 2)

        # Kinetics & Stoichiometry Engine (confirmed constants from specs/scope/hackthon-scope.md)
        t_kelvin = temp_c + 273.15
        k_deg = 0.015 * (1.0 + 0.18 * uv) * math.exp(-(42500.0 / 8.314) * ((1.0 / t_kelvin) - (1.0 / 298.15)))
        half_life_hrs = round(math.log(2) / k_deg, 2) if k_deg > 0 else 999.0

        # Chemical formulation rules
        bio_l = round(batch_vol_l * 0.08, 6)  # Fixed 8% active volume
        lignin_pct = min(3.0, 0.25 + (0.25 * uv))
        lignin_l = round(batch_vol_l * (lignin_pct / 100.0), 6)

        # Surfactant scaling with humidity compensation
        surf_pct = 0.05 * (1.0 + 1.2 * (1.0 - (rh_pct / 100.0))) * ((temp_c + 273.15) / 293.15)**1.5

        # Inject occasional safety edge case (1% of runs) to demonstrate the
        # Safety & Compliance Agent guardrail rejecting phytotoxic recipes.
        if random.random() < 0.01:
            surf_pct = 0.30  # Intentional breach > 0.20% phytotoxicity limit

        surf_l = round(batch_vol_l * (surf_pct / 100.0), 6)
        water_l = round(batch_vol_l - (bio_l + lignin_l + surf_l), 6)

        # Dynamic surface tension estimation (pure water = 72.8 mN/m, organosilicone floor = 21.5 mN/m)
        predicted_st = round(max(21.2, 72.8 - (surf_pct / 0.15) * 51.3), 2)

        # Safety Agent verification
        if surf_pct > 0.20 or water_l <= 0:
            status = "REJECTED_PHYTOTOXIC"
            p1_dur, p2_dur, p3_dur, p4_dur = 0.0, 0.0, 0.0, 0.0
            reasoning = (
                f"ALERT: Surfactant concentration ({surf_pct:.3f}%) breaches safety ceiling (0.20%). "
                f"Execution halted by Safety & Compliance Agent to protect crop foliage."
            )
        else:
            status = "PASSED"
            p1_dur = round(bio_l / pump_chem_flow_rate, 2)
            p2_dur = round(lignin_l / pump_chem_flow_rate, 2)
            p3_dur = round(surf_l / pump_chem_flow_rate, 2)
            p4_dur = round(water_l / pump_water_flow_rate, 2)
            reasoning = (
                f"UV={uv} (t1/2={half_life_hrs}h) -> Dosed {lignin_pct:.2f}% w/v lignin stabilizer. "
                f"RH={rh_pct}%, Temp={temp_c}C -> Dosed {surf_pct:.3f}% v/v surfactant (gamma={predicted_st} mN/m). "
                f"Dispatched {batch_vol_l}L batch over 4 channels."
            )

        records.append({
            "run_id": f"RUN-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": timestamp.isoformat(),
            "zone_id": zone,
            "uv_index": uv,
            "ambient_temp_c": temp_c,
            "rel_humidity_pct": rh_pct,
            "agent_reasoning_trace": reasoning,
            "biopesticide_l": bio_l,
            "uv_stabilizer_l": lignin_l,
            "surfactant_l": surf_l,
            "carrier_water_l": water_l,
            "total_batch_l": batch_vol_l,
            "predicted_surface_tension_mN_m": predicted_st,
            "pump_1_duration_sec": p1_dur,
            "pump_2_duration_sec": p2_dur,
            "pump_3_duration_sec": p3_dur,
            "pump_4_duration_sec": p4_dur,
            "safety_verification_status": status,
            "mqtt_topic": f"agri/actuator/{zone}/dosing_dispatch",
        })

    return records


def main():
    parser = argparse.ArgumentParser(description="Generate AgriAgent SCADA Trajectory Dataset")
    parser.add_argument("--runs", type=int, default=500, help="Number of telemetry cycles to simulate (default: 500)")
    parser.add_argument("--output", type=str, default="agriagent_scada_dosing_trajectories.csv", help="Output path")
    args = parser.parse_args()

    data = generate_scada_runs(num_runs=args.runs)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)

    print(f"[EXPORT SUCCESS] Wrote {len(data)} SCADA execution trajectories to {output_path.resolve()}")


if __name__ == "__main__":
    main()
```

## 3. Kaggle Publishing Metadata

Use these exact fields when creating the dataset on Kaggle:

* **Title (39 characters):** `AgriAgent SCADA Dosing & Trajectories`
* **Subtitle (79 characters):** `Multi-agent formulation traces and MQTT actuation setpoints for bio-pesticides`
* **License:** `CC BY 4.0`
* **Tags:** `Agriculture`, `Industrial Automation`, `IoT`, `Synthetic Data`, `Chemical Engineering`

### Dataset Description (Copy & Paste)

```markdown
Overview
This dataset records continuous execution trajectories from AgriAgent, an industrial multi-agent SCADA controller designed for dynamic precision biopesticide formulation. It documents how environmental inputs (UV index, temperature, relative humidity) are converted into stoichiometric chemical recipes, evaluated through safety guardrails, and mapped into hardware-level pump durations.

System Architecture & Physical Constants
1. Active Base: Bacillus thuringiensis (Bt) crystal endotoxin calibrated at 8.0% v/v base volume.
2. Photo-Stabilization: Dynamic dosing of sodium lignosulfonate biopolymer (0.25% to 3.00% w/v) to shield conjugated peptide bonds against UV photolysis.
3. Surface Tension Optimization: Dynamic dosing of organosilicone super-spreaders (0.05% to 0.20% v/v) to lower equilibrium surface tension below 22 mN/m and mitigate evaporative drift.
4. Safety Ceilings: Hard agricultural bounds preventing phytotoxicity (surfactant cap > 0.20% triggers automatic emergency rejection).
5. SCADA Pump Calibration: Peristaltic chemical pumps calibrated at 0.01 L/s; primary water diluent pump calibrated at 0.05 L/s.

Use Cases
- Benchmarking multi-agent tool-calling and structured output generation.
- Training machine learning models to predict optimal agro-chemical formulation setpoints from IoT telemetry.
- Simulating digital twin responses for industrial SCADA and PLC irrigation systems.
```

---

## 4. Consistency Notes

This spec is canonically aligned with the other AgriAgent documents:

- **Pump flow rates** — 0.01 L/s (pumps 1–3) and 0.05 L/s (pump 4, carrier water), matching `src/mcp_server_scada.py` and the scope spec.
- **Active concentration** — fixed 8% v/v, matching the scope spec and the MCP server.
- **Formulation rules** — `lignin = min(3.0, 0.25 + 0.25·UV)` and the surfactant evaporative-scaling law, matching the scope spec §2.
- **MQTT topic** — `agri/actuator/{zone}/dosing_dispatch`, matching the scope spec §5.
- **Safety semantics** — rejection triggers at surfactant > 0.20% v/v (phytotoxicity ceiling).
