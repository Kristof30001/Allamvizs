"""
FusionSolar Inverter Adatfeldolgozó
====================================
Használat:
  1. Tedd az összes letöltött XLSX fájlt egy mappába
  2. Futtasd: python3 inverter_feldolgoz.py
  3. Eredmény: inverter_osszes.csv és reprezentativ_napok.csv
"""

import pandas as pd
import glob
import os

# ── KONFIGURÁCIÓ ──────────────────────────────────────────────
MAPPA = "."          # Az XLSX fájlok mappája (. = ugyanaz a mappa)
KIMENETI_OSSZES = "inverter_osszes.csv"
KIMENETI_REP    = "reprezentativ_napok.csv"

# Határok évszakonként (napi kWh alapján)
HATAROK = {
    "Tel":    {"jo": 6.0,  "rossz": 1.0},
    "Tavasz": {"jo": 14.0, "rossz": 3.0},
    "Nyar":   {"jo": 18.0, "rossz": 5.0},
    "Osz":    {"jo": 14.0, "rossz": 3.0},
}

def evszak(month):
    if month in [12, 1, 2]:  return "Tel"
    if month in [3, 4, 5]:   return "Tavasz"
    if month in [6, 7, 8]:   return "Nyar"
    return "Osz"

# ── BEOLVASÁS ─────────────────────────────────────────────────
def beolvas_xlsx(path):
    """Egy FusionSolar XLSX fájl beolvasása és tisztítása."""
    try:
        raw = pd.read_excel(path, sheet_name="5 minutes", header=2)
        raw.columns = raw.iloc[0]
        raw = raw.iloc[1:].reset_index(drop=True)

        df = pd.DataFrame()
        df["timestamp"]   = pd.to_datetime(raw["Start Time"], errors="coerce")
        df["power_kW"]    = pd.to_numeric(raw["Active power(kW)"], errors="coerce").fillna(0)
        df["daily_kWh"]   = pd.to_numeric(raw["Daily energy(kWh)"], errors="coerce").fillna(0)
        df["total_kWh"]   = pd.to_numeric(raw["Total yield(kWh)"], errors="coerce")
        df["temp_C"]      = pd.to_numeric(raw["Internal temperature(℃)"], errors="coerce")
        df["pv1_V"]       = pd.to_numeric(raw["PV1 input voltage(V)"], errors="coerce")
        df["pv2_V"]       = pd.to_numeric(raw["PV2 input voltage(V)"], errors="coerce")
        df["pv1_A"]       = pd.to_numeric(raw["PV1 input current(A)"], errors="coerce")
        df["pv2_A"]       = pd.to_numeric(raw["PV2 input current(A)"], errors="coerce")
        df["status"]      = raw["Inverter status"].astype(str)
        df["freq_Hz"]     = pd.to_numeric(raw["Grid frequency(Hz)"], errors="coerce")

        df = df.dropna(subset=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        print(f"  ✅ {os.path.basename(path)}: {len(df)} sor, "
              f"{df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
        return df

    except Exception as e:
        print(f"  ❌ {os.path.basename(path)}: {e}")
        return None

# ── FŐ FELDOLGOZÁS ────────────────────────────────────────────
print("=" * 55)
print("FusionSolar Inverter Adatfeldolgozó")
print("=" * 55)

fajlok = sorted(glob.glob(os.path.join(MAPPA, "Inverter_*.xlsx")))
if not fajlok:
    print("❌ Nem találhatók Inverter_*.xlsx fájlok a mappában!")
    exit()

print(f"\n{len(fajlok)} fájl megtalálva:\n")
reszek = [beolvas_xlsx(f) for f in fajlok]
reszek = [r for r in reszek if r is not None]

if not reszek:
    print("❌ Egyetlen fájl sem olvasható be.")
    exit()

# Összefűzés és duplikátumok eltávolítása
df_all = pd.concat(reszek, ignore_index=True)
df_all = df_all.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

print(f"\n📊 Összesen: {len(df_all)} mérés | "
      f"{df_all['timestamp'].min().date()} → {df_all['timestamp'].max().date()}")

# ── NAPI ÖSSZESÍTŐK ───────────────────────────────────────────
df_all["date"]   = df_all["timestamp"].dt.date
df_all["month"]  = df_all["timestamp"].dt.month
df_all["hour"]   = df_all["timestamp"].dt.hour

daily = df_all.groupby("date").agg(
    napi_kWh       = ("daily_kWh",  "max"),
    csucs_kW       = ("power_kW",   "max"),
    aktiv_ora      = ("power_kW",   lambda x: round((x > 0.01).sum() * 5 / 60, 2)),
    atlag_kW       = ("power_kW",   lambda x: round(x[x > 0.01].mean(), 3) if (x > 0.01).any() else 0),
    max_temp_C     = ("temp_C",     "max"),
    csucside       = ("power_kW",   lambda x: df_all.loc[x.idxmax(), "timestamp"].strftime("%H:%M") if x.max() > 0 else "--"),
).reset_index()

daily["month"]   = pd.to_datetime(daily["date"].astype(str)).dt.month
daily["evszak"]  = daily["month"].apply(evszak)

# ── MINŐSÍTÉS ─────────────────────────────────────────────────
def minosit(row):
    h = HATAROK[row["evszak"]]
    if row["napi_kWh"] >= h["jo"]:    return "jo"
    if row["napi_kWh"] <= h["rossz"]: return "rossz"
    return "kozepes"

daily["minosites"] = daily.apply(minosit, axis=1)

# ── KIMENETEK ─────────────────────────────────────────────────
# 1. Teljes 5 perces adatsor
df_all[["timestamp","power_kW","daily_kWh","total_kWh",
        "temp_C","pv1_V","pv2_V","pv1_A","pv2_A","status"]].to_csv(
    KIMENETI_OSSZES, index=False)
print(f"\n💾 Teljes adatsor mentve → {KIMENETI_OSSZES}")

# 2. Reprezentatív napok összesítője
daily.to_csv(KIMENETI_REP, index=False)
print(f"💾 Napi összesítő mentve  → {KIMENETI_REP}")

# ── ÖSSZEFOGLALÓ TÁBLÁZAT ─────────────────────────────────────
print("\n" + "=" * 55)
print("NAPI TERMELÉS ÖSSZESÍTŐ")
print("=" * 55)
print(f"{'Dátum':<12} {'Évszak':<8} {'kWh':>6} {'Csúcs kW':>9} {'Aktív h':>8} {'Minősítés':<10}")
print("-" * 55)
for _, r in daily.iterrows():
    jel = "✅" if r["minosites"]=="jo" else ("❌" if r["minosites"]=="rossz" else "➖")
    print(f"{str(r['date']):<12} {r['evszak']:<8} {r['napi_kWh']:>6.2f} "
          f"{r['csucs_kW']:>9.3f} {r['aktiv_ora']:>8.1f} {jel} {r['minosites']}")

# ── ÉVSZAK STATISZTIKA ────────────────────────────────────────
print("\n" + "=" * 55)
print("ÉVSZAK STATISZTIKA")
print("=" * 55)
for ev in ["Tel", "Tavasz", "Nyar", "Osz"]:
    sub = daily[daily["evszak"] == ev]
    if sub.empty:
        print(f"{ev:<8}: nincs adat")
        continue
    jo    = len(sub[sub["minosites"] == "jo"])
    kozep = len(sub[sub["minosites"] == "kozepes"])
    rossz = len(sub[sub["minosites"] == "rossz"])
    print(f"{ev:<8}: {len(sub):>3} nap | "
          f"✅ {jo} jó | ➖ {kozep} közepes | ❌ {rossz} rossz | "
          f"Átlag: {sub['napi_kWh'].mean():.2f} kWh/nap")

print("\n✅ Kész!")
