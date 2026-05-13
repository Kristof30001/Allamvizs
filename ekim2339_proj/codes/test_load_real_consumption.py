import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_generator import load_real_consumption
import numpy as np

# Teszteljük a valós fogyasztás betöltőjét
profile = load_real_consumption(
    csv_path=r'd:\UBB\Allamvizs\consumtion\household_power_consumption_2.csv',
    days=0.1  # Csak néhány óra a gyors teszthez
)

if profile is not None:
    print(f"✓ Valós fogyasztási profil sikeresen betöltve!")
    print(f"  Hossz: {len(profile)} óra")
    print(f"  Átlag: {np.mean(profile):.2f} kW")
    print(f"  Min: {np.min(profile):.2f} kW")
    print(f"  Max: {np.max(profile):.2f} kW")
    print(f"\n  Első 24 óra (kW):")
    print("  " + " ".join([f"{v:.2f}" for v in profile[:24]]))
else:
    print("❌ Hiba a betöltéskor!")