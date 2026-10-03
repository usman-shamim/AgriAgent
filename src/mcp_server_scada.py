"""
AgriAgent — MCP SCADA Tool Server

Exposes the confirmed biopesticide formulation math (kinetics, recipe, safety)
as Model Context Protocol tools so the agent pipeline (Perception → Formulation
→ Safety → Actuator) can call deterministic chemistry instead of prompting for it.

The pure-math core (KineticsEngine / FormulationEngine / SafetyValidator) has
zero third-party dependencies and is unit-testable on its own. MCP registration
and MQTT dispatch are lazy-imported so the server runs even before the SDK is
installed (tools fall back to a local function-calling surface).

Formulas (specs/scope/hackthon-scope.md §2, specs/data/Biopesticide-Kinetics-&-Telemetry-Pipeline.md):
  k_baseline = ln(2) / DT50_hours                        (per hour)
  k_dynamic  = k_baseline * (1 + alpha * UV) * exp(-(Ea/R)(1/T - 1/T0))
  C_lignin   = min(3.00%, 0.25% + 0.25% * UV)           (% w/v)
  V_surf     = 0.05 * (1 + 1.2*(1 - RH)) * (T/293.15)^1.5   (% v/v), capped 0.20%
  t_1/2      = ln(2) / k_dynamic
  duration   = volume_l / flow_rate_l_per_sec

All volumes are SI litres (L) and flows L/s.

Usage:
    python mcp_server_scada.py                      # run MCP stdio server
    python mcp_server_scada.py --selftest           # run the built-in test
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 1. Confirmed empirical constants (specs, PPDB / EPA CompTox anchors)
# ---------------------------------------------------------------------------

DT50_BASE_HOURS = 48.0          # Baseline dark half-life of Bt endotoxin (hours)
K_BASELINE_PER_HR = math.log(2) / DT50_BASE_HOURS   # 0.01444 hr^-1
T0_KELVIN = 298.15              # Reference temperature 25 C
EA_J_PER_MOL = 42_500.0         # Denaturation activation energy (J/mol)
R_GAS = 8.314                   # Universal gas constant J/(mol*K)
ALPHA_UV = 0.18                 # UV photolysis scaling (Index^-1)

LIGNIN_BASE_PCT = 0.25          # % w/v baseline stabilizer
LIGNIN_BETA_PCT_PER_UV = 0.25   # % w/v per UV index unit
LIGNIN_MAX_PCT = 3.00           # Solubility cap (nozzle clogging)

SURF_BASE_PCT = 0.05            # % v/v baseline surfactant
SURF_DELTA = 1.2                # Evaporative compensation coefficient
SURF_TEMP_REF_K = 293.15        # 20 C
SURF_MAX_PCT = 0.20             # Phytotoxicity ceiling

ACTIVE_RATIO = 0.08             # Canonical active concentrate fraction of batch
BATCH_DEFAULT_L = 0.5

# Confirmed pump calibration: pumps 1-3 at 0.01 L/s, carrier water at 0.05 L/s.
# Duration is COMPUTED from volume / flow rate — never accepted from a caller.
PUMP_FLOW_L_PER_S: Dict[int, float] = {1: 0.01, 2: 0.01, 3: 0.01, 4: 0.05}
MAX_PUMP_CYCLE_SEC = 30.0       # Safety thermal threshold per pump cycle

MQTT_TOPIC = "agri/actuator/{zone_id}/dosing_dispatch"
MQTT_BROKER_DEFAULT = os.getenv("AGRIA_MQTT_BROKER", "localhost")
MQTT_PORT_DEFAULT = int(os.getenv("AGRIA_MQTT_PORT", "1883"))

# Litre-scale rounding: 6 dp keeps sub-mL components (e.g. surfactant ~5e-4 L)
# alive and non-zero, unlike the 2 dp that was sufficient at mL scale.
VOLUME_DECIMALS = 6
DURATION_DECIMALS = 3
VOLUME_BALANCE_ABS_TOL = 1e-5   # L; ~0.01 mL, absorbs 6 dp rounding noise

# Telemetry/batch operating envelope shared by every tool surface (MCP schemas,
# SDK @function_tool engines, dashboard). The engines reject out-of-envelope
# inputs so no surface can bypass validation with raw floats.
UV_INDEX_MIN = 0.0
UV_INDEX_MAX = 16.0
TEMP_C_MIN = -10.0
TEMP_C_MAX = 55.0
RH_PCT_MIN = 5.0
RH_PCT_MAX = 100.0
BATCH_L_MAX = 10.0


# ---------------------------------------------------------------------------
# 2. Pure-math domain engine (zero dependencies)
# ---------------------------------------------------------------------------

def _kelvin(temp_c: float) -> float:
    return temp_c + 273.15


@dataclass(frozen=True)
class KineticsResult:
    k_baseline_per_hr: float
    f_uv: float
    f_temp: float
    k_dynamic_per_hr: float
    half_life_hrs: float
    viability_pct_after_1h: float


@dataclass(frozen=True)
class RecipeResult:
    biopesticide_l: float
    uv_stabilizer_l: float
    surfactant_l: float
    carrier_water_l: float
    total_batch_volume_l: float
    recommended_lignin_pct: float
    surfactant_pct: float
    uv_index: float
    ambient_temp_c: float
    relative_humidity_pct: float


@dataclass(frozen=True)
class SafetyViolation:
    rule: str
    detail: str


class KineticsEngine:
    """Deterministic degradation kinetics per the confirmed formulas."""

    def f_uv(self, uv_index: float) -> float:
        return 1.0 + ALPHA_UV * max(0.0, uv_index)

    def f_temp(self, temp_c: float) -> float:
        t = _kelvin(temp_c)
        if t <= 0.0:
            return 1.0
        return math.exp(-(EA_J_PER_MOL / R_GAS) * ((1.0 / t) - (1.0 / T0_KELVIN)))

    def k_dynamic(self, uv_index: float, temp_c: float) -> float:
        return K_BASELINE_PER_HR * self.f_uv(uv_index) * self.f_temp(temp_c)

    def half_life(self, uv_index: float, temp_c: float) -> float:
        k = self.k_dynamic(uv_index, temp_c)
        return math.log(2) / k if k > 0 else math.inf

    def compute(self, uv_index: float, temp_c: float) -> KineticsResult:
        if not UV_INDEX_MIN <= uv_index <= UV_INDEX_MAX:
            raise ValueError(
                f"uv_index must be in [{UV_INDEX_MIN}, {UV_INDEX_MAX}], got {uv_index}"
            )
        if not TEMP_C_MIN <= temp_c <= TEMP_C_MAX:
            raise ValueError(
                f"ambient_temp_c must be in [{TEMP_C_MIN}, {TEMP_C_MAX}], got {temp_c}"
            )
        f_uv = self.f_uv(uv_index)
        f_temp = self.f_temp(temp_c)
        k = K_BASELINE_PER_HR * f_uv * f_temp
        hl = math.log(2) / k if k > 0 else math.inf
        return KineticsResult(
            k_baseline_per_hr=round(K_BASELINE_PER_HR, 6),
            f_uv=round(f_uv, 4),
            f_temp=round(f_temp, 4),
            k_dynamic_per_hr=round(k, 6),
            half_life_hrs=round(hl, 3) if math.isfinite(hl) else None,
            viability_pct_after_1h=round(100.0 * math.exp(-k * 1.0), 4),
        )


class FormulationEngine:
    """Recipe stoichiometry per the confirmed scaling laws."""

    def recommended_lignin_pct(self, uv_index: float) -> float:
        return min(LIGNIN_MAX_PCT, LIGNIN_BASE_PCT + LIGNIN_BETA_PCT_PER_UV * max(0.0, uv_index))

    def surfactant_pct(self, rh_pct: float, temp_c: float) -> float:
        base = SURF_BASE_PCT * (1.0 + SURF_DELTA * (1.0 - rh_pct / 100.0))
        temp_factor = (_kelvin(temp_c) / SURF_TEMP_REF_K) ** 1.5
        return min(SURF_MAX_PCT, base * temp_factor)

    def recipe(
        self,
        batch_volume_l: float,
        uv_index: float,
        temp_c: float,
        rh_pct: float,
    ) -> RecipeResult:
        if not 0.0 < batch_volume_l <= BATCH_L_MAX:
            raise ValueError(
                f"batch_volume_l must be in (0, {BATCH_L_MAX}], got {batch_volume_l}"
            )
        if not UV_INDEX_MIN <= uv_index <= UV_INDEX_MAX:
            raise ValueError(
                f"uv_index must be in [{UV_INDEX_MIN}, {UV_INDEX_MAX}], got {uv_index}"
            )
        if not TEMP_C_MIN <= temp_c <= TEMP_C_MAX:
            raise ValueError(
                f"ambient_temp_c must be in [{TEMP_C_MIN}, {TEMP_C_MAX}], got {temp_c}"
            )
        if not RH_PCT_MIN <= rh_pct <= RH_PCT_MAX:
            raise ValueError(
                f"relative_humidity_pct must be in [{RH_PCT_MIN}, {RH_PCT_MAX}], got {rh_pct}"
            )
        bio_l = batch_volume_l * ACTIVE_RATIO
        lignin_pct = self.recommended_lignin_pct(uv_index)
        surf_pct = self.surfactant_pct(rh_pct, temp_c)
        uv_l = batch_volume_l * (lignin_pct / 100.0)
        surf_l = batch_volume_l * (surf_pct / 100.0)
        water_l = batch_volume_l - (bio_l + uv_l + surf_l)
        return RecipeResult(
            biopesticide_l=round(bio_l, VOLUME_DECIMALS),
            uv_stabilizer_l=round(uv_l, VOLUME_DECIMALS),
            surfactant_l=round(surf_l, VOLUME_DECIMALS),
            carrier_water_l=round(water_l, VOLUME_DECIMALS),
            total_batch_volume_l=round(batch_volume_l, VOLUME_DECIMALS),
            recommended_lignin_pct=round(lignin_pct, 4),
            surfactant_pct=round(surf_pct, 4),
            uv_index=uv_index,
            ambient_temp_c=temp_c,
            relative_humidity_pct=rh_pct,
        )


class SafetyValidator:
    """Guardrail checks against the confirmed regulatory and mechanical limits."""

    def validate_recipe(self, recipe: RecipeResult) -> List[SafetyViolation]:
        violations: List[SafetyViolation] = []
        if recipe.surfactant_pct > SURF_MAX_PCT:
            violations.append(
                SafetyViolation(
                    "surfactant_phytotoxicity",
                    f"surfactant {recipe.surfactant_pct:.4f}% exceeds cap {SURF_MAX_PCT:.2f}%",
                )
            )
        if recipe.recommended_lignin_pct > LIGNIN_MAX_PCT:
            violations.append(
                SafetyViolation(
                    "lignin_solubility",
                    f"lignin {recipe.recommended_lignin_pct:.3f}% exceeds solubility {LIGNIN_MAX_PCT:.2f}%",
                )
            )
        negative_components = [
            name
            for name, volume in (
                ("biopesticide", recipe.biopesticide_l),
                ("uv_stabilizer", recipe.uv_stabilizer_l),
                ("surfactant", recipe.surfactant_l),
                ("carrier_water", recipe.carrier_water_l),
            )
            if volume < 0
        ]
        if negative_components:
            violations.append(
                SafetyViolation(
                    "negative_volume",
                    "recipe contains negative component volume(s): "
                    + ", ".join(negative_components),
                )
            )
        if not math.isclose(
            recipe.biopesticide_l
            + recipe.uv_stabilizer_l
            + recipe.surfactant_l
            + recipe.carrier_water_l,
            recipe.total_batch_volume_l,
            rel_tol=1e-9,
            abs_tol=VOLUME_BALANCE_ABS_TOL,
        ):
            violations.append(SafetyViolation("volume_balance", "component volumes do not sum to batch volume"))
        return violations

    def validate_dispatch(self, commands: List[Dict[str, Any]]) -> List[SafetyViolation]:
        violations: List[SafetyViolation] = []
        for cmd in commands:
            if cmd["duration_sec"] > MAX_PUMP_CYCLE_SEC:
                violations.append(
                    SafetyViolation(
                        "pump_thermal_cycle",
                        f"pump {cmd['pump_id']} runtime {cmd['duration_sec']:.1f}s exceeds "
                        f"{MAX_PUMP_CYCLE_SEC:.0f}s threshold",
                    )
                )
        return violations


# ---------------------------------------------------------------------------
# 3. Tool surface (Pydantic schemas when available, dicts otherwise)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field, field_validator  # type: ignore
    HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    HAS_PYDANTIC = False
    BaseModel = object  # type: ignore

# Shared SCADA contract (src/twin/contracts.py, ticket #6). Imported lazily so
# the pure-math core keeps working when the contracts' deps are absent.
try:
    from src.twin.contracts import ChemicalRecipe, PumpCommand, SCADAPayload  # type: ignore
    HAS_CONTRACTS = True
except ImportError:  # pragma: no cover
    HAS_CONTRACTS = False
    ChemicalRecipe = PumpCommand = SCADAPayload = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _pydantic_schemas() -> Dict[str, type]:
    """Define Pydantic tool-input models (only when pydantic is installed)."""
    if not HAS_PYDANTIC:
        return {}

    class FieldTelemetryInput(BaseModel):
        zone_id: str = Field(description="Field management sector identifier")
        uv_index: float = Field(ge=UV_INDEX_MIN, le=UV_INDEX_MAX, description="Ambient UV Index")
        ambient_temp_c: float = Field(ge=TEMP_C_MIN, le=TEMP_C_MAX, description="Temperature in Celsius")
        relative_humidity_pct: float = Field(ge=RH_PCT_MIN, le=RH_PCT_MAX, description="Relative humidity percentage")
        batch_volume_l: float = Field(default=BATCH_DEFAULT_L, gt=0.0, le=BATCH_L_MAX, description="Batch volume in litres")

    class BatchRecipeInput(BaseModel):
        zone_id: str = Field(description="Field management sector identifier")
        batch_volume_l: float = Field(default=BATCH_DEFAULT_L, gt=0.0, le=BATCH_L_MAX, description="Batch volume in litres")
        uv_index: float = Field(ge=UV_INDEX_MIN, le=UV_INDEX_MAX, description="Ambient UV Index")
        ambient_temp_c: float = Field(ge=TEMP_C_MIN, le=TEMP_C_MAX, description="Temperature in Celsius")
        relative_humidity_pct: float = Field(ge=RH_PCT_MIN, le=RH_PCT_MAX, description="Relative humidity percentage")

    class DispatchInput(BaseModel):
        zone_id: str = Field(description="Field management sector identifier")
        batch_volume_l: float = Field(default=BATCH_DEFAULT_L, gt=0.0, le=BATCH_L_MAX, description="Batch volume in litres")
        uv_index: float = Field(ge=UV_INDEX_MIN, le=UV_INDEX_MAX, description="Ambient UV Index")
        ambient_temp_c: float = Field(ge=TEMP_C_MIN, le=TEMP_C_MAX, description="Temperature in Celsius")
        relative_humidity_pct: float = Field(ge=RH_PCT_MIN, le=RH_PCT_MAX, description="Relative humidity percentage")
        dispatch: bool = Field(default=False, description="Publish to MQTT broker (requires broker running)")
        sim_speed: int = Field(default=10, ge=1, le=1000, description="Digital twin simulation acceleration factor")

        @field_validator("relative_humidity_pct")
        @classmethod
        def _rh_range(cls, v: float) -> float:
            if not RH_PCT_MIN <= v <= RH_PCT_MAX:
                raise ValueError(f"relative_humidity_pct must be in [{RH_PCT_MIN}, {RH_PCT_MAX}]")
            return v

    return {
        "telemetry": FieldTelemetryInput,
        "recipe": BatchRecipeInput,
        "dispatch": DispatchInput,
    }


_SCHEMAS: Dict[str, type] = _pydantic_schemas()


# ---------------------------------------------------------------------------
# 4. MQTT dispatch (lazy — only used when --dispatch / explicit tool arg)
# ---------------------------------------------------------------------------

def _publish_scada_payload(zone_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except ImportError as exc:  # pragma: no cover
        return {"published": False, "error": f"paho-mqtt not installed: {exc}"}

    topic = MQTT_TOPIC.format(zone_id=zone_id)
    client = mqtt.Client(client_id="AgriAgent_SCADA")
    client.connect(MQTT_BROKER_DEFAULT, MQTT_PORT_DEFAULT, 60)
    # QoS 1 needs the network loop running to receive the PUBACK that
    # wait_for_publish() waits on; without it the call blocks forever.
    client.loop_start()
    try:
        info = client.publish(topic, json.dumps(payload), qos=1)
        info.wait_for_publish()
    finally:
        client.loop_stop()
        client.disconnect()
    return {"published": True, "topic": topic, "broker": f"{MQTT_BROKER_DEFAULT}:{MQTT_PORT_DEFAULT}"}


def _build_dispatch_payload(
    zone_id: str,
    recipe: RecipeResult,
    safety_validated: bool,
    sim_speed: int = 10,
    safety_violations: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Build the canonical SCADAPayload dict (contract shape, ticket #6).

    duration_sec is informational: the twin recomputes runtimes from its own
    calibrated flow table. sim_speed is explicit and defaults to 10.
    """
    commands: List[Dict[str, Any]] = []
    for pump_id, (chem, volume) in enumerate(
        (
            ("biopesticide", recipe.biopesticide_l),
            ("uv_stabilizer", recipe.uv_stabilizer_l),
            ("surfactant", recipe.surfactant_l),
            ("carrier_water", recipe.carrier_water_l),
        ),
        start=1,
    ):
        if volume <= 0:
            continue
        flow = PUMP_FLOW_L_PER_S[pump_id]
        commands.append(
            {
                "pump_id": pump_id,
                "chemical_name": chem,
                "volume_l": round(volume, VOLUME_DECIMALS),
                "flow_rate_l_per_sec": flow,
                "duration_sec": round(volume / flow, DURATION_DECIMALS),
            }
        )

    payload: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "zone_id": zone_id,
        "safety_validated": safety_validated,
        "sim_speed": sim_speed,
        "recipe": {
            "biopesticide_l": recipe.biopesticide_l,
            "uv_stabilizer_l": recipe.uv_stabilizer_l,
            "surfactant_l": recipe.surfactant_l,
            "carrier_water_l": recipe.carrier_water_l,
            "total_batch_volume_l": recipe.total_batch_volume_l,
        },
        "commands": commands,
    }
    if safety_violations:
        payload["safety_violations"] = [v.__dict__ for v in safety_violations]

    # When the shared contract is available, validate/normalize the payload
    # through it so the twin and any consumer parse an identical shape.
    if HAS_CONTRACTS:
        try:
            payload = SCADAPayload(**payload).model_dump()
        except Exception:
            pass  # keep the dict; the twin validates on its side too
    return payload


