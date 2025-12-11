# Final Project Proposal — TravelSafe: A Multi-Dimensional Risk Index for International Travel

**Team Members**
*   Sylvan Wang (USC ID: 6176724527, zichenw@usc.edu)
*   Ningjun Li (USC ID: 5528989772, ningjunl@usc.edu)

## Problem Statement
International travelers—especially students—often rely on fragmented or biased information when evaluating destination safety. Existing government advisories vary widely, and single metrics such as homicide rate fail to capture public-health readiness or perceived political stability. To provide a more balanced view, this project aims to construct a multi-dimensional **TravelSafe Index (TSI)** integrating violence, emergency-health capacity, and official advisories. The results will support both our course analysis and a future lightweight safety layer for a travel-planning assistant.

## Data Sources and Collection
We combine three publicly accessible datasets:
1.  **REST Countries API** provides standardized country identifiers, regions, and demographic context.
2.  **Wikipedia tables** supply the most recent intentional homicide rates using `pandas.read_html()`, ensuring consistent extraction without custom scraping.
3.  **Global Peace Index (GPI) 2025** (Institute for Economics & Peace) provides a country-level peacefulness score; we extract the overall score from the official 2025 report PDF (`Global-Peace-Index-2025-web.pdf`).
4.  **U.S. Department of State travel advisory levels (1–4)** will be manually recorded for key travel-relevant countries to ensure reliability.

Together these cover 150+ countries with at least two safety dimensions and ~70–80 countries with all three.

## Data Cleaning
**REST Countries** serves as the canonical table for joining datasets. We standardize ISO3 codes, resolve naming inconsistencies (e.g., “South Korea” vs. “Republic of Korea”), convert homicide and advisory values into numeric form, and retain the latest available year for each indicator (2019–2022). Missing or unreliable entries are flagged rather than imputed, and sensitivity checks will be conducted on analyses requiring complete cases.

## Analysis Plan
We first summarize regional patterns in homicide, GPI scores, and advisory levels. Each indicator is normalized onto a 0–100 safety scale (reversing homicide, advisory levels, and inverting the GPI score so that higher means safer) and combined into a composite **TravelSafe Index** using equal or lightly adjusted weights. We test specific hypotheses—e.g., whether higher-income regions exhibit higher TSI, or whether advisory levels align with data-driven safety estimates. Finally, we apply **k-means clustering** to group countries into 3–5 data-driven risk tiers and compare them with official advisory categories to identify over- or under-rated destinations.

## Visualization
We will produce concise bar charts, scatterplots, and a simple interactive map or **Plotly dashboard** allowing users to explore homicide, GPI, advisory level, and TSI side-by-side. This satisfies the course’s interactive requirement and forms a reusable prototype for traveler-facing safety insights.

## Limitations
Homicide rates exclude petty crime that travelers experience more frequently, GPI is a broad country-level peacefulness measure (not a precise trip-risk predictor), and U.S. advisories reflect diplomatic considerations. All analyses will be framed as high-level comparative signals rather than precise risk predictions.
