import numpy as np

class SmartHomeEnvironment:
    def __init__(self, load_profile, pv_profile, price_profile):
        self.load = load_profile
        self.pv = pv_profile
        self.price = price_profile
        
        # --- 1. Akkumulátor paraméterek ---
        self.batt_cap = 10.0 
        self.min_soc = 0.2
        self.max_soc = 0.9
        self.init_soc = 0.5
        self.max_rate = 3.0 # Max 3 kW töltés/kisütés
        
        # --- 2. Eltolható fogyasztók (Shiftable Loads) ---
        # Lista: (Név, Teljesítmény [kW], Időtartam [óra])
        self.shiftable_devices = [
            ("Mosógép", 1.8, 2),      # 1.8 kW, 2 órás program
            ("Mosogatógép", 1.5, 2)   # 1.5 kW, 2 órás program
        ]
        
        # Dimenziók meghatározása
        # Az első 24 dimenzió: Akkumulátor vezérlés (óra 0..23)
        # A következő N dimenzió: Eszközök indítási ideje (Start Time)
        self.n_batt = 24
        self.n_shift = len(self.shiftable_devices)
        self.dim = self.n_batt + self.n_shift
        
        # --- 3. Keresési tér határai (Bounds) ---
        self.lb = np.zeros(self.dim)
        self.ub = np.zeros(self.dim)
        
        # Akkumulátor határok: [-3, 3] kW
        self.lb[:self.n_batt] = -self.max_rate
        self.ub[:self.n_batt] = self.max_rate
        
        # Eszköz időzítés határok: [0, 24 - duration]
        # Pl. ha 2 órás a program, legkésőbb 22:00-kor indulhat (index 22), hogy éjfélre (24) végezzen.
        for i, (name, power, duration) in enumerate(self.shiftable_devices):
            idx = self.n_batt + i
            self.lb[idx] = 0.0
            self.ub[idx] = 24.0 - duration - 0.01 # Kis biztonsági sáv a kerekítéshez

    def objective_function(self, x):
        """
        x: [p_batt_0, ..., p_batt_23, start_dev_1, start_dev_2]
        """
        cost = 0
        penalty = 0
        
        # --- A. Shiftable Load profil felépítése ---
        # Létrehozunk egy terhelési vektort, amit hozzáadunk az alapfogyasztáshoz
        shiftable_load_profile = np.zeros(24)
        
        for i, (name, power, duration) in enumerate(self.shiftable_devices):
            # A folytonos változót egész órára kerekítjük
            idx = self.n_batt + i
            start_hour = int(round(x[idx]))
            
            # Határok betartása (extra védelem a kerekítés után)
            max_start = 24 - duration
            if start_hour < 0: start_hour = 0
            if start_hour > max_start: start_hour = max_start
            
            # Fogyasztás hozzáadása a megfelelő órákhoz
            for h in range(start_hour, start_hour + duration):
                if h < 24:
                    shiftable_load_profile[h] += power

        # --- B. Szimuláció (Akku + Hálózat) ---
        current_soc = self.init_soc * self.batt_cap
        
        for t in range(24):
            p_batt = x[t] # Akku teljesítmény
            
            # SOC frissítés
            next_soc = current_soc + p_batt
            soc_perc = next_soc / self.batt_cap
            
            # Büntetések (SOC határok)
            if soc_perc < self.min_soc:
                penalty += 5000 * (self.min_soc - soc_perc) ** 2
                next_soc = self.min_soc * self.batt_cap
            elif soc_perc > self.max_soc:
                penalty += 5000 * (soc_perc - self.max_soc) ** 2
                next_soc = self.max_soc * self.batt_cap
            
            current_soc = next_soc
            
            # Teljes fogyasztás = Alap Load + Eltolt Eszközök
            total_load_at_t = self.load[t] + shiftable_load_profile[t]
            
            # Energiamérleg: P_grid = Load - PV + Battery
            grid_power = total_load_at_t - self.pv[t] + p_batt
            
            # Költségszámítás
            if grid_power > 0: # Vétel
                cost += grid_power * self.price[t]
            else: # Eladás (csökkentett áron)
                cost += grid_power * (self.price[t] * 0.3)
        
        # --- C. Fenntarthatóság ---
        # A nap végén az akku töltöttsége legyen közel a kezdetihez
        final_soc_perc = current_soc / self.batt_cap
        if abs(final_soc_perc - self.init_soc) > 0.1:
            penalty += 2000 * abs(final_soc_perc - self.init_soc)

        return cost + penalty
