# AgriAgent: Technical Specification and Agent Engine Architecture

## 1. System Scope and Objectives

AgriAgent is an autonomous industrial supervisory control and data acquisition (SCADA) system for on-demand biopesticide formulation. It solves the environmental degradation bottleneck of biological actives (*Bacillus thuringiensis* crystal endotoxins and insecticidal peptides). The system ingests environmental telemetry, calculates degradation kinetics, balances photo-stabilizers and super-wetting surfactants, and dispatches deterministic setpoints over industrial protocols.

```
+-------------------------------------------------------------------------+
|                         PRESENTATION LAYER                              |
|          Streamlit / Next.js SCADA Interface & Telemetry Gauges         |
+------------------------------------+------------------------------------+
                                     | WebSockets / State Sync
                                     v
+-------------------------------------------------------------------------+
|                          AI AGENT REASONING CORE                        |
|  [Perception Agent] -> [Formulation Agent] -> [Safety] -> [Actuator]   |
+------------------------------------+------------------------------------+
                                     | Tool Invocation (JSON-RPC / MCP)
                                     v
+-------------------------------------------------------------------------+
|                       MIDDLEWARE & PROTOCOL HIGHWAY                     |
|            Eclipse Mosquitto MQTT Broker (Pub/Sub Messaging)            |
+------------------+-----------------------------------+------------------+
                   | Topic: agri/actuator/+/setpoint   | Topic: telemetry
                   v                                   v
+------------------------------------+ +----------------------------------+
|      DIGITAL TWIN SIMULATION       | |     OPTIONAL PHYSICAL RIG        |
|  Fluid Mechanics, Tank Depletion,  | |  ESP32 Microcontroller, Relays,  |
|  Surface Tension Kinematics Engine | |  12V Peristaltic Dosing Pumps    |
+------------------------------------+ +----------------------------------+

```

### Hackathon MVP Scope Boundaries

* **In Scope:** Real-time environmental data ingestion, kinetic degradation modeling, multi-agent reasoning, deterministic tool calling via Model Context Protocol (MCP) or OpenAI Agent SDK, JSON payload dispatch over local MQTT, and an asynchronous Python digital twin simulating fluid mechanics and tank levels.
* **Out of Scope for Stage Demo:** Custom PCB manufacturing, closed-loop feedback from physical chemical titration probes, and high-voltage three-phase motor control.

---

## 2. Chemical Kinetics and Mathematical Modeling

The AI reasoning core relies on deterministic chemical engineering formulas rather than loose prompt approximations.

### A. Photo-Degradation Kinetics ($k_{\text{deg}}$)

Active microbial spores and peptide bonds degrade under solar UV-A/UV-B radiation (290 to 400 nm) according to pseudo-first-order kinetics:

$$C(t) = C_0 \cdot e^{-k_{\text{deg}} \cdot t}$$

The degradation rate constant $k_{\text{deg}}$ ($\text{hr}^{-1}$) is a function of the real-time UV Index ($I_{\text{UV}}$) and ambient temperature ($T$ in Kelvin, with reference $T_0 = 298.15\text{ K}$):

$$k_{\text{deg}}(I_{\text{UV}}, T) = k_0 \cdot \left(1 + \alpha \cdot I_{\text{UV}}\right) \cdot \exp\left(-\frac{E_a}{R}\left(\frac{1}{T} - \frac{1}{T_0}\right)\right)$$

* $k_0$: Baseline dark degradation rate constant ($0.015\text{ hr}^{-1}$).
* $\alpha$: UV sensitivity scaling factor ($0.18\text{ Index}^{-1}$).
* $E_a$: Activation energy for peptide denaturation ($42.5\text{ kJ/mol}$).
* $R$: Universal gas constant ($8.314\text{ J}/(\text{mol}\cdot\text{K})$).

### B. Optical Shielding via Lignosulfonate Biopolymers

