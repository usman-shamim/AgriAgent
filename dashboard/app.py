"""
AgriAgent — SCADA dashboard (prototype).

Prototype answer: does a live Streamlit view of the telemetry → recipe → dispatch
→ twin tank state loop feel right for the stage demo?

Reads the digital twin's tank_status topic over MQTT and renders KPIs, the
computed recipe, dispatch preview, and tank depletion live. Pure prototype —
no persistence, minimal polish, state in memory.

Run: streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import streamlit as st

# Allow `streamlit run dashboard/app.py` from the repo root: ensure the repo
# root is importable so `src.*` resolves (same shim as src/twin/twin.py).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mcp_server_scada import (
    KineticsEngine,
    FormulationEngine,
    SafetyValidator,
    _build_dispatch_payload,
    _tool_dispatch_scada_dosing,
)

# ---------------------------------------------------------------------------
# MQTT state feed (background thread → process-wide state, cached across reruns)
# ---------------------------------------------------------------------------

ZONE_ID = "zone_north"
_BROKER = os.getenv("AGRIA_MQTT_BROKER", "localhost")
_PORT = int(os.getenv("AGRIA_MQTT_PORT", "1883"))


@st.cache_resource
def _twin_state() -> Dict[str, Any]:
    """Latest tank_status plus recent events, held in a cache_resource so there
    is exactly ONE instance per process. A module-level global would be reset to
    empty on every full-script rerun, dropping the retained message the twin sent."""
    return {"latest": {}, "events": []}


def _mqtt_listen() -> None:
    """Subscribe to the twin's tank_status and events topics and record them."""
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="AgriAgent_Dashboard")

    def on_connect(c, u, f, rc, p=None):
        c.subscribe("agri/digital_twin/+/tank_status")
        c.subscribe("agri/digital_twin/+/events")

    def on_message(c, u, msg):
        shared = _twin_state()
        payload = json.loads(msg.payload.decode("utf-8"))
        if msg.topic.endswith("/events"):
            shared["events"] = (shared["events"] + [payload])[-8:]
        else:
            shared["latest"] = payload

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(_BROKER, _PORT, 60)
        client.loop_start()  # non-blocking: returns immediately, runs callbacks in a thread
    except Exception:
        pass  # broker down — dashboard still renders with defaults


