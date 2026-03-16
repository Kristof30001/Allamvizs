import numpy as np

class DataGenerator:
    """
    Valósághű fogyasztási és termelési profilok generálása.
    Támogatja a TÉLI (kevés PV, nagy fogyasztás) és NYÁRI (sok PV) módokat.
    """
    def __init__(self, hours=24):
        self.hours = hours
        self.time_steps = np.arange(hours)

    def generate_pv_profile(self, season="summer"):
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
            peak_power = np.random.uniform(3.0, 5.5)
            variation = 0.2

        base_curve = np.exp(-((self.time_steps - mu) ** 2) / (2 * sigma ** 2))
        noise = np.random.normal(0, variation, self.hours)
        pv_profile = peak_power * base_curve + noise
        return np.clip(pv_profile, 0, None)

    def generate_load_profile(self, season="summer"):
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
        
        noise = np.random.normal(0, 0.1, self.hours)
        total_load = base_load + morning_curve + evening_curve + noise
        return np.clip(total_load, 0.1, None)

    def get_tou_prices(self):
        """ RON árazás: 0.70 (völgy) és 1.50 (csúcs) """
        prices = np.array([0.70]*7 + [1.50]*15 + [0.70]*2)
        return prices