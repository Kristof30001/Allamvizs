# Benchmark: 2x2 Kiserleti Matrix

- Kivalasztott napok: 16
- Terheles replikak/nap: 1
- Futas/algoritmus/profil: 5

## real_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 12.57 | 7.51 | 1.17 | 7 | 43.8 | 0.994 |
| GA (P=50) | 12.69 | 7.58 | 1.50 | 2 | 12.5 | 0.497 |
| GWO | 12.78 | 7.20 | 1.89 | 7 | 43.8 | 0.629 |
| Hybrid | 13.85 | 7.31 | 10.93 | 0 | 0.0 | 0.415 |
| PSO | 14.91 | 7.33 | 13.05 | 0 | 0.0 | 0.370 |

## real_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 15.31 | 11.49 | 1.05 | 8 | 50.0 | 0.953 |
| GA (P=50) | 15.43 | 11.54 | 1.51 | 1 | 6.2 | 0.479 |
| GWO | 15.59 | 11.09 | 1.63 | 7 | 43.8 | 0.621 |
| Hybrid | 16.65 | 11.24 | 11.53 | 0 | 0.0 | 0.415 |
| PSO | 17.60 | 11.29 | 18.02 | 0 | 0.0 | 0.363 |

## synthetic_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 9.57 | 3.48 | 0.62 | 8 | 50.0 | 0.923 |
| GA (P=50) | 9.71 | 3.52 | 1.56 | 3 | 18.8 | 0.465 |
| GWO | 10.19 | 3.79 | 2.73 | 5 | 31.2 | 0.601 |
| Hybrid | 10.96 | 3.58 | 8.71 | 0 | 0.0 | 0.401 |
| PSO | 12.09 | 3.77 | 15.33 | 0 | 0.0 | 0.353 |

## synthetic_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 12.19 | 7.07 | 0.15 | 10 | 62.5 | 0.925 |
| GA (P=50) | 12.38 | 7.13 | 0.77 | 1 | 6.2 | 0.466 |
| GWO | 12.76 | 7.17 | 1.84 | 5 | 31.2 | 0.604 |
| Hybrid | 13.74 | 7.16 | 8.76 | 0 | 0.0 | 0.402 |
| PSO | 15.01 | 7.08 | 14.77 | 0 | 0.0 | 0.350 |

## Konkluzio

- **real_pv_load_real** legjobbja: GA (P=100) (atlag gap: 1.17%, gyozelmi arany: 43.8%)
- **real_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 1.05%, gyozelmi arany: 50.0%)
- **synthetic_pv_load_real** legjobbja: GA (P=100) (atlag gap: 0.62%, gyozelmi arany: 50.0%)
- **synthetic_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 0.15%, gyozelmi arany: 62.5%)

A kiertékeles osszesen 1600 egyedi algoritmusfutast tartalmaz.