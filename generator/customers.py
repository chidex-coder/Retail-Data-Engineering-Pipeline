import pandas as pd
from faker import Faker
from tqdm import tqdm
import random
from dirty_data import inject_missing, inject_duplicate, mess_up_date, mess_up_email

fake = Faker()

def generate_customers(count, error_rates):
    print(f"Generating {count} customers...")
    data = []
    for _ in tqdm(range(count)):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        record = {
            "CustomerID": f"C{fake.unique.random_int(min=10000, max=9999999)}",
            "FirstName": inject_missing(first_name, error_rates['missing_values']),
            "LastName": inject_missing(last_name, error_rates['missing_values']),
            "DOB": mess_up_date(fake.date_of_birth(minimum_age=18, maximum_age=90), error_rates['mixed_date_formats']),
            "Gender": random.choice(["M", "F", "Other", "NULL"]),
            "Phone": inject_missing(fake.phone_number(), error_rates['missing_values']),
            "Email": mess_up_email(fake.email(), error_rates['invalid_emails']),
            "Country": random.choice(["UK", "United Kingdom", "England", "GB", "U.K."]),
            "City": fake.city(),
            "Postcode": fake.postcode(),
            "RegistrationDate": mess_up_date(fake.date_between(start_date='-5y', end_date='today'), error_rates['mixed_date_formats'])
        }
        data.append(record)
    
    df = pd.DataFrame(data)
    df = inject_duplicate(df, error_rates['duplicates'])
    return df