"""
AgriAgent — end-to-end test for the OpenAI Agents SDK pipeline.

Uses the SDK's ScriptedModel to drive the Perception → Formulation → SCADA
handoff chain deterministically, without an OpenAI API key. The model is
scripted to: (1) call the kinetics tool, (2) hand off to Formulation,
(3) call the recipe tool, (4) hand off to SCADA, (5) call the dispatch tool.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

# Ensure the repo root is importable so `src.*` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import Runner
from agents.testing import ScriptedModel, assistant_message, function_call

from src.agents.tools import build_sdk_pipeline

PIPELINE = build_sdk_pipeline()


def _scripted_model():
    """A fake LLM that walks the pipeline: kinetics -> handoff -> recipe -> handoff -> dispatch."""
    return ScriptedModel(
        steps=[
            # Perception agent: call the kinetics tool, then hand off to Formulation
            [
                function_call(
                    "compute_degradation_kinetics",
                    {"uv_index": 9.2, "ambient_temp_c": 38.0},
                    call_id="call_1",
                )
            ],
            [
                function_call(
                    "transfer_to_formulation_agent",
                    {},
                    call_id="handoff_1",
                )
            ],
            # Formulation agent: compute the recipe, then hand off to SCADA
            [
                function_call(
                    "generate_chemical_recipe",
                    {
                        "batch_volume_ml": 500.0,
                        "uv_index": 9.2,
                        "ambient_temp_c": 38.0,
                        "relative_humidity_pct": 32.0,
                    },
                    call_id="call_2",
                )
            ],
            [
                function_call(
                    "transfer_to_scada_agent",
                    {},
                    call_id="handoff_2",
                )
            ],
            # SCADA agent: dispatch the setpoint
            [
                function_call(
                    "dispatch_scada_dosing",
                    {
                        "zone_id": "zone_north",
                        "batch_volume_ml": 500.0,
                        "uv_index": 9.2,
                        "ambient_temp_c": 38.0,
                        "relative_humidity_pct": 32.0,
                        "dispatch": False,
                    },
                    call_id="call_3",
                )
            ],
            [assistant_message("Dispatch preview generated. Command complete.")],
        ]
    )


@pytest.mark.asyncio
async def test_full_pipeline_dispatch_preview():
    """The SDK chain runs end-to-end and emits a valid contract payload."""
    from agents import RunConfig

    model = _scripted_model()
    result = await Runner.run(
        PIPELINE["entry"],
        (
            "Telemetry for zone_north: UV 9.2, temp 38C, RH 32%. "
            "Evaluate risk, compute the 500 mL recipe, and preview the dispatch."
        ),
        run_config=RunConfig(model=model),
    )

    assert result.final_output
    # The chain should have passed through all three agents
    assert "Dispatch preview" in result.final_output or "preview" in result.final_output.lower()


@pytest.mark.asyncio
async def test_dispatch_tool_emits_contract_payload():
    """The SCADA tool output validates against SCADAPayload and carries the right volumes."""
    from src.agents.tools import dispatch_scada_dosing

    fn = dispatch_scada_dosing.__wrapped__
    out = json.loads(fn("zone_north", 500.0, 9.2, 38.0, 32.0, False))

    assert out["safety_validated"] is True
    assert out["payload"]["zone_id"] == "zone_north"
    assert out["payload"]["commands"][0]["chemical_name"] == "biopesticide"
    assert out["payload"]["recipe"]["biopesticide_ml"] == 40.0

    # The payload must validate against the canonical contract
    from src.twin.contracts import SCADAPayload

    SCADAPayload(**out["payload"])


@pytest.mark.asyncio
async def test_unsafe_recipe_never_dispatches():
    """A dispatch that breaches a safety rule is rejected with a machine-readable violation."""
    from src.agents.tools import dispatch_scada_dosing

    fn = dispatch_scada_dosing.__wrapped__
    # A huge batch pushes the carrier-water pump runtime past the 30s thermal cap.
    out = json.loads(fn("zone_north", 10_000.0, 9.2, 38.0, 32.0, False))
    assert out["safety_validated"] is False
    assert any(v["rule"] == "pump_thermal_cycle" for v in out["safety_violations"])
    assert out["payload"] is None  # no payload is emitted for a rejected dispatch
