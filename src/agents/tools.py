"""
AgriAgent — Deterministic tool surface for the OpenAI Agents SDK pipeline.

Wraps the confirmed chemistry engines (src/mcp_server_scada.py) and the shared
SCADA contract (src/twin/contracts.py) as @function_tool functions. The LLM
agents can only call these tools — they never improvise the math.

Backbone decision (wayfinder map): OpenAI Agents SDK (Agent, Runner, handoffs).
Constants: k0 = ln(2)/48 (ticket #4), surfactant cap 0.20% v/v (ticket #5).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from agents import function_tool

# Allow `python src/agents/tools.py` and `python -m src.agents.tools`:
# ensure the repo root is importable so `src.*` resolves.
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.mcp_server_scada import (
    KineticsEngine,
    FormulationEngine,
    SafetyValidator,
    _build_dispatch_payload,
)
from src.twin.contracts import ChemicalRecipe, PumpCommand, SCADAPayload

# Shared engine instances (pure math, no third-party deps beyond stdlib).
_kinetics = KineticsEngine()
_formulation = FormulationEngine()
_safety = SafetyValidator()


@function_tool
def compute_degradation_kinetics(uv_index: float, ambient_temp_c: float) -> str:
    """Perception Agent tool.

    Compute the Bt degradation half-life and 1-hour viability from live UV index
    and ambient temperature (Celsius). Returns a JSON string.
    """
    result = _kinetics.compute(uv_index, ambient_temp_c)
    return json.dumps(result.__dict__, default=str)


@function_tool
def generate_chemical_recipe(
    batch_volume_ml: float,
    uv_index: float,
    ambient_temp_c: float,
    relative_humidity_pct: float,
) -> str:
    """Formulation Agent tool.

    Compute the exact mL recipe for biopesticide, UV stabilizer, surfactant, and
    carrier water for a batch. Returns a JSON string with the recipe and safety
    verdict.
    """
    recipe = _formulation.recipe(
        batch_volume_ml, uv_index, ambient_temp_c, relative_humidity_pct
    )
    violations = _safety.validate_recipe(recipe)
    return json.dumps(
        {
            "recipe": recipe.__dict__,
            "safety_ok": len(violations) == 0,
            "safety_violations": [v.__dict__ for v in violations],
        },
        default=str,
    )


@function_tool
def dispatch_scada_dosing(
    zone_id: str,
    batch_volume_ml: float,
    uv_index: float,
    ambient_temp_c: float,
    relative_humidity_pct: float,
    dispatch: bool = False,
) -> str:
    """SCADA Agent tool.

    Safety-gate the recipe, compute pump runtimes from the confirmed flow table
    (10/10/10/50 mL/s), and (optionally) publish the SCADAPayload over MQTT to
    agri/actuator/{zone_id}/dosing_dispatch at QoS 1. Returns a JSON string.
    """
    recipe = _formulation.recipe(
        batch_volume_ml, uv_index, ambient_temp_c, relative_humidity_pct
    )
    recipe_violations = _safety.validate_recipe(recipe)
    sim_speed = 10
    payload = _build_dispatch_payload(
        zone_id,
        recipe,
        safety_validated=not recipe_violations,
        sim_speed=sim_speed,
        safety_violations=recipe_violations,
    )
    dispatch_violations = _safety.validate_dispatch(payload["commands"])
    all_violations = recipe_violations + dispatch_violations

    result: Dict[str, Any] = {
        "zone_id": zone_id,
        "safety_validated": not all_violations,
        "safety_violations": [v.__dict__ for v in all_violations],
        "payload": payload if not all_violations else None,
    }
    if all_violations:
        result["message"] = "DISPATCH REJECTED by safety guardrail."
        return json.dumps(result, default=str)

    if dispatch:
        mqtt_result = _publish_scada_payload(zone_id, payload)
        result["mqtt"] = mqtt_result
        result["message"] = (
            f"DISPATCH SUCCESS to {mqtt_result.get('topic', '')}"
            if mqtt_result.get("published")
            else f"DISPATCH FAILED: {mqtt_result.get('error', 'unknown')}"
        )
    else:
        result["message"] = "DISPATCH PREVIEW (pass dispatch=true to publish over MQTT)."
    return json.dumps(result, default=str)


def _publish_scada_payload(zone_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Publish a SCADAPayload to the broker. Reuses the MCP server's helper."""
    from src.mcp_server_scada import _publish_scada_payload as _pub

    return _pub(zone_id, payload)


def build_sdk_pipeline() -> Dict[str, Any]:
    """Construct the three agents wired with handoffs. Returns {agents, entry}."""
    from agents import Agent

    scada_agent = Agent(
        name="SCADA Agent",
        instructions=(
            "You are the Industrial SCADA Controller. You receive a validated recipe and "
            "dispatch it over MQTT via the dispatch_scada_dosing tool. "
            "Use dispatch=true to publish to the broker; otherwise return the preview."
        ),
        tools=[dispatch_scada_dosing],
    )

    formulation_agent = Agent(
        name="Formulation Agent",
        instructions=(
            "You are the Agro-Chemical Formulation Engineer. Use the generate_chemical_recipe "
            "tool to compute the exact stoichiometric blend from telemetry. "
            "If safety_ok is true, hand off to the SCADA Agent to dispatch."
        ),
        tools=[generate_chemical_recipe],
        handoffs=[scada_agent],
    )

    perception_agent = Agent(
        name="Perception Agent",
        instructions=(
            "You are the Environmental Perception Agent. Analyze raw field telemetry for UV "
            "and thermal threats using compute_degradation_kinetics, then hand off to the "
            "Formulation Agent to compute the recipe."
        ),
        tools=[compute_degradation_kinetics],
        handoffs=[formulation_agent],
    )

    return {
        "perception": perception_agent,
        "formulation": formulation_agent,
        "scada": scada_agent,
        "entry": perception_agent,
    }
