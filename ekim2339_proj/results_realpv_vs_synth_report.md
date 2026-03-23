# Benchmark: valos PV vs szintetikus

- Kivalasztott napok: 16
- Terheles replikak/nap: 1
- Futas/algoritmus/profil: 2

## real_pv

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 26.82 | 21.32 | 3.77 | 6 | 37.5 | 0.202 |
| GA (P=50) | 27.16 | 20.78 | 12.38 | 1 | 6.2 | 0.102 |
| GWO | 25.65 | 19.49 | 16.20 | 9 | 56.2 | 0.150 |
| Hybrid | 28.30 | 20.07 | 31.21 | 0 | 0.0 | 0.085 |
| PSO | 30.03 | 19.86 | 53.31 | 0 | 0.0 | 0.068 |

## synthetic

| Algoritmus | Atlag koltseg | Szoras | Atlag gap % | Gyozelmek | Gyozelmi arany % | Atlag ido (s) |
|---|---:|---:|---:|---:|---:|---:|
| GA (P=100) | 16.79 | 12.12 | 3.34 | 10 | 62.5 | 0.209 |
| GA (P=50) | 17.33 | 11.91 | 8.14 | 4 | 25.0 | 0.106 |
| GWO | 17.99 | 11.45 | 15.56 | 2 | 12.5 | 0.154 |
| Hybrid | 20.20 | 12.04 | 31.55 | 0 | 0.0 | 0.084 |
| PSO | 21.08 | 11.46 | 42.84 | 0 | 0.0 | 0.068 |

## Konkluzio

A valos PV adatokon a legstabilabb algoritmus: GA (P=100) (atlag gap: 3.77%, gyozelmi arany: 37.5%).
A teljesen szintetikus adatokon a legstabilabb algoritmus: GA (P=100) (atlag gap: 3.34%, gyozelmi arany: 62.5%).
A ket adathalmazon ugyanaz a nyertes, ami jo generalizaciot jelez.
A kiertékeles osszesen 320 egyedi algoritmusfutast tartalmaz.