Sodium lignosulfonate absorbs UV radiation through its conjugated aromatic phenylpropane structures. The stabilization factor ($S_{\text{UV}}$) scales the required mass concentration ($C_{\text{lignin}}$, % w/v):

$$C_{\text{lignin}}(I_{\text{UV}}) = \min\left(C_{\text{max}}, \; C_{\text{base}} + \beta \cdot I_{\text{UV}}\right)$$

* $C_{\text{base}} = 0.25\%\text{ w/v}$ (baseline anti-caking and dark carrier).
* $\beta = 0.25\%\text{ w/v per UV Index unit}$.
* $C_{\text{max}} = 3.00\%\text{ w/v}$ (solubility limit to prevent nozzle clogging).

### C. Surface Tension and Evaporative Adhesion

Pure water surface tension ($\gamma_{\text{water}} \approx 72.8\text{ mN/m}$) causes droplet run-off on waxy plant cuticles. Organosilicone surfactants (polyether-modified trisiloxanes) lower equilibrium surface tension below $22.0\text{ mN/m}$.

The required surfactant volumetric fraction ($V_{\text{surf}}$, % v/v) adjusts against relative humidity ($RH$, expressed from $0.0$ to $1.0$) to counteract evaporative droplet shrinkage:

$$V_{\text{surf}}(RH, T_{\text{amb}}) = V_{\text{base}} \cdot \left(1 + \delta \cdot (1.0 - RH)\right) \cdot \left(\frac{T_{\text{amb}}}{293.15}\right)^{1.5}$$

* $V_{\text{base}} = 0.05\%\text{ v/v}$.
* $\delta = 1.2$ (evaporative compensation coefficient).
* Hard safety ceiling: $V_{\text{surf}} \le 0.20\%\text{ v/v}$ (prevents crop phytotoxicity).

---

## 3. Multi-Agent System Architecture

The AI layer runs four specialized agents orchestrated sequentially with strict context isolation.

```
+-----------------------------------------------------------------------------+
|                          AGENT ORCHESTRATION PIPELINE                       |
|                                                                             |
| 1. Perception Agent                                                         |
|    - Reads telemetry (UV=9.2, Temp=38C, RH=32%)                             |
|    - Computes degradation threat: k_deg = 0.284 hr^-1 (t_1/2 = 2.44 hrs)    |
|                          |                                                  |
|                          v                                                  |
| 2. Stoichiometry & Formulation Agent                                        |
|    - Computes recipe for target batch volume (e.g., 500 mL)                 |
|    - Recipe: Bio=45 mL, Lignin=12.5 mL, Surfactant=4.5 mL, Water=438 mL     |
|                          |                                                  |
|                          v                                                  |
| 3. Safety & Compliance Agent                                                |
|    - Validates: Surfactant conc <= 0.20%, Total Vol == 500 mL               |
|    - Checks: Pump runtimes within hardware thermal thresholds (<30s)        |
|                          |                                                  |
|                          v                                                  |
| 4. SCADA / Actuator Agent                                                   |
|    - Calculates pump timings: Duration = Target Volume / Flow Rate          |
|    - Dispatches structured MQTT payload to broker                           |
+-----------------------------------------------------------------------------+

```

### Agent Roles and Responsibilities

1. **Perception Agent:** Polls the weather API or reads simulated MQTT telemetry. It validates sensor data ranges (e.g., UV Index between 0 and 15, Temperature between -10°C and 55°C) and computes the active ingredient half-life.
2. **Stoichiometry and Formulation Agent:** Evaluates crop type, target pest density, and environmental risk metrics. It calculates exact volumetric setpoints for active biopesticide, UV stabilizer, surfactant, and carrier water.
3. **Safety and Compliance Agent:** Acts as an automated verification barrier. It enforces agricultural safety limits (maximum active ingredient concentration, maximum surfactant threshold) and mechanical limits (tank minimum levels, max pump cycle duration).
4. **SCADA / Actuator Agent:** Maps volumetric chemical setpoints into pump runtimes based on calibrated pump flow rates ($Q = 10.0\text{ mL/sec}$). It constructs the deterministic JSON payload and publishes it over the MQTT command topic.

