import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from algorithms import GA, PSO, GWO, Hybrid
from data_generator import DataGenerator, load_real_consumption
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


def build_realpv_profiles(real_pv_profiles, day_price_map, gen, load_replicas, seed_base, load_source="synthetic", real_load_profile=None):
    """
    Valós PV adatokat tartalmazó profilokat építünk.
    
    Args:
        load_source: "synthetic" (generált) vagy "real" (UCI adatsor)
        real_load_profile: Ha load_source="real", akkor az órás fogyasztási profil numpy tömb
    """
    profiles = []
    default_price = gen.get_tou_prices().copy()
    for day in SELECTED_DAYS:
        if day not in real_pv_profiles:
            continue
        meta = real_pv_profiles[day]
        season = meta["season"]
        for rep in range(load_replicas):
            rng = np.random.default_rng(seed_base + stable_seed_from_day_rep(day, rep))
            
            # Fogyasztás forrásának kiválasztása
            if load_source == "real" and real_load_profile is not None:
                # Valós adatokból vegyünk 24 órát
                start_idx = (rep * 24) % (len(real_load_profile) - 24)
                load = real_load_profile[start_idx:start_idx + 24].copy()
            else:
                # Szintetikus generálás
                load = gen.generate_load_profile(season=season, rng=rng)
            
            dataset_name = f"real_pv_load_{load_source}"
            profiles.append(
                {
                    "profile_id": f"{day}_rep{rep:02d}",
                    "dataset": dataset_name,
                    "day": day,
                    "season": season,
                    "load": load,
                    "pv": meta["pv"].copy(),
                    "price": resolve_day_price(day, day_price_map, default_price),
                }
            )
    return profiles


