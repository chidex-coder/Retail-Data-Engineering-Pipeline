import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, count, expr, to_date, dayofweek, month, year, weekofyear, row_number
from pyspark.sql.window import Window

def main():
    # 1. Initialize Spark with S3/LocalStack Configurations
    spark = SparkSession.builder \
        .appName("RetailFlow_Pipeline") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    base_data_dir = "./data"
    silver_dir = os.path.join(base_data_dir, "silver")
    gold_dir = os.path.join(base_data_dir, "gold")

    # ==========================================
    # 1. Load Silver Data
    # ==========================================
    print("Loading Silver tables...")
    df_customers = spark.read.parquet(os.path.join(silver_dir, "customers"))
    df_products = spark.read.parquet(os.path.join(silver_dir, "products"))
    df_orders = spark.read.parquet(os.path.join(silver_dir, "orders"))

    # ==========================================
    # 2. Create Dimension Tables
    # ==========================================
    print("Building Dimension Tables...")
    
    # DimCustomer: Add a surrogate key
    df_dim_customer = df_customers.withColumnRenamed("CustomerID", "CustomerID_BK") \
        .withColumn("CustomerKey", row_number().over(Window.orderBy("CustomerID_BK")))
    
    # DimProduct: Add a surrogate key
    df_dim_product = df_products.withColumnRenamed("ProductID", "ProductID_BK") \
        .withColumn("ProductKey", row_number().over(Window.orderBy("ProductID_BK")))

    # DimDate: Generate a calendar table from the min to max order dates
    min_date = df_orders.selectExpr("min(OrderDate)").first()[0]
    max_date = df_orders.selectExpr("max(OrderDate)").first()[0]
    
    df_dim_date = spark.sql(f"""
        SELECT explode(sequence(to_date('{min_date}'), to_date('{max_date}'), interval 1 day)) as Date
    """)
    df_dim_date = df_dim_date.withColumn("DateKey", expr("date_format(Date, 'yyyyMMdd')").cast("int")) \
        .withColumn("Day", expr("day(Date)")) \
        .withColumn("Month", month(col("Date"))) \
        .withColumn("Year", year(col("Date"))) \
        .withColumn("WeekOfYear", weekofyear(col("Date"))) \
        .withColumn("DayOfWeek", dayofweek(col("Date")))

    # ==========================================
    # 3. Create Fact Table (FactSales)
    # ==========================================
    print("Building Fact Table...")
    
        # Join Orders with Products to get prices and calculate metrics
    df_fact_sales = df_orders.join(df_dim_product, df_orders.ProductID == df_dim_product.ProductID_BK, "inner") \
        .join(df_dim_customer, df_orders.CustomerID == df_dim_customer.CustomerID_BK, "inner")
    
    # Join with DimDate to get DateKey
    df_fact_sales = df_fact_sales.join(df_dim_date, df_fact_sales.OrderDate == df_dim_date.Date, "left")

    # Calculate Business Metrics: Total Revenue and Profit
    df_fact_sales = df_fact_sales.withColumn("Revenue", col("Quantity") * col("SellingPrice")) \
                                 .withColumn("Cost", col("Quantity") * col("CostPrice")) \
                                 .withColumn("Profit", col("Revenue") - col("Cost"))

    # DROP rows where Revenue or Cost is NULL (incomplete product data)
    df_fact_sales = df_fact_sales.filter(col("Revenue").isNotNull() & col("Cost").isNotNull())

    # Select only the necessary columns for the Star Schema
    df_fact_sales_final = df_fact_sales.select(
        col("OrderID").alias("OrderID_BK"),
        col("CustomerKey"),
        col("ProductKey"),
        col("DateKey"),
        col("Quantity"),
        col("Revenue"),
        col("Cost"),
        col("Profit"),
        col("Status"),
        col("PaymentMethod")
    )

    # ==========================================
    # 4. Write to Gold Layer
    # ==========================================
    print("Writing Gold tables...")
    
    df_dim_customer.write.mode("overwrite").parquet(os.path.join(gold_dir, "dim_customer"))
    df_dim_product.write.mode("overwrite").parquet(os.path.join(gold_dir, "dim_product"))
    df_dim_date.write.mode("overwrite").parquet(os.path.join(gold_dir, "dim_date"))
    df_fact_sales_final.write.mode("overwrite").parquet(os.path.join(gold_dir, "fact_sales"))

    print("\nGold layer processing complete! Star Schema is ready for BI.")
    spark.stop()

if __name__ == "__main__":
    main()