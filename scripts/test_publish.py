import json
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# 1. The Option A Contract Payload
test_payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "zone_id": "zone_north",
    "safety_validated": True,
    "sim_speed": 10,
    "recipe": {
        "biopesticide_ml": 40.0,
        "uv_stabilizer_ml": 12.5,
        "surfactant_ml": 4.5,
        "carrier_water_ml": 443.0,
        "total_batch_volume_ml": 500.0
    },
    "commands": [
        {
            "pump_id": 1,
            "chemical_name": "biopesticide",
            "volume_ml": 40.0,
            "duration_sec": 4.0  # Twin should ignore this and calculate 40.0 / 10.0 = 4.0s
        },
        {
            "pump_id": 2,
            "chemical_name": "uv_stabilizer",
            "volume_ml": 12.5,
            "duration_sec": 1.25 # Twin should ignore this and calculate 12.5 / 10.0 = 1.25s
        },
        {
            "pump_id": 3,
            "chemical_name": "surfactant",
            "volume_ml": 4.5,
            "duration_sec": 0.45 # Twin should ignore this and calculate 4.5 / 10.0 = 0.45s
        },
        {
            "pump_id": 4,
            "chemical_name": "carrier_water",
            "volume_ml": 443.0,
            "duration_sec": 8.86 # Twin should ignore this and calculate 443.0 / 50.0 = 8.86s
        }
    ]
}

# 2. Configure MQTT Client
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "agri/actuator/zone_north/dosing_dispatch"

client = mqtt.Client(client_id="Test_Dispatcher_01")

print(f"Connecting to broker at {BROKER_HOST}:{BROKER_PORT}...")
client.connect(BROKER_HOST, BROKER_PORT, 60)

# 3. Publish the Payload
print(f"Publishing SCADAPayload to {TOPIC}...")
client.publish(TOPIC, json.dumps(test_payload), qos=1)

# Allow time for network delivery before disconnecting
time.sleep(1)
client.disconnect()
print("Dispatch complete.")
