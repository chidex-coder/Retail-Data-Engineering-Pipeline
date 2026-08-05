from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
import os

# Default arguments for the DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define the DAG
with DAG(
    dag_id='retail_flow_pipeline',
    default_args=default_args,
    description='End-to-End Retail Data Engineering Pipeline',
    schedule_interval=None, # We will trigger this manually for now
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['retail', 'spark', 'pipeline'],
) as dag:

    # Define the base path to your project inside the Docker container
    PROJECT_DIR = "/opt/airflow"
    PYTHON_BIN = "python"

    # Task 1: Generate Data
    t1_generate_data = BashOperator(
        task_id='generate_data',
        bash_command=f'cd {PROJECT_DIR}/generator && {PYTHON_BIN} run.py --scale 0.01'
    )

    # Task 2: Bronze to Silver
    t2_bronze_to_silver = BashOperator(
        task_id='bronze_to_silver',
        bash_command=f'cd {PROJECT_DIR} && {PYTHON_BIN} spark/bronze_to_silver.py'
    )

    # Task 3: Silver to Gold
    t3_silver_to_gold = BashOperator(
        task_id='silver_to_gold',
        bash_command=f'cd {PROJECT_DIR} && {PYTHON_BIN} spark/silver_to_gold.py'
    )

    # Task 4: Analytics
    t4_analytics = BashOperator(
        task_id='run_analytics',
        bash_command=f'cd {PROJECT_DIR} && {PYTHON_BIN} spark/gold_analytics.py'
    )

    # Task 5: Run Data Quality Tests
    t5_data_quality = BashOperator(
        task_id='run_data_quality_tests',
        bash_command=f'cd {PROJECT_DIR} && {PYTHON_BIN} -m pytest tests/ -v'
    )

    # Set the task dependencies (Order of execution)
    t1_generate_data >> t2_bronze_to_silver >> t3_silver_to_gold >> t4_analytics >> t5_data_quality