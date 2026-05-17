# Benchmark: 2x2 Kiserleti Matrix

- Kivalasztott napok: 16
- Terheles replikak/nap: 1
- Futas/algoritmus/profil: 2

## real_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 10.80 | 7.65 | 1.97 | 8 | 50.0 | 0.217 |
| GA (P=50) | 11.13 | 7.67 | 5.24 | 5 | 31.2 | 0.111 |
| GWO | 11.64 | 7.56 | 17.29 | 3 | 18.8 | 0.156 |
| Hybrid | 13.17 | 7.59 | 44.28 | 0 | 0.0 | 0.086 |
| PSO | 13.92 | 7.08 | 72.32 | 0 | 0.0 | 0.071 |

## real_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 13.61 | 11.59 | 0.96 | 10 | 62.5 | 0.232 |
| GA (P=50) | 13.90 | 11.43 | 32.08 | 3 | 18.8 | 0.117 |
| GWO | 14.23 | 11.12 | 60.65 | 3 | 18.8 | 0.166 |
| Hybrid | 15.43 | 11.52 | 82.20 | 0 | 0.0 | 0.095 |
| PSO | 16.70 | 10.88 | 159.08 | 0 | 0.0 | 0.075 |

## synthetic_pv_load_real

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 7.76 | 3.43 | 2.73 | 10 | 62.5 | 0.207 |
| GA (P=50) | 7.96 | 3.66 | 3.72 | 5 | 31.2 | 0.105 |
| GWO | 8.77 | 3.92 | 13.15 | 1 | 6.2 | 0.149 |
| Hybrid | 9.79 | 3.92 | 23.30 | 0 | 0.0 | 0.085 |
| PSO | 11.14 | 4.44 | 45.33 | 0 | 0.0 | 0.068 |

## synthetic_pv_load_synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 10.50 | 7.21 | 1.56 | 10 | 62.5 | 0.207 |
| GA (P=50) | 10.86 | 7.18 | 4.69 | 4 | 25.0 | 0.105 |
| GWO | 11.37 | 7.12 | 10.14 | 2 | 12.5 | 0.149 |
| Hybrid | 13.04 | 7.36 | 27.45 | 0 | 0.0 | 0.085 |
| PSO | 14.02 | 7.05 | 41.00 | 0 | 0.0 | 0.069 |

## Konkluzio

- **real_pv_load_real** legjobbja: GA (P=100) (atlag gap: 1.97%, gyozelmi arany: 50.0%)
- **real_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 0.96%, gyozelmi arany: 62.5%)
- **synthetic_pv_load_real** legjobbja: GA (P=100) (atlag gap: 2.73%, gyozelmi arany: 62.5%)
- **synthetic_pv_load_synthetic** legjobbja: GA (P=100) (atlag gap: 1.56%, gyozelmi arany: 62.5%)

A kiertékeles osszesen 640 egyedi algoritmusfutast tartalmaz.