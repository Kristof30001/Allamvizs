import numpy as np

class AlgorithmBase:
    def __init__(self, objective_func, dim, lb, ub, pop_size=50, max_iter=100):
        self.func = objective_func
        self.dim = dim
        self.lb = lb
        self.ub = ub
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.history = []

# --- 1. Genetikus Algoritmus (GA) - MÓDOSÍTVA ---
class GA(AlgorithmBase):
    def solve(self, initial_pop=None): # <--- ÚJ PARAMÉTER: fogadja a kezdő populációt
        
        # DÖNTÉS: Ha kaptunk kezdő populációt (a PSO-tól), azt használjuk.
        # Ha nem (sima GA futás), akkor generálunk véletleneket.
        if initial_pop is not None:
            pop = initial_pop.copy()
        else:
            pop = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dim))
            
        fitness = np.array([self.func(ind) for ind in pop])
        
        best_idx = np.argmin(fitness)
        best_sol = pop[best_idx].copy()
        best_fit = fitness[best_idx]
        self.history = [best_fit]

        for _ in range(self.max_iter):
            # Elitizmus: a legjobb 2 egyed automatikusan túléli
            indices = np.argsort(fitness)
            elites = pop[indices[:2]].copy()
            
            # Tournament selection
            new_pop = []
            for _ in range(self.pop_size - 2): # -2 az elitek miatt
                ids = np.random.randint(0, self.pop_size, 3)
                sub_fits = fitness[ids]
                winner = pop[ids[np.argmin(sub_fits)]]
                new_pop.append(winner)
            
            # Crossover
            parents = np.array(new_pop)
            offspring = np.zeros_like(parents)
            
            for i in range(0, len(parents), 2):
                if i+1 < len(parents):
                    child1 = 0.5 * parents[i] + 0.5 * parents[i+1]
                    child2 = 0.7 * parents[i] + 0.3 * parents[i+1]
                    offspring[i] = child1
                    offspring[i+1] = child2
                else:
                    offspring[i] = parents[i]

            # Mutation
            mutation_mask = np.random.rand(*offspring.shape) < 0.1
            mutation = np.random.normal(0, 1.0, offspring.shape)
            offspring += mutation * mutation_mask
            
            # Reinsert elites
            pop = np.vstack((elites, np.clip(offspring, self.lb, self.ub)))
            fitness = np.array([self.func(ind) for ind in pop])

            current_best = np.min(fitness)
            if current_best < best_fit:
                best_fit = current_best
                best_sol = pop[np.argmin(fitness)].copy()
            self.history.append(best_fit)
            
        return best_sol, best_fit

# --- 2. PSO (unchanged) ---
class PSO(AlgorithmBase):
    def solve(self):
        w, c1, c2 = 0.6, 1.8, 1.8 
        X = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dim))
        V = np.zeros_like(X)
        P_best = X.copy()
        P_best_fit = np.array([self.func(x) for x in X])
        
        g_best = P_best[np.argmin(P_best_fit)].copy()
        g_best_fit = np.min(P_best_fit)
        self.history = [g_best_fit]

        for _ in range(self.max_iter):
            r1, r2 = np.random.rand(self.pop_size, self.dim), np.random.rand(self.pop_size, self.dim)
            V = w * V + c1 * r1 * (P_best - X) + c2 * r2 * (g_best - X)
            X = np.clip(X + V, self.lb, self.ub)
            
            fits = np.array([self.func(x) for x in X])
            better = fits < P_best_fit
            P_best[better] = X[better]
            P_best_fit[better] = fits[better]
            
            current_min = np.min(fits)
            if current_min < g_best_fit:
                g_best_fit = current_min
                g_best = X[np.argmin(fits)].copy()
            self.history.append(g_best_fit)
            
        return g_best, g_best_fit

# --- 3. GWO (unchanged) ---
class GWO(AlgorithmBase):
    def solve(self):
        wolves = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dim))
        fits = np.array([self.func(w) for w in wolves])
        
        # Initial sorting
        idx = np.argsort(fits)
        alpha, beta, delta = wolves[idx[:3]].copy()
        
        # Elitizmus
        best_sol = alpha.copy()
        best_fit = fits[idx[0]]
        self.history = [best_fit]

        for t in range(self.max_iter):
            a = 2 - t * (2 / self.max_iter) 
            
            for i in range(self.pop_size):
                r1, r2 = np.random.rand(self.dim), np.random.rand(self.dim)
                A1, C1 = 2 * a * r1 - a, 2 * r2
                D_alpha = np.abs(C1 * alpha - wolves[i])
                X1 = alpha - A1 * D_alpha
                
                r1, r2 = np.random.rand(self.dim), np.random.rand(self.dim)
                A2, C2 = 2 * a * r1 - a, 2 * r2
                D_beta = np.abs(C2 * beta - wolves[i])
                X2 = beta - A2 * D_beta
                
                r1, r2 = np.random.rand(self.dim), np.random.rand(self.dim)
                A3, C3 = 2 * a * r1 - a, 2 * r2
                D_delta = np.abs(C3 * delta - wolves[i])
                X3 = delta - A3 * D_delta
                
                wolves[i] = np.clip((X1 + X2 + X3) / 3, self.lb, self.ub)
            
            fits = np.array([self.func(w) for w in wolves])
            
            current_pool = np.vstack((wolves, alpha, beta, delta))
            current_fits = np.hstack((fits, self.func(alpha), self.func(beta), self.func(delta)))
            
            idx = np.argsort(current_fits)
            alpha, beta, delta = current_pool[idx[:3]].copy()
            
            current_best = current_fits[idx[0]]
            if current_best < best_fit:
                best_fit = current_best
                best_sol = alpha.copy()
            self.history.append(best_fit)
            
        return best_sol, best_fit

# --- 4. Hybrid - JAVÍTVA ---
class Hybrid(AlgorithmBase):
    def solve(self):
        # 1. fázis: PSO (Felfedezés)
        pso_steps = int(self.max_iter * 0.6) 
        pso = PSO(self.func, self.dim, self.lb, self.ub, self.pop_size, pso_steps)
        gb, gb_fit = pso.solve()
        
        # 2. fázis: GA (Finomhangolás)
        ga = GA(self.func, self.dim, self.lb, self.ub, self.pop_size, self.max_iter - pso_steps)
        
        # Populáció "átoltása" (Seed Injection)
        # Létrehozunk egy új populációt, ami alapvetően véletlenszerű...
        pop_start = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dim))
        
        # ...DE az első helyre betesszük a PSO abszolút legjobbját...
        pop_start[0] = gb 
        
        # ...és a populáció felét lecseréljük a legjobb megoldás "mutációira" (környezetére).
        # Ez biztosítja, hogy a GA a jó helyről induljon, de legyen elég variációja a fejlődéshez.
        for i in range(1, int(self.pop_size/2)):
            pop_start[i] = gb + np.random.normal(0, 0.5, self.dim) 
        
        sol_ga, fit_ga = ga.solve(initial_pop=pop_start)
        
        final_sol = sol_ga if fit_ga < gb_fit else gb
        final_fit = min(fit_ga, gb_fit)
        
        self.history = pso.history + ga.history
        return final_sol, final_fit