"""Shared SCADA contract — single source of truth for payload schemas.

This module is the canonical contract consumed by the MCP SCADA tool server
(src/mcp_server_scada.py), the digital twin (src/twin/twin.py), and the
physical rig firmware. Nothing drifts: every layer imports these models.

Settled by wayfinder ticket #6 (Option A): sim_speed is explicit in the
payload; duration_sec is informational only — the twin recomputes runtimes
from its own calibrated flow table.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class ChemicalRecipe(BaseModel):
    biopesticide_ml: float = Field(ge=0.0, description="Bacillus thuringiensis or peptide active volume in mL")
    uv_stabilizer_ml: float = Field(ge=0.0, description="Sodium lignosulfonate solution volume in mL")
    surfactant_ml: float = Field(ge=0.0, description="Organosilicone surfactant volume in mL")
    carrier_water_ml: float = Field(ge=0.0, description="Diluent water volume in mL")
    total_batch_volume_ml: float = Field(gt=0.0, description="Total mix volume in mL")


class PumpCommand(BaseModel):
    pump_id: int = Field(ge=1, le=4, description="Hardware pump identifier")
    chemical_name: Literal["biopesticide", "uv_stabilizer", "surfactant", "carrier_water"]
    volume_ml: float = Field(gt=0.0, description="Volume to dispense in mL")
    duration_sec: float = Field(gt=0.0, description="Informational runtime calculated by sender (overridden by twin calibration)")


class SCADAPayload(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    zone_id: str
    safety_validated: bool
    sim_speed: int = Field(default=10, description="Acceleration factor for digital twin simulation")
    recipe: ChemicalRecipe
    commands: List[PumpCommand]
