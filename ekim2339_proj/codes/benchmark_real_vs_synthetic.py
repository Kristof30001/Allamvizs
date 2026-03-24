import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from algorithms import GA, PSO, GWO, Hybrid
from data_generator import DataGenerator
from hems_problem import SmartHomeEnvironment
from price_loader import (
    build_daily_price_map,
    find_default_price_csv,
    load_entsoe_hourly_prices,
)


SELECTED_DAYS = [
    "2025-01-14", "2025-01-22",
    "2025-03-17", "2025-03-19",
    "2025-05-23", "2025-05-30",
    "2025-06-12", "2025-06-28",
    "2025-08-01", "2025-08-22",
    "2025-09-01", "2025-09-25",
    "2025-11-02", "2025-11-30",
    "2025-12-24", "2025-12-27",
]

LOAD_REPLICAS = 1
RUNS_PER_PROFILE = 2
SEED_BASE = 20260323


ALGORITHMS = {
    "GA (P=50)": (GA, 40, 60),
    "GA (P=100)": (GA, 80, 60),
    "PSO": (PSO, 40, 60),
    "GWO": (GWO, 40, 60),
    "Hybrid": (Hybrid, 40, 60),
}


def stable_seed_from_day_rep(day, rep):
    # Python hash randomizacio helyett stabil, reprodukalhato seed.
    return int(day.replace("-", "")) * 10 + int(rep)


def month_to_season_tag(month):
    if month in (12, 1, 2):
        return "winter"
    if month in (6, 7, 8):
        return "summer"
    return "cloudy"


