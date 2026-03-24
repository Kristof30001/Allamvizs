# Benchmark: valos PV vs szintetikus

- Kivalasztott napok: 16
- Terheles replikak/nap: 1
- Futas/algoritmus/profil: 2

## real_pv

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 13.61 | 11.59 | 0.96 | 10 | 62.5 | 0.156 |
| GA (P=50) | 13.90 | 11.43 | 32.08 | 3 | 18.8 | 0.079 |
| GWO | 14.23 | 11.12 | 60.65 | 3 | 18.8 | 0.119 |
| Hybrid | 15.43 | 11.52 | 82.20 | 0 | 0.0 | 0.066 |
| PSO | 16.70 | 10.88 | 159.08 | 0 | 0.0 | 0.055 |

## synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 10.47 | 7.11 | 0.91 | 12 | 75.0 | 0.159 |
| GA (P=50) | 10.84 | 7.13 | 4.25 | 3 | 18.8 | 0.080 |
| GWO | 11.62 | 7.51 | 10.80 | 1 | 6.2 | 0.120 |
| Hybrid | 12.98 | 7.00 | 28.15 | 0 | 0.0 | 0.067 |
| PSO | 13.52 | 7.15 | 33.21 | 0 | 0.0 | 0.056 |

## Konkluzio

A valos PV adatokon a legstabilabb algoritmus: GA (P=100) (atlag gap: 0.96%, gyozelmi arany: 62.5%).
A teljesen szintetikus adatokon a legstabilabb algoritmus: GA (P=100) (atlag gap: 0.91%, gyozelmi arany: 75.0%).
A ket adathalmazon ugyanaz a nyertes, ami jo generalizaciot jelez.
A kiertékeles osszesen 320 egyedi algoritmusfutast tartalmaz.