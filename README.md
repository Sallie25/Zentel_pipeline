# Zentel Network Service — Ticket Performance Analysis

## Project Summary

This project analyzes customer support ticket performance for Zentel Network Services. Using Python and pandas, the pipeline ingests, cleans, and enriches ticket and lookup data, computes SLA metrics, identifies escalations, ranks managers and operators, and outputs reproducible weekly KPIs and summary reports.

The main goal is to provide actionable insights on how well Zentel’s customer service teams meet SLAs and where improvements can be made.

## Folder Structure

```
zentel_pipeline/
├── pipeline/               # ETL modules and optional visualization helpers
│   ├── __init__.py
│   ├── etl.py
│   ├── analysis.py
│   └── viz.py
├── data/                   # Input CSV files
├── reports/                # Generated CSV, JSON, and plots
├── tests/                  # pytest test files
├── main.py                 # Script to run the pipeline
├── README.md
├── .gitignore
└── pyproject.toml          # Poetry project config & dependencies
```

## Quick Start (Poetry)

1. Clone the repository:

```bash
git clone https://github.com/Sallie25/zentel_pipeline.git
cd zentel_pipeline
```

2. Install dependencies:

```bash
poetry install
```

3. Activate the environment:

```bash
poetry shell
```

4. Run the pipeline:

```bash
poetry run python main.py
```

5. Run tests:

```bash
poetry run pytest
```

## Outputs

* `reports/weekly_kpis.csv` — weekly aggregated KPIs
* `reports/manager_operator_report.json` — manager/operator metrics and rankings
* `reports/escalations.csv` — tickets violating resolution SLA
* Optional bar charts under `reports/` for visual analysis

## Key Assumptions & Decisions

* Missing `Operator` values are filled with `UNKNOWN`.
* All timestamps are parsed as timezone-naive `datetime` objects.
* SLA calculations follow the project brief: response ≤ 10s, resolution ≤ 3 hours.
* Week grouping uses ISO week numbering (week starts Monday).

## Testing

All small, deterministic functions are tested using pytest. Run tests with:

```bash
poetry run pytest
```

Tests cover:

* Cleaning and enrichment of ticket data
* SLA calculations and categorization
* Escalation detection
* Manager/operator ranking logic

