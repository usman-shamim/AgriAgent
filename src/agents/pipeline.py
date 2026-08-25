"""
AgriAgent — OpenAI Agents SDK pipeline (Perception → Formulation → SCADA).

The demo backbone: named agents wired with native handoffs, driven by
`Runner.run(...)`. The LLM agents are thin parsers — every chemistry formula
runs inside the deterministic @function_tool surface in src/agents/tools.py.

Usage:
    python -m src.agents.pipeline                      # run the demo scenario
    python -m src.agents.pipeline --uv 8.2 --temp 39 --rh 28 --batch 500
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Dict, Any

from agents import Runner

from src.agents.tools import build_sdk_pipeline

# The agents are constructed once per process (module-level singleton).
_PIPELINE: Dict[str, Any] = build_sdk_pipeline()


async def run_formulation_cycle(
    zone_id: str,
    uv_index: float,
    ambient_temp_c: float,
    relative_humidity_pct: float,
    batch_volume_ml: float = 500.0,
    dispatch: bool = False,
) -> str:
    """Run the Perception → Formulation → SCADA chain for one telemetry event."""
    prompt = (
        f"Telemetry Alert for {zone_id}: Ambient Temperature = {ambient_temp_c}°C, "
        f"Relative Humidity = {relative_humidity_pct}%, UV Index = {uv_index}. "
        f"Evaluate degradation risk, calculate the dynamic recipe for a "
        f"{batch_volume_ml} mL batch, and "
        + ("dispatch the setpoint to the broker." if dispatch else "preview the dispatch.")
    )
    print(f"[SYSTEM START] Initiating OpenAI Agents SDK Runner...\n")
    result = await Runner.run(_PIPELINE["entry"], input=prompt)
    print(f"\n[FINAL AGENT OUTPUT]\n{result.final_output}")
    return result.final_output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zone", default="zone_north", help="Field management sector identifier")
    parser.add_argument("--uv", type=float, default=9.2, help="Ambient UV Index")
    parser.add_argument("--temp", type=float, default=38.0, help="Ambient temperature in Celsius")
    parser.add_argument("--rh", type=float, default=32.0, help="Relative humidity percentage")
    parser.add_argument("--batch", type=float, default=500.0, help="Batch volume in mL")
    parser.add_argument("--dispatch", action="store_true", help="Publish the SCADAPayload over MQTT")
    args = parser.parse_args()

    asyncio.run(
        run_formulation_cycle(
            args.zone, args.uv, args.temp, args.rh, args.batch, args.dispatch
        )
    )


if __name__ == "__main__":
    main()
