import csv
from pathlib import Path

import numpy as np

class DataGenerator:
    """
    Valósághű fogyasztási és termelési profilok generálása.
    Támogatja a TÉLI (kevés PV, nagy fogyasztás) és NYÁRI (sok PV) módokat.
    """
    def __init__(self, hours=24):
        self.hours = hours
        self.time_steps = np.arange(hours)

    def generate_pv_profile(self, season="summer", rng=None):
        """
        Napelem profil generálása.
        season: 'summer' (erős nap), 'winter' (gyenge nap), 'random' (átlagos)
        """
        mu = 12
        sigma = 2.5
        
        # Szezonális beállítások
        if season == "summer":
            peak_power = 6.0  # Nyáron erős
            variation = 0.1   # Tiszta égbolt
        elif season == "winter":
            peak_power = 2.5  # Télen gyenge
            variation = 0.3   # Felhősebb
        elif season == "cloudy":
            peak_power = 4.5  # Egész jó erősség...
            variation = 0.8   # ...DE BRUTÁLIS ZAJ (felhők jönnek-mennek)
        else: # random
            if rng is None:
                peak_power = np.random.uniform(3.0, 5.5)
            else:
                peak_power = rng.uniform(3.0, 5.5)
            variation = 0.2

        base_curve = np.exp(-((self.time_steps - mu) ** 2) / (2 * sigma ** 2))
        if rng is None:
            noise = np.random.normal(0, variation, self.hours)
        else:
            noise = rng.normal(0, variation, self.hours)
        pv_profile = peak_power * base_curve + noise
        return np.clip(pv_profile, 0, None)

    def generate_load_profile(self, season="summer", rng=None):
        """
        Fogyasztás generálása.
        Télen nagyobb a fűtés miatt, nyáron kisebb (vagy klíma miatt nappali csúcs).
        """
        # Reggeli és Esti csúcsok helye
        morning_peak_pos = 8
        evening_peak_pos = 19
        
        if season == "winter":
            base_load = 0.8       # Magasabb alapfogyasztás
            peak_multiplier = 1.5 # Nagyobb esti csúcs (világítás, fűtés)
        elif season == "summer":
            base_load = 0.4
            peak_multiplier = 1.0
        else:
            base_load = 0.5
            peak_multiplier = 1.2

        morning_curve = 1.5 * np.exp(-((self.time_steps - morning_peak_pos) ** 2) / (2 * 1.5 ** 2))
        evening_curve = 2.5 * peak_multiplier * np.exp(-((self.time_steps - evening_peak_pos) ** 2) / (2 * 2.0 ** 2))
        
        if rng is None:
            noise = np.random.normal(0, 0.1, self.hours)
        else:
            noise = rng.normal(0, 0.1, self.hours)
        total_load = base_load + morning_curve + evening_curve + noise
        return np.clip(total_load, 0.1, None)

    def get_tou_prices(self):
        """ RON árazás: 0.70 (völgy) és 1.50 (csúcs) """
        prices = np.array([0.70]*7 + [1.50]*15 + [0.70]*2)
        return prices

    def generate_day_profile(self, season="summer", rng=None):
        """Egyetlen nap profilját adja vissza load/pv/price mezőkkel."""
        return {
            "day": "synthetic",
            "load": self.generate_load_profile(season=season, rng=rng),
            "pv": self.generate_pv_profile(season=season, rng=rng),
            "price": self.get_tou_prices().copy(),
        }

    def generate_multi_day_profiles(self, season="summer", n_days=1, seed=None):
        """
        Több nap szintetikus profilgenerálása.
        Minden nap külön zajt kap, de seed esetén reprodukálható.
        """
        if n_days < 1:
            raise ValueError("n_days legalább 1 kell legyen")

        rng = np.random.default_rng(seed) if seed is not None else None
        profiles = []
        for day_idx in range(n_days):
            day_profile = self.generate_day_profile(season=season, rng=rng)
            day_profile["day"] = f"day_{day_idx:03d}"
            profiles.append(day_profile)
        return profiles

    def _validate_profile(self, values, name):
        arr = np.asarray(values, dtype=float)
        if arr.shape != (self.hours,):
            raise ValueError(f"{name} profil hossza {self.hours} kell legyen, kapott: {arr.shape}")
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} profil nem véges értéket tartalmaz")
        return arr

    def load_profiles_from_csv(
        self,
        csv_path,
        day_col="day",
        hour_col="hour",
        load_col="load",
        pv_col="pv",
        price_col="price",
        delimiter=",",
    ):
        """
        Többnapos profil betöltése CSV-ből long-form formátumban.

        Elvárt oszlopok:
        - kötelező: hour, load, pv
        - opcionális: day, price

        Ha nincs price oszlop, vagy egyes órákban hiányzik, a TOU tarifa kerül behelyettesítésre.
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV fájl nem található: {csv_path}")

        grouped = {}

        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames:
                raise ValueError("Üres vagy hibás CSV fejléc")

            required = {hour_col, load_col, pv_col}
            missing = [c for c in required if c not in reader.fieldnames]
            if missing:
                raise ValueError(f"Hiányzó kötelező oszlop(ok): {missing}")

            has_day = day_col in reader.fieldnames
            has_price = price_col in reader.fieldnames

            for line_no, row in enumerate(reader, start=2):
                day_key = row.get(day_col, "day_000") if has_day else "day_000"

                try:
                    hour = int(float(row[hour_col]))
                except (TypeError, ValueError):
                    raise ValueError(f"Hibás óra érték a {line_no}. sorban: {row.get(hour_col)}")

                if hour < 0 or hour >= self.hours:
                    raise ValueError(f"Óra tartományon kívül a {line_no}. sorban: {hour}")

                try:
                    load_val = float(row[load_col])
                    pv_val = float(row[pv_col])
                except (TypeError, ValueError):
                    raise ValueError(f"Hibás load/pv érték a {line_no}. sorban")

                price_val = None
                if has_price:
                    raw_price = row.get(price_col, "")
                    if raw_price is not None and str(raw_price).strip() != "":
                        try:
                            price_val = float(raw_price)
                        except (TypeError, ValueError):
                            raise ValueError(f"Hibás price érték a {line_no}. sorban")

                day_bucket = grouped.setdefault(
                    day_key,
                    {
                        "load": [None] * self.hours,
                        "pv": [None] * self.hours,
                        "price": [None] * self.hours,
                    },
                )

                if day_bucket["load"][hour] is not None:
                    raise ValueError(f"Duplikált (day, hour) sor: day={day_key}, hour={hour}")

                day_bucket["load"][hour] = load_val
                day_bucket["pv"][hour] = pv_val
                day_bucket["price"][hour] = price_val

        if not grouped:
            raise ValueError("A CSV nem tartalmaz adat sort")

        default_price = self.get_tou_prices()
        profiles = []

        for day_key, day_data in grouped.items():
            if any(v is None for v in day_data["load"]):
                raise ValueError(f"Hiányzó load óra a(z) {day_key} napnál")
            if any(v is None for v in day_data["pv"]):
                raise ValueError(f"Hiányzó pv óra a(z) {day_key} napnál")

            price_values = [
                default_price[h] if v is None else v
                for h, v in enumerate(day_data["price"])
            ]

            load = self._validate_profile(day_data["load"], "load")
            pv = self._validate_profile(day_data["pv"], "pv")
            price = self._validate_profile(price_values, "price")

            profiles.append(
                {
                    "day": str(day_key),
                    "load": np.clip(load, 0.0, None),
                    "pv": np.clip(pv, 0.0, None),
                    "price": np.clip(price, 0.0, None),
                }
            )

        return profiles


def load_real_consumption(csv_path="household_power_consumption.csv", days=1):
    """
    Beolvassa az UCI valós okosotthon fogyasztási adatokat (1 perces felbontás),
    és átalakítja órás felbontású (kW) profillá a HEMS szimuláció számára.
    
    Args:
        csv_path: A household_power_consumption.csv fájl elérési útja
        days: Hány nap adatát szeretnénk betölteni (24 óra = 1 nap)
    
    Returns:
        np.ndarray: Órás fogyasztási profil (kW), max 24 elem
    
    Megjegyzés:
        A perces adatokat resample-vel átlagoljuk órás felbontásra,
        hogy passzoljon az 1 órás ár- és PV-adatokhoz.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("A real_consumption betöltéshez szükséges a pandas: pip install pandas")
    
    try:
        print(f"Valós fogyasztási adatok beolvasása ({csv_path})...")
        
        # 1. Beolvasás (csak a szükséges oszlopok)
        df = pd.read_csv(csv_path, usecols=['Date', 'Time', 'Global_active_power'], 
                        low_memory=False, na_values='?')
        
        # 2. Numerikus konverzió
        df['Global_active_power'] = pd.to_numeric(df['Global_active_power'], errors='coerce')
        
        # 3. Dátum és idő egyesítése
        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], 
                                       dayfirst=True, format='mixed', errors='coerce')
        df = df.dropna(subset=['Datetime'])
        df.set_index('Datetime', inplace=True)
        
        # 4. Órás felbontás készítése átlagolással
        df_hourly = df[['Global_active_power']].resample('h').mean()
        
        # 5. Hiányzó órák kitöltése (forward fill, majd backward fill)
        df_hourly.ffill(inplace=True)
        df_hourly.bfill(inplace=True)
        
        # 6. Szükséges óraszám meghatározása
        hours_needed = int(days * 24)
        
        # 7. Adatok kiválasztása (egy jó téli kezdődátumtól, kb 2007 február)
        try:
            profile = df_hourly.loc['2007-02-01':]['Global_active_power'].values[:hours_needed]
        except:
            # Ha az első megoldás nem működik, az első elérhető dátumtól indulunk
            profile = df_hourly['Global_active_power'].values[:hours_needed]
        
        # 8. Kitöltés vagy csonkítás, hogy pontosan 24*days órára jussunk
        if len(profile) < hours_needed:
            # Ha kevesebb adat van, kitöltjük az átlag értékkel
            mean_val = np.nanmean(profile) if len(profile) > 0 else 0.5
            profile = np.concatenate([profile, np.full(hours_needed - len(profile), mean_val)])
        else:
            # Ha több van, csonkítunk
            profile = profile[:hours_needed]
        
        # 9. Biztonsági konverziók: negatív értékek -> 0, NaN -> 0
        profile = np.nan_to_num(profile, nan=0.0)
        profile = np.clip(profile, 0.0, None)
        
        print(f"✓ Valós fogyasztási profil betöltve ({len(profile)} óra, "
              f"átlag: {np.mean(profile):.2f} kW)")
        
        return profile
        
    except FileNotFoundError:
        print(f"❌ HIBA: {csv_path} nem található!")
        print("   Helyettesítés: szintetikus profil használata fallback-ként.")
        return None
    except Exception as e:
        print(f"❌ HIBA a valós fogyasztási adat betöltésénél: {e}")
        print("   Helyettesítés: szintetikus profil használata fallback-ként.")
        return None
