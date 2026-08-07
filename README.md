# 🚀 RetailFlow: Enterprise Data Engineering Platform

![Python](https://img.shields.io/badge/Python-3.9-blue?logo=python)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-PySpark-orange?logo=apachespark)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-Orchestration-017CEE?logo=apacheairflow)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions)
![License](https://img.shields.io/badge/License-MIT-green)

## 🔗 Live Interactive Dashboard

**https://chidex-coder.github.io/Retail-Data-Engineering-Pipeline/**

---

# 📖 Project Overview

RetailFlow is a production-inspired **Enterprise Data Engineering Platform** that simulates the analytics infrastructure of a Fortune 500 retail company.

The platform generates millions of messy synthetic retail transactions, processes them using **PySpark**, transforms them into a **Medallion Data Lakehouse Architecture (Bronze → Silver → Gold)**, models the data into a **Star Schema**, orchestrates the pipeline using **Apache Airflow**, validates data quality with **Pytest**, and delivers executive business insights through an interactive **Plotly Dashboard**.

This project demonstrates many of the technologies and engineering practices used by modern Data Engineers in production environments.

---

# 🏗️ Solution Architecture

```text
                  +----------------+
                  | Synthetic Data |
                  | Generator       |
                  +--------+-------+
                           |
                           v
                 Bronze Data Lake
                  Raw CSV /Parquet
                           |
                           v
               PySpark Cleaning Jobs
     Schema Drift • Nulls • Dedup • Validation
                           |
                           v
                 Silver Data Lake
               Standardized Parquet
                           |
                           v
              Star Schema Transformation
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
  DimCustomer        DimProduct         DimDate
        \                 |                 /
         \                |                /
          +---------------+---------------+
                          |
                          v
                    FactSales Table
                          |
                          v
                  Gold Analytics Layer
                          |
            +-------------+-------------+
            |                           |
            v                           v
      Plotly Dashboard           Pytest Validation
            |                           |
            +-------------+-------------+
                          |
                          v
                 Apache Airflow DAG
                          |
                          v
                    GitHub Actions CI
```

---

# ⚙️ Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Data Processing | Apache Spark (PySpark) |
| Workflow Orchestration | Apache Airflow |
| Storage | CSV, Parquet |
| Data Architecture | Medallion Data Lakehouse |
| Data Warehouse | Star Schema |
| Containerization | Docker & Docker Compose |
| CI/CD | GitHub Actions |
| Testing | Pytest |
| Dashboard | Plotly.js, embedded in a self-contained HTML page |
| Version Control | Git & GitHub |

---

# ✨ Features

- Generate **1.2–5 million** synthetic retail transactions
- Simulate real-world dirty data
- Handle schema drift automatically
- Clean and standardize data with PySpark
- Bronze → Silver → Gold Medallion Architecture
- Star Schema Data Warehouse
- Executive dashboard with browser-side cross-filtering across 8 dimensions
- Self-contained, offline-capable HTML report (light and dark themes)
- Automated Apache Airflow Pipeline
- Dockerized Deployment
- Automated Data Quality Testing
- GitHub Actions CI/CD Pipeline

---

# 📂 Project Structure

```text
Retail-Data-Engineering-Pipeline/
│
├── generator/                    # Faker-based synthetic data generator
│   ├── run.py                    # entry point (--scale controls volume)
│   ├── config.yaml               # output paths and formats
│   ├── customers.py · products.py · orders.py
│   └── dirty_data.py             # injects the realistic quality issues
│
├── spark/
│   ├── bronze_to_silver.py       # cleaning and standardisation
│   ├── silver_to_gold.py         # star schema build
│   ├── gold_analytics.py         # Gold → dashboard payload
│   └── dashboard_builder.py      # HTML assembly and column encoding
│
├── dashboards/
│   ├── executive_dashboard.html  # generated report
│   └── assets/
│       ├── app.css               # design tokens, cards, filter bar
│       └── app.js                # client-side aggregation and charts
│
├── docs/
│   └── index.html                # GitHub Pages copy of the dashboard
│
├── data/
│   ├── raw/                      # Bronze
│   ├── silver/
│   └── gold/                     # fact_sales + dim_customer/product/date
│
├── airflow/dags/
│   └── retail_pipeline_dag.py
│
├── tests/
│   └── test_gold_data.py
│
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

# 🛠️ Data Generation

The synthetic data generator uses **Faker** to create between **1.2 and 5 million** retail transactions with configurable volumes.

It intentionally introduces realistic data quality issues including:

- Missing values
- Duplicate records
- Mixed date formats
- Invalid currencies
- Negative prices
- HTML tags
- Emoji characters
- Schema drift
- Incorrect data types
- Random formatting inconsistencies

This closely mimics production datasets encountered by enterprise Data Engineers.

---

# 🥉 Bronze Layer

Stores raw transactional data exactly as received.

**Format**

- CSV
- Parquet

No transformations are performed at this stage.

---

# 🥈 Silver Layer

PySpark cleans and standardizes the data by performing:

- Schema validation
- Data type conversion
- Null handling
- Deduplication
- Currency normalization
- Date standardization
- Invalid record filtering

Outputs are written as **partitioned Parquet files** for efficient analytical queries.

---

# 🥇 Gold Layer

The Gold Layer builds an analytical Star Schema consisting of:

- FactSales
- DimCustomer
- DimProduct
- DimDate

Business metrics surfaced from this layer:

- Revenue, cost and gross profit per order line
- Average order value and average profit margin
- Order counts by fulfilment status and payment method
- Revenue by brand, category, city and customer demographic
- Monthly revenue, profit, quantity and order-volume trends

---

# ⚡ Spark Optimizations

The ETL pipeline uses several Spark optimization techniques:

- Broadcast Joins
- Repartitioning
- Predicate Pushdown
- Partitioned Parquet Storage
- Lazy Evaluation
- Column Pruning

These techniques improve scalability and execution performance.

---

# 📊 Executive Dashboard

The Gold layer feeds a single **self-contained HTML report** — no server, no build step, no external requests. Open the file and it works offline.

**[View the live dashboard →](https://chidex-coder.github.io/Retail-Data-Engineering-Pipeline/)**

### What's on it

**8 KPI cards** — Revenue, Gross Profit, Orders, Customers, Products Sold, Avg Order Value, Avg Profit Margin, Cities Served.

**9 visuals**, in three rows:

| Row | Visuals |
|-----|---------|
| 1 | Revenue Trend · Top Products by Brand · Revenue by Category |
| 2 | Revenue by City · Revenue by Gender · Payment Methods |
| 3 | Order Status · Top Customers · Monthly Orders |

### Interactivity

Every filter re-aggregates the **entire fact table in the browser**. The Gold rows are dictionary-encoded into base64 typed arrays and embedded in the page, so one filter change recomputes all eight KPIs and all nine charts in roughly **70 ms** — no server round trip, no pre-baked trace toggling.

- **Filters** — Year, Month, Category, Brand, Payment Method, Gender, Order Status, plus a type-ahead City search
- **Metric switch** — Revenue / Profit / Quantity, repainting every value-based chart and rewriting its title
- **Themes** — light and dark, each a separately chosen palette rather than an inverted one
- **Export** — the current selection downloads as CSV; Plotly's PNG export is kept, its logo and lasso/box-select tools removed

### Design decisions

- **Bars, not pies.** Length is easier to compare than angle, so payment methods and order status are horizontal bars rather than donuts.
- **Colour encodes the measure**, not decoration — Revenue green, Profit blue, Quantity orange, order counts purple. Every colour was checked for contrast against its surface and for colour-vision separation.
- **Order Status uses a reserved status palette** (Delivered green through Cancelled red) with values always labelled, so colour never carries meaning on its own.
- **No legends.** Each chart shows one series at a time and the metric switch says which.
- **Real date axes.** Trend charts plot actual dates, so `Jan 2024` reads as a month instead of the integer `202401`.
- **Left joins, not filters.** An order line with an unresolved brand or payment method still counts toward revenue and only drops out of that one breakdown — dropping those rows outright would silently delete a fifth of the revenue. The unresolved counts are printed in the dashboard footer.

### Data standardisation

`spark/gold_analytics.py` normalises dimension attributes before they reach a chart: HTML fragments (`<b>Sony</b>`) and emoji (`IKEA📱💻`) are stripped, and placeholder values (`NULL`, `Unknown`, `-`, `N/A`) become genuine nulls instead of showing up as categories.

### Generating it

```bash
python spark/gold_analytics.py
```

Writes `dashboards/executive_dashboard.html` and `docs/index.html` (the GitHub Pages copy). The Airflow DAG runs this as its `run_analytics` task.

---

# 🔄 Apache Airflow

The entire ETL pipeline is fully automated using Apache Airflow.

Pipeline:

```
Generate Data
      ↓
Bronze → Silver
      ↓
Silver → Gold
      ↓
Generate Dashboard
      ↓
Run Pytest
```

Airflow provides:

- Scheduling
- Monitoring
- Retry Logic
- Pipeline Dependency Management

---

# ✅ Data Quality

Automated testing is implemented using **Pytest**.

Current validation includes:

- Null checks
- Positive revenue validation
- Primary key uniqueness
- Referential integrity
- Duplicate detection

The pipeline automatically fails if validation tests do not pass.

---

# 🚀 CI/CD

GitHub Actions automatically executes on every push.

Pipeline steps include:

- Install dependencies
- Validate project
- Execute PySpark jobs
- Run Pytest suite
- Publish build status

---

# 💻 Running Locally

## Clone Repository

```bash
git clone https://github.com/chidex-coder/Retail-Data-Engineering-Pipeline.git
```

## Enter Project

```bash
cd Retail-Data-Engineering-Pipeline
```

## Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Pipeline Directly

Runs the whole pipeline without Docker (requires a JRE for PySpark):

```bash
python generator/run.py --scale 0.01
python spark/bronze_to_silver.py
python spark/silver_to_gold.py
python spark/gold_analytics.py
python -m pytest tests/ -v
```

Then open `dashboards/executive_dashboard.html` in a browser.

## Start Airflow

```bash
docker compose up --build
```

Open Airflow:

```
http://localhost:8082
```

Default Credentials:

```
Username: admin

Password: admin
```

Trigger:

```
retail_flow_pipeline
```

---

# 📈 Skills Demonstrated

- Python
- SQL
- PySpark
- Apache Spark
- Apache Airflow
- Docker
- Docker Compose
- GitHub Actions
- Plotly
- ETL
- ELT
- Data Engineering
- Data Warehousing
- Star Schema
- Medallion Architecture
- Data Lakehouse
- Data Quality
- Data Validation
- Automation
- CI/CD

---

# 🏆 Project Outcomes

✔ Generated over **5 million** synthetic retail transactions

✔ Built an end-to-end enterprise ETL pipeline

✔ Implemented Bronze → Silver → Gold architecture

✔ Automated data quality validation

✔ Delivered executive analytics dashboard

✔ Containerized the entire platform with Docker

✔ Automated orchestration using Apache Airflow

✔ Integrated continuous integration with GitHub Actions

✔ Demonstrated production-ready Data Engineering workflows

---

# 🔮 Future Improvements

- Kafka Streaming
- Delta Lake
- dbt Transformations
- Great Expectations
- AWS S3 Data Lake
- Snowflake Integration
- Terraform Infrastructure
- Kubernetes Deployment

---

# 👨‍💻 Author

**Chiagoziem Cyriacus Ugoh**

Data Engineer | Data Analyst | Python Developer

GitHub: https://github.com/chidex-coder

---

# ⭐ If you found this project interesting, consider giving it a Star!