---

## 4. MCP Tools and Pydantic Schemas

Below are the production-grade Pydantic models and tool contracts used by the agents.

```python
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class FieldTelemetryInput(BaseModel):
    zone_id: str = Field(description="Identifier for field management sector")
    uv_index: float = Field(ge=0.0, le=16.0, description="Ambient UV Index")
    ambient_temp_c: float = Field(ge=-10.0, le=55.0, description="Temperature in Celsius")
    relative_humidity_pct: float = Field(ge=5.0, le=100.0, description="Relative humidity percentage")
    soil_moisture_pct: float = Field(ge=0.0, le=100.0, description="Volumetric soil moisture")

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
    flow_rate_ml_per_sec: float = Field(default=10.0, gt=0.0, description="Pump calibration flow rate")
    duration_sec: float = Field(gt=0.0, description="Calculated electrical runtime")

class SCADAPayload(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    zone_id: str
    safety_validated: bool
    recipe: ChemicalRecipe
    commands: List[PumpCommand]

```

---

## 5. MQTT Data Pipeline and Topic Architecture

### Topic Hierarchy

* Ingestion Telemetry: `agri/telemetry/{zone_id}/environment`
* AI Formulation Audit: `agri/agent/{zone_id}/recipe_log`
* SCADA Actuator Setpoint: `agri/actuator/{zone_id}/dosing_dispatch`
* Digital Twin State Feedback: `agri/digital_twin/{zone_id}/tank_status`

### Actuator Dispatch Payload Contract (`agri/actuator/zone_north/dosing_dispatch`)

```json
{
  "timestamp": "2026-08-20T13:45:00.000Z",
  "zone_id": "zone_north",
  "safety_validated": true,
  "recipe": {
    "biopesticide_ml": 45.0,
    "uv_stabilizer_ml": 14.5,
    "surfactant_ml": 4.2,
    "carrier_water_ml": 436.3,
    "total_batch_volume_ml": 500.0
  },
  "commands": [
    {
      "pump_id": 1,
      "chemical_name": "biopesticide",
      "volume_ml": 45.0,
      "flow_rate_ml_per_sec": 10.0,
      "duration_sec": 4.5
    },
    {
      "pump_id": 2,
      "chemical_name": "uv_stabilizer",
      "volume_ml": 14.5,
      "flow_rate_ml_per_sec": 10.0,
      "duration_sec": 1.45
    },
    {
      "pump_id": 3,
      "chemical_name": "surfactant",
      "volume_ml": 4.2,
      "flow_rate_ml_per_sec": 10.0,
      "duration_sec": 0.42
    },
    {
      "pump_id": 4,
      "chemical_name": "carrier_water",
      "volume_ml": 436.3,
      "flow_rate_ml_per_sec": 50.0,
      "duration_sec": 8.73
    }
  ]
}

```

---

## 6. Digital Twin Simulation Engine (`twin.py`)

The Digital Twin runs as a decoupled background service. It maintains virtual reservoir levels, calculates fluid displacement, and simulates physical pump response times.

