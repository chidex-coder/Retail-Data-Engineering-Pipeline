import yaml
import os
import pandas as pd
import argparse
from customers import generate_customers
from products import generate_products
from orders import generate_orders  # <-- Added this import

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_data(df, entity_name, config):
    base_dir = os.path.join(config['output']['base_dir'], entity_name)
    os.makedirs(base_dir, exist_ok=True)
    
    for fmt in config['output']['formats']:
        file_path = os.path.join(base_dir, f"{entity_name}_full.{fmt}")
        if fmt == 'csv':
            df.to_csv(file_path, index=False)
        elif fmt == 'parquet':
            df_clean = df.copy()
            for col in df_clean.select_dtypes(include=['object']).columns:
                df_clean[col] = df_clean[col].astype(str)
            df_clean.to_parquet(file_path, index=False)
        elif fmt == 'json':
            df.to_json(file_path, orient='records', lines=True)
        print(f"Saved {fmt} to {file_path}")

def main():
    parser = argparse.ArgumentParser(description="RetailFlow Enterprise Data Generator")
    parser.add_argument('--scale', type=float, default=1.0, help="Scale factor for data generation (1.0 = full scale)")
    args = parser.parse_args()

    config = load_config()
    
    # 1. Generate Customers
    cust_count = int(config['entities']['customers']['count'] * args.scale)
    customers_df = generate_customers(cust_count, config['entities']['customers']['error_rates'])
    save_data(customers_df, 'customers', config)
    
    # 2. Generate Products
    prod_count = int(config['entities']['products']['count'] * args.scale)
    products_df = generate_products(prod_count, config['entities']['products']['error_rates'])
    save_data(products_df, 'products', config)
    
    # 3. Generate Orders <-- Added this block
    order_count = int(config['entities']['orders']['count'] * args.scale)
    orders_df = generate_orders(order_count, config['entities']['orders']['error_rates'], config['output']['base_dir'])
    if not orders_df.empty:
        save_data(orders_df, 'orders', config)

    print("\nData generation complete!")

if __name__ == "__main__":
    main()