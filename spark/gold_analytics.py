"""Gold layer -> RetailFlow Executive Business Intelligence Dashboard.

Reads the Gold star schema, standardises the dimension attributes that arrive
dirty from the source systems (HTML fragments, emoji, "NULL"/"Unknown"/"-"
placeholders), then hands the fact rows to `dashboard_builder`, which renders a
single self-contained, cross-filterable HTML report.
"""

import os
import sys
from datetime import datetime, timezone

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dashboard_builder as db  # noqa: E402

# Placeholders the source systems use for "we don't know". Compared lower-cased.
BLANK_TOKENS = ["", "-", "--", "n/a", "na", "null", "none", "nil", "nan", "unknown", "?"]


def tidy(column):
    """Strip HTML tags and non-printable junk, then null out placeholder values."""
    text = column.cast("string")
    text = F.regexp_replace(text, r"<[^>]*>", "")       # <b>Sony</b> -> Sony
    text = F.regexp_replace(text, r"[^\x20-\x7E]", "")  # IKEA<emoji> -> IKEA
    text = F.trim(text)
    return F.when(text.isNull() | F.lower(text).isin(BLANK_TOKENS), F.lit(None)).otherwise(text)


def normalise_gender(column):
    value = F.upper(tidy(column))
    return (F.when(value.isin("M", "MALE"), F.lit("Male"))
             .when(value.isin("F", "FEMALE"), F.lit("Female"))
             .when(value.isin("OTHER", "NON-BINARY", "NONBINARY", "X"), F.lit("Other"))
             .otherwise(F.lit(None)))


def load_facts(spark, gold_dir):
    """Join the star schema into one flat, cleaned frame of order lines."""
    fact_sales = spark.read.parquet(os.path.join(gold_dir, "fact_sales"))
    dim_product = spark.read.parquet(os.path.join(gold_dir, "dim_product"))
    dim_customer = spark.read.parquet(os.path.join(gold_dir, "dim_customer"))
    dim_date = spark.read.parquet(os.path.join(gold_dir, "dim_date"))

    products = dim_product.select(
        "ProductKey",
        tidy(F.col("Category")).alias("Category"),
        tidy(F.col("Brand")).alias("Brand"),
    )

    customers = dim_customer.select(
        "CustomerKey",
        normalise_gender(F.col("Gender")).alias("Gender"),
        tidy(F.col("City")).alias("City"),
        F.trim(F.concat_ws(" ", tidy(F.col("FirstName")), tidy(F.col("LastName")))).alias("CustomerName"),
    ).withColumn(
        "CustomerName",
        F.when(F.col("CustomerName") == "", F.lit(None)).otherwise(F.col("CustomerName")),
    )

    dates = dim_date.select("DateKey", "Year", "Month")

    # Left joins on the dimensions: an order line with an unresolved attribute
    # still belongs in the revenue totals, it just drops out of that breakdown.
    facts = (fact_sales
             .join(F.broadcast(products), "ProductKey", "left")
             .join(F.broadcast(customers), "CustomerKey", "left")
             .join(F.broadcast(dates), "DateKey", "left"))

    return facts.select(
        F.col("Year"),
        F.col("Month"),
        F.col("Category"),
        F.col("Brand"),
        tidy(F.col("PaymentMethod")).alias("PaymentMethod"),
        F.col("Gender"),
        F.initcap(tidy(F.col("Status"))).alias("Status"),
        F.col("City"),
        F.col("CustomerName"),
        F.col("CustomerKey"),
        F.col("ProductKey"),
        F.col("Revenue"),
        F.col("Profit"),
        F.col("Quantity"),
    )


def codes_and_labels(series):
    """Dictionary-encode a column: codes (-1 where missing) plus sorted labels."""
    labels = sorted(series.dropna().unique().tolist())
    categorical = pd.Categorical(series, categories=labels)
    return categorical.codes.astype("int64"), [str(label) for label in labels]


def keyed_codes(keys, labels_by_key):
    """Encode by surrogate key so two customers sharing a name stay distinct."""
    unique_keys = sorted(keys.dropna().unique().tolist())
    categorical = pd.Categorical(keys, categories=unique_keys)
    labels = [str(labels_by_key.get(key) or f"Customer {int(key)}") for key in unique_keys]
    return categorical.codes.astype("int64"), labels


def to_pence(series):
    return series.fillna(0).mul(100).round().clip(lower=0).astype("int64")


# Columns the Dash app reads. Categoricals keep the file ~1.6 MB and let it
# load in single-digit milliseconds, so the served app needs no Spark at runtime.
ANALYTICS_COLUMNS = [
    "Year", "Month", "Category", "Brand", "PaymentMethod", "Gender",
    "Status", "City", "CustomerName", "CustomerKey", "ProductKey",
    "Revenue", "Profit", "Quantity",
]
CATEGORICAL_COLUMNS = [
    "Category", "Brand", "PaymentMethod", "Gender", "Status", "City", "CustomerName",
]


