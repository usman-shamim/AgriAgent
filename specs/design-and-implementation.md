# Design and Implementation of an Agentic AI System for Low-Pesticide Agriculture and Dynamic Bio-Pesticide Formulation

## Agribusiness and Chemical Technology Landscape

Chemical and physical stability represent the primary operational bottlenecks in transitioning global agricultural practices from synthetic, persistent organochemicals to biologically derived pest control agents. Unlike stable, synthetic small-molecule pesticides, biopesticides—including delicate bioactive peptides, live bacterial spores, fungal conidia, and botanical extracts—are highly susceptible to rapid environmental degradation when exposed to field conditions.

### Chemical Stability and Degradation Bottlenecks

Bioactive peptides represent a highly target-specific class of biopesticides, but their field efficacy is severely limited by complex chemical and physical degradation pathways. Chemical degradation alters the primary structure of the peptide via covalent bond modification, which is catalyzed by ambient pH, temperature, and trace metals. Hydrolysis is a major chemical degradation pathway that exhibits a strict dependency on environmental pH and buffer species.

Under highly acidic conditions ($\text{pH } 1 \text{ to } 3$), peptides containing C-terminal amides undergo rapid acid-catalyzed hydrolysis, primarily via the deamidation of the terminal amide. In moderately acidic to neutral environments ($\text{pH } 5 \text{ to } 6$), the peptide backbone is susceptible to site-specific hydrolysis on the N-terminal side of serine ($\text{Ser}$) residues. This reaction is initiated by the nucleophilic attack of the side-chain hydroxyl group of the $\text{Ser}$ residue on the adjacent carbonyl carbon of the peptide backbone, forming a cyclic ester intermediate that leads to chain cleavage and loss of structural integrity.

Under basic conditions ($\text{pH} > 7$), base-catalyzed epimerization and racemization represent the dominant degradation pathways. This process is highly accelerated in residues such as $\text{Ser}$ due to the stabilization of the resulting carbanion intermediate through intramolecular hydrogen bridging, which forms a stable, six-membered intermediate ring.

$$\text{Asn} \xrightarrow{\text{pH} > 5} \text{Succinimide Intermediate} \rightarrow \text{Asp / Iso-Asp Mixture}$$

Peptides containing asparagine ($\text{Asn}$) and glutamine ($\text{Gln}$) are also highly susceptible to deamidation under physiological and basic conditions, converting into aspartate ($\text{Asp}$) and glutamate ($\text{Glu}$), respectively. When the ambient $\text{pH}$ is above $5$, $\text{Asn}$ deamidation occurs via an intramolecular cyclization reaction. In this pathway, the nitrogen atom of the adjacent peptide bond attacks the side-chain carbonyl carbon of the $\text{Asn}$ residue, forming a five-membered cyclic succinimide intermediate. Subsequent hydrolysis of this intermediate yields a mixture of $\text{Asp}$ and iso-aspartate, altering the spatial conformation of the peptide and destroying its receptor-binding capability. Because the formation of a five-membered ring intermediate is kinetically more favorable than the six-membered ring required for $\text{Gln}$ cyclization, $\text{Gln}$ deamidation proceeds at a significantly slower rate under identical environmental conditions.

Light- and metal-induced oxidation further degrades biopesticide active ingredients. Histidine ($\text{His}$) residues are highly sensitive to photodynamic and transition metal-catalyzed oxidation. This reaction attacks the imidazole ring of the $\text{His}$ residue, generating reactive oxygen species ($\text{ROS}$) and yielding $2\text{-oxo-histidine}$ ($2\text{-O-His}$), $\text{Asn}$, or $\text{Asp}$ as primary degradation products. The formation of these oxidized moieties disrupts local electrostatic interactions, triggering rapid hydrophobic protein aggregation and subsequent physical precipitation out of suspension. Tyrosine ($\text{Tyr}$) residues are similarly prone to light-driven oxidation, resulting in the formation of covalent bityrosine cross-links that aggregate the protein and render the biopesticide biological agent inactive.

Physical instability, distinct from covalent bond modification, involves structural changes in non-covalent interactions (e.g., hydrogen bonding, hydrophobic interactions, and electrostatic forces). These changes alter the secondary and tertiary structures of the biopesticide proteins, causing adsorption to the hydrophobic surfaces of spray tanks, self-aggregation, and irreversible precipitation in aqueous carriers.

On a macroscale, botanical active ingredients such as natural pyrethrins, baculoviruses, and neem oil are characterized by rapid volatilization and acute photo-degradation. Solar ultraviolet ($\text{UV}$) radiation, specifically $\text{UV-A}$ and $\text{UV-B}$ bands, rapidly cleaves the ester bonds of pyrethrins, resulting in a field half-life ($DT_{50}$) of only a few hours in raw form, which necessitates frequent re-applications.