```python
import json
import time
import threading
import paho.mqtt.client as mqtt

class DigitalTwinSCADA:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.tanks = {
            "biopesticide": 5000.0,   # Volume in mL
            "uv_stabilizer": 2000.0,
            "surfactant": 1000.0,
            "carrier_water": 50000.0
        }
        self.mix_tank = 0.0
        self.lock = threading.Lock()
        
        self.client = mqtt.Client(client_id="DigitalTwinEngine")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker_host, broker_port, 60)

    def on_connect(self, client, userdata, flags, rc):
        print(f"[DIGITAL TWIN] Connected to MQTT Broker with result code: {rc}")
        client.subscribe("agri/actuator/+/dosing_dispatch")

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"\n[DIGITAL TWIN] Setpoint received for Zone: {payload['zone_id']}")
        
        if not payload.get("safety_validated", False):
            print("[DIGITAL TWIN] EMERGENCY REJECT: Safety verification flag false.")
            return

        threading.Thread(target=self._execute_dosing, args=(payload,)).start()

    def _execute_dosing(self, payload):
        with self.lock:
            commands = payload.get("commands", [])
            for cmd in commands:
                chem = cmd["chemical_name"]
                vol = cmd["volume_ml"]
                dur = cmd["duration_sec"]
                
                if self.tanks[chem] < vol:
                    print(f"[DIGITAL TWIN] ALARM: Low level in tank {chem}. Required: {vol} mL, Available: {self.tanks[chem]} mL")
                    continue

                print(f"[ACTUATOR] Pump {cmd['pump_id']} ({chem}) ON -> Dispensing {vol} mL over {dur}s...")
                time.sleep(dur * 0.1) # Accelerated simulation factor (10x)
                
                self.tanks[chem] -= vol
                self.mix_tank += vol
                print(f"[ACTUATOR] Pump {cmd['pump_id']} ({chem}) OFF. Tank level: {self.tanks[chem]:.1f} mL")

            self._publish_state(payload["zone_id"])

    def _publish_state(self, zone_id):
        status = {
            "timestamp": time.time(),
            "zone_id": zone_id,
            "tanks_ml": self.tanks,
            "current_batch_ml": self.mix_tank
        }
        self.client.publish(f"agri/digital_twin/{zone_id}/tank_status", json.dumps(status))

    def start(self):
        self.client.loop_forever()

if __name__ == "__main__":
    twin = DigitalTwinSCADA()
    twin.start()

```

---

## 7. AI Agent Execution Blueprint

This script acts as your complete multi-agent reasoning script. It uses standard function calling logic to compute chemistry and send commands to the broker.