def write_analytics_table(frame, path):
    """Persist the cleaned, joined fact rows for the Dash app to serve from."""
    table = frame[ANALYTICS_COLUMNS].copy()
    for column in CATEGORICAL_COLUMNS:
        table[column] = table[column].astype("category")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    table.to_parquet(path, compression="snappy", index=False)
    return os.path.getsize(path)


def build_payload(frame):
    """Dictionary-encode the flat frame into the client payload plus QA counts."""
    years = frame["Year"].astype("Int64").astype("object").where(frame["Year"].notna(), None)
    year_codes, year_labels = codes_and_labels(pd.Series(years))
    category_codes, category_labels = codes_and_labels(frame["Category"])
    brand_codes, brand_labels = codes_and_labels(frame["Brand"])
    payment_codes, payment_labels = codes_and_labels(frame["PaymentMethod"])
    gender_codes, gender_labels = codes_and_labels(frame["Gender"])
    status_codes, status_labels = codes_and_labels(frame["Status"])
    city_codes, city_labels = codes_and_labels(frame["City"])

    names_by_key = (frame[["CustomerKey", "CustomerName"]]
                    .dropna(subset=["CustomerKey"])
                    .drop_duplicates("CustomerKey")
                    .set_index("CustomerKey")["CustomerName"].to_dict())
    customer_codes, customer_labels = keyed_codes(frame["CustomerKey"], names_by_key)

    product_keys = sorted(frame["ProductKey"].dropna().unique().tolist())
    product_codes = pd.Categorical(frame["ProductKey"], categories=product_keys).codes.astype("int64")

    months = frame["Month"].fillna(0).astype("int64")  # 0 = order date unresolved

    payload = {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC"),
            "rowCount": int(len(frame)),
            "productCount": len(product_keys),
        },
        "theme": db.load_chart_theme(),
        "n": int(len(frame)),
        "dims": {
            "year": year_labels,
            "month": db.MONTH_NAMES,
            "category": category_labels,
            "brand": brand_labels,
            "payment": payment_labels,
            "gender": gender_labels,
            "status": status_labels,
            "city": city_labels,
            "customer": customer_labels,
        },
        "cols": {
            "year": db.dim_column(year_codes, len(year_labels)),
            "month": db.value_column(months),
            "category": db.dim_column(category_codes, len(category_labels)),
            "brand": db.dim_column(brand_codes, len(brand_labels)),
            "payment": db.dim_column(payment_codes, len(payment_labels)),
            "gender": db.dim_column(gender_codes, len(gender_labels)),
            "status": db.dim_column(status_codes, len(status_labels)),
            "city": db.dim_column(city_codes, len(city_labels)),
            "customer": db.dim_column(customer_codes, len(customer_labels)),
            "product": db.dim_column(product_codes, len(product_keys)),
            "revenue": db.value_column(to_pence(frame["Revenue"])),
            "profit": db.value_column(to_pence(frame["Profit"])),
            "quantity": db.value_column(frame["Quantity"].fillna(0).astype("int64")),
        },
    }

    quality = [
        ("without a brand", int((brand_codes < 0).sum())),
        ("without a payment method", int((payment_codes < 0).sum())),
        ("without a gender", int((gender_codes < 0).sum())),
        ("without an order date", int((year_codes < 0).sum())),
    ]

    return payload, quality


def main():
    spark = (SparkSession.builder
             .appName("RetailFlow_Pipeline")
             .master("local[*]")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    gold_dir = os.path.join("./data", "gold")
    outputs = [
        os.path.join("./dashboards", "executive_dashboard.html"),
        os.path.join("./docs", "index.html"),  # GitHub Pages copy
    ]

    print("Loading Gold tables and standardising dimension attributes...")
    frame = load_facts(spark, gold_dir).toPandas()
    print(f"  {len(frame):,} order lines loaded")

    analytics_path = os.path.join(gold_dir, "analytics_facts.parquet")
    size = write_analytics_table(frame, analytics_path)
    print(f"  wrote {analytics_path} ({size / 1_048_576:.1f} MB) for the Dash app")

    print("Encoding the fact rows for the browser runtime...")
    payload, quality = build_payload(frame)
    for label, value in quality:
        print(f"  {value:>8,} rows {label}")

    print("Rendering the executive dashboard...")
    page = db.build_html(payload, quality)
    for path, size in db.write_dashboard(page, outputs):
        print(f"  wrote {path} ({size / 1_048_576:.1f} MB)")

    print("\nSuccess! Open dashboards/executive_dashboard.html in a browser.")
    spark.stop()


if __name__ == "__main__":
    main()