| Biopesticide Class | Representative Active Ingredient | Primary Degradation Pathway | Dominant Environmental Driver | Degradation Product / Operational Impact |
|---|---|---|---|---|
| Bioactive Peptide | Gonadorelin & Triptorelin Analogs | Backbone chain cleavage & $\text{Ser}$ racemization | $\text{pH } 5 \text{ to } 6$ (cleavage), $\text{pH} > 7$ (racemization) | Cyclic intermediate formation, peptide fragmentation, and loss of receptor affinity |
| Recombinant Protein | rhPTH & r-GLP-1 Analogs | Acid-catalyzed $\text{Asp}$ cleavage & $\text{Asn}$ deamidation | $\text{pH} < 3$ ($\text{Asp}$ cleavage), $\text{pH} > 5$ ($\text{Asn}$ deamidation) | Direct backbone cleavage, cyclic succinimide intermediate formation, and structural denaturation |
| Botanical Extract | Natural Pyrethrins | Photolytic ester cleavage and volatilization | Solar radiation ($\text{UV-A/B}$ spectrum) and high surface temperature | Inactive photolytic isomers, rapid evaporation, and complete loss of contact toxicity |
| Microbial Pathogen conidia | Beauveria bassiana & Metarhizium anisopliae | Solar-induced DNA damage and membrane desiccation | Direct solar radiation and low relative humidity ($< 40\%$) | Viability loss, failure of conidial germination on insect cuticle |

### Modern Precise Formulation and Dynamic Blending Adjuvants

To overcome these environmental degradation barriers, precise agricultural systems utilize advanced formulation engineering, dynamically adjusting the ratios of UV protectors, surfactants, and macromolecular stabilizers based on real-time environmental telemetry.

Sodium lignosulfonate and Kraft lignin are highly effective, low-cost macromolecular UV stabilizers. Lignin is a complex, water-insoluble aromatic polymer, whereas lignosulfonates are water-soluble derivatives obtained by introducing sulfonic acid groups into the lignin matrix. The dense, conjugated aromatic structures of these polymers act as natural UV chromophores. These chromophores absorb high-energy UV radiation and dissipate the energy as harmless thermal vibration, shielding the co-formulated biopesticides from photodegradation.

Encapsulating natural pyrethrins with sodium lignosulfonate and Kraft lignin (utilizing techniques such as ionotropic gelation with sodium alginate or spray drying) achieves an encapsulation efficiency greater than $77\%$. In outdoor simulated sunlight exposure trials, raw pyrethrum extract exhibits rapid photolysis; however, Kraft lignin-encapsulated formulations extend the photolytic half-life ($DT_{50}$) to $115 \text{ hours}$, while sodium lignosulfonate-encapsulated formulations extend the $DT_{50}$ to $231 \text{ hours}$. This represents a $7$-fold and $14$-fold stabilization improvement, respectively, while significantly reducing active ingredient loss from volatilization.

$$\text{Encapsulation Efficiency (\%)} = \left( \frac{\text{Mass of Encapsulated Active Ingredient}}{\text{Total Mass of Active Ingredient Added}} \right) \times 100 \ge 77\% \ [1, 5]$$

Wetting agents and surfactants are also critical for modifying formulation rheology, reducing droplet surface tension, and improving leaf canopy wetting. The non-ionic surfactant Tween-80 (polyoxyethylene sorbitan monooleate) is widely utilized to stabilize aqueous suspensions and oil-in-water emulsions. Incorporating $0.1\%$ to $0.2\% \text{ v/v}$ Tween-80 into industrial fermentation media, such as those used for Bacillus thuringiensis kurstaki (Btk), modifies sludge rheology, decreases mean particle size ($D_{50}$), and enhances the oxygen volumetric mass transfer coefficient ($k_L a$).

This optimization results in a $1.6$-fold increase in cell density, a $1.3$-fold increase in spore concentration, and a $29.7\%$ increase in entomotoxicity ($Tx$) against target pests. Similarly, adding Tween-80, sodium citrate, and sodium lignosulfonate to Bacillus amyloliquefaciens fermentation broths achieves up to $84.78\%$ biological control of plant pathogens such as apple rot under field conditions.

$$\text{Btk Cell Density Increase} = 1.6 \times \text{Baseline}, \quad \text{Btk Spore Count Increase} = 1.3 \times \text{Baseline} \ [9]$$

For highly sensitive peptide and protein biopesticides, short, synthetic surfactant-like peptides (SLPs) are utilized as advanced, bio-compatible stabilizers. These SLPs, typically $6 \text{ to } 10$ amino acids in length ($2.5 \text{ to } 3.0 \text{ nm}$), mimic the structural topology of natural phospholipids. They feature a distinct hydrophilic head group composed of negatively charged aspartic acid or positively charged lysine, coupled to a hydrophobic tail of consecutive hydrophobic amino acids (e.g., alanine, glycine, valine, or leucine).

When dissolved in aqueous media, SLPs self-assemble above their critical aggregation concentration (CAC) to form nanovesicles, micelles, or nanotubes. A representative SLP, $(Ala)_9-Arg$ ($\text{A9R}$), self-assembles into stable $\beta$-sheet fiber networks that coat oil-in-water emulsion droplets. This nanostructured coating provides physical stabilization against thermal denaturation and coalescence, enables selective antimicrobial action against Gram-negative pathogens such as Pseudomonas aeruginosa, and allows for controlled release via protease-responsive (elastase) de-emulsification.

## South Asian Agribusiness Market Dynamics and Crop Profiles

In the agricultural landscape of South Asia, and specifically Pakistan, the transition from persistent synthetic organochemicals to dynamically formulated biopesticides presents significant commercial opportunities. This transition is driven by increasingly strict export regulations, pest resistance, and rising input costs.

### Pakistan Agricultural Export Corridors & Key Chemical Bottlenecks

