import pandas as pd
from faker import Faker
from tqdm import tqdm
import random
import os
from dirty_data import inject_missing, inject_duplicate, mess_up_date

fake = Faker()

def generate_orders(count, error_rates, data_dir):
    print(f"Generating {count} orders...")
    
    # Load valid IDs from previously generated data to maintain referential integrity
    cust_file = os.path.join(data_dir, 'customers', 'customers_full.csv')
    prod_file = os.path.join(data_dir, 'products', 'products_full.csv')
    
    try:
        cust_ids = pd.read_csv(cust_file, usecols=['CustomerID'])['CustomerID'].tolist()
        prod_ids = pd.read_csv(prod_file, usecols=['ProductID'])['ProductID'].tolist()
    except FileNotFoundError:
        print("Error: Customer or Product files not found. Please generate them first.")
        return pd.DataFrame()

    data = []
    for _ in tqdm(range(count)):
        qty = random.randint(1, 5)
        
        # Inject negative quantities
        if random.random() < error_rates['negative_quantities']:
            qty = qty * -1
            
        record = {
            "OrderID": f"ORD{fake.unique.random_int(min=100000, max=9999999)}",
            "CustomerID": inject_missing(random.choice(cust_ids), error_rates['missing_customer_ids']),
            "ProductID": random.choice(prod_ids),
            "Quantity": qty,
            "OrderDate": mess_up_date(fake.date_between(start_date='-3y', end_date='today'), error_rates['invalid_dates']),
            "Status": random.choice(["Pending", "Shipped", "Delivered", "Cancelled", "Returned"]),
            "PaymentMethod": random.choice(["Credit Card", "PayPal", "Bank Transfer", "Apple Pay", "NULL"])
        }
        data.append(record)
    
    df = pd.DataFrame(data)
    df = inject_duplicate(df, error_rates['duplicates'])
    return df