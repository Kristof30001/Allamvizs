# Benchmark: 2x2 Kiserleti Matrix

- Kivalasztott napok: 16
- Terheles replikak/nap: 1
- Futas/algoritmus/profil: 5

## real_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 13.07 | 7.64 | 1.08 | 10 | 62.5 | 0.293 |
| GA (P=50) | 13.35 | 7.63 | 1.96 | 2 | 12.5 | 0.147 |
| GWO | 13.48 | 7.24 | 5.40 | 4 | 25.0 | 0.195 |
| Hybrid | 15.85 | 7.65 | 24.07 | 0 | 0.0 | 0.129 |
| PSO | 17.61 | 7.54 | 38.14 | 0 | 0.0 | 0.110 |

## real_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 15.74 | 11.59 | 1.03 | 8 | 50.0 | 0.281 |
| GA (P=50) | 16.12 | 11.59 | 3.75 | 2 | 12.5 | 0.143 |
| GWO | 16.07 | 11.20 | 4.06 | 6 | 37.5 | 0.198 |
| Hybrid | 18.54 | 11.36 | 27.29 | 0 | 0.0 | 0.127 |
| PSO | 20.24 | 11.22 | 44.00 | 0 | 0.0 | 0.109 |

## synthetic_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 10.07 | 3.63 | 0.45 | 13 | 81.2 | 0.310 |
| GA (P=50) | 10.33 | 3.71 | 2.02 | 2 | 12.5 | 0.154 |
| GWO | 10.89 | 3.94 | 5.07 | 1 | 6.2 | 0.205 |
| Hybrid | 12.98 | 4.04 | 21.78 | 0 | 0.0 | 0.134 |
| PSO | 14.75 | 4.45 | 35.73 | 0 | 0.0 | 0.115 |

## synthetic_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 12.67 | 7.20 | 0.32 | 12 | 75.0 | 0.294 |
| GA (P=50) | 13.01 | 7.24 | 2.01 | 3 | 18.8 | 0.147 |
| GWO | 13.34 | 7.28 | 3.29 | 1 | 6.2 | 0.195 |
| Hybrid | 15.58 | 7.52 | 17.20 | 0 | 0.0 | 0.129 |
| PSO | 17.71 | 7.19 | 34.74 | 0 | 0.0 | 0.110 |

## Konkluzio

- **real_pv_load_real** legjobbja: GA (P=100) (atlag gap: 1.08%, gyozelmi arany: 62.5%)
- **real_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 1.03%, gyozelmi arany: 50.0%)
- **synthetic_pv_load_real** legjobbja: GA (P=100) (atlag gap: 0.45%, gyozelmi arany: 81.2%)
- **synthetic_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 0.32%, gyozelmi arany: 75.0%)

A kiertékeles osszesen 1600 egyedi algoritmusfutast tartalmaz.