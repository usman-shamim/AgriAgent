"""
AgriAgent — SCADA Dosing & Execution Trajectories Generator

Simulates multi-agent formulation runs across fluctuating field conditions.
Outputs stoichiometric chemical recipes, surface tension models, safety checks,
and exact MQTT pump actuation parameters for Kaggle hosting.

All volumes are SI litres (L) and flows L/s.

Usage:
    python scada_trajectory_pipeline.py --runs 500 --output agriagent_scada_dosing_trajectories.csv
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

        # Safety Agent verification — single rejection condition: surfactant
        # exceeding the 0.20% v/v phytotoxicity ceiling (status name matches).
        if surf_pct > 0.20:
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