def build_synthetic_profiles(real_pv_profiles, day_price_map, gen, load_replicas, seed_base, load_source="synthetic", real_load_profile=None):
    """
    Szintetikus PV adatokat tartalmazó profilokat építünk.
    
    Args:
        load_source: "synthetic" (generált) vagy "real" (UCI adatsor)
        real_load_profile: Ha load_source="real", akkor az órás fogyasztási profil numpy tömb
    """
    profiles = []
    default_price = gen.get_tou_prices().copy()
    for day in SELECTED_DAYS:
        if day not in real_pv_profiles:
            continue
        season = real_pv_profiles[day]["season"]
        for rep in range(load_replicas):
            rng = np.random.default_rng(seed_base + 10_000_000 + stable_seed_from_day_rep(day, rep))
            
            # Fogyasztás forrásának kiválasztása
            if load_source == "real" and real_load_profile is not None:
                # Valós adatokból vegyünk 24 órát
                start_idx = (rep * 24) % (len(real_load_profile) - 24)
                load = real_load_profile[start_idx:start_idx + 24].copy()
            else:
                # Szintetikus generálás
                load = gen.generate_load_profile(season=season, rng=rng)
            
            pv = gen.generate_pv_profile(season=season, rng=rng)
            dataset_name = f"synthetic_pv_load_{load_source}"
            profiles.append(
                {
                    "profile_id": f"{day}_rep{rep:02d}",
                    "dataset": dataset_name,
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
    lines.append("# Benchmark: 2x2 Kiserleti Matrix")
    lines.append("")
    lines.append(f"- Kivalasztott napok: {len(SELECTED_DAYS)}")
    lines.append(f"- Terheles replikak/nap: {LOAD_REPLICAS}")
    lines.append(f"- Futas/algoritmus/profil: {RUNS_PER_PROFILE}")
    lines.append("")

    # Dinamikusan lekérjük az összes forgatókönyv nevét (mind a 4-et)
    datasets = summary_df["dataset"].unique()

    for dataset in datasets:
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

    lines.append("## Konkluzio")
    lines.append("")
    
    # Kiírjuk minden eset nyertesét
    for dataset in datasets:
        best = summary_df[summary_df["dataset"] == dataset].sort_values("avg_gap_pct").iloc[0]
        lines.append(
            f"- **{dataset}** legjobbja: {best['algorithm']} "
            f"(atlag gap: {best['avg_gap_pct']:.2f}%, gyozelmi arany: {best.get('win_rate_pct', 0.0):.1f}%)"
        )

    n_rows = len(raw_df)
    lines.append("")
    lines.append(f"A kiertékeles osszesen {n_rows} egyedi algoritmusfutast tartalmaz.")

    return "\n".join(lines)


def prepare_output_dirs(base_dir):
    output_root = base_dir / "outputs"
    tables_dir = output_root / "tables"
    reports_dir = output_root / "reports"
    plots_days_dir = output_root / "plots" / "days"
    plots_summary_dir = output_root / "plots" / "summary"

    for p in [tables_dir, reports_dir, plots_days_dir, plots_summary_dir]:
        p.mkdir(parents=True, exist_ok=True)

    return {
        "output_root": output_root,
        "tables": tables_dir,
        "reports": reports_dir,
        "plots_days": plots_days_dir,
        "plots_summary": plots_summary_dir,
    }


def build_real_day_load_map(real_profiles):
    day_load_map = {}
    for p in real_profiles:
        day = p.get("day")
        if day not in day_load_map:
            day_load_map[day] = np.asarray(p["load"], dtype=float)
    return day_load_map


def _upsample_hourly(values, factor=4):
    base_x = np.arange(len(values), dtype=float)
    dense_x = np.linspace(0.0, len(values) - 1, len(values) * factor)
    dense_y = np.interp(dense_x, base_x, values)
    return dense_x, dense_y


def plot_daily_realpv_price(real_pv_map, day_price_map, day_load_map, out_dir):
    generated = 0
    for day, meta in real_pv_map.items():
        if day not in day_price_map or day not in day_load_map:
            continue

        hours = np.arange(24)
        pv = np.asarray(meta["pv"], dtype=float)
        load = np.asarray(day_load_map[day], dtype=float)
        price = np.asarray(day_price_map[day], dtype=float)
        if pv.shape != (24,) or load.shape != (24,) or price.shape != (24,):
            continue
        net = load - pv

        h_fine, pv_fine = _upsample_hourly(pv, factor=4)
        _, load_fine = _upsample_hourly(load, factor=4)
        _, net_fine = _upsample_hourly(net, factor=4)
        _, price_fine = _upsample_hourly(price, factor=4)

        fig, ax1 = plt.subplots(figsize=(10, 4.8))
        ax1.plot(h_fine, pv_fine, color="#1f77b4", linewidth=2.0, label="PV (kW)")
        ax1.plot(h_fine, load_fine, color="#2ca02c", linewidth=2.0, label="Load (kW)")
        ax1.plot(h_fine, net_fine, color="#9467bd", linewidth=1.8, linestyle="-.", label="Net (Load-PV) (kW)")
        ax1.scatter(hours, pv, color="#1f77b4", s=14, alpha=0.8)
        ax1.scatter(hours, load, color="#2ca02c", s=14, alpha=0.8)
        ax1.set_xlabel("Ora")
        ax1.set_ylabel("Teljesitmeny (kW)")
        ax1.set_xticks(np.arange(0, 24, 1))
        ax1.grid(True, alpha=0.25)

        ax2 = ax1.twinx()
        ax2.plot(h_fine, price_fine, color="#d62728", linewidth=2.0, linestyle="--", label="Ar (RON/kWh)")
        ax2.scatter(hours, price, color="#d62728", s=12, alpha=0.8)
        ax2.set_ylabel("Ar (RON/kWh)", color="#d62728")
        ax2.tick_params(axis="y", labelcolor="#d62728")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        plt.title(f"{day} - Valos PV, load, netto gorbe es villamosenergia-ar")
        plt.tight_layout()
        fig.savefig(out_dir / f"{day}_realpv_price.png", dpi=150)
        plt.close(fig)
        generated += 1

    return generated


def _plot_metric_bar(summary_df, dataset, metric_col, ylabel, title, out_path):
    sub = summary_df[summary_df["dataset"] == dataset].copy()
    if sub.empty:
        return False

    sub = sub.sort_values(metric_col, ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.barh(sub["algorithm"], sub[metric_col], color="#4e79a7")
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="x", alpha=0.2)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def _plot_cost_runs_scatter(raw_df, dataset, out_path):
    sub = raw_df[raw_df["dataset"] == dataset].copy()
    if sub.empty:
        return False

    algos = list(ALGORITHMS.keys())
    fig, ax = plt.subplots(figsize=(9.5, 5.0))

    rng = np.random.default_rng(42)
    for idx, algo in enumerate(algos):
        a = sub[sub["algorithm"] == algo]
        if a.empty:
            continue
        x = idx + rng.uniform(-0.15, 0.15, size=len(a))
        ax.scatter(x, a["cost"], s=20, alpha=0.45, label=algo)
        ax.scatter([idx], [a["cost"].mean()], s=80, marker="D", color="black", zorder=5)

    ax.set_xticks(range(len(algos)))
    ax.set_xticklabels(algos, rotation=15)
    ax.set_ylabel("Cost")
    ax.set_title(f"{dataset} - Run szintu cost pontfelho (fekete: atlag)")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def _plot_daily_best_cost_lines(raw_df, dataset, out_path):
    sub = raw_df[raw_df["dataset"] == dataset].copy()
    if sub.empty:
        return False

    best = (
        sub.groupby(["day", "algorithm"], as_index=False)["cost"]
        .min()
    )
    pivot = best.pivot(index="day", columns="algorithm", values="cost").sort_index()
    if pivot.empty:
        return False

    x = np.arange(len(pivot.index))
    fig, ax = plt.subplots(figsize=(10.2, 5.0))
    for algo in ALGORITHMS.keys():
        if algo not in pivot.columns:
            continue
        y = pivot[algo].to_numpy(dtype=float)
        ax.plot(x, y, marker="o", linewidth=1.8, markersize=4, label=algo)

    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.set_ylabel("Napi legjobb cost")
    ax.set_title(f"{dataset} - Napi legjobb cost algoritmusonkent")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def plot_summary_charts(summary_df, raw_df, out_dir):
    generated = 0
    # Itt is dinamikusan végigmegyünk a 4 forgatókönyvön
    datasets = summary_df["dataset"].unique()
    for dataset in datasets:
        ok1 = _plot_metric_bar(
            summary_df,
            dataset,
            "mean_cost",
            "Atlag koltseg",
            f"{dataset} - Atlag koltseg algoritmusonkent",
            out_dir / f"{dataset}_mean_cost.png",
        )
        ok2 = _plot_metric_bar(
            summary_df,
            dataset,
            "avg_gap_pct",
            "Atlag gap (%)",
            f"{dataset} - Atlag gap algoritmusonkent",
            out_dir / f"{dataset}_avg_gap_pct.png",
        )
        ok3 = _plot_metric_bar(
            summary_df,
            dataset,
            "mean_runtime_s",
            "Atlag futasi ido (s)",
            f"{dataset} - Atlag futasi ido algoritmusonkent",
            out_dir / f"{dataset}_mean_runtime_s.png",
        )
        ok4 = _plot_cost_runs_scatter(
            raw_df,
            dataset,
            out_dir / f"{dataset}_cost_scatter_runs.png",
        )
        ok5 = _plot_daily_best_cost_lines(
            raw_df,
            dataset,
            out_dir / f"{dataset}_daily_best_cost_lines.png",
        )
        generated += int(ok1) + int(ok2) + int(ok3) + int(ok4) + int(ok5)
    return generated


def main():
    repo_root = Path(__file__).resolve().parents[2]
    inverter_csv = repo_root / "Reports" / "Inverter" / "inverter_osszes.csv"
    price_dir = repo_root / "Reports" / "Price"
    project_dir = repo_root / "ekim2339_proj"
    dirs = prepare_output_dirs(project_dir)

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

    # ============================================================
    # 2x2 KÍSÉRLET MÁTRIX: PV × Load kombinációk
    # ============================================================
    # Valós fogyasztási profil betöltése az UCI adatsorból
    # Valós fogyasztási profil betöltése az UCI adatsorból (kisebb, előtisztított verzió)
    # Az előtisztított, kisebb verzió használata (13 MB helyett 47 MB)
    consumption_csv = Path(__file__).resolve().parents[2] / "consumtion" / "household_power_consumption_2.csv"
    
    real_load_profile = load_real_consumption(
        csv_path=str(consumption_csv),
        days=60  # 60 nap adat a variáció érdekében
    )
    
    all_profiles = []
    experiments = [
        ("real_pv", "synthetic"),   # 1. Valós PV + Szintetikus Load
        ("real_pv", "real"),        # 2. Valós PV + Valós Load
        ("synthetic", "synthetic"), # 3. Szintetikus PV + Szintetikus Load
        ("synthetic", "real"),      # 4. Szintetikus PV + Valós Load
    ]
    
    print(f"\n{'='*70}")
    print("2x2 BENCHMARK MÁTRIX: PV Termelés × Háztartási Fogyasztás")
    print(f"{'='*70}")
    
    for pv_type, load_type in experiments:
        print(f"\n→ Profil készítés: PV={pv_type}, Load={load_type}")
        
        if pv_type == "real_pv":
            profiles_batch = build_realpv_profiles(
                real_pv_map, day_price_map, gen, LOAD_REPLICAS, SEED_BASE,
                load_source=load_type,
                real_load_profile=real_load_profile if load_type == "real" else None
            )
        else:  # synthetic PV
            profiles_batch = build_synthetic_profiles(
                real_pv_map, day_price_map, gen, LOAD_REPLICAS, SEED_BASE,
                load_source=load_type,
                real_load_profile=real_load_profile if load_type == "real" else None
            )
        
        all_profiles.extend(profiles_batch)
        print(f"   ✓ {len(profiles_batch)} profil készítve")
    
    if day_price_map:
        missing_price_days = [d for d in SELECTED_DAYS if d not in day_price_map]
        if missing_price_days:
            print(f"\nFigyelem: ezekre a napokra TOU fallback ar lesz: {missing_price_days}")
    else:
        print("\nFigyelem: Minden profil TOU arat hasznal (valos ar map ures).")

    profiles = all_profiles
    print(f"\nÖsszes profil: {len(profiles)}")
    print(f"  - Kísérlet kombinációk: {len(experiments)}")
    print(f"  - Napok/kombináció: {len(SELECTED_DAYS)}")
    print(f"  - Terhelés replikák/nap: {LOAD_REPLICAS}")

    raw_df = evaluate_profiles(profiles, RUNS_PER_PROFILE, SEED_BASE)
    summary_df, gaps_df, winners_df = build_summary(raw_df)

    # Output fájlnevei a 2x2 mátrixhoz (új verzió)
    raw_path = dirs["tables"] / "results_2x2_benchmark_raw.csv"
    summary_path = dirs["tables"] / "results_2x2_benchmark_summary.csv"
    gaps_path = dirs["tables"] / "results_2x2_benchmark_gaps.csv"
    winners_path = dirs["tables"] / "results_2x2_benchmark_winners.csv"
    report_path = dirs["reports"] / "results_2x2_benchmark_report.md"
    json_path = dirs["tables"] / "results_2x2_benchmark_summary.json"

    raw_df.to_csv(raw_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    gaps_df.to_csv(gaps_path, index=False)
    winners_df.to_csv(winners_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary_df.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    report_text = to_markdown_report(summary_df, winners_df, raw_df)
    report_path.write_text(report_text, encoding="utf-8")

    day_load_map = build_real_day_load_map(profiles)
    daily_plot_count = plot_daily_realpv_price(real_pv_map, day_price_map, day_load_map, dirs["plots_days"])
    summary_plot_count = plot_summary_charts(summary_df, raw_df, dirs["plots_summary"])

    print(f"Mentve: {raw_path}")
    print(f"Mentve: {summary_path}")
    print(f"Mentve: {gaps_path}")
    print(f"Mentve: {winners_path}")
    print(f"Mentve: {json_path}")
    print(f"Mentve: {report_path}")
    print(f"Mentve napi PNG-k: {daily_plot_count} -> {dirs['plots_days']}")
    print(f"Mentve summary PNG-k: {summary_plot_count} -> {dirs['plots_summary']}")


if __name__ == "__main__":
    main()