```text
┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│    Basmati Rice Sector   │      │   Kunri Chili Cluster    │      │    Punjab Cotton Belt    │
│  - EU Tricyclazole MRL   │      │  - High Aflatoxins       │      │  - Sucking Pests & Worms │
│    Limit: 0.01 mg/kg     │      │    (> 32 ug/kg average)  │      │  - Annual Spray Costs    │
│  - High risk: Pusa 1121  │      │  - Post-Harvest Waste    │      │    up to 50,000 PKR/Acre │
└─────────────┬────────────┘      └─────────────┬────────────┘      └─────────────┬────────────┘
              │                                 │                                 │
              ▼                                 ▼                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                             AGENTIC BIO-FORMULATION ALTERNATIVES                             │
│       - Pseudomonas fluorescens (biocontrol) & Trichoderma viride (soil inoculation)         │
│       - Bacillus amyloliquefaciens stabilized with Tween-80 and Lignosulfonates              │
│       - Target-specific HaNPV baculoviruses and stabilized botanical extracts                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

The Basmati rice export corridor is a primary agribusiness sector for Pakistan. Historically, India dominated Basmati exports to the European Union (EU). However, on January 1, 2018, the European Commission reduced the Maximum Residue Limit (MRL) for the widely used fungicide tricyclazole from $1.0 \text{ mg/kg}$ to a near-zero detection limit of $0.01 \text{ mg/kg}$. Because Indian farmers heavily relied on tricyclazole to control rice blast in over $70\%$ of their Basmati crops, Indian exports to the EU immediately fell, allowing Pakistani exporters (who did not traditionally use tricyclazole) to capture a substantial share of this $\$260 \text{ million}$ market.

Despite this initial advantage, Pakistani exports have faced rising EU Rapid Alert System for Food and Feed (RASFF) notifications since 2022 due to pesticide residues and aflatoxin contamination. The most frequent pesticide detections exceeding EU MRLs in Pakistani shipments include acetamiprid, imidacloprid, thiamethoxam, chlorpyrifos-ethyl, triazophos, and hexaconazole.

These detections are highly concentrated in the popular Pusa 1121 variety, whereas varieties within the "Super Basmati Family" (including Super Basmati, Basmati 515, and Basmati 2000) show significantly lower pesticide residue levels. Transitioning Pusa 1121 and Super Basmati crops to biological alternatives, such as Pseudomonas fluorescens (which suppresses soil-borne pathogens and induces systemic resistance via the production of hydrogen cyanide and 2,4-diacetylphloroglucinol) and Trichoderma viride, offers a direct pathway to eliminate chemical residues, stabilize export quality, and protect premium values ranging from $\$820 \text{ to } \$900$ per metric ton.

$$\text{Basmati Export Market Value} = \$820 \text{ to } \$900 \text{ per Metric Ton} \ [16]$$

In southern Pakistan, the Kunri chili cluster in Sindh represents another key export market. Kunri is home to the largest chili market in Pakistan, but the region faces severe post-harvest losses and high aflatoxin levels. While the EU enforces a maximum limit of $10 \ \mu\text{g/kg}$ of total aflatoxins in imported chilies, Pakistani chili samples average over $32 \ \mu\text{g/kg}$.

This contamination is driven by open drying on the ground, high humidity during maturity, and viral and fungal infections. Approximately $10\%$ to $12\%$ of the harvest is discarded due to poor post-harvest handling. Applying stabilized pre-harvest bio-fungicidal formulations, such as Bacillus amyloliquefaciens co-formulated with sodium lignosulfonate, suppresses Aspergillus flavus growth in the field, helping to bring aflatoxin levels below the $10 \ \mu\text{g/kg}$ export threshold and restoring access to premium international markets.

In the Punjab and Sindh cotton belts, the excessive use of broad-spectrum synthetic pesticides has led to high insect resistance and rising input costs. Cotton farmers routinely spend up to $\text{PKR } 50,000$ per acre on synthetic chemical sprays to control pests like Helicoverpa armigera and whiteflies.

By integrating simple agronomic tools (such as yellow sticky traps) with target-specific bio-pesticides (including Helicoverpa armigera Nucleopolyhedrovirus / HaNPV, Beauveria bassiana, and azadirachtin), chemical costs can be reduced significantly. Furthermore, optimizing inputs through soil testing and organic amendments has been shown to increase cotton yields by $5\%$ while reducing fertilizer costs by $\text{PKR } 5,000 \text{ to } 7,000$ per acre.

## System Architecture and Agentic Workflow (OpenAI Agent SDK / MCP)

The autonomous formulation and dosing system is orchestrated by a multi-agent framework built on the OpenAI Agent SDK, using the Model Context Protocol (MCP) to bridge the cloud-based AI agents with physical field actuators.

### Multi-Agent Interaction Model and Orchestration

The system uses a collaborative multi-agent architecture where specialized agents execute tasks under the coordination of a central Orchestrator Agent. This design leverages the thinnest possible abstraction layer of the OpenAI Agent SDK, using the Runner execution engine to handle turn-based loops, asynchronous tool calling, and multi-agent handoffs.

```text
                               ┌───────────────────────────┐
                               │     Orchestrator Agent    │
                               │   (OpenAI Agent SDK Loop) │
                               └─────────────┬─────────────┘
                                             │
                       ┌─────────────────────┼─────────────────────┐
                       │                     │                     │
                       ▼                     ▼                     ▼
          ┌─────────────────────────┐ ┌─────────────┐ ┌─────────────────────────┐
          │  Environmental Agent    │ │ Stoichiom.  │ │    Safety & Guardrail   │
          │ (Weather, Soil Sensors) │ │  Formulator │ │      Compliance Agent   │
          └─────────────────────────┘ └─────────────┘ └─────────────────────────┘
                       │                     │                     │
                       ▼                     ▼                     ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                           SCADA / Industrial Agent                            │
