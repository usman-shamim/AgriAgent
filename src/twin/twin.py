"""
AgriAgent — Digital Twin Simulation Engine

A decoupled background service that consumes validated SCADAPayload dispatches
from the MCP tool server, simulates reservoir depletion and pump actuation, and
publishes TwinState feedback to the digital-twin status topic.

Contract (src/twin/contracts.py, settled by wayfinder ticket #6):
  - Incoming messages are validated through SCADAPayload before actuation.
  - The twin is AUTHORITATIVE for pump runtimes: it recomputes each duration
    from its own calibrated flow table, ignoring the sender's informational
    duration_sec.
  - Simulation speed is explicit via the payload's sim_speed field
    (default 10): sleep = actual_duration / sim_speed.
  - Low-tank events raise machine-readable alarms in the published state
    instead of silently skipping.
  - State is published after EVERY pump command (not only at the end), so tank
    levels are observable as they fall. Alarms and rejections also go out as
    transient events on the events topic.

All volumes are SI litres (L) and flows L/s.

Usage:
    python -m src.twin.twin            # connect to localhost:1883
    AGRIA_MQTT_BROKER=192.168.1.5 python -m src.twin.twin
"""

from __future__ import annotations

import json
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# Allow both `python src/twin/twin.py` and `python -m src.twin.twin`:
# ensure the repo root is importable so `src.twin.contracts` resolves.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.twin.contracts import SCADAPayload

DISPATCH_TOPIC = "agri/actuator/+/dosing_dispatch"
STATE_TOPIC = "agri/digital_twin/{zone_id}/tank_status"
EVENTS_TOPIC = "agri/digital_twin/{zone_id}/events"


class TwinState:
    """State feedback schema for the digital-twin status topic (ticket #6)."""

    def __init__(
        self,
        timestamp: float,
        zone_id: str,
        tanks_l: Dict[str, float],
        current_batch_l: float,
        total_dispensed_l: float,
        alarms: List[str],
        last_dispatch_id: str,
    ) -> None:
        self.timestamp = timestamp
        self.zone_id = zone_id
        self.tanks_l = tanks_l
        self.current_batch_l = current_batch_l
        self.total_dispensed_l = total_dispensed_l
        self.alarms = alarms
        self.last_dispatch_id = last_dispatch_id

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "zone_id": self.zone_id,
            "tanks_l": self.tanks_l,
            "current_batch_l": self.current_batch_l,
            "total_dispensed_l": self.total_dispensed_l,
            "alarms": self.alarms,
            "last_dispatch_id": self.last_dispatch_id,
        }


class DigitalTwinSCADA:
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        # Virtual reservoir levels in litres (scope doc §6)
        self.tanks: Dict[str, float] = {
            "biopesticide": 5.0,
            "uv_stabilizer": 2.0,
            "surfactant": 1.0,
            "carrier_water": 50.0,
        }
        self.total_dispensed = 0.0
        self.lock = threading.Lock()

        # Twin-authoritative pump calibration (L/sec), ticket #3/#6.
        # The sender's duration_sec is informational only — recomputed here.
        self.flow_rates: Dict[str, float] = {
            "biopesticide": 0.01,
            "uv_stabilizer": 0.01,
            "surfactant": 0.01,
            "carrier_water": 0.05,
        }

        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id="DigitalTwinEngine")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker_host, broker_port, 60)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[DIGITAL TWIN] Connected to MQTT Broker with result code: {reason_code}")
        client.subscribe(DISPATCH_TOPIC)

    def on_message(self, client, userdata, msg):
        zone_id = msg.topic.split("/")[2] if len(msg.topic.split("/")) > 2 else "unknown"
        try:
            payload = SCADAPayload(**json.loads(msg.payload.decode("utf-8")))
        except Exception as exc:
            print(f"[DIGITAL TWIN] REJECT: invalid payload ({exc})")
            self._publish_event(zone_id, "INVALID_PAYLOAD", str(exc))
            return

        print(f"\n[DIGITAL TWIN] Setpoint received for Zone: {payload.zone_id}")

        if not payload.safety_validated:
            print("[DIGITAL TWIN] EMERGENCY REJECT: Safety verification flag false.")
            self._publish_event(
                payload.zone_id, "SAFETY_REJECTED", "safety_validated is false; dispatch not actuated"
            )
            return

        threading.Thread(target=self._execute_dosing, args=(payload,)).start()

    def _execute_dosing(self, payload: SCADAPayload):
        with self.lock:
            alarms: List[str] = []
            batch_l = 0.0
            for cmd in payload.commands:
                chem = cmd.chemical_name
                vol = cmd.volume_l

                if self.tanks[chem] < vol:
                    msg = (
                        f"LOW_TANK {chem}: required {vol:.4f} L, available {self.tanks[chem]:.3f} L"
                    )
                    print(f"[DIGITAL TWIN] ALARM: {msg}")
                    alarms.append(msg)
                    self._publish_event(payload.zone_id, "LOW_TANK", msg)
                    self._publish_state(payload.zone_id, batch_l, alarms, payload.timestamp)
                    continue

                # Twin-authoritative runtime: volume / own calibrated flow rate.
                actual_dur = vol / self.flow_rates.get(chem, 0.01)
                print(
                    f"[ACTUATOR] Pump {cmd.pump_id} ({chem}) ON -> "
                    f"Dispensing {vol:.4f} L over {actual_dur:.2f}s (sim x{payload.sim_speed})..."
                )
                time.sleep(actual_dur / payload.sim_speed)

                self.tanks[chem] -= vol
                self.total_dispensed += vol
                batch_l += vol
                print(
                    f"[ACTUATOR] Pump {cmd.pump_id} ({chem}) OFF. "
                    f"Tank level: {self.tanks[chem]:.3f} L"
                )
                # Progressive feedback: one state publish per pump command.
                self._publish_state(payload.zone_id, batch_l, alarms, payload.timestamp)

            self._publish_event(
                payload.zone_id, "DISPATCH_COMPLETE", f"batch {batch_l:.4f} L dispensed"
            )

    def _publish_state(
        self, zone_id: str, current_batch_l: float, alarms: List[str], last_dispatch_id: str
    ) -> None:
        state = TwinState(
            timestamp=time.time(),
            zone_id=zone_id,
            tanks_l=dict(self.tanks),
            current_batch_l=current_batch_l,
            total_dispensed_l=self.total_dispensed,
            alarms=alarms,
            last_dispatch_id=last_dispatch_id,
        )
        self.client.publish(
            STATE_TOPIC.format(zone_id=zone_id),
            json.dumps(state.to_dict()),
            retain=True,  # late-joining subscribers (e.g. the dashboard) get the current state immediately
        )

    def _publish_event(self, zone_id: str, code: str, detail: str) -> None:
        """Transient operational events (not retained — they are history, not state)."""
        self.client.publish(
            EVENTS_TOPIC.format(zone_id=zone_id),
            json.dumps(
                {
                    "timestamp": time.time(),
                    "zone_id": zone_id,
                    "code": code,
                    "detail": detail,
                }
            ),
        )

    def start(self):
        self.client.loop_forever()


if __name__ == "__main__":
    twin = DigitalTwinSCADA()
    twin.start()
