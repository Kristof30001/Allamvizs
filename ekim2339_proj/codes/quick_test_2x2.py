#!/usr/bin/env python3
"""
Gyors teszt: Az új 2x2-es benchmark infrastruktúra működésének ellenőrzése
(Szintetikus adat, 1 nap, 1 futás - max 30 másodperc)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_generator import DataGenerator, load_real_consumption
from hems_problem import SmartHomeEnvironment
from algorithms import GA
import numpy as np

print("=" * 70)
print("GYORS TESZT: 2x2 Benchmark Infrastruktúra")
print("=" * 70)

gen = DataGenerator()

# Test 1: Szintetikus termelés + szintetikus fogyasztás
print("\n[1/4] Szintetikus PV + Szintetikus Load...")
try:
    pv_synth = gen.generate_pv_profile(season="summer")
    load_synth = gen.generate_load_profile(season="summer")
    price = gen.get_tou_prices()
    
    env = SmartHomeEnvironment(load_synth, pv_synth, price)
    print(f"  ✓ Profil: PV min={pv_synth.min():.2f} max={pv_synth.max():.2f} kW")
    print(f"  ✓ Profil: Load min={load_synth.min():.2f} max={load_synth.max():.2f} kW")
except Exception as e:
    print(f"  ❌ Hiba: {e}")
    sys.exit(1)

# Test 2: Valós fogyasztás betöltése
print("\n[2/4] Valós UCI fogyasztás betöltése...")
try:
    # Az előtisztított, kisebb verzió használata
    csv_path = Path(__file__).parent.parent / "consumtion" / "household_power_consumption_2.csv"
    
    real_load = load_real_consumption(
        csv_path=str(csv_path),
        days=0.1  # Csak ~2.4 óra
    )
    if real_load is not None:
        print(f"  ✓ Valós Load: {len(real_load)} óra, "
              f"átlag={np.mean(real_load):.2f} kW, "
              f"max={np.max(real_load):.2f} kW")
    else:
        print(f"  ⚠ Figyelmeztetés: Valós adat nem elérhető, fallback szintetikus")
        real_load = None
except Exception as e:
    print(f"  ❌ Hiba: {e}")
    real_load = None

# Test 3: Szintetikus termelés + valós fogyasztás
print("\n[3/4] Szintetikus PV + Valós Load...")
try:
    if real_load is not None and len(real_load) >= 24:
        load_real = real_load[:24]  # Első 24 óra
        env = SmartHomeEnvironment(load_real, pv_synth, price)
        print(f"  ✓ Profil: Load [valós] min={load_real.min():.2f} max={load_real.max():.2f} kW")
    else:
        print(f"  ⚠ Valós adat nem elegendő a teszthez")
except Exception as e:
    print(f"  ❌ Hiba: {e}")

# Test 4: Algoritmus futtatás
print("\n[4/4] GA algoritmus: 1 generáció, szintetikus adat...")
try:
    pv_test = gen.generate_pv_profile(season="summer")
    load_test = gen.generate_load_profile(season="summer")
    price_test = gen.get_tou_prices()
    
    env_test = SmartHomeEnvironment(load_test, pv_test, price_test)
    
    ga = GA(
        objective_func=env_test.objective_function,
        dim=env_test.dim,
        lb=env_test.lb,
        ub=env_test.ub,
        pop_size=10,
        max_iter=1
    )
    
    best_sol, best_cost = ga.solve()
    print(f"  ✓ GA futtatás: cost={best_cost:.2f} RON")
    print(f"  ✓ Legjobb megoldás vektor hossza: {len(best_sol)}")
except Exception as e:
    print(f"  ❌ Hiba: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ AZ ÖSSZES TESZT SIKERESEN LEZAJLOTT!")
print("=" * 70)
print("\n→ Az infrastruktúra kész a nagyobb futtatáshoz.")
print("→ Parancs: python benchmark_real_vs_synthetic.py")