│           - Exposes MCP Tools and maps parameters to device topics            │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │ (MQTT over TCP)
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                           Industrial IoT Broker                               │
│                         - EMQX MQTT Broker Platform -                         │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │ (Publish / Subscribe)
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                      Physical Field Actuator Nodes                            │
│                   - ESP32 Dosing & Peristaltic Pump Rig -                     │
└───────────────────────────────────────────────────────────────────────────────┘
```

The execution workflow is structured around four specialized agents:

- **Perception and Environmental Agent**: This agent monitors crop conditions by querying real-time weather APIs (obtaining UV indices, temperature, wind speed, and relative humidity) and reading edge soil sensors (soil moisture, pH, and temperature).
- **Stoichiometry and Formulation Agent**: Using current environmental readings, this agent calculates the optimum chemical ratios for the biopesticide mixture. If the solar UV index is high ($\ge 6$), it increases the sodium lignosulfonate ratio to provide adequate photoprotection. If relative humidity is low ($< 45\%$) or wind speed is high, it adjusts the concentration of Tween-80 and surfactant-like peptides to enhance leaf adhesion and minimize evaporation losses.
- **Safety and Compliance Agent**: This agent acts as a strict guardrail before any recipe is approved. It runs compliance checks to ensure that the calculated chemical concentrations do not cause phytotoxicity to the crop, that surfactant ratios remain within safe regulatory limits, and that the mixture complies with international MRL guidelines.
- **Industrial Automation and SCADA Agent**: Once a recipe is approved, this agent translates the volumetric ratios into specific motor speeds, valve states, and pump runtimes, formatting these instructions into industrial control payloads.

This multi-agent system is managed via the `Runner.run()` or `Runner.run_sync()` methods, which execute the agent loop asynchronously. The runner queries the current agent, executes any returned tool calls, processes handoffs to other agents, and handles state persistence.

By integrating `SQLiteSession` from the OpenAI Agent SDK, conversational states can be saved to a local database (`conversations.db`), enabling the system to preserve historical context and resume interrupted tasks. For real-time monitoring, `Runner.run_streamed()` streams execution events as they occur, providing immediate feedback to the operator interface.

To monitor and debug these multi-agent workflows, the system utilizes the SDK's built-in tracing capabilities. Each execution run is automatically wrapped in hierarchical tracing spans. Developers can view detailed performance metrics, model generations, tool call delays, and handoff events on the OpenAI Traces dashboard. These tracing spans can be configured and managed via the `RunConfig` class:

```python
from agents import RunConfig, Runner

# Disabling automatic task and turn spans for a cleaner, high-level trace hierarchy
run_configuration = RunConfig(
    tracing={
        "include_task_and_turn_spans": False,
        "api_key": "sk-tracing-api-key-here"
    }
)
```

By wrapping units of work in a `with trace("workflow_id"):` context manager and calling `flush_traces()` upon completion, the system ensures that performance telemetry is delivered to the tracing backend. This monitoring is crucial for debugging high-latency industrial control loops.

### Model Context Protocol (MCP) Server Architecture

The Model Context Protocol (MCP), introduced in November 2024, establishes a standardized, open communication framework between LLM-based agents and external systems, resolving data silos and eliminating the need for custom, proprietary integration code for every legacy industrial protocol.

The system architecture utilizes MCP over MQTT, replacing standard HTTP and Server-Sent Events (SSE) transports with the lightweight, publish/subscribe MQTT protocol. This transport layer is highly optimized for unstable, low-bandwidth agricultural edge networks.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          MCP over MQTT Bridge                          │
│                                                                        │
│   ┌────────────────────────┐            ┌──────────────────────────┐   │
│   │   Industrial Device    │            │     MCP Server Proxy     │   │
│   │   (Attributes, e.g.,   │───────────►│  Exposes real-time state │   │
│   │   pH, Tank Levels)     │ (MQTT Pub) │   as MCP Resources       │   │
│   └────────────────────────┘            └──────────────────────────┘   │
│                                                      ▲                 │
│                                                      │ (Tool Call)     │
│   ┌────────────────────────┐            ┌────────────┴─────────────┐   │
│   │    Active Actuators    │◄───────────│   Agent Commands         │   │
│   │    (Functions, e.g.,   │ (MQTT Sub) │  mapped as MCP Tools     │   │
│   │    Solv. Pump Speeds)  │            │                          │   │
│   └────────────────────────┘            └──────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

The digital twin of the physical formulation system is defined via the **Device Model** standard, which maps real-world attributes, functions, and events to corresponding MCP concepts:

- **Attributes to MCP Resources**: Real-time physical states—such as reactor pH, liquid storage tank levels, and chemical flow rates—are exposed as read-only MCP Resources. Agents read these resources using standard URI paths, such as `device://zone1/dosing_tank/level`.
- **Functions to MCP Tools**: Actuator control mechanisms are mapped to executable MCP Tools. An agent can dynamically trigger a command, such as adjusting a motor speed or closing a solenoid valve, by invoking the corresponding tool.
- **Events to MCP Prompts**: Critical system events—such as low tank warnings, pH anomalies, or pump failures—are registered as MCP Prompts, enabling the agentic system to receive and act upon real-time alerts.

