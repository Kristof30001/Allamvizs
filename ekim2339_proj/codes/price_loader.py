from pathlib import Path

import numpy as np
import pandas as pd


def _parse_mtu_start(series):
    start = series.astype(str).str.split(" - ").str[0]
    start = start.str.replace(r" \(CE(S)?T\)", "", regex=True)
    dt = pd.to_datetime(start, dayfirst=True, errors="coerce")
    return dt


def load_entsoe_hourly_prices(csv_path, exchange_rate=4.97, area="BZN|RO"):
    """
    ENTSO-E GUI CSV beolvasása és órás RON/kWh árak előállítása.
    Visszatér: DatetimeIndex + price_ron_kwh oszlop.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Nem található ár CSV: {csv_path}")

    df = pd.read_csv(path)

    required = {"MTU (CET/CEST)", "Day-ahead Price (EUR/MWh)"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Hiányzó kötelező oszlop(ok): {missing}")

    if "Area" in df.columns and area is not None:
        df = df[df["Area"].astype(str) == area].copy()

    if df.empty:
        raise ValueError("Az ár CSV üres a szűrés után")

    df["timestamp"] = _parse_mtu_start(df["MTU (CET/CEST)"])
    df = df.dropna(subset=["timestamp"]).copy()

    df["price_ron_kwh"] = (
        pd.to_numeric(df["Day-ahead Price (EUR/MWh)"], errors="coerce") / 1000.0
    ) * float(exchange_rate)
    df = df.dropna(subset=["price_ron_kwh"]).copy()

    hourly = (
        df.set_index("timestamp")[["price_ron_kwh"]]
        .sort_index()
        .resample("h")
        .mean()
    )

    hourly = hourly.ffill().bfill()
    return hourly


def build_daily_price_map(hourly_df, selected_days):
    """
    selected_days: [YYYY-MM-DD, ...]
    Visszatér: dict[day] -> np.ndarray(24,) RON/kWh
    """
    if "price_ron_kwh" not in hourly_df.columns:
        raise ValueError("hourly_df-ben hiányzik a price_ron_kwh oszlop")

    price_map = {}
    for day in selected_days:
        start = pd.Timestamp(day)
        idx = pd.date_range(start=start, periods=24, freq="h")
        sub = hourly_df.reindex(idx)
        if sub["price_ron_kwh"].isna().all():
            continue

        values = sub["price_ron_kwh"].ffill().bfill().to_numpy(dtype=float)
        if values.shape == (24,):
            price_map[day] = np.clip(values, 0.0, None)

    return price_map


def find_default_price_csv(price_dir):
    """
    A price_dir alatt megpróbálja kiválasztani a legnagyobb (tipikusan éves) GUI_ENERGY_PRICES fájlt.
    """
    base = Path(price_dir)
    if not base.exists():
        return None

    files = sorted(base.glob("GUI_ENERGY_PRICES_*.csv"))
    if not files:
        return None

    files = sorted(files, key=lambda p: p.stat().st_size, reverse=True)
    return files[0]
