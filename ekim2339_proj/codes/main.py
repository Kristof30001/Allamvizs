import numpy as np
import matplotlib.pyplot as plt
import time
import os
import json
import csv
from data_generator import DataGenerator
from hems_problem import SmartHomeEnvironment
from algorithms import GA, PSO, GWO, Hybrid

DEFAULT_SCENARIOS = ("winter", "summer", "cloudy")
DEFAULT_N_DAYS = 3
DEFAULT_RUNS = 20


def build_profiles(gen, season_name, base_seed, n_days, data_source="synthetic", csv_path=None):
    """A szcenárióhoz szükséges (load, pv, price) napi profilok előállítása."""
    if data_source == "synthetic":
        return gen.generate_multi_day_profiles(season=season_name, n_days=n_days, seed=base_seed)

    if data_source == "csv":
        if not csv_path:
            raise ValueError("CSV forrás esetén kötelező a csv_path megadása")

        profiles = gen.load_profiles_from_csv(csv_path)
        if n_days is not None and n_days > 0:
            profiles = profiles[:n_days]
        if not profiles:
            raise ValueError("A CSV-ből nem érkezett feldolgozható nap")
        return profiles

    raise ValueError(f"Ismeretlen data_source: {data_source}")


def run_scenario(season_name, base_seed=42, n_days=1, runs=20, data_source="synthetic", csv_path=None):
    print(f"\n{'='*65}")
    print(f"TESZTESET FUTTATÁSA: {season_name.upper()} SZENÁRIÓ")
    print(f"Forrás: {data_source} | Napok száma: {n_days} | Futások/algoritmus/nap: {runs}")
    print(f"{'='*65}")

    if n_days < 1:
        raise ValueError("n_days legalább 1 kell legyen")
    if runs < 1:
        raise ValueError("runs legalább 1 kell legyen")

    # --- 0. MENTÉSI HELY BEÁLLÍTÁSA ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.dirname(script_dir) 
    source_csv_path = csv_path

    # 1. ADATFORRÁS ÖSSZEÁLLÍTÁSA
    gen = DataGenerator()
    profiles = build_profiles(
        gen=gen,
        season_name=season_name,
        base_seed=base_seed,
        n_days=n_days,
        data_source=data_source,
        csv_path=source_csv_path,
    )

    used_days = len(profiles)
    preview_profile = profiles[0]
    load = preview_profile["load"]
    pv = preview_profile["pv"]
    price = preview_profile["price"]
    
    # --- ÁBRA 1: Mintanap Profil (első nap) ---
    plt.figure(figsize=(10,4))
    plt.plot(load, 'r-', label='Alap Fogyasztás (Load)')
    plt.plot(pv, 'g--', label='Napelem (PV)')
    plt.plot(price, 'b:', label='Ár (RON/kWh)')
    plt.title(f"Profil minta ({used_days} napból az első) - {season_name.upper()}")
    plt.xlabel("Óra")
    plt.ylabel("Érték (kW / RON)")
    plt.legend()
    plt.savefig(os.path.join(save_dir, f"generated_day_{season_name}.png"))
    plt.close()
    
    # Algoritmusok és paraméter-változatok
    # Kulcs: Megjelenítendő név
    # Érték: (Osztály, Populáció méret, Iterációk száma)
    algos = {
        "GA (P=50)":   (GA, 50, 150),
        "GA (P=100)":  (GA, 100, 150), # Változat paraméter-összehasonlításhoz
        "PSO":         (PSO, 50, 150),
        "GWO":         (GWO, 50, 150),
        "Hybrid":      (Hybrid, 50, 150)
    }
 
    results = {}
    times = {}
    curves = {}
    day_best = {}
    raw_rows = []

    for name in algos.keys():
        results[name] = []
        times[name] = []
        curves[name] = None
        day_best[name] = {}
    
    print(f"Algoritmusok futtatása ({used_days} nap x {runs} futás/nap)...")
    print(f"{'Algoritmus':<15} | {'Átlag Költség':<15} | {'Legjobb':<10} | {'Átlag Idő (s)':<15}")
    print("-" * 65)

    for day_idx, day_profile in enumerate(profiles):
        day_name = str(day_profile.get("day", f"day_{day_idx:03d}"))
        env = SmartHomeEnvironment(day_profile["load"], day_profile["pv"], day_profile["price"])

        for name, (AlgoClass, p_size, m_iter) in algos.items():
            min_cost_local = float('inf')
            best_run_curve = None

            for r in range(runs):
                # Reprodukálható, de variábilis seed nap+futás szinten
                np.random.seed(base_seed + day_idx * 1000 + r)
                start_time = time.time()
                solver = AlgoClass(
                    env.objective_function,
                    env.dim,
                    env.lb,
                    env.ub,
                    pop_size=p_size,
                    max_iter=m_iter,
                )
                _, cost = solver.solve()
                runtime = time.time() - start_time

                cost = float(cost)
                runtime = float(runtime)

                results[name].append(cost)
                times[name].append(runtime)

                raw_rows.append({
                    "season": season_name,
                    "data_source": data_source,
                    "day": day_name,
                    "day_idx": day_idx,
                    "algorithm": name,
                    "run": r,
                    "cost": cost,
                    "runtime_s": runtime,
                })

                if cost < min_cost_local:
                    min_cost_local = cost
                    best_run_curve = solver.history

            day_best[name][day_name] = float(min_cost_local)

            if curves[name] is None or min_cost_local < curves[name]["best_cost"]:
                curves[name] = {
                    "best_cost": float(min_cost_local),
                    "history": best_run_curve,
                }

    for name in algos.keys():
        avg_cost = np.mean(results[name])
        best_cost = np.min(results[name])
        avg_time = np.mean(times[name])
        print(f"{name:<15} | {avg_cost:<15.2f} | {best_cost:<10.2f} | {avg_time:<15.4f}")

    # --- 4. NYERS EREDMÉNYEK MENTÉSE (CSV + JSON) ---
    csv_out_path = os.path.join(save_dir, f"results_{season_name}.csv")
    with open(csv_out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["season", "data_source", "day", "day_idx", "algorithm", "run", "cost", "runtime_s"])
        for row in raw_rows:
            writer.writerow([
                row["season"],
                row["data_source"],
                row["day"],
                row["day_idx"],
                row["algorithm"],
                row["run"],
                row["cost"],
                row["runtime_s"],
            ])

    json_out_path = os.path.join(save_dir, f"results_{season_name}.json")
    json_payload = {
        "season": season_name,
        "data_source": data_source,
        "source_csv_path": source_csv_path,
        "days_requested": n_days,
        "days_used": used_days,
        "day_labels": [str(p.get("day", f"day_{i:03d}")) for i, p in enumerate(profiles)],
        "runs": runs,
        "seed_base": base_seed,
        "algorithms": {
            name: {
                "pop_size": p_size,
                "max_iter": m_iter,
                "costs": results[name],
                "runtimes": times[name],
                "best_cost_by_day": day_best[name],
            }
            for name, (AlgoClass, p_size, m_iter) in algos.items()
        }
    }
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    print(f"Mentve: {csv_out_path}")
    print(f"Mentve: {json_out_path}")

    # --- ÁBRA 2: Boxplot (Statisztikai eloszlás) ---
    plt.figure(figsize=(10,6))
    # Matplotlib verzió-biztos megoldás a címkékhez
    plt.boxplot(results.values(), tick_labels=list(results.keys()))
    plt.title(f"Költség eloszlás ({used_days} nap x {runs} futás) - {season_name.upper()}")
    plt.xlabel("Algoritmus")
    plt.ylabel("Költség (RON)")
    plt.xticks(rotation=15) # Döntött feliratok, hogy kiférjenek
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout() # Hogy ne lógjon le semmi
    plt.savefig(os.path.join(save_dir, f"results_boxplot_{season_name}.png"))
    plt.close()

    # --- ÁBRA 3: Konvergencia (Tanulási görbék) ---
    plt.figure(figsize=(10,6))
    for name, curve_info in curves.items():
        if curve_info and curve_info["history"]:
            plt.plot(curve_info["history"], label=name, linewidth=1.5)
    plt.title(f"Konvergencia (Legjobb futások) - {season_name.upper()}")
    plt.xlabel("Iteráció")
    plt.ylabel("Költség (Fitness)")
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.savefig(os.path.join(save_dir, f"results_convergence_{season_name}.png"))
    plt.close()


def run_simulation():
    # Alap benchmark: több napos szintetikus futtatás
    for idx, season in enumerate(DEFAULT_SCENARIOS):
        run_scenario(
            season_name=season,
            base_seed=42 + idx * 10000,
            n_days=DEFAULT_N_DAYS,
            runs=DEFAULT_RUNS,
            data_source="synthetic",
        )

    # Példa valós adat futtatásra (ha megvan a CSV):
    # run_scenario(
    #     season_name="real_csv",
    #     base_seed=777,
    #     n_days=30,
    #     runs=DEFAULT_RUNS,
    #     data_source="csv",
    #     csv_path=r"d:\UBB\OptiProj\ekim2339_proj\real_profiles.csv",
    # )

if __name__ == "__main__":
    run_simulation()