This integration can be deployed using two different architectural approaches:

- **Device Proxy Solution**: Standard edge devices publish their sensor data and subscribe to commands using standard MQTT topics. A centralized MCP Server, acting as a proxy, subscribes to these topics, maintains a registry of the devices, and exposes their states as standardized MCP resources and tools. This approach allows legacy SCADA and PLC infrastructure to be integrated with AI agents without requiring hardware upgrades.
- **Native Solution**: High-performance, edge-compute platforms (such as an industrial Raspberry Pi or smart PLC) run a native MCP Server directly on the device. The device communicates directly with the EMQX broker using the native MCP over MQTT SDK, enabling end-to-end intelligent control.

To ensure structured, secure, and discoverable communication across the network, the system follows standard MQTT topic naming conventions:

- **Device Registration**: `$ai/{DOMAIN}/{GROUP}/d/{DEVICE_ID}` is used for automatic discovery and status monitoring.
- **Rule Coordination**: `$ai/{DOMAIN}/{GROUP}/r/{RULE_ID}` handles automated safety rules and coordination logic.

Industrial administrators use the EMQX broker's centralized authentication, authorization, and load-balancing services to manage service routing, restrict access to authorized agents, and scale MCP servers horizontally while maintaining state consistency.

The physical MCP server is implemented in Python, leveraging FastAPI to support both Streamable HTTP/SSE and standard stdio transports. The following skeleton shows the implementation structure using the v2 MCP Python SDK:

```python
from mcp.server import MCPServer
from mcp.server.stdio import stdio_server
import anyio

# Initialize the MCPServer wrapper using the modern v2 SDK
mcp_server = MCPServer("Dynamic-AgTech-Formulation-Controller")

@mcp_server.tool()
def set_pump_speed(pump_id: int, speed_rpm: int) -> str:
    """
    Directly writes a rotational speed command (RPM) to a specified dosing pump.
    """
    # In practice, this converts parameters to an MQTT payload and publishes to EMQX
    return f"Success: Dosing pump {pump_id} set point updated to {speed_rpm} RPM."

async def run_server():
    # Run the server utilizing stdio transport for direct CLI/agent integration
    async with stdio_server() as streams:
        await mcp_server.run(
            streams,
            streams,
            mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    anyio.run(run_server)
```

## Hardware and Industrial Automation Implementation

To move the system from a simulated framework to a physical proof-of-concept, a low-cost, precise prototyping hardware stack was developed.

### Prototyping Hardware Stack Architecture

The hardware demonstration rig simulates an automated multi-channel chemical dosing station. It dynamically blends four fluid streams: **Active Biopesticide Concentrate**, **Surfactant (Tween-80)**, **UV Stabilizer (Sodium Lignosulfonate)**, and a **Distilled Water Carrier**.

- **Edge Compute Unit**: An ESP32 development board serves as the primary controller. Its dual-core processor handles real-time MQTT subscriptions over Wi-Fi while generating precise PWM hardware interrupts.
- **Actuation System**: Four $12\text{V}$ DC peristaltic dosing pumps control fluid movement. Peristaltic pumps use positive displacement, ensuring a linear relationship between pump runtime, motor speed, and volumetric output.
- **Driver Interface**: An L298N Dual H-Bridge Motor Driver module controls the speeds of Pumps 1 and 2 via PWM duty cycle modulation. Pumps 3 and 4 are controlled using a 4-channel, optoisolated $5\text{V}$ relay module for simple binary (on/off) dosing.
- **Power Supply**: A regulated $12\text{V}$, $5\text{A}$ DC switching power supply powers the motors, while an LM2596 buck converter steps the voltage down to $5\text{V}$ to safely power the ESP32 and relay logic boards.

| Hardware Component | Functional Specifications | Interface Protocol | ESP32 GPIO Mapping |
|---|---|---|---|
| ESP32 DevKit V1 | Dual-core $240\text{MHz}$ CPU, integrated Wi-Fi | FreeRTOS thread scheduler | N/A (Master Unit) |
| L298N Driver | Dual H-bridge, max $2\text{A}$ per channel | PWM & digital GPIO direction | GPIO 12 (PWM A), GPIO 13 (IN1), GPIO 14 (PWM B), GPIO 27 (IN3) |
| 12V Peristaltic Pumps | $100 \text{ ml/min}$ nominal flow rate ($1.66 \text{ ml/sec}$) | High-current analog drive | Pump 1 & 2 via L298N; Pump 3 & 4 via Relay Board |
| 4-Channel Relay Board | Optoisolated coil protection, $10\text{A}$ contacts | $5\text{V}$ digital logic active-low | GPIO 18 (Relay 1), GPIO 19 (Relay 2) |
| LM2596 Buck Converter | Adjustable output, $3\text{A}$ max continuous | Step-down ($12\text{V}$ to $5\text{V}$) | Direct DC bus power |

### Python OpenAI Agent SDK MQTT Integration

The following script implements a complete multi-agent formulation loop using the OpenAI Agent SDK. When invoked, the agent calculates the required chemical ratios based on incoming environmental conditions, validates the recipe, and publishes a structured JSON control payload to the EMQX broker to actuate the physical pumps.

