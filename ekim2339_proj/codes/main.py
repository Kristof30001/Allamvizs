import numpy as np
import matplotlib.pyplot as plt
import time
import os
import json
import csv
from data_generator import DataGenerator
from hems_problem import SmartHomeEnvironment
from algorithms import GA, PSO, GWO, Hybrid

def run_scenario(season_name, base_seed=42):
    print(f"\n{'='*65}")
    print(f"TESZTESET FUTTATÁSA: {season_name.upper()} SZENÁRIÓ")
    print(f"{'='*65}")

    # --- 0. MENTÉSI HELY BEÁLLÍTÁSA ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.dirname(script_dir) 

    # Globális seed a profilok reprodukálhatóságához
    np.random.seed(base_seed)

    # 1. ADATGENERÁLÁS
    gen = DataGenerator()
    load = gen.generate_load_profile(season=season_name)
    pv = gen.generate_pv_profile(season=season_name)
    price = gen.get_tou_prices()
    
    # --- ÁBRA 1: Napi Profil ---
    plt.figure(figsize=(10,4))
    plt.plot(load, 'r-', label='Alap Fogyasztás (Load)')
    plt.plot(pv, 'g--', label='Napelem (PV)')
    plt.plot(price, 'b:', label='Ár (RON/kWh)')
    plt.title(f"Generált nap - {season_name.upper()}")
    plt.xlabel("Óra")
    plt.ylabel("Érték (kW / RON)")
    plt.legend()
    plt.savefig(os.path.join(save_dir, f"generated_day_{season_name}.png"))
    plt.close()

    # Környezet inicializálása
    env = SmartHomeEnvironment(load, pv, price)
    
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
    
    runs = 20 # Megemelt futásszám a statisztikai szignifikanciáért
    results = {}
    times = {}
    curves = {} 
    
    print(f"Algoritmusok futtatása ({runs} futás/db)...")
    print(f"{'Algoritmus':<15} | {'Átlag Költség':<15} | {'Legjobb':<10} | {'Átlag Idő (s)':<15}")
    print("-" * 65)
    
    for name, (AlgoClass, p_size, m_iter) in algos.items():
        costs = []
        runtimes = []
        best_run_curve = None
        min_cost_local = float('inf')
        
        for r in range(runs):
            # Reprodukálható, de variábilis sorozat: determinisztikus seed futásonként
            np.random.seed(base_seed + r)
            start_time = time.time()
            # Példányosítás dinamikus paraméterekkel
            solver = AlgoClass(env.objective_function, env.dim, env.lb, env.ub, pop_size=p_size, max_iter=m_iter)
            sol, cost = solver.solve()
            end_time = time.time()
            
            costs.append(cost)
            runtimes.append(end_time - start_time)
            
            if cost < min_cost_local:
                min_cost_local = cost
                best_run_curve = solver.history
        
        results[name] = costs
        times[name] = runtimes
        curves[name] = best_run_curve
        
        avg_cost = np.mean(costs)
        best_cost = np.min(costs)
        avg_time = np.mean(runtimes)
        
        print(f"{name:<15} | {avg_cost:<15.2f} | {best_cost:<10.2f} | {avg_time:<15.4f}")

    # --- 4. NYERS EREDMÉNYEK MENTÉSE (CSV + JSON) ---
    csv_path = os.path.join(save_dir, f"results_{season_name}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["algorithm", "run", "cost", "runtime_s"])
        for name, cost_list in results.items():
            for run_idx, (cost_val, time_val) in enumerate(zip(cost_list, times[name])):
                writer.writerow([name, run_idx, cost_val, time_val])

    json_path = os.path.join(save_dir, f"results_{season_name}.json")
    json_payload = {
        "season": season_name,
        "runs": runs,
        "seed_base": base_seed,
        "algorithms": {
            name: {
                "pop_size": p_size,
                "max_iter": m_iter,
                "costs": results[name],
                "runtimes": times[name]
            }
            for name, (AlgoClass, p_size, m_iter) in algos.items()
        }
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    print(f"Mentve: {csv_path}")
    print(f"Mentve: {json_path}")

    # --- ÁBRA 2: Boxplot (Statisztikai eloszlás) ---
    plt.figure(figsize=(10,6))
    # Matplotlib verzió-biztos megoldás a címkékhez
    plt.boxplot(results.values(), tick_labels=list(results.keys()))
    plt.title(f"Költség eloszlás (20 futás) - {season_name.upper()}")
    plt.xlabel("Algoritmus")
    plt.ylabel("Költség (RON)")
    plt.xticks(rotation=15) # Döntött feliratok, hogy kiférjenek
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout() # Hogy ne lógjon le semmi
    plt.savefig(os.path.join(save_dir, f"results_boxplot_{season_name}.png"))
    plt.close()

    # --- ÁBRA 3: Konvergencia (Tanulási görbék) ---
    plt.figure(figsize=(10,6))
    for name, curve in curves.items():
        if curve:
            plt.plot(curve, label=name, linewidth=1.5)
    plt.title(f"Konvergencia (Legjobb futások) - {season_name.upper()}")
    plt.xlabel("Iteráció")
    plt.ylabel("Költség (Fitness)")
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.savefig(os.path.join(save_dir, f"results_convergence_{season_name}.png"))
    plt.close()

def run_simulation():
    run_scenario("winter")
    run_scenario("summer")
    run_scenario("cloudy") 

if __name__ == "__main__":
    run_simulation()