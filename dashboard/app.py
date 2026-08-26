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
import queue
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

from src.mcp_server_scada import KineticsEngine, FormulationEngine, SafetyValidator, _build_dispatch_payload

# ---------------------------------------------------------------------------
# MQTT state feed (background thread → thread-safe queue → st.session_state)
# ---------------------------------------------------------------------------

_MSG_QUEUE: "queue.Queue[Dict[str, Any]]" = queue.Queue()
_LATEST_STATE: Dict[str, Any] = {}  # most recent tank_status, shared across fragments/reruns
_BROKER = os.getenv("AGRIA_MQTT_BROKER", "localhost")
_PORT = int(os.getenv("AGRIA_MQTT_PORT", "1883"))


def _mqtt_listen() -> None:
    """Subscribe to the twin's tank_status topic and push payloads to the queue."""
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="AgriAgent_Dashboard")

    def on_connect(c, u, f, rc, p=None):
        c.subscribe("agri/digital_twin/+/tank_status")

    def on_message(c, u, msg):
        payload = json.loads(msg.payload.decode("utf-8"))
        global _LATEST_STATE
        _LATEST_STATE = payload
        _MSG_QUEUE.put(payload)

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
    violations = _safety.validate_recipe(recipe)
    payload = _build_dispatch_payload("zone_north", recipe, safety_validated=not violations, sim_speed=10)
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
    batch = st.number_input("Batch volume (mL)", 100, 10_000, 500, 50)
    st.caption("Drag to re-run the pipeline")

# --- Computed preview (deterministic, instant) ---
preview = compute_preview(uv, temp, rh, batch)
kin = preview["kinetics"]
recipe = preview["recipe"]

# --- KPI row: kinetics ---
with st.container(horizontal=True):
    st.metric("Degradation rate k", f"{kin['k_dynamic_per_hr']:.4f} /hr", border=True)
    st.metric("Half-life", f"{kin['half_life_hrs']:.1f} h", border=True)
    st.metric("Viability after 1h", f"{kin['viability_pct_after_1h']:.1f}%", border=True)

st.header("Recipe")
with st.container(horizontal=True):
    st.metric("Biopesticide", f"{recipe['biopesticide_ml']:.1f} mL", border=True)
    st.metric("UV stabilizer", f"{recipe['uv_stabilizer_ml']:.1f} mL", border=True)
    st.metric("Surfactant", f"{recipe['surfactant_ml']:.1f} mL", border=True)
    st.metric("Carrier water", f"{recipe['carrier_water_ml']:.1f} mL", border=True)
    st.metric("Batch total", f"{recipe['total_batch_volume_ml']:.0f} mL", border=True)

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
    """Render the latest twin state (the MQTT thread keeps _LATEST_STATE current)."""
    state = _LATEST_STATE or None

    st.subheader("Tank levels")
    if state is None:
        st.caption("No twin state yet — waiting for `agri/digital_twin/+/tank_status`...")
        return

    tanks = state["tanks_ml"]
    col1, col2, col3, col4 = st.columns(4, border=True)
    col1.metric("Biopesticide", f"{tanks.get('biopesticide', 0):.0f} mL")
    col2.metric("UV stabilizer", f"{tanks.get('uv_stabilizer', 0):.0f} mL")
    col3.metric("Surfactant", f"{tanks.get('surfactant', 0):.0f} mL")
    col4.metric("Carrier water", f"{tanks.get('carrier_water', 0):.0f} mL")
    st.metric("Mixed batch so far", f"{state['current_batch_ml']:.0f} mL", border=True)
    if state.get("alarms"):
        for a in state["alarms"]:
            st.warning(a, icon=":material/warning:")
    st.caption(f"Zone {state['zone_id']} · last updated {state['timestamp']}")

    df = pd.DataFrame([{"Chemical": k, "Level (mL)": v} for k, v in tanks.items()])
    st.bar_chart(df, x="Chemical", y="Level (mL)", horizontal=True)


twin_panel()
