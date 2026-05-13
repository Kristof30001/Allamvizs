# HEMS Optimization Project (Allamvizs)

This repository contains a complete workflow for evaluating home energy management optimization algorithms on:

- synthetic daily profiles (load, PV, TOU price), and
- real PV production data (inverter logs) with real day-ahead prices (ENTSO-E CSV), when available.

It also includes thesis/report material (LaTeX sources and generated reports/figures).

## Main Goal

Compare multiple metaheuristic solvers for a 24-hour smart-home scheduling problem with:

- battery charge/discharge control,
- shiftable appliances (washing machine, dishwasher),
- time-varying electricity prices,
- PV self-consumption and export.

Evaluated algorithms:

- GA (P=50)
- GA (P=100)
- PSO
- GWO
- Hybrid (PSO + GA)

## Repository Structure

Key folders:

- `ekim2339_proj/` - Python code, benchmark scripts, generated results and plots
- `Reports/` - input data (inverter and energy price CSV files)
- `Dolgozattex/` - thesis/report LaTeX project
- `Sablon/` - thesis template files

Important code files:

- `ekim2339_proj/codes/main.py` - synthetic seasonal benchmark runner (winter/summer/cloudy)
- `ekim2339_proj/codes/benchmark_real_vs_synthetic.py` - real PV vs synthetic benchmark
- `ekim2339_proj/codes/algorithms.py` - GA, PSO, GWO, Hybrid implementations
- `ekim2339_proj/codes/hems_problem.py` - optimization environment and objective function
- `ekim2339_proj/codes/data_generator.py` - synthetic profile generator + CSV profile loader
- `ekim2339_proj/codes/price_loader.py` - ENTSO-E day-ahead price loading (RON/kWh)
- `ekim2339_proj/codes/inverter_feldolgoz.py` - FusionSolar XLSX preprocessing utility

## Optimization Model (Short)

Decision vector includes:

- 24 hourly battery power values (negative/positive for charge/discharge according to model convention), and
- start times for shiftable devices.

Objective minimizes daily cost:

- import cost from grid at hourly prices,
- reduced revenue factor for export,
- penalties for battery SoC constraint violations,
- end-of-day SoC consistency penalty.

Battery and device constraints are implemented in `hems_problem.py`.

## Setup

Python 3.10+ recommended.

Install dependencies:

```bash
pip install numpy pandas matplotlib
```

## Data Inputs

Expected input locations used by benchmark scripts:

- Inverter data: `Reports/Inverter/inverter_osszes.csv`
- Price data directory: `Reports/Price/`

`benchmark_real_vs_synthetic.py` auto-selects the largest matching price file:

- `GUI_ENERGY_PRICES_*.csv`

If no valid real price data is found, scripts fall back to built-in TOU prices.

## How To Run

From repository root:

### 1) Seasonal synthetic benchmark

```bash
python ekim2339_proj/codes/main.py
```

Generates (in `ekim2339_proj/`):

- per-scenario CSV/JSON results (`results_winter.*`, `results_summer.*`, `results_cloudy.*`)
- profile plots (`generated_day_*.png`)
- cost distribution boxplots (`results_boxplot_*.png`)
- convergence curves (`results_convergence_*.png`)

### 2) Real-PV vs synthetic benchmark

```bash
python ekim2339_proj/codes/benchmark_real_vs_synthetic.py
```

Generates (mostly in `ekim2339_proj/outputs/`):

- tables: raw runs, summary, gaps, winners
- report: markdown summary
- daily real-PV+price figures
- summary comparison plots (mean cost, gap, runtime, scatter, daily best)

## Current Benchmark Snapshot

Based on existing repository outputs (`results_realpv_vs_synth_report.md`):

- Real PV dataset winner: **GA (P=100)**
  - average gap: ~0.96%
  - win rate: 62.5%
- Synthetic dataset winner: **GA (P=100)**
  - average gap: ~0.91%
  - win rate: 75.0%

This indicates consistent best performance of GA (P=100) across both datasets in the current evaluation configuration.

## Outputs Guide

Detailed explanation of output artifacts:

- `ekim2339_proj/outputs/README.md`

Primary output paths:

- `ekim2339_proj/outputs/tables/`
- `ekim2339_proj/outputs/reports/`
- `ekim2339_proj/outputs/plots/days/`
- `ekim2339_proj/outputs/plots/summary/`

## Notes

- Random seeds are controlled in scripts for reproducibility.
- Benchmark scripts define selected days, run counts, and algorithm parameters at file level constants.
- For custom experiments, modify:
  - `SELECTED_DAYS`, `RUNS_PER_PROFILE`, `LOAD_REPLICAS` in `benchmark_real_vs_synthetic.py`
  - `DEFAULT_SCENARIOS`, `DEFAULT_N_DAYS`, `DEFAULT_RUNS` in `main.py`

## Thesis/Report Material

LaTeX thesis project:

- main file: `Dolgozattex/tex/hems_proj.tex`

Template resources are in:

- `Sablon/`
