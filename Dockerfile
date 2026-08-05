FROM apache/airflow:2.9.3-python3.9

# Install Java and required system dependencies for Spark
USER root
RUN apt-get update && apt-get install -y default-jre && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install pyspark==3.5.1