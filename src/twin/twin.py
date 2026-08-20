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

Usage:
    python -m src.twin.twin            # connect to localhost:1883
    AGRIA_MQTT_BROKER=192.168.1.5 python -m src.twin.twin
"""

from __future__ import annotations

import json
import time
import threading
from typing import Dict, List

import paho.mqtt.client as mqtt

from src.twin.contracts import SCADAPayload


class TwinState:
    """State feedback schema for the digital-twin status topic (ticket #6)."""

    def __init__(
        self,
        timestamp: float,
        zone_id: str,
        tanks_ml: Dict[str, float],
        current_batch_ml: float,
        alarms: List[str],
        last_dispatch_id: str,
    ) -> None:
        self.timestamp = timestamp
        self.zone_id = zone_id
        self.tanks_ml = tanks_ml
        self.current_batch_ml = current_batch_ml
        self.alarms = alarms
        self.last_dispatch_id = last_dispatch_id

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "zone_id": self.zone_id,
            "tanks_ml": self.tanks_ml,
            "current_batch_ml": self.current_batch_ml,
            "alarms": self.alarms,
            "last_dispatch_id": self.last_dispatch_id,
        }


class DigitalTwinSCADA:
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        # Virtual reservoir levels in mL (scope doc §6)
        self.tanks: Dict[str, float] = {
            "biopesticide": 5000.0,
            "uv_stabilizer": 2000.0,
            "surfactant": 1000.0,
            "carrier_water": 50000.0,
        }
        self.mix_tank = 0.0
        self.lock = threading.Lock()

        # Twin-authoritative pump calibration (mL/sec), ticket #3/#6.
        # The sender's duration_sec is informational only — recomputed here.
        self.flow_rates: Dict[str, float] = {
            "biopesticide": 10.0,
            "uv_stabilizer": 10.0,
            "surfactant": 10.0,
            "carrier_water": 50.0,
        }

        self.client = mqtt.Client(client_id="DigitalTwinEngine")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker_host, broker_port, 60)

    def on_connect(self, client, userdata, flags, rc):
        print(f"[DIGITAL TWIN] Connected to MQTT Broker with result code: {rc}")
        client.subscribe("agri/actuator/+/dosing_dispatch")

    def on_message(self, client, userdata, msg):
        try:
            payload = SCADAPayload(**json.loads(msg.payload.decode("utf-8")))
        except Exception as exc:
            print(f"[DIGITAL TWIN] REJECT: invalid payload ({exc})")
            return

        print(f"\n[DIGITAL TWIN] Setpoint received for Zone: {payload.zone_id}")

        if not payload.safety_validated:
            print("[DIGITAL TWIN] EMERGENCY REJECT: Safety verification flag false.")
            return

        threading.Thread(target=self._execute_dosing, args=(payload,)).start()

    def _execute_dosing(self, payload: SCADAPayload):
        with self.lock:
            alarms: List[str] = []
            for cmd in payload.commands:
                chem = cmd.chemical_name
                vol = cmd.volume_ml

                if self.tanks[chem] < vol:
                    msg = (
                        f"LOW_TANK {chem}: required {vol} mL, available {self.tanks[chem]:.1f} mL"
                    )
                    print(f"[DIGITAL TWIN] ALARM: {msg}")
                    alarms.append(msg)
                    continue

                # Twin-authoritative runtime: volume / own calibrated flow rate.
                actual_dur = vol / self.flow_rates.get(chem, 10.0)
                print(
                    f"[ACTUATOR] Pump {cmd.pump_id} ({chem}) ON -> "
                    f"Dispensing {vol} mL over {actual_dur:.2f}s (sim x{payload.sim_speed})..."
                )
                time.sleep(actual_dur / payload.sim_speed)

                self.tanks[chem] -= vol
                self.mix_tank += vol
                print(
                    f"[ACTUATOR] Pump {cmd.pump_id} ({chem}) OFF. "
                    f"Tank level: {self.tanks[chem]:.1f} mL"
                )

            self._publish_state(payload.zone_id, alarms, payload.timestamp)

    def _publish_state(self, zone_id: str, alarms: List[str], last_dispatch_id: str):
        state = TwinState(
            timestamp=time.time(),
            zone_id=zone_id,
            tanks_ml=dict(self.tanks),
            current_batch_ml=self.mix_tank,
            alarms=alarms,
            last_dispatch_id=last_dispatch_id,
        )
        self.client.publish(
            f"agri/digital_twin/{zone_id}/tank_status",
            json.dumps(state.to_dict()),
        )

    def start(self):
        self.client.loop_forever()


if __name__ == "__main__":
    twin = DigitalTwinSCADA()
    twin.start()