```python
import os
import json
import asyncio
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool
import paho.mqtt.client as mqtt

# Ensure the system client is initialized asynchronously
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class FormulationRecipe(BaseModel):
    batch_volume_ml: float = Field(..., description="Target volume of the final formulation batch in milliliters.")
    active_ratio: float = Field(..., description="Calculated ratio of active microbial/peptide concentrate (0.0 to 1.0).")
    surfactant_ratio: float = Field(..., description="Calculated ratio of Tween-80 surfactant (0.0 to 1.0).")
    stabilizer_ratio: float = Field(..., description="Calculated ratio of Sodium Lignosulfonate stabilizer (0.0 to 1.0).")

@function_tool
def publish_dosing_transaction(recipe_payload_json: str) -> str:
    """
    Accepts a validated formulation recipe, converts the ratios into specific pump
    runtimes, and publishes the control parameters to the physical dosing rig via MQTT.
    """
    try:
        # Parse the JSON string into the validation model
        data = json.loads(recipe_payload_json)
        recipe = FormulationRecipe(**data)

        # Verify stoichiometric boundaries (sum of active ingredients must not exceed 100%)
        combined_ratio = recipe.active_ratio + recipe.surfactant_ratio + recipe.stabilizer_ratio
        if combined_ratio > 1.0:
            return f"Stoichiometric failure: Total ratio ({combined_ratio}) exceeds 1.0. Formulation rejected."

        # Compute absolute volumetric outputs
        v_active = recipe.batch_volume_ml * recipe.active_ratio
        v_surfactant = recipe.batch_volume_ml * recipe.surfactant_ratio
        v_stabilizer = recipe.batch_volume_ml * recipe.stabilizer_ratio
        v_water = recipe.batch_volume_ml * (1.0 - combined_ratio)

        # Convert volumes to runtimes based on calibrated pump flow rate (1.66 ml/sec)
        calibration_factor = 1.66
        runtimes = {
            "pump_1_active_seconds": round(v_active / calibration_factor, 2),
            "pump_2_surfactant_seconds": round(v_surfactant / calibration_factor, 2),
            "pump_3_stabilizer_seconds": round(v_stabilizer / calibration_factor, 2),
            "pump_4_water_seconds": round(v_water / calibration_factor, 2)
        }

        # Build the structured, device-compliant payload
        payload = {
            "transaction_id": "TX_AG_2026_9938",
            "operation": "BATCH_EXECUTION",
            "target_system": "peristaltic_dosing_rig_01",
            "volumes_ml": {
                "active": round(v_active, 1),
                "surfactant": round(v_surfactant, 1),
                "stabilizer": round(v_stabilizer, 1),
                "water": round(v_water, 1)
            },
            "execution_runtimes_sec": runtimes
        }

        # Publish the payload to the EMQX broker
        mqtt_broker = "broker.emqx.io"
        mqtt_port = 1883
        # Use standard topic naming conventions for device registration and commands
        target_topic = "$ai/agtech/zone1/d/peristaltic_dosing_rig_01"

        client = mqtt.Client()
        client.connect(mqtt_broker, mqtt_port, 60)

        # Publish with QoS 1 to guarantee delivery to the edge node
        message_info = client.publish(target_topic, json.dumps(payload), qos=1)
        message_info.wait_for_publish()
        client.disconnect()

        return (
            f"Recipe successfully compiled and verified. Volumetric split: Active={v_active:.1f}ml, "
            f"Surfactant={v_surfactant:.1f}ml, Stabilizer={v_stabilizer:.1f}ml, Water={v_water:.1f}ml. "
            f"Dosing payload successfully published to topic '{target_topic}'."
        )

    except Exception as e:
        return f"Operational failure during dosing transaction: {str(e)}"

# Define the specialized formulation agent with strict, environmental instructions
formulator_agent = Agent(
    name="AgTech-Chemical-Formulator",
    instructions=(
        "You are an expert chemical process automation agent. Your role is to compute optimal "
        "biopesticide formulations based on environmental conditions and control physical dosing pumps. "
        "Follow these rules precisely:\n"
        "1. Active ingredient ratio is always fixed at 0.35 (35%).\n"
        "2. If the environmental UV index is >= 6.0, set the stabilizer_ratio to 0.15 (15%), else set to 0.05.\n"
        "3. If relative humidity is < 40.0%, set the surfactant_ratio to 0.10 (10%), else set to 0.05.\n"
        "4. Water acts as the remaining carrier volume to make up 1.0 (100%).\n"
        "Calculate these ratios, build the FormulationRecipe, and call the publish_dosing_transaction tool."
    ),
    tools=[publish_dosing_transaction],
    model="gpt-4o"
)

async def main():
    # Simulate a hot, dry, high-UV scenario in the South Asian cotton belt
    sensor_input = "Environmental Telemetry - UV Index: 8.2, Humidity: 28.5%. Prepare a 400ml formulation batch."
    print("Initiating agentic formulation control loop...")

    # Run the agentic sequence using the SDK's Runner engine
    run_result = await Runner.run(formulator_agent, sensor_input)
    print("\n=== Agent Decision & Execution Output ===")
    print(run_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## ROI, Metrics and Feasibility Analysis

Transitioning from broad-spectrum synthetic organochemicals to dynamically formulated biopesticides provides quantifiable economic and ecological benefits.

### Agribusiness Economic Metrics

The traditional pest control baseline in the South Asian cotton belt relies on excessive prophylactic spraying of synthetic insecticides, costing farmers up to $\text{PKR } 50,000$ per acre annually.

$$\text{Pesticide Cost Reduction Rate (\%)} = \left(1 - \frac{C_{\text{agentic}}}{C_{\text{synthetic}}}\right) \times 100\%$$

In this equation, $C_{\text{synthetic}}$ represents the baseline cost of synthetic pesticides ($\text{PKR } 50,000$ per acre), and $C_{\text{agentic}}$ represents the dynamic bio-pesticide operating cost, estimated at $\text{PKR } 5,000$ per acre. Integrating target-specific bio-formulations with real-time pest monitoring achieves a $90\%$ reduction in chemical application volume.

$$\text{Pesticide Cost Reduction Rate (\%)} = \left(1 - \frac{5,000}{50,000}\right) \times 100\% = 90\% \text{ Savings}$$

This transition saves farmers approximately $\text{PKR } 45,000$ per acre annually. Furthermore, optimizing soil conditions and shifting from synthetic fertilizers to organic amendments can enhance crop yields by $5\%$ while saving an additional $\text{PKR } 5,000 \text{ to } 7,000$ per acre.

$$\text{Financial Risk Avoided (per Export Consignment)} = Q \times P_{\text{market}}$$

For export crops such as Basmati rice, the economic impact is directly tied to regulatory compliance. If a standard $100 \text{ metric ton}$ ($Q$) shipment of Pusa 1121 Basmati rice is rejected at an EU port of entry due to pesticide residues (such as tricyclazole exceeding the $0.01 \text{ mg/kg}$ limit), the exporter faces a direct loss of $\$82,000 \text{ to } \$90,000$, based on a market price ($P_{\text{market}}$) of $\$820 \text{ to } \$900$ per metric ton. By replacing chemical fungicides with dynamically stabilized biopesticides, exporters avoid these costly rejections, protecting export values and securing premium market access.

**Estimated Financial Performance per Acre (PKR)**

```text
Synthetic Baseline:   ██████████████████████████████ 50,000 PKR
Bio-Agentic Cost:     ███ 5,000 PKR (90% reduction)
Direct Savings:       ████████████████████████─── 45,000 PKR Saved
```

### Environmental Impact Metrics

- **Preservation of Soil Microbiome Diversity**: Broad-spectrum synthetic chemicals can degrade soil microbial health. In contrast, beneficial biopesticides such as Pseudomonas fluorescens function as plant growth-promoting rhizobacteria (PGPR). These bacteria actively colonize root systems, solubilizing inorganic phosphate, producing natural iron-chelating siderophores, and synthesizing indole-3-acetic acid (IAA) to enhance root growth. They also suppress soil pathogens by producing natural compounds like hydrogen cyanide (HCN) and 2,4-diacetylphloroglucinol (2,4-DAPG).
- **Reduction in Groundwater Contamination**: Synthetic organochemicals exhibit high soil mobility, leading to the contamination of local aquifers via runoff and leaching. In contrast, biopesticides degrade naturally without leaving persistent, toxic residues. Encapsulating these bio-agents in porous sodium lignosulfonate microcapsules regulates active ingredient release and minimizes premature runoff, reducing environmental leaching.
- **Conservation of Beneficial Insects and Pollinators**: Synthetic insecticides are non-selective, resulting in high mortality rates among beneficial insects and pollinators, which can lead to secondary pest outbreaks. Conversely, target-specific biopesticides, such as Bacillus thuringiensis and host-specific NPV baculoviruses, selectively target pest larvae while leaving non-target beneficial organisms unharmed.

## Hackathon Pitch and Demo Strategy

Successfully presenting this project at the Bano Qabil AI Hackathon requires bridging deep chemical technology with state-of-the-art agentic AI systems.

### Dynamic Live-Actuation Stage Demonstration

To captivate the evaluation panel, the developer must present a reliable, visual demonstration of the integrated software and hardware stack.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        STAGE PRESENTATION LAYOUT                       │
│                                                                        │
│   ┌───────────────────────┐            ┌──────────────────────────┐    │
│   │   Operator Terminal   │            │   Physical Dosing Rig    │    │
│   │   - Interactive input │───────────►│   - Red/Blue/Yellow/Clear│    │
│   │   - Live Agent logs   │ (EMQX MQTT)│     colored reservoirs   │    │
│   │   - Tracing spans     │            │   - 12V Peristaltic pumps│    │
│   └───────────────────────┘            └────────────┬─────────────┘    │
│                                                     │                  │
│                                                     ▼                  │
│                                                      │                 │
│                                            - Visual color shifts       │
└────────────────────────────────────────────────────────────────────────┘
```

