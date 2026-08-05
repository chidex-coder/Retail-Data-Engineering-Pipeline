import os
from pyspark.sql import SparkSession
import pytest

@pytest.fixture(scope="module")
def spark():
    # Configure Spark to talk to LocalStack S3 (use localhost for Mac)
    return SparkSession.builder \
        .master("local[*]") \
        .appName("pytest") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

# NOTE: These tests validate the local gold layer produced by the pipeline at ./data/gold.
# The pipeline writes gold tables to local disk, so we do not read from LocalStack S3 here.

def test_fact_sales_no_nulls(spark):
    """Ensure no critical fields in FactSales are NULL."""
    df = spark.read.parquet("./data/gold/fact_sales")
    null_counts = df.filter("CustomerKey is null OR ProductKey is null OR Revenue is null").count()
    assert null_counts == 0, "Found NULL values in critical FactSales columns!"

def test_revenue_is_positive(spark):
    """Ensure all Revenue values are greater than 0."""
    df = spark.read.parquet("./data/gold/fact_sales")
    negative_revenue = df.filter("Revenue <= 0").count()
    assert negative_revenue == 0, "Found negative or zero revenue values!"

def test_dim_product_uniqueness(spark):
    """Ensure DimProduct has unique ProductKey."""
    df = spark.read.parquet("./data/gold/dim_product")
    total_rows = df.count()
    distinct_rows = df.select("ProductKey").distinct().count()
    assert total_rows == distinct_rows, "DimProduct contains duplicate ProductKeys!"