# ---------------------------------------------------------------------------
# 5. Tool implementations (shared by MCP registration and local invocation)
# ---------------------------------------------------------------------------

_kinetics = KineticsEngine()
_formulation = FormulationEngine()
_safety = SafetyValidator()


def _tool_compute_degradation_kinetics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Perception Agent: degradation half-life from live UV + temperature."""
    result = _kinetics.compute(float(args["uv_index"]), float(args["ambient_temp_c"]))
    return {
        "zone_id": args.get("zone_id", ""),
        **result.__dict__,
        "viability_pct_after_1h": result.viability_pct_after_1h,
    }


def _tool_generate_chemical_recipe(args: Dict[str, Any]) -> Dict[str, Any]:
    """Formulation Agent: exact litre setpoints for the batch."""
    recipe = _formulation.recipe(
        float(args["batch_volume_l"]),
        float(args["uv_index"]),
        float(args["ambient_temp_c"]),
        float(args["relative_humidity_pct"]),
    )
    violations = _safety.validate_recipe(recipe)
    return {
        "zone_id": args.get("zone_id", ""),
        "recipe": recipe.__dict__,
        "safety_ok": len(violations) == 0,
        "safety_violations": [v.__dict__ for v in violations],
    }


def _tool_dispatch_scada_dosing(args: Dict[str, Any]) -> Dict[str, Any]:
    """Actuator Agent: compute pump runtimes, safety-gate, optionally publish."""
    recipe = _formulation.recipe(
        float(args["batch_volume_l"]),
        float(args["uv_index"]),
        float(args["ambient_temp_c"]),
        float(args["relative_humidity_pct"]),
    )
    recipe_violations = _safety.validate_recipe(recipe)
    sim_speed = int(args.get("sim_speed", 10))
    payload = _build_dispatch_payload(
        args["zone_id"],
        recipe,
        safety_validated=not recipe_violations,
        sim_speed=sim_speed,
        safety_violations=recipe_violations,
    )
    dispatch_violations = _safety.validate_dispatch(payload["commands"])
    all_violations = recipe_violations + dispatch_violations

    result: Dict[str, Any] = {
        "zone_id": args["zone_id"],
        "safety_validated": not all_violations,
        "safety_violations": [v.__dict__ for v in all_violations],
        "payload": payload if not all_violations else None,
    }
    if all_violations:
        result["message"] = "DISPATCH REJECTED by safety guardrail."
        return result

    if args.get("dispatch"):
        mqtt_result = _publish_scada_payload(args["zone_id"], payload)
        result["mqtt"] = mqtt_result
        result["message"] = (
            f"DISPATCH SUCCESS to {mqtt_result.get('topic', '')}"
            if mqtt_result.get("published")
            else f"DISPATCH FAILED: {mqtt_result.get('error', 'unknown')}"
        )
    else:
        result["message"] = "DISPATCH PREVIEW (pass dispatch=true to publish over MQTT)."
    return result


TOOLS: Dict[str, Dict[str, Any]] = {
    "compute_degradation_kinetics": {
        "description": "Compute Bt degradation half-life and 1-hour viability from UV index and temperature (Perception Agent).",
        "schema_name": "telemetry",
        "handler": _tool_compute_degradation_kinetics,
    },
    "generate_chemical_recipe": {
        "description": "Compute the exact litre recipe for biopesticide, UV stabilizer, surfactant, and carrier water (Formulation Agent).",
        "schema_name": "recipe",
        "handler": _tool_generate_chemical_recipe,
    },
    "dispatch_scada_dosing": {
        "description": "Safety-gate the recipe, compute pump runtimes, and (optionally) publish the SCADA payload over MQTT (Actuator Agent).",
        "schema_name": "dispatch",
        "handler": _tool_dispatch_scada_dosing,
    },
}


# ---------------------------------------------------------------------------
# 6. MCP server registration (lazy — needs the mcp SDK)
# ---------------------------------------------------------------------------

def _run_mcp_stdio() -> int:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except ImportError as exc:  # pragma: no cover
        print(f"mcp SDK not installed ({exc}). Install with: pip install mcp", file=sys.stderr)
        return 2

    mcp = FastMCP("AgriAgent-SCADA")

    schema = _SCHEMAS.get("telemetry")
    if schema:

        @mcp.tool()
        def compute_degradation_kinetics(telemetry: schema) -> Dict[str, Any]:  # type: ignore[misc]
            """Compute Bt degradation half-life and viability from live UV + temperature."""
            return _tool_compute_degradation_kinetics(telemetry.model_dump())

        @mcp.tool()
        def generate_chemical_recipe(input: schema) -> Dict[str, Any]:  # type: ignore[misc]
            """Compute exact litre recipe setpoints for the batch."""
            return _tool_generate_chemical_recipe(input.model_dump())

        @mcp.tool()
        def dispatch_scada_dosing(input: schema) -> Dict[str, Any]:  # type: ignore[misc]
            """Safety-gate recipe, compute pump runtimes, optionally publish over MQTT."""
            return _tool_dispatch_scada_dosing(input.model_dump())
    else:  # pragma: no cover
        # Fallback: register tools taking raw JSON strings when pydantic is absent.
        for name, spec in TOOLS.items():

            @mcp.tool()
            def _raw(name: str = name, spec: Dict[str, Any] = spec, **kwargs: Any) -> str:
                """Fallback tool taking JSON args (pydantic not installed)."""
                return json.dumps(spec["handler"](kwargs))

    mcp.run(transport="stdio")
    return 0


# ---------------------------------------------------------------------------
# 7. CLI + self-test
# ---------------------------------------------------------------------------

def _selftest() -> int:
    """Run the deterministic engine checks without any MCP/MQTT dependency."""
    failures = []

    def check(label: str, got: Any, expected: Any, tol: float = 1e-3) -> None:
        ok = abs(float(got) - float(expected)) <= tol
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got={got} expected~{expected}")
        if not ok:
            failures.append(label)

    # 1. Kinetics — doc scenario (UV 9.2, 38 C). Confirmed: k_deg ~0.082/hr, t1/2 ~8.5 hr.
    kin = _kinetics.compute(9.2, 38.0)
    check("k_baseline", kin.k_dynamic_per_hr, 0.082, tol=0.005)
    check("half_life", kin.half_life_hrs, 8.5, tol=0.6)
    check("f_uv", kin.f_uv, 1 + 0.18 * 9.2)
    check("viability_1h", kin.viability_pct_after_1h, 100 * math.exp(-0.082), tol=0.6)

    # 2. Recipe — same scenario, 0.5 L batch. Confirmed: bio 0.04 L, lignin 2.55%,
    #    surfactant ~0.099% (capped at 0.20%), water balances.
    rec = _formulation.recipe(0.5, 9.2, 38.0, 32.0)
    check("bio_l", rec.biopesticide_l, 0.04, tol=1e-6)
    check("lignin_pct", rec.recommended_lignin_pct, 2.55, tol=0.01)
    check("lignin_l", rec.uv_stabilizer_l, 0.01275, tol=1e-5)
    check("surf_pct_capped", rec.surfactant_pct, 0.099, tol=0.01)
    check("surf_l", rec.surfactant_l, 0.0005, tol=1e-4)
    check("water_l", rec.carrier_water_l, 0.5 - 0.04 - 0.01275 - 0.0005, tol=1e-4)

    # 3. Safety — the doc's bad example (0.9% surfactant) must be REJECTED.
    bad = RecipeResult(
        biopesticide_l=0.045, uv_stabilizer_l=0.0145, surfactant_l=0.0045,
        carrier_water_l=0.4363, total_batch_volume_l=0.5,
        recommended_lignin_pct=2.55, surfactant_pct=0.9,
        uv_index=9.2, ambient_temp_c=38.0, relative_humidity_pct=32.0,
    )
    viol = _safety.validate_recipe(bad)
    check("rejects_overcap_surfactant", len(viol) > 0, True)
    check("violation_is_phytotoxicity", any(v.rule == "surfactant_phytotoxicity" for v in viol), True)

    # 4. Pump runtimes from confirmed flow table (pump 4 at 0.05 L/s).
    payload = _build_dispatch_payload("zone_north", rec, safety_validated=True)
    durs = {c["pump_id"]: c["duration_sec"] for c in payload["commands"]}
    check("pump1_duration", durs[1], 0.04 / 0.01, tol=0.01)
    check("pump4_duration", durs[4], rec.carrier_water_l / 0.05, tol=0.01)
    check("all_runtimes_under_30s", max(durs.values()) <= 30.0, True)

    # 5. Extreme UV caps lignin at 3.00%.
    rec_extreme = _formulation.recipe(0.5, 16.0, 38.0, 32.0)
    check("lignin_cap", rec_extreme.recommended_lignin_pct, 3.0, tol=0.001)

    # 6. Out-of-envelope inputs are rejected loudly (never silently approved).
    for label, kwargs in (
        ("rejects_out_of_range_rh", dict(batch_volume_l=0.5, uv_index=9.2, temp_c=38.0, rh_pct=200.0)),
        ("rejects_sub_absolute_zero_temp", dict(batch_volume_l=0.5, uv_index=9.2, temp_c=-300.0, rh_pct=32.0)),
        ("rejects_oversized_batch", dict(batch_volume_l=20.0, uv_index=9.2, temp_c=38.0, rh_pct=32.0)),
        ("kinetics_rejects_out_of_range_uv", None),
    ):
        try:
            if kwargs is None:
                _kinetics.compute(99.0, 38.0)
            else:
                _formulation.recipe(**kwargs)
            rejected = False
        except ValueError:
            rejected = True
        check(label, rejected, True)

    # 7. Any negative component volume is a safety violation (FR-3).
    neg = RecipeResult(
        biopesticide_l=0.04, uv_stabilizer_l=0.01275, surfactant_l=-0.0005,
        carrier_water_l=0.4473, total_batch_volume_l=0.5,
        recommended_lignin_pct=2.55, surfactant_pct=-0.01,
        uv_index=9.2, ambient_temp_c=38.0, relative_humidity_pct=200.0,
    )
    neg_viol = _safety.validate_recipe(neg)
    check("rejects_negative_component_volume", any(v.rule == "negative_volume" for v in neg_viol), True)

    print(f"\n{'SELFTEST PASSED' if not failures else 'SELFTEST FAILED: ' + ', '.join(failures)}")
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="Run engine self-test and exit")
    parser.add_argument("--demo", action="store_true", help="Print a sample recipe + dispatch preview and exit")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if args.demo:
        rec = _formulation.recipe(BATCH_DEFAULT_L, 9.2, 38.0, 32.0)
        payload = _build_dispatch_payload("zone_north", rec, safety_validated=True)
        print(json.dumps({"recipe": rec.__dict__, "dispatch": payload}, indent=2))
        return 0
    return _run_mcp_stdio()


if __name__ == "__main__":
    sys.exit(main())
