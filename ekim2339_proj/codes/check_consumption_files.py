import os
import pandas as pd

csv_dir = r"d:\UBB\Allamvizs\consumtion"

for fname in os.listdir(csv_dir):
    if fname.endswith('.csv') or fname.endswith('.txt'):
        fpath = os.path.join(csv_dir, fname)
        print(f"\n{'='*60}")
        print(f"FILE: {fname}")
        print(f"{'='*60}")
        try:
            df = pd.read_csv(fpath, nrows=3)
            print(f"Oszlopok: {list(df.columns)}")
            print(f"Méret: {os.path.getsize(fpath) / (1024*1024):.1f} MB")
            print("\nElső 3 sor:")
            print(df.to_string())
        except Exception as e:
            print(f"HIBA: {e}")