@st.cache_resource
def _start_mqtt_thread() -> None:
    t = threading.Thread(target=_mqtt_listen, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Deterministic chemistry (reuses the confirmed engines)
# ---------------------------------------------------------------------------

_kinetics = KineticsEngine()
_formulation = FormulationEngine()
_safety = SafetyValidator()


def compute_preview(uv: float, temp: float, rh: float, batch: float) -> Dict[str, Any]:
    kin = _kinetics.compute(uv, temp)
    recipe = _formulation.recipe(batch, uv, temp, rh)
    recipe_violations = _safety.validate_recipe(recipe)
    payload = _build_dispatch_payload(
        ZONE_ID, recipe, safety_validated=not recipe_violations, sim_speed=10
    )
    # The preview verdict must match the dispatch verdict: the 30s pump-cycle
    # thermal cap is a dispatch-time rule, so validate it here too.
    violations = recipe_violations + _safety.validate_dispatch(payload["commands"])
    payload["safety_validated"] = not violations
    return {
        "kinetics": kin.__dict__,
        "recipe": recipe.__dict__,
        "safety_ok": not violations,
        "violations": [v.__dict__ for v in violations],
        "payload": payload,
    }


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AgriAgent SCADA", page_icon=":material/agriculture:", layout="wide")

_start_mqtt_thread()

st.title("AgriAgent SCADA")
st.caption("Live biopesticide formulation — Perception → Formulation → Safety → Actuator")

# --- Telemetry inputs (sidebar) ---
with st.sidebar:
    st.header("Telemetry")
    uv = st.slider("UV index", 0.0, 16.0, 9.2, 0.1)
    temp = st.slider("Temperature (°C)", -10.0, 55.0, 38.0, 0.5)
    rh = st.slider("Relative humidity (%)", 5, 100, 32, 1)
    batch = st.number_input("Batch volume (L)", 0.1, 10.0, 0.5, 0.05, format="%.2f")
    st.caption("Preview only — nothing is dosed until you dispatch")

# --- Computed preview (deterministic, instant) ---
preview = compute_preview(uv, temp, rh, batch)

# --- Dispatch control (sidebar, below the telemetry inputs) ---
with st.sidebar:
    st.header("Dispatch")
    if st.button(
        "Dispatch now",
        type="primary",
        use_container_width=True,
        disabled=not preview["safety_ok"],
    ):
        with st.spinner("Publishing setpoint to the twin..."):
            st.session_state["dispatch_result"] = _tool_dispatch_scada_dosing(
                {
                    "zone_id": ZONE_ID,
                    "batch_volume_l": batch,
                    "uv_index": uv,
                    "ambient_temp_c": temp,
                    "relative_humidity_pct": float(rh),
                    "dispatch": True,
                    "sim_speed": 10,
                }
            )
    if not preview["safety_ok"]:
        st.caption("Disabled — the recipe fails safety validation.")

    last_result = st.session_state.get("dispatch_result")
    if last_result is not None:
        if last_result["safety_validated"]:
            st.success(last_result["message"], icon=":material/check_circle:")
        else:
            st.error(last_result["message"], icon=":material/error:")
            for v in last_result["safety_violations"]:
                st.caption(f"{v['rule']}: {v['detail']}")
kin = preview["kinetics"]
recipe = preview["recipe"]

# --- KPI row: kinetics ---
with st.container(horizontal=True):
    st.metric("Degradation rate k", f"{kin['k_dynamic_per_hr']:.4f} /hr", border=True)
    st.metric("Half-life", f"{kin['half_life_hrs']:.1f} h", border=True)
    st.metric("Viability after 1h", f"{kin['viability_pct_after_1h']:.1f}%", border=True)

st.header("Recipe")
with st.container(horizontal=True):
    st.metric("Biopesticide", f"{recipe['biopesticide_l']:.4f} L", border=True)
    st.metric("UV stabilizer", f"{recipe['uv_stabilizer_l']:.4f} L", border=True)
    st.metric("Surfactant", f"{recipe['surfactant_l']:.4f} L", border=True)
    st.metric("Carrier water", f"{recipe['carrier_water_l']:.4f} L", border=True)
    st.metric("Batch total", f"{recipe['total_batch_volume_l']:.2f} L", border=True)

if preview["safety_ok"]:
    st.success("Safety check passed — recipe approved.", icon=":material/check_circle:")
else:
    st.error("Safety check FAILED — " + "; ".join(v["detail"] for v in preview["violations"]), icon=":material/error:")

# --- Dispatch preview ---
with st.expander("Dispatch payload", icon=":material/terminal:"):
    st.json(preview["payload"])

# --- Twin live state (auto-refreshing fragment) ---
st.header("Digital twin")


@st.fragment(run_every=2)
def twin_panel() -> None:
    """Render the latest twin state (the MQTT thread keeps _twin_state current)."""
    shared = _twin_state()
    state = shared["latest"] or None
    events = shared["events"]

    st.subheader("Tank levels")
    if state is None:
        st.caption("No twin state yet — waiting for `agri/digital_twin/+/tank_status`...")
    else:
        tanks = state["tanks_l"]
        col1, col2, col3, col4 = st.columns(4, border=True)
        col1.metric("Biopesticide", f"{tanks.get('biopesticide', 0):.3f} L")
        col2.metric("UV stabilizer", f"{tanks.get('uv_stabilizer', 0):.3f} L")
        col3.metric("Surfactant", f"{tanks.get('surfactant', 0):.3f} L")
        col4.metric("Carrier water", f"{tanks.get('carrier_water', 0):.3f} L")
        with st.container(horizontal=True):
            st.metric("Latest batch", f"{state['current_batch_l']:.3f} L", border=True)
            st.metric("Total dispensed", f"{state['total_dispensed_l']:.3f} L", border=True)
        if state.get("alarms"):
            st.warning("; ".join(state["alarms"]), icon=":material/warning:")
        st.caption(f"Zone {state['zone_id']} · last updated {state['timestamp']}")

        df = pd.DataFrame([{"Chemical": k, "Level (L)": v} for k, v in tanks.items()])
        st.bar_chart(df, x="Chemical", y="Level (L)", horizontal=True)

    if events:
        st.subheader("Events")
        for event in reversed(events):
            label = f"{event['code']}: {event['detail']}"
            if event["code"] in ("SAFETY_REJECTED", "INVALID_PAYLOAD"):
                st.error(label, icon=":material/error:")
            elif event["code"] == "LOW_TANK":
                st.warning(label, icon=":material/warning:")
            else:
                st.info(label, icon=":material/info:")


twin_panel()
