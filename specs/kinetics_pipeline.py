"""
AgriAgent — Biopesticide Kinetics & Telemetry Pipeline

Fetches hourly historical weather (Open-Meteo) for the South Asian cotton belt
(Multan / Hyderabad corridor), binds it to published lab constants for
Bacillus thuringiensis (Bt) crystal endotoxins, and computes a time-varying
first-order degradation curve. Exports the result as the Kaggle-ready CSV
specified in Biopesticide-Kinetics-&-Telemetry-Pipeline.md.

Usage:
    python kinetics_pipeline.py                          # fetch + compute + export
    python kinetics_pipeline.py --offline                # use bundled sample data
    python kinetics_pipeline.py --days 7 --output out.csv

Output columns (per spec):
    timestamp, ambient_temp_c, rel_humidity_pct, uv_index, solar_irradiance_wm2,
    k_dynamic_per_hr, calculated_half_life_hrs, bt_viability_pct, recommended_lignin_pct
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import urllib.request
import json

# ---------------------------------------------------------------------------
# 2. Empirical baseline constants (PPDB / EPA CompTox reference values)
# ---------------------------------------------------------------------------

DT50_BASE_HOURS = 48.0          # Baseline dark half-life (hours), PPDB
T0_KELVIN = 298.15              # Reference temperature 25 C
EA_J_PER_MOL = 42_500.0         # Denaturation activation energy (J/mol), EPA CompTox
R_GAS = 8.314                   # Universal gas constant J/(mol*K)
ALPHA_UV = 0.18                 # UV photolysis scaling factor (Index^-1)

# Derived baseline rate constant. Spec formula (section 3) expresses this in
# minutes, but the CSV schema declares k_dynamic_per_hr, so we keep per-hour
# units end to end and label the column accordingly.
K_BASELINE_PER_HR = math.log(2) / DT50_BASE_HOURS  # ~0.01444 hr^-1


# ---------------------------------------------------------------------------
# 3. Deterministic kinetics model
# ---------------------------------------------------------------------------

def f_uv(uv_index: float) -> float:
    """Photolysis multiplier: 1.0 at night (no UV), grows linearly with UV."""
    return 1.0 + ALPHA_UV * max(0.0, uv_index)


def f_temp(temp_c: float) -> float:
    """Arrhenius thermal multiplier (dimensionless, =1.0 at 25 C)."""
    t_amb = temp_c + 273.15
    if t_amb <= 0.0:
        return 1.0
    return math.exp(-(EA_J_PER_MOL / R_GAS) * ((1.0 / t_amb) - (1.0 / T0_KELVIN)))


def k_dynamic_per_hr(uv_index: float, temp_c: float) -> float:
    """Hourly degradation rate constant for the given weather snapshot."""
    return K_BASELINE_PER_HR * f_uv(uv_index) * f_temp(temp_c)


def recommended_lignin_pct(uv_index: float) -> float:
    """Dynamic UV-stabilizer setpoint: min(3.0, 0.25 + 0.25 * UV) (% w/v)."""
    return min(3.0, 0.25 + 0.25 * max(0.0, uv_index))


# ---------------------------------------------------------------------------
# 4. Ingestion — Open-Meteo historical API (Multan cotton belt)
# ---------------------------------------------------------------------------

MULTAN_LAT, MULTAN_LON = 30.1575, 71.5249

# The archive API does NOT provide uv_index / shortwave_radiation (verified
# 2026-08-20: uv_index is all None). Use the forecast API for the recent
# window (it has both variables) and fall back to thermal-only for older days.
FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&start_date={start}&end_date={end}"
    "&hourly=temperature_2m,relative_humidity_2m,uv_index,shortwave_radiation"
    "&timezone=UTC"
)
ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude={lat}&longitude={lon}"
    "&start_date={start}&end_date={end}"
    "&hourly=temperature_2m,relative_humidity_2m,uv_index,shortwave_radiation"
    "&timezone=UTC"
)


@dataclass
class WeatherHour:
    timestamp: datetime
    temp_c: float
    rh_pct: float
    uv_index: float
    solar_wm2: float


def fetch_open_meteo(start_date: str, end_date: str) -> List[WeatherHour]:
    """Fetch hourly weather for [start_date, end_date] (YYYY-MM-DD, inclusive).

    Uses the forecast API when the window is within its range so UV/solar data
    is real; falls back to the archive API (thermal-only) for older windows.
    """
    # Open-Meteo forecast supports ~16 days back. Use it when the window is
    # recent enough; otherwise use the archive (UV will be null).
    today = datetime.now(timezone.utc).date()
    window_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    use_forecast = (today - window_start).days <= 16

    url_template = FORECAST_URL if use_forecast else ARCHIVE_URL
    url = url_template.format(
        lat=MULTAN_LAT, lon=MULTAN_LON, start=start_date, end=end_date
    )
    print(f"[INGEST] {'FORECAST' if use_forecast else 'ARCHIVE'} GET {url}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    hourly = data["hourly"]
    hours: List[WeatherHour] = []
    uv_null_count = 0
    for ts, temp, rh, uv, solar in zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["relative_humidity_2m"],
        hourly["uv_index"],
        hourly["shortwave_radiation"],
    ):
        # API returns None for missing observations; default sensibly.
        if uv is None:
            uv_null_count += 1
        hours.append(
            WeatherHour(
                timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
                temp_c=temp if temp is not None else 25.0,
                rh_pct=rh if rh is not None else 60.0,
                uv_index=uv if uv is not None else 0.0,
                solar_wm2=solar if solar is not None else 0.0,
            )
        )
    if not hours:
        raise RuntimeError("Open-Meteo returned no hourly data.")

    if uv_null_count:
        print(
            f"[WARN] uv_index unavailable for {uv_null_count}/{len(hours)} hours "
            f"({use_forecast and 'forecast' or 'archive'} API); "
            f"photolysis term will be thermal-only for those hours."
        )
    return hours


# ---------------------------------------------------------------------------
# 4b. Offline fallback — deterministic synthetic telemetry for demo/testing
# ---------------------------------------------------------------------------

def synthetic_telemetry(start: datetime, n_hours: int) -> List[WeatherHour]:
    """Generate a realistic hot/dry cotton-belt day cycle without the network."""
    hours: List[WeatherHour] = []
    for i in range(n_hours):
        t = start + timedelta(hours=i)
        # Diurnal temperature: min ~22C at 05:00, max ~40C at 15:00 local
        hour_of_day = t.hour
        temp_c = 31.0 + 9.0 * math.sin(math.pi * (hour_of_day - 9.0) / 12.0)
        # UV follows the sun: zero at night, peak ~11.5 at solar noon
        uv_index = max(0.0, 11.5 * math.sin(math.pi * (hour_of_day - 6.0) / 12.0))
        rh_pct = max(10.0, 100.0 - 2.2 * temp_c + 3.0 * math.sin(math.pi * (hour_of_day - 15.0) / 12.0))
        solar_wm2 = max(0.0, 950.0 * math.sin(math.pi * (hour_of_day - 6.0) / 12.0))
        hours.append(
            WeatherHour(
                timestamp=t,
                temp_c=round(temp_c, 1),
                rh_pct=round(rh_pct, 1),
                uv_index=round(uv_index, 2),
                solar_wm2=round(solar_wm2, 1),
            )
        )
    return hours


# ---------------------------------------------------------------------------
# 4c. CSV export (Kaggle-ready schema)
# ---------------------------------------------------------------------------

CSV_HEADERS = [
    "timestamp",
    "ambient_temp_c",
    "rel_humidity_pct",
    "uv_index",
    "solar_irradiance_wm2",
    "k_dynamic_per_hr",
    "calculated_half_life_hrs",
    "bt_viability_pct",
    "recommended_lignin_pct",
]


def run_pipeline(hours: List[WeatherHour], output_path: Path) -> Path:
    """Compute time-stepped degradation and write the CSV. Returns output path."""
    # Sequential decay: C(t + dt) = C(t) * exp(-k_dynamic * dt), dt = 1 hour
    viability = 100.0
    rows: List[dict] = []

    print("\n[KINETICS] Hourly degradation simulation")
    print(f"{'time':<20}{'UV':>6}{'T(C)':>7}{'k/hr':>9}{'t1/2(hr)':>10}{'viab%':>8}")
    for h in hours:
        k = k_dynamic_per_hr(h.uv_index, h.temp_c)
        half_life = math.log(2) / k if k > 0 else math.inf
        viability *= math.exp(-k * 1.0)  # dt = 1 hour
        viability = max(0.0, min(100.0, viability))  # spec: bound to [0, C0]

        rows.append(
            {
                "timestamp": h.timestamp.isoformat(),
                "ambient_temp_c": round(h.temp_c, 2),
                "rel_humidity_pct": round(h.rh_pct, 2),
                "uv_index": round(h.uv_index, 2),
                "solar_irradiance_wm2": round(h.solar_wm2, 2),
                "k_dynamic_per_hr": round(k, 6),
                "calculated_half_life_hrs": round(half_life, 3) if math.isfinite(half_life) else "inf",
                "bt_viability_pct": round(viability, 4),
                "recommended_lignin_pct": round(recommended_lignin_pct(h.uv_index), 4),
            }
        )
        if len(rows) <= 24 or len(rows) % 24 == 0:
            hl = half_life if math.isfinite(half_life) else float("inf")
            print(
                f"{h.timestamp:%Y-%m-%d %H:%M}  "
                f"UV {h.uv_index:5.2f}  T {h.temp_c:5.1f}C  "
                f"k {k:6.4f}/hr  t1/2 {hl:6.2f}hr  viability {viability:6.2f}%"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[EXPORT] Wrote {len(rows)} rows -> {output_path.resolve()}")
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def default_date_range(days: int) -> tuple[str, str]:
    end = datetime.now(timezone.utc) - timedelta(days=1)  # archive lags ~2 days
    start = end - timedelta(days=days - 1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="Use deterministic synthetic telemetry instead of Open-Meteo")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of days of hourly history (default: 7)")
    parser.add_argument("--start", type=str, default=None,
                        help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", type=str, default=None,
                        help="End date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV path (default: synthetic_biopesticide_telemetry.csv)")
    args = parser.parse_args()

    if args.start and args.end:
        start_date, end_date = args.start, args.end
    else:
        start_date, end_date = default_date_range(args.days)

    output = Path(args.output) if args.output else Path("synthetic_biopesticide_telemetry.csv")

    if args.offline:
        print(f"[INGEST] Synthetic telemetry: {args.days} days from {start_date}")
        start_dt = datetime.fromisoformat(start_date + "T00:00:00+00:00")
        hours = synthetic_telemetry(start_dt, args.days * 24)
    else:
        hours = fetch_open_meteo(start_date, end_date)

    run_pipeline(hours, output)


if __name__ == "__main__":
    main()