- **Hardware Setup**: Mount the ESP32, L298N driver, relay board, and four peristaltic pumps onto a clear acrylic board. Connect the pump inputs to four glass reservoirs containing water dyed with distinct, food-grade colors:
  - Reservoir 1 (Active Microbial Concentrate): **Yellow**
  - Reservoir 2 (Tween-80 Surfactant): **Blue**
  - Reservoir 3 (Sodium Lignosulfonate Stabilizer): **Red**
  - Reservoir 4 (Distilled Water Carrier): **Clear**
  - Place the output tubes of all four pumps into a single glass mixing beaker at the front of the stage.
- **Local Networking**: Run a local EMQX MQTT broker on the presenter's laptop and configure a dedicated Wi-Fi router. This ensures stable communication between the laptop and the ESP32, avoiding the high latency and interference of shared public venue networks.
- **Execution Sequence**:
  1. Enter an environmental scenario on the laptop interface, such as: *"High temperature and intense UV-B index of 8.5 detected on a Pusa 1121 Basmati crop in Punjab."* Project the terminal onto the stage screen, showing the OpenAI Agent SDK processing the command. The Stoichiometry Agent reasons through the UV degradation risks, while the Safety Agent confirms that the calculated stabilizer ratio is safe.
  2. The SCADA Agent compiles the recipe into runtimes (e.g., Pump 1: $72\text{s}$, Pump 2: $24\text{s}$, Pump 3: $36\text{s}$, Pump 4: $108\text{s}$) and publishes this payload to the `ai/agtech/zone1/d/peristaltic_dosing_rig_01` topic.
  3. The ESP32 immediately registers the payload, triggering the colored pumps. As the dyed liquids flow into the mixing beaker, the changing colors provide immediate, visual proof of the dynamic formulation process.

