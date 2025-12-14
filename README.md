## TravelSafe: A Global Data-Driven Travel Safety Assessment System

Final Project — DSCI 510: Principles of Programming for Data Science

### 1) Project Summary

TravelSafe is a Python-based data science project designed to evaluate international travel safety using publicly available web-based information sources. The project collects raw data from REST Countries, Wikipedia homicide tables, the Global Peace Index (GPI) report, and a curated subset of U.S. State Department travel advisories. After retrieving the data, the project performs structured cleaning and standardization, merges datasets into a unified schema, and produces global safety comparisons.

This repository supports two ways to reproduce results:

- Option A (recommended): run a consolidated script (`run_full_analysis.py`) that outputs the final dataset and summary.
- Option B: run the original modular pipeline under `src/`.

### 2) Team Members

- Sylvan Wang (Zichen Wang) — ID: 6176724527 — zichenw@usc.edu
- Ningjun Li — ID: 5528989772 — ningjunl@usc.edu

### 3) Repository Structure

The repository contains scripts, data, results, and a small website prototype.

TravelSafe/
│
├── README.md
├── requirements.txt
│
├── data/
│ ├── raw/
│ └── processed/
│
├── src/
│ ├── get_data.py
│ ├── clean_data.py
│ ├── run_analysis.py
│ └── visualize_results.py
│
├── results/
│ ├── TravelSafe_Analysis.ipynb
│ ├── analysis_summary.json
│ └── visualizations/
│
└── website/
├── index.html
├── tn.css
└── tn.js

Note: this branch also includes a consolidated runner (`run_full_analysis.py`) and its outputs in the repo root.

### 4) Environment Setup

Create and activate a virtual environment:

MacOS / Linux

python3 -m venv venv
source venv/bin/activate

Windows (PowerShell)

python -m venv venv
venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Python 3+ is required.

### 5) Reproducing the Full Pipeline

#### Option A (recommended): one-command runner

python run_full_analysis.py

Expected outputs (repo root):

- TravelSafe_Final_Analysis.csv
- analysis_summary.json

#### Option B: modular pipeline (original structure)

Step 1 — Data collection

python src/get_data.py

Step 2 — Cleaning and standardization

python src/clean_data.py

Step 3 — Statistical analysis

python src/run_analysis.py

Step 4 — Visualization output

python src/visualize_results.py

### 6) Completion Benchmark

After running the pipeline, you should have a cleaned dataset, a summary JSON, and exported visualizations. The notebook (`TravelSafe_Analysis.ipynb`) provides exploratory analysis and validation.

### Appendix: Project Proposal (High-Level)

#### Problem Statement

International travelers—especially students—often rely on fragmented or biased information when evaluating destination safety. Existing government advisories vary widely, and single metrics such as homicide rate fail to capture public-health readiness or perceived political stability. This project constructs a multi-dimensional **TravelSafe Index (TSI)** integrating violence, public safety stability, and official advisories.

#### Data Sources

- REST Countries API (identifiers, regions, demographics)
- Wikipedia homicide tables (`pandas.read_html()`)
- Global Peace Index (GPI) 2025 (official PDF)
- U.S. travel advisories (curated subset)

#### Methods

Indicators are normalized onto a 0–100 safety scale (higher = safer) and combined into a composite **TSI**. We apply k-means clustering to derive data-driven risk tiers and compare them with advisory categories.
