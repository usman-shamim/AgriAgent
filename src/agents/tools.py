"""
AgriAgent — Deterministic tool surface for the OpenAI Agents SDK pipeline.

Thin @function_tool wrappers over the shared TOOLS handlers in
src/mcp_server_scada.py (one business-flow copy for MCP, SDK, and dashboard).
The LLM agents can only call these tools — they never improvise the math, and
out-of-envelope inputs are rejected by the shared engines.

Backbone decision (wayfinder map): OpenAI Agents SDK (Agent, Runner, handoffs).
Constants: k0 = ln(2)/48 (ticket #4), surfactant cap 0.20% v/v (ticket #5).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from agents import function_tool

# Allow `python src/agents/tools.py` and `python -m src.agents.tools`:
# ensure the repo root is importable so `src.*` resolves.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.mcp_server_scada import TOOLS


def _invoke_shared(tool_name: str, args: Dict[str, Any]) -> str:
    """Run the canonical MCP tool handler and serialize its result."""
    return json.dumps(TOOLS[tool_name]["handler"](args), default=str)


@function_tool
def compute_degradation_kinetics(uv_index: float, ambient_temp_c: float) -> str:
    """Perception Agent tool.

    Compute the Bt degradation half-life and 1-hour viability from live UV index
    (0-16) and ambient temperature (-10 to 55 C). Returns a JSON string.
    """
    return _invoke_shared(
        "compute_degradation_kinetics",
        {"uv_index": uv_index, "ambient_temp_c": ambient_temp_c},
    )


@function_tool
def generate_chemical_recipe(
    batch_volume_l: float,
    uv_index: float,
    ambient_temp_c: float,
    relative_humidity_pct: float,
) -> str:
    """Formulation Agent tool.

    Compute the exact litre recipe for biopesticide, UV stabilizer, surfactant,
    and carrier water for a batch of at most 10 L. Telemetry must be within the
    validated envelope: UV 0-16, temperature -10 to 55 C, humidity 5-100%.
    Returns a JSON string with the recipe and safety verdict.
    """
    return _invoke_shared(
        "generate_chemical_recipe",
        {
            "batch_volume_l": batch_volume_l,
            "uv_index": uv_index,
            "ambient_temp_c": ambient_temp_c,
            "relative_humidity_pct": relative_humidity_pct,
        },
    )


@function_tool
def dispatch_scada_dosing(
    zone_id: str,
    batch_volume_l: float,
    uv_index: float,
    ambient_temp_c: float,
    relative_humidity_pct: float,
    dispatch: bool = False,
) -> str:
    """SCADA Agent tool.

    Safety-gate the recipe, compute pump runtimes from the confirmed flow table
    (0.01/0.01/0.01/0.05 L/s), and (optionally) publish the SCADAPayload over
    MQTT to agri/actuator/{zone_id}/dosing_dispatch at QoS 1. Returns a JSON string.
    """
    return _invoke_shared(
        "dispatch_scada_dosing",
        {
            "zone_id": zone_id,
            "batch_volume_l": batch_volume_l,
            "uv_index": uv_index,
            "ambient_temp_c": ambient_temp_c,
            "relative_humidity_pct": relative_humidity_pct,
            "dispatch": dispatch,
            "sim_speed": 10,
        },
    )


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