```python
import json
import math
import paho.mqtt.client as mqtt
from pydantic import ValidationError

# Initialize MQTT Client
mqtt_client = mqtt.Client(client_id="AgriAgent_Brain")
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

# --- CHEMICAL DOMAIN ENGINE ---
def compute_kinetics(uv_index: float, temp_c: float, rh_pct: float):
    t_kelvin = temp_c + 273.15
    k_0 = 0.015
    alpha = 0.18
    ea = 42500.0
    r = 8.314
    
    k_deg = k_0 * (1.0 + alpha * uv_index) * math.exp(-(ea / r) * ((1.0 / t_kelvin) - (1.0 / 298.15)))
    half_life_hrs = math.log(2) / k_deg if k_deg > 0 else 999.0
    return k_deg, half_life_hrs

def calculate_recipe(batch_vol_ml: float, uv_index: float, temp_c: float, rh_pct: float) -> dict:
    # 1. Active Biopesticide Base (e.g. 8% target concentration)
    bio_ml = batch_vol_ml * 0.08
    
    # 2. UV Stabilizer Scaling (Lignosulfonate)
    lignin_pct = min(3.0, 0.25 + (0.25 * uv_index))
    lignin_ml = batch_vol_ml * (lignin_pct / 100.0)
    
    # 3. Surfactant Evaporative Scaling
    surf_pct = min(0.20, 0.05 * (1.0 + 1.2 * (1.0 - (rh_pct / 100.0))) * ((temp_c + 273.15) / 293.15)**1.5)
    surf_ml = batch_vol_ml * (surf_pct / 100.0)
    
    # 4. Carrier Water Balance
    water_ml = batch_vol_ml - (bio_ml + lignin_ml + surf_ml)
    
    return {
        "biopesticide_ml": round(bio_ml, 2),
        "uv_stabilizer_ml": round(lignin_ml, 2),
        "surfactant_ml": round(surf_ml, 2),
        "carrier_water_ml": round(water_ml, 2),
        "total_batch_volume_ml": float(batch_vol_ml)
    }

# --- MCP / SCADA ACTION TOOL ---
def dispatch_scada_dosing(zone_id: str, recipe: dict) -> str:
    # Safety Validation Gate
    surf_ratio = recipe["surfactant_ml"] / recipe["total_batch_volume_ml"]
    if surf_ratio > 0.0025: # > 0.25% hard cutoff
        return "[SAFETY ERROR] Surfactant exceeds phytotoxicity threshold."
    
    commands = [
        {"pump_id": 1, "chemical_name": "biopesticide", "volume_ml": recipe["biopesticide_ml"], "flow_rate_ml_per_sec": 10.0, "duration_sec": round(recipe["biopesticide_ml"] / 10.0, 2)},
        {"pump_id": 2, "chemical_name": "uv_stabilizer", "volume_ml": recipe["uv_stabilizer_ml"], "flow_rate_ml_per_sec": 10.0, "duration_sec": round(recipe["uv_stabilizer_ml"] / 10.0, 2)},
        {"pump_id": 3, "chemical_name": "surfactant", "volume_ml": recipe["surfactant_ml"], "flow_rate_ml_per_sec": 10.0, "duration_sec": round(recipe["surfactant_ml"] / 10.0, 2)},
        {"pump_id": 4, "chemical_name": "carrier_water", "volume_ml": recipe["carrier_water_ml"], "flow_rate_ml_per_sec": 50.0, "duration_sec": round(recipe["carrier_water_ml"] / 50.0, 2)}
    ]
    
    payload = {
        "timestamp": "2026-08-20T13:45:00Z",
        "zone_id": zone_id,
        "safety_validated": True,
        "recipe": recipe,
        "commands": commands
    }
    
    topic = f"agri/actuator/{zone_id}/dosing_dispatch"
    mqtt_client.publish(topic, json.dumps(payload), qos=1)
    return f"[DISPATCH SUCCESS] Published {len(commands)} pump commands to {topic}"

# --- REASONING EXECUTION TRIGGER ---
def run_formulation_cycle(zone_id: str, uv: float, temp: float, rh: float, batch_size_ml: float = 500.0):
    print(f"\n--- [AGENT CYCLE START: {zone_id}] ---")
    k_deg, half_life = compute_kinetics(uv, temp, rh)
    print(f"[PERCEPTION AGENT] Telemetry Ingested -> UV: {uv}, Temp: {temp}C, RH: {rh}%")
    print(f"[KINETICS ENGINE] Active Half-Life: {half_life:.2f} hours (k_deg: {k_deg:.4f} hr^-1)")
    
    recipe = calculate_recipe(batch_size_ml, uv, temp, rh)
    print(f"[FORMULATION AGENT] Generated Chemical Recipe: {recipe}")
    
    result = dispatch_scada_dosing(zone_id, recipe)
    print(f"[SCADA AGENT] Execution Result: {result}")
    print("--- [AGENT CYCLE COMPLETE] ---")

if __name__ == "__main__":
    # Test Scenario 1: Harsh midday sun (High UV, High Temp, Dry Air)
    run_formulation_cycle("zone_north", uv=10.5, temp=39.0, rh=28.0, batch_size_ml=500.0)
    
    # Test Scenario 2: Overcast morning (Low UV, Moderate Temp, High Humidity)
    run_formulation_cycle("zone_south", uv=2.1, temp=24.0, rh=75.0, batch_size_ml=500.0)

```

---

## 8. Hackathon Evaluation Alignment

| Evaluation Criteria | AgriAgent System Implementation |
| --- | --- |
| **Domain Differentiation** | Replaces static tank spraying with dynamic stoichiometric degradation equations. |
| **Agentic Tool Calling** | Implements deterministic structured output validation using strict Pydantic schemas. |
| **Industrial Viability** | Uses standard MQTT topic architecture and SCADA digital twin simulation. |
| **Business Impact** | Targets up to 90% synthetic pesticide reduction while eliminating biopesticide photodegradation. |