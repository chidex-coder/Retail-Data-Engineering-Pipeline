import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, lower, when, to_date, regexp_replace, lit
from pyspark.sql.types import DoubleType

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
    bronze_dir = os.path.join(base_data_dir, "raw")
    silver_dir = os.path.join(base_data_dir, "silver")

    # ==========================================
    # 2. Clean Customers
    # ==========================================
    print("Processing Customers...")
    customers_path = os.path.join(bronze_dir, "customers", "customers_full.csv")
    df_customers = spark.read.csv(customers_path, header=True, inferSchema=True)

    # Standardize strings: trim whitespace, lowercase emails
    df_customers = df_customers.withColumn("Email", lower(trim(col("Email")))) \
                               .withColumn("Country", trim(col("Country")))
    
    # Standardize Country Names
    df_customers = df_customers.withColumn("Country", 
        when(col("Country").isin(["UK", "U.K.", "GB", "Great Britain", "England"]), "United Kingdom")
        .otherwise(col("Country")))

    # Standardize Dates (handles mixed formats to 'yyyy-MM-dd')
    df_customers = df_customers.withColumn("RegistrationDate", to_date(col("RegistrationDate"), "yyyy-MM-dd")) \
                               .withColumn("DOB", to_date(col("DOB"), "yyyy-MM-dd"))

    # Drop rows with completely missing CustomerID (Critical Key)
    df_customers_clean = df_customers.na.drop(subset=["CustomerID"]).dropDuplicates(["CustomerID"])

    # Write to Silver
    cust_silver_path = os.path.join(silver_dir, "customers")
    df_customers_clean.write.mode("overwrite").parquet(cust_silver_path)
    print(f"Saved cleaned customers to {cust_silver_path}")

    # ==========================================
    # 3. Clean Products
    # ==========================================
    print("Processing Products...")
    products_path = os.path.join(bronze_dir, "products", "products_full.csv")
    df_products = spark.read.csv(products_path, header=True, inferSchema=True)

    # Clean prices: Remove '£', 'GBP', commas, and cast to double
    df_products = df_products.withColumn("CostPrice", regexp_replace(col("CostPrice"), "[^0-9.]", "")) \
                             .withColumn("SellingPrice", regexp_replace(col("SellingPrice"), "[^0-9.]", ""))
    
    df_products = df_products.withColumn("CostPrice", col("CostPrice").cast(DoubleType())) \
                             .withColumn("SellingPrice", col("SellingPrice").cast(DoubleType()))

    # Handle missing/invalid brands
    df_products = df_products.withColumn("Brand", 
        when(col("Brand").isNull() | (col("Brand") == "NULL") | (col("Brand") == ""), lit("Unknown"))
        .otherwise(trim(col("Brand"))))

    # Drop rows with missing ProductID
    df_products_clean = df_products.na.drop(subset=["ProductID"]).dropDuplicates(["ProductID"])

    # Write to Silver
    prod_silver_path = os.path.join(silver_dir, "products")
    df_products_clean.write.mode("overwrite").parquet(prod_silver_path)
    print(f"Saved cleaned products to {prod_silver_path}")

    # ==========================================
    # 4. Clean Orders
    # ==========================================
    print("Processing Orders...")
    orders_path = os.path.join(bronze_dir, "orders", "orders_full.csv")
    df_orders = spark.read.csv(orders_path, header=True, inferSchema=True)

    # Drop rows with missing CustomerID or ProductID (referential integrity)
    df_orders_clean = df_orders.na.drop(subset=["CustomerID", "ProductID"])

    # Filter out negative quantities
    df_orders_clean = df_orders_clean.filter(col("Quantity") > 0)

    # Standardize OrderDate
    df_orders_clean = df_orders_clean.withColumn("OrderDate", to_date(col("OrderDate"), "yyyy-MM-dd"))

    # Drop exact duplicate orders
    df_orders_clean = df_orders_clean.dropDuplicates()

    # Write to Silver
    ord_silver_path = os.path.join(silver_dir, "orders")
    df_orders_clean.write.mode("overwrite").parquet(ord_silver_path)
    print(f"Saved cleaned orders to {ord_silver_path}")

    print("\nSilver layer processing complete!")
    spark.stop()

if __name__ == "__main__":
    main()