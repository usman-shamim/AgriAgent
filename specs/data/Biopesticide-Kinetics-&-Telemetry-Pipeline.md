# Biopesticide Kinetics & Telemetry Pipeline

## 1. Pipeline Architecture & Execution Flow

The pipeline fetches historical environmental telemetry, binds it to empirical laboratory constants, and calculates dynamic degradation kinetics across discrete time steps.

```
[Open-Meteo Forecast / Archive API] (Multan / Sindh Corridor)
                   │
                   ▼ (Hourly Ingestion: Temp, Direct Solar, RH, UV Index)
[Baseline Parameters Engine] (PPDB / BPDB / EPA Reference Constants)
                   │
                   ▼ (Arrhenius Scaling + UV Photolysis)
[Deterministic Kinetics Engine] (C(t) = C_0 * exp(-k_dynamic * t))
                   │
                   ▼
[Export Target] -> synthetic_biopesticide_telemetry.csv (Kaggle Dataset)
```

The reference implementation is `specs/code/kinetics_pipeline.py`. It uses the **forecast** Open-Meteo API for the recent window (the archive API does not expose `uv_index` or solar radiation) and falls back to the archive API for older windows, warning when UV is unavailable.

## 2. Ingestion & Empirical Baseline Constants

The engine uses published laboratory reference constants for *Bacillus thuringiensis* (Bt) crystal endotoxins as anchor baselines:

| Parameter | Symbol | Reference Value | Source / Standard |
| --- | --- | --- | --- |
| Baseline Dark Half-Life | $DT_{50,\text{base}}$ | $48.0\text{ hours}$ (2 days) | Model baseline within the published range — soil-lab DT50 ≈ 2.7 days (BPDB, *B. thuringiensis* subsp. *kurstaki*); foliar field t½ 13.6–18.4 h (Haddad et al. 2005). Not a direct PPDB entry. |
| Reference Temperature | $T_0$ | $298.15\text{ K}\ (25^\circ\text{C})$ | Standard Ambient Temperature |
| Denaturation Activation Energy | $E_a$ | $42.5\text{ kJ/mol}$ | Apparent activation energy (biological degradation, Q10 ≈ 1.7). Not an EPA CompTox entry; see wayfinder resolution on ticket #4. |
| Universal Gas Constant | $R$ | $8.314\text{ J}/(\text{mol}\cdot\text{K})$ | Thermodynamic Constant |
| UV Sensitivity Scaling Factor | $\alpha$ | $0.18\text{ Index}^{-1}$ | Empirical linear heuristic (kept for MVP; see ticket #4 for the additive photolysis form planned for v2) |

* **Environmental Ingestion Contract:** Pulls hourly historical data for the cotton belt (Multan / Hyderabad: latitude 30.1575, longitude 71.5249).
* **Ingested Variables:** 2-meter air temperature ($^\circ\text{C}$), relative humidity (%), surface solar radiation ($W/m^2$), and UV index.

## 3. Deterministic Kinetics Model

The degradation rate constant ($k_{\text{dynamic}}$) adjusts programmatically at every hourly interval ($t_i$) based on weather flux. All rates are **per hour** (matching the CSV schema; the minute-based form is dropped):

$$k_{\text{baseline}} = \frac{\ln(2)}{DT_{50,\text{base}}} \quad (\text{hr}^{-1})$$

$$f(\text{UV}) = 1.0 + \alpha \times I_{\text{UV}}$$

$$f(\text{Temp}) = \exp\left(-\frac{E_a}{R}\left(\frac{1}{T_{\text{amb}} + 273.15} - \frac{1}{T_0}\right)\right)$$

$$k_{\text{dynamic}}(t) = k_{\text{baseline}} \times f(\text{UV}) \times f(\text{Temp})$$

Concentration decay over each interval $\Delta t = 1\text{ hour}$ is computed sequentially:

$$C(t + \Delta t) = C(t) \times \exp\left(-k_{\text{dynamic}}(t) \times \Delta t\right)$$

* **Nighttime Boundary Condition:** When $I_{\text{UV}} = 0$, photolysis stops ($f(\text{UV}) = 1.0$), leaving only thermal degradation active.
* **Viability Cutoff:** Concentration $C(t)$ is bounded such that $0.0 \le C(t) \le C_0$, preventing numerical divergence or negative values.

## 4. Output CSV Schema & Kaggle Deployment

The pipeline generates an exportable tabular format structured for Kaggle hosting and agent ingestion:

| Column Name | Data Type | Physical Unit | Description |
| --- | --- | --- | --- |
| `timestamp` | ISO-8601 String | UTC / Local Time | Observation interval timestamp |
| `ambient_temp_c` | Float | °C | Ingested dry-bulb air temperature |
| `rel_humidity_pct` | Float | % | Ingested relative humidity |
| `uv_index` | Float | Index (0 to 16) | Direct UV Index metric |
| `solar_irradiance_wm2` | Float | W/m² | Global horizontal solar irradiance |
| `k_dynamic_per_hr` | Float | hr⁻¹ | Calculated dynamic degradation rate constant |
| `calculated_half_life_hrs` | Float | Hours | Instantaneous half-life: $t_{1/2} = \ln(2)/k_{\text{dynamic}}$ |
| `bt_viability_pct` | Float | % ($C_0 = 100\%$) | Surviving unshielded active biopesticide fraction |
| `recommended_lignin_pct` | Float | % w/v | Dynamic UV stabilizer setpoint: $\min(3.0, 0.25 + 0.25 \times I_{\text{UV}})$ |

* **Integration with AgriAgent:** The Formulation Agent queries this tabular benchmark via Python or MCP tools to validate its dynamic dosing calculations deterministically against ground truth.

## 5. Run Instructions

```bash
# Live fetch (forecast API, real UV for Multan), 7 days
python3 specs/code/kinetics_pipeline.py --days 7 --output data/synthetic_biopesticide_telemetry.csv

# Offline deterministic demo (no network)
python3 specs/code/kinetics_pipeline.py --offline --days 2
```

The pipeline is pure standard library — no third-party install required.