### Structured Three-Minute Pitch Script

**0:00 - 0:45: The Problem & Regional Bottleneck**

> "Good afternoon, judges. Today, South Asian agriculture is facing a critical crisis. In Pakistan, synthetic chemical pesticide costs have risen to an unsustainable $\text{PKR } 50,000$ per acre annually, squeezing farmer margins. More critically, our agricultural export sectors are suffering. Our premium Basmati rice exports to the European Union are threatened by strict chemical residue limits of $0.01 \text{ mg/kg}$. Our chili crops in the Kunri region face high aflatoxin levels averaging $32 \ \mu\text{g/kg}$—three times the international safety limit. Biopesticides offer a clean solution, but they are fragile; UV radiation, pH fluctuations, and dry air can degrade them on the leaf surface in just a few hours. This leaves crops unprotected and limits farmers' returns."

**0:46 - 1:30: The Agentic Solution**

> "To solve this, we developed ChemAgent-Agro: an autonomous formulation and dosing system. Our solution combines a Diploma of Associate Engineering in Chemical Technology with advanced Agentic AI engineering. Built on the OpenAI Agent SDK, our system coordinates specialized agents—monitoring environmental data, calculating formulation stoichiometry, validating chemical safety, and translating these choices into physical SCADA commands. When sensors detect high solar radiation or dry air, our agents dynamically adjust the formulation. They increase sodium lignosulfonate to absorb UV, extending the active half-life of the biopesticide by up to $14$-fold. They also modulate Tween-80 and surfactant-like peptides to enhance leaf retention and prevent evaporation."

**1:31 - 2:15: The Live Actuation**

> "We can see this in action on our stage demonstration rig. Our local sensors have detected a high UV index of 8.2 and dry conditions. Our Agentic controller processes these inputs and calculates the optimal recipe, maintaining active ingredients at $35\%$ while increasing the stabilizer to $15\%$ and surfactant to $10\%$. The SCADA Agent maps these parameters directly to industrial MQTT topics. Instantly, our physical ESP32 controller activates the dosing pumps. Watch as these color-coded components are precisely blended into our mixing beaker, proving that we can bridge digital reasoning with real-world physical execution."

**2:16 - 3:00: Agribusiness ROI & Market Impact**

> "Our system delivers clear economic benefits. By replacing blanket chemical applications with targeted, bio-formulated micro-dosing, we achieve a $90\%$ reduction in chemical volume. This saves Pakistani farmers an average of $\text{PKR } 45,000$ per acre annually. For rice and chili exporters, this technology eliminates the risk of costly border rejections, protecting shipments valued at up to $\$90,000$ per consignment. By using the Model Context Protocol, our system integrates seamlessly with legacy SCADA systems and modern IoT brokers, avoiding expensive hardware overhauls. We are not just building software; we are connecting AI directly to physical infrastructure to make agriculture sustainable, compliant, and profitable. Thank you."

## Conclusions

Implementing an agentic AI system for low-pesticide agriculture addresses critical economic, operational, and ecological challenges in modern agribusiness. This technology helps bridge the gap between chemical process engineering and physical automation.

### Actionable System Integration Strategy

```text
                          ┌───────────────────────────┐
                          │    Continuous Telemetry   │
                          │   (Weather & Soil Nodes)  │
                          └─────────────┬─────────────┘
                                        │ (Real-time updates)
                                        ▼
                          ┌───────────────────────────┐
                          │   Agentic Formulation     │
                          │   (OpenAI SDK & Safety)   │
                          └─────────────┬─────────────┘
                                        │ (Validated recipe)
                                        ▼
                          ┌───────────────────────────┐
                          │   Edge Actuation Bridge   │
                          │   (MCP over MQTT / ESP32) │
                          └───────────────────────────┘
```

- **Deploying the Telemetry Network**: Implement edge sensor nodes across agricultural zones to continuously monitor ambient pH, UV index, wind speed, and relative humidity, transmitting this data directly to the environmental agent.
- **Integrating Safety Guardrails**: Configure the safety agent to cross-verify all calculated chemical concentrations against regional environmental and maximum residue limit (MRL) standards prior to any physical execution.
- **Establishing the Protocol Bridge**: Deploy the Model Context Protocol (MCP) over MQTT using an EMQX broker to establish low-latency, secure communication between the cloud-based AI agents and physical field actuators.
- **Optimizing Dosing Control**: Program edge controllers (e.g., ESP32 or PLCs) to convert incoming agent instructions into precise pump speeds and runtimes, ensuring accurate stoichiometric blending.

By establishing this integrated workflow, agricultural operations can systematically reduce synthetic chemical usage, protect crucial export corridors, and improve overall crop health and sustainability.
