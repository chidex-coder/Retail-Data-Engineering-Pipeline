import pandas as pd
from faker import Faker
from tqdm import tqdm
import random
from dirty_data import inject_missing, inject_duplicate, mess_up_price, inject_html, inject_emoji

fake = Faker()

categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys"]
brands = ["Sony", "Samsung", "Nike", "Adidas", "IKEA", "AmazonBasics", "Unknown"]

def generate_products(count, error_rates):
    print(f"Generating {count} products...")
    data = []
    for _ in tqdm(range(count)):
        cost_price = round(random.uniform(5.0, 500.0), 2)
        selling_price = round(cost_price * random.uniform(1.2, 2.0), 2)
        
        category = random.choice(categories)
        brand = inject_missing(random.choice(brands), error_rates['missing_brands'])
        brand = inject_html(brand, error_rates['html_in_text'])
        brand = inject_emoji(brand, error_rates['emojis_in_text'])
        
        record = {
            "ProductID": f"P{fake.unique.random_int(min=1000, max=999999)}",
            "Category": category,
            "Brand": brand,
            "CostPrice": mess_up_price(cost_price, error_rates['negative_prices']),
            "SellingPrice": mess_up_price(selling_price, error_rates['negative_prices']),
            "Weight": inject_missing(round(random.uniform(0.1, 50.0), 2), error_rates['missing_values']),
            "SupplierID": f"S{random.randint(1, 20000)}"
        }
        data.append(record)
    
    df = pd.DataFrame(data)
    df = inject_duplicate(df, error_rates['duplicate_skus'])
    return df