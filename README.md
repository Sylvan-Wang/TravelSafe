TravelSafe: A Global Data-Driven Travel Safety Assessment System
Final Project — DSCI 510: Principles of Programming for Data Science
1. Project Summary

TravelSafe is a Python-based data science project designed to evaluate international travel safety using publicly available web-based information sources. The project collects raw data from REST Countries, Wikipedia homicide tables, and the U.S. State Department Travel Advisory service. After retrieving the data, the project performs structured cleaning and standardization, merges datasets into a unified schema, and generates analytical insights to produce global safety comparisons. Visualizations are then exported as PNG figures to illustrate safety differences across regions and country risk categories.

All components of the work follow the project requirements for data acquisition, preprocessing, statistical analysis, and visualization, and the pipeline can be fully reproduced by running the scripts provided in the /src directory.

2. Team Members
Sylvan Wang (Zichen Wang) ID:6176724527 Email:zichenw@usc.edu
Ningjun Li ID:5528989772 Email:ningjunl@usc.edu

3. Repository Structure

The GitHub repository is organized into separated modules for data, processing scripts, results, and reproducibility artifacts. A complete structure overview is shown below:

TravelSafe/
│
├── README.md                     
├── requirements.txt             
├── project_proposal.pdf
│
├── data/
│   ├── raw/                    
│   └── processed/               
│
├── src/
│   ├── get_data.py              
│   ├── clean_data.py             
│   ├── run_analysis.py           
│   └──  visualize_results.py                      
│
├── results/
│   ├── final_report.pdf         
│   ├── TravelSafe_Analysis.ipynb 
│   └── visualizations/          
│
└── website/ (optional extension)
    ├── index.html
    ├── tn.css
    └── tn.js

4. Environment Setup and Installation

The project is intended to run in an isolated Python virtual environment.
Below are the full instructions to create and activate one.

Create Virtual Environment

MacOS / Linux

python3 -m venv venv
source venv/bin/activate


Windows (PowerShell)

python -m venv venv
venv\Scripts\activate


Once the environment is active, install all required libraries:

pip install -r requirements.txt


The project requires Python 3 or higher.

5. Reproducing the Full Data Pipeline

The execution flow moves sequentially through data collection, cleaning, analysis, and visualization.
Each script prints progress logs to the console and writes output files into the appropriate directories.

Step 1 — Data Collection

This script retrieves raw country metrics and advisory risk levels from their online sources.

python src/get_data.py


After execution, raw results will appear inside:

data/raw/

Step 2 — Cleaning and Standardization

This script merges datasets, resolves missing values, formats homicide rate numeric fields, and exports the processed dataset.

python src/clean_data.py


The processed data files are written to:

data/processed/country_safety.json
data/processed/country_safety.csv

Step 3 — Statistical Analysis

Running the analysis generates summary metrics, rankings, and correlation insights.

python src/run_analysis.py


Expected output location:

results/analysis_summary.json

Step 4 — Visualization Output

This component produces all final visual analytics, including risk histograms, category distributions, regional comparisons, and extreme-value country sets.

python src/visualize_results.py


PNG visualizations are automatically saved to:

results/visualizations/

6. Completion Benchmark

Once all scripts have been executed successfully, your repository should contain both raw and cleaned data, a statistical summary, and a complete gallery of analysis figures. The notebook TravelSafe_Analysis.ipynb additionally provides an exploratory breakdown and supports result validation.
