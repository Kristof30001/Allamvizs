# Outputs mappa összefoglaló

Ez a fájl leírja, hogy az `ekim2339_proj/outputs` alatt melyik mappában milyen típusú kimenet található, és az egyes ábrák/fájlok mit jelentenek.

## Mappastruktúra

- `tables/` – táblázatos nyers és aggregált benchmark eredmények (CSV/JSON)
- `reports/` – szöveges összefoglaló riport
- `plots/days/` – napi (day-level) vizualizációk
- `plots/summary/` – összesített (dataset/algoritmus szintű) vizualizációk

---

## `tables/` tartalma és jelentése

### `results_realpv_vs_synth_raw.csv`

- Minden egyes futás soronként.
- Tartalmazza: dataset, profil, nap, algoritmus, run index, cost, runtime.
- Erre épül minden további összegzés.

### `results_realpv_vs_synth_summary.csv`

- Algoritmusonként és datasetenként aggregált mutatók.
- Fő oszlopok: `mean_cost`, `std_cost`, `best_cost`, `mean_runtime_s`, `avg_gap_pct`, `wins`, `win_rate_pct`.

### `results_realpv_vs_synth_summary.json`

- Ugyanaz az aggregált tartalom, mint a summary CSV-ben, JSON formátumban.
- Könnyebb gépi feldolgozáshoz / API-szerű használathoz.

### `results_realpv_vs_synth_gaps.csv`

- Profil-szintű gap számítások.
- Megmutatja, hogy adott algoritmus mennyivel maradt el a profilon mért globális legjobb költségtől.

### `results_realpv_vs_synth_winners.csv`

- Profilonként a nyertes algoritmus.
- Gyors összehasonlításra, hogy melyik algoritmus hányszor nyert.

---

## `reports/` tartalma és jelentése

### `results_realpv_vs_synth_report.md`

- Emberileg olvasható benchmark riport.
- Tartalmazza a fő táblákat (real_pv vs synthetic), rövid konklúzióval.

---

## `plots/days/` tartalma és jelentése

Fájlnév minta:

- `YYYY-MM-DD_realpv_price.png`
- Példa: `2025-06-12_realpv_price.png`

Egy napi ábra jelentése:

- **PV (kW)** görbe: valós inverterből származó órás PV teljesítmény.
- **Load (kW)** görbe: a profilhoz generált fogyasztás.
- **Net (Load-PV) (kW)**: nettó terhelés (pozitív: hálózati import igény, negatív: többlet PV).
- **Ár (RON/kWh)**: a nap órás valós (ENTSO-E alapú) energiaára.
- Az ábrán markerpontok is láthatók (órás minták), a görbe pedig sűrítve jelenik meg jobb olvashatóságért.

---

## `plots/summary/` tartalma és jelentése

A fájlok datasetenként (`real_pv`, `synthetic`) készülnek.

### `real_pv_mean_cost.png` / `synthetic_mean_cost.png`

- Algoritmusonkénti átlagos költség.
- Minél alacsonyabb, annál jobb.

### `real_pv_avg_gap_pct.png` / `synthetic_avg_gap_pct.png`

- Algoritmusonkénti átlagos eltérés (%) a profilonkénti legjobbtól.
- Minél alacsonyabb, annál stabilabb/versenyképesebb.

### `real_pv_mean_runtime_s.png` / `synthetic_mean_runtime_s.png`

- Algoritmusonkénti átlag futási idő másodpercben.
- Minél alacsonyabb, annál gyorsabb.

### `real_pv_cost_scatter_runs.png` / `synthetic_cost_scatter_runs.png`

- Futás-szintű pontfelhő (run-by-run cost eloszlás).
- A fekete jelölő az adott algoritmus átlagos cost értéke.
- Jól mutatja a szórást és a robusztusságot.

### `real_pv_daily_best_cost_lines.png` / `synthetic_daily_best_cost_lines.png`

- Naponkénti legjobb cost érték algoritmusonként vonaldiagramon.
- Segít látni, mely napokon melyik algoritmus teljesít jobban/rosszabbul.

---

## Gyors értelmezési sorrend (ajánlott)

1. `tables/results_realpv_vs_synth_summary.csv` – fő mutatók áttekintése.
2. `plots/summary/*mean_cost*.png` és `*avg_gap_pct*.png` – gyors rangsorolás.
3. `plots/summary/*cost_scatter_runs*.png` – stabilitás/szórás ellenőrzése.
4. `plots/days/*.png` – napi mintázatok és ár-PV-load kapcsolat kvalitatív vizsgálata.