def load_real_hourly_pv(inverter_csv, selected_days):
    df = pd.read_csv(inverter_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    df = df[df["date"].isin(selected_days)].copy()

    # 5 perces teljesítményből órás átlagteljesítmény
    df["hour"] = df["timestamp"].dt.hour
    hourly = (
        df.groupby(["date", "hour"], as_index=False)["power_kW"]
        .mean()
        .rename(columns={"power_kW": "pv"})
    )

    profiles = {}
    for day in selected_days:
        day_rows = hourly[hourly["date"] == day]
        if day_rows.empty:
            continue
        pv = np.zeros(24)
        for _, row in day_rows.iterrows():
            h = int(row["hour"])
            pv[h] = max(float(row["pv"]), 0.0)
        month = int(day[5:7])
        profiles[day] = {
            "day": day,
            "season": month_to_season_tag(month),
            "pv": pv,
        }
    return profiles


def resolve_day_price(day, day_price_map, default_price):
    if day in day_price_map:
        return day_price_map[day].copy()
    return default_price.copy()


def build_realpv_profiles(real_pv_profiles, day_price_map, gen, load_replicas, seed_base):
    profiles = []
    default_price = gen.get_tou_prices().copy()
    for day in SELECTED_DAYS:
        if day not in real_pv_profiles:
            continue
        meta = real_pv_profiles[day]
        season = meta["season"]
        for rep in range(load_replicas):
            rng = np.random.default_rng(seed_base + stable_seed_from_day_rep(day, rep))
            load = gen.generate_load_profile(season=season, rng=rng)
            profiles.append(
                {
                    "profile_id": f"{day}_rep{rep:02d}",
                    "dataset": "real_pv",
                    "day": day,
                    "season": season,
                    "load": load,
                    "pv": meta["pv"].copy(),
                    "price": resolve_day_price(day, day_price_map, default_price),
                }
            )
    return profiles


def build_synthetic_profiles(real_pv_profiles, day_price_map, gen, load_replicas, seed_base):
    profiles = []
    default_price = gen.get_tou_prices().copy()
    for day in SELECTED_DAYS:
        if day not in real_pv_profiles:
            continue
        season = real_pv_profiles[day]["season"]
        for rep in range(load_replicas):
            rng = np.random.default_rng(seed_base + 10_000_000 + stable_seed_from_day_rep(day, rep))
            load = gen.generate_load_profile(season=season, rng=rng)
            pv = gen.generate_pv_profile(season=season, rng=rng)
            profiles.append(
                {
                    "profile_id": f"{day}_rep{rep:02d}",
                    "dataset": "synthetic",
                    "day": day,
                    "season": season,
                    "load": load,
                    "pv": pv,
                    "price": resolve_day_price(day, day_price_map, default_price),
                }
            )
    return profiles


def evaluate_profiles(profiles, runs_per_profile, seed_base):
    rows = []

    for p_idx, p in enumerate(profiles):
        env = SmartHomeEnvironment(p["load"], p["pv"], p["price"])

        for a_idx, (algo_name, (AlgoClass, pop_size, max_iter)) in enumerate(ALGORITHMS.items()):
            for run_idx in range(runs_per_profile):
                np.random.seed(seed_base + p_idx * 10_000 + a_idx * 1_000 + run_idx)
                t0 = time.time()
                solver = AlgoClass(
                    env.objective_function,
                    env.dim,
                    env.lb,
                    env.ub,
                    pop_size=pop_size,
                    max_iter=max_iter,
                )
                _, cost = solver.solve()
                runtime_s = time.time() - t0

                rows.append(
                    {
                        "dataset": p["dataset"],
                        "profile_id": p["profile_id"],
                        "day": p["day"],
                        "season": p["season"],
                        "algorithm": algo_name,
                        "run": run_idx,
                        "cost": float(cost),
                        "runtime_s": float(runtime_s),
                    }
                )

    return pd.DataFrame(rows)


def build_summary(raw_df):
    perf = (
        raw_df.groupby(["dataset", "algorithm"], as_index=False)
        .agg(
            mean_cost=("cost", "mean"),
            std_cost=("cost", "std"),
            best_cost=("cost", "min"),
            mean_runtime_s=("runtime_s", "mean"),
        )
    )

    per_profile_best = (
        raw_df.groupby(["dataset", "profile_id", "algorithm"], as_index=False)["cost"]
        .min()
        .rename(columns={"cost": "best_cost_algo"})
    )

    global_best = (
        per_profile_best.groupby(["dataset", "profile_id"], as_index=False)["best_cost_algo"]
        .min()
        .rename(columns={"best_cost_algo": "global_best"})
    )

    merged = per_profile_best.merge(global_best, on=["dataset", "profile_id"], how="left")
    merged["gap_pct"] = (
        (merged["best_cost_algo"] - merged["global_best"]) /
        (merged["global_best"].abs() + 1e-9) * 100.0
    )

    gap_stats = (
        merged.groupby(["dataset", "algorithm"], as_index=False)
        .agg(avg_gap_pct=("gap_pct", "mean"))
    )

    winners = (
        merged.sort_values(["dataset", "profile_id", "best_cost_algo"])
        .groupby(["dataset", "profile_id"], as_index=False)
        .first()[["dataset", "profile_id", "algorithm"]]
    )

    win_counts = (
        winners.groupby(["dataset", "algorithm"], as_index=False)
        .size()
        .rename(columns={"size": "wins"})
    )

    profile_counts = winners.groupby("dataset", as_index=False).size().rename(columns={"size": "profiles"})
    win_rates = win_counts.merge(profile_counts, on="dataset", how="left")
    win_rates["win_rate_pct"] = win_rates["wins"] / win_rates["profiles"] * 100.0

    summary = perf.merge(gap_stats, on=["dataset", "algorithm"], how="left")
    summary = summary.merge(win_rates[["dataset", "algorithm", "wins", "win_rate_pct"]], on=["dataset", "algorithm"], how="left")
    summary["wins"] = summary["wins"].fillna(0).astype(int)
    summary["win_rate_pct"] = summary["win_rate_pct"].fillna(0.0)

    summary = summary.sort_values(["dataset", "avg_gap_pct", "mean_cost"]).reset_index(drop=True)
    return summary, merged, winners


def to_markdown_report(summary_df, winners_df, raw_df):
    lines = []
    lines.append("# Benchmark: valos PV vs szintetikus")
    lines.append("")
    lines.append(f"- Kivalasztott napok: {len(SELECTED_DAYS)}")
    lines.append(f"- Terheles replikak/nap: {LOAD_REPLICAS}")
    lines.append(f"- Futas/algoritmus/profil: {RUNS_PER_PROFILE}")
    lines.append("")

    for dataset in ["real_pv", "synthetic"]:
        lines.append(f"## {dataset}")
        sub = summary_df[summary_df["dataset"] == dataset].copy()
        sub = sub.sort_values("avg_gap_pct")

        lines.append("")
        lines.append("| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            lines.append(
                f"| {r['algorithm']} | {r['mean_cost']:.2f} | {r['std_cost']:.2f} | "
                f"{r['avg_gap_pct']:.2f} | {int(r['wins'])} | "
                f"{r['win_rate_pct']:.1f} | {r['mean_runtime_s']:.3f} |"
            )

        lines.append("")

    # Egyszeru konkluzio automatikusan
    real_best = summary_df[summary_df["dataset"] == "real_pv"].sort_values("avg_gap_pct").iloc[0]
    synth_best = summary_df[summary_df["dataset"] == "synthetic"].sort_values("avg_gap_pct").iloc[0]

    lines.append("## Konkluzio")
    lines.append("")
    lines.append(
        f"A valos PV adatokon a legstabilabb algoritmus: {real_best['algorithm']} "
        f"(atlag gap: {real_best['avg_gap_pct']:.2f}%, gyozelmi arany: {real_best.get('win_rate_pct', 0.0):.1f}%)."
    )
    lines.append(
        f"A teljesen szintetikus adatokon a legstabilabb algoritmus: {synth_best['algorithm']} "
        f"(atlag gap: {synth_best['avg_gap_pct']:.2f}%, gyozelmi arany: {synth_best.get('win_rate_pct', 0.0):.1f}%)."
    )

    if real_best["algorithm"] == synth_best["algorithm"]:
        lines.append("A ket adathalmazon ugyanaz a nyertes, ami jo generalizaciot jelez.")
    else:
        lines.append("A ket adathalmazon mas a nyertes, ez domain-fuggo viselkedest jelez.")

    n_rows = len(raw_df)
    lines.append(f"A kiertékeles osszesen {n_rows} egyedi algoritmusfutast tartalmaz.")

    return "\n".join(lines)


def main():
    repo_root = Path(__file__).resolve().parents[2]
    inverter_csv = repo_root / "Reports" / "Inverter" / "inverter_osszes.csv"
    price_dir = repo_root / "Reports" / "Price"
    out_dir = repo_root / "ekim2339_proj"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not inverter_csv.exists():
        raise FileNotFoundError(f"Nem talalhato: {inverter_csv}")

    gen = DataGenerator()
    real_pv_map = load_real_hourly_pv(inverter_csv, SELECTED_DAYS)

    day_price_map = {}
    price_csv = find_default_price_csv(price_dir)
    if price_csv is not None:
        try:
            hourly_prices = load_entsoe_hourly_prices(price_csv)
            day_price_map = build_daily_price_map(hourly_prices, SELECTED_DAYS)
            print(f"Valos ENTSO-E arak betoltve: {price_csv.name} | napok: {len(day_price_map)}")
        except Exception as e:
            print(f"Figyelem: valos arak betoltese sikertelen ({e}), TOU fallback lesz.")
    else:
        print("Figyelem: nincs ENTSO-E ar CSV, TOU fallback lesz.")

    missing_days = [d for d in SELECTED_DAYS if d not in real_pv_map]
    if missing_days:
        print("Figyelem, ezekre a napokra nem volt adatsor:", missing_days)

    real_profiles = build_realpv_profiles(real_pv_map, day_price_map, gen, LOAD_REPLICAS, SEED_BASE)
    synth_profiles = build_synthetic_profiles(real_pv_map, day_price_map, gen, LOAD_REPLICAS, SEED_BASE)

    if day_price_map:
        missing_price_days = [d for d in SELECTED_DAYS if d not in day_price_map]
        if missing_price_days:
            print("Figyelem: ezekre a napokra TOU fallback ar lesz:", missing_price_days)
    else:
        print("Minden profil TOU arat hasznal (valos ar map ures).")

    profiles = real_profiles + synth_profiles
    print(f"Profilok szama: {len(profiles)} (real_pv={len(real_profiles)}, synthetic={len(synth_profiles)})")

    raw_df = evaluate_profiles(profiles, RUNS_PER_PROFILE, SEED_BASE)
    summary_df, gaps_df, winners_df = build_summary(raw_df)

    raw_path = out_dir / "results_realpv_vs_synth_raw.csv"
    summary_path = out_dir / "results_realpv_vs_synth_summary.csv"
    gaps_path = out_dir / "results_realpv_vs_synth_gaps.csv"
    winners_path = out_dir / "results_realpv_vs_synth_winners.csv"
    report_path = out_dir / "results_realpv_vs_synth_report.md"
    json_path = out_dir / "results_realpv_vs_synth_summary.json"

    raw_df.to_csv(raw_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    gaps_df.to_csv(gaps_path, index=False)
    winners_df.to_csv(winners_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary_df.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    report_text = to_markdown_report(summary_df, winners_df, raw_df)
    report_path.write_text(report_text, encoding="utf-8")

    print(f"Mentve: {raw_path}")
    print(f"Mentve: {summary_path}")
    print(f"Mentve: {gaps_path}")
    print(f"Mentve: {winners_path}")
    print(f"Mentve: {json_path}")
    print(f"Mentve: {report_path}")


if __name__ == "__main__":
    main()
