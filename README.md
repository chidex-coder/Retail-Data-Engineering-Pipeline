# 🚀 RetailFlow: Enterprise Data Engineering Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
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
| Dashboard | Plotly |
| Version Control | Git & GitHub |

---

# ✨ Features

- Generate **1.2–5 million** synthetic retail transactions
- Simulate real-world dirty data
- Handle schema drift automatically
- Clean and standardize data with PySpark
- Bronze → Silver → Gold Medallion Architecture
- Star Schema Data Warehouse
- Executive Plotly Dashboard
- Automated Apache Airflow Pipeline
- Dockerized Deployment
- Automated Data Quality Testing
- GitHub Actions CI/CD Pipeline

---

# 📂 Project Structure

```text
RetailFlow/
│
├── airflow/
│   ├── dags/
│   ├── plugins/
│
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│
├── generators/
│
├── transformations/
│
├── dashboards/
│
├── tests/
│
├── docker/
│
├── .github/
│
├── requirements.txt
│
└── docker-compose.yml
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

Business metrics include:

- Revenue
- Order Status Distribution

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

# 📊 Dashboard

The executive dashboard provides interactive business insights including:

- Revenue
- Order Status Distribution

Dashboard is built using **Plotly**.

### Live Dashboard

https://chidex-coder.github.io/Retail-Data-Engineering-Pipeline/

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
