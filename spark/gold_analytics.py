import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, round, desc, count
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    gold_dir = "./data/gold"
    dash_dir = "./dashboards"
    os.makedirs(dash_dir, exist_ok=True)

    # 2. Load Gold Tables
    print("Loading Gold tables for analytics...")
    fact_sales = spark.read.parquet(os.path.join(gold_dir, "fact_sales"))
    dim_product = spark.read.parquet(os.path.join(gold_dir, "dim_product"))
    dim_date = spark.read.parquet(os.path.join(gold_dir, "dim_date"))

    # ==========================================
    # 3. Executive KPIs (Console Output)
    # ==========================================
    print("\n" + "="*40)
    print("EXECUTIVE DASHBOARD SUMMARY")
    print("="*40)
    
    total_revenue = fact_sales.agg({"Revenue": "sum"}).first()[0]
    total_profit = fact_sales.agg({"Profit": "sum"}).first()[0]
    total_orders = fact_sales.select("OrderID_BK").distinct().count()

    print(f"Total Revenue:  £{total_revenue:,.2f}")
    print(f"Total Profit:   £{total_profit:,.2f}")
    print(f"Total Orders:   {total_orders:,}")
    print("="*40)

    # ==========================================
    # 4. Prepare Data for Plotly (Convert Spark -> Pandas)
    # ==========================================
    print("\nPreparing data for unified Plotly dashboard...")

    # Top 5 Products by Revenue
    top_products = fact_sales.join(dim_product, "ProductKey") \
        .groupBy("Category", "Brand") \
        .agg(round(sum("Revenue"), 2).alias("TotalRevenue")) \
        .orderBy(desc("TotalRevenue")) \
        .limit(5)
    df_top_products = top_products.toPandas()

    # Monthly Revenue Trend
    monthly_trend = fact_sales.join(dim_date, "DateKey") \
        .withColumn("YearMonth", col("Year") * 100 + col("Month")) \
        .groupBy("YearMonth") \
        .agg(round(sum("Revenue"), 2).alias("MonthlyRevenue")) \
        .orderBy("YearMonth")
    df_monthly_trend = monthly_trend.toPandas()

    # Order Status Distribution
    status_dist = fact_sales.groupBy("Status").count().withColumnRenamed("count", "OrderCount")
    df_status = status_dist.toPandas()

    # ==========================================
    # 5. Generate Unified Plotly Dashboard
    # ==========================================
    print("Generating unified interactive HTML dashboard...")

    # Create a 2x2 grid layout. The bottom row spans both columns for the time series.
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "domain"}],
               [{"type": "xy", "colspan": 2}, None]],
        subplot_titles=("Top 5 Products by Revenue", "Order Status Distribution", "Monthly Revenue Trend")
    )

    # Chart 1: Top 5 Products (Bar Chart - Top Left)
    fig.add_trace(
        go.Bar(
            x=df_top_products["Brand"], 
            y=df_top_products["TotalRevenue"],
            name="Revenue",
            marker_color='royalblue',
            text=df_top_products["TotalRevenue"],
            texttemplate='£%{text:,.2s}'
        ),
        row=1, col=1
    )

    # Chart 2: Order Status (Pie Chart - Top Right)
    fig.add_trace(
        go.Pie(
            labels=df_status["Status"], 
            values=df_status["OrderCount"],
            name="Status",
            hole=0.4
        ),
        row=1, col=2
    )

    # Chart 3: Monthly Trend (Line Chart - Bottom Spanning)
    fig.add_trace(
        go.Scatter(
            x=df_monthly_trend["YearMonth"], 
            y=df_monthly_trend["MonthlyRevenue"],
            mode="lines+markers",
            name="Monthly Revenue",
            line=dict(color="firebrick", width=2)
        ),
        row=2, col=1
    )

    # Update layout and titles
    fig.update_layout(
        title_text=f"<b>RetailFlow Executive Dashboard</b><br>Total Revenue: £{total_revenue:,.2f} | Total Profit: £{total_profit:,.2f}",
        title_x=0.5,
        height=800,
        showlegend=False
    )

    # Save the single unified HTML file
    dashboard_path = os.path.join(dash_dir, "executive_dashboard.html")
    fig.write_html(dashboard_path)

    print(f"\nSuccess! Unified dashboard saved to: {dashboard_path}")
    spark.stop()

if __name__ == "__main__":
    main()