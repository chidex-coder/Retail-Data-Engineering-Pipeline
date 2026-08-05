import random
import string
import codecs
import pandas as pd

def inject_missing(value, missing_rate=0.05):
    if random.random() < missing_rate:
        return random.choice(["NULL", "N/A", "", "Unknown", "-"])
    return value

def inject_duplicate(df, duplicate_rate=0.05):
    num_duplicates = int(len(df) * duplicate_rate)
    if num_duplicates > 0:
        duplicates = df.sample(n=num_duplicates, replace=True)
        return pd.concat([df, duplicates]).reset_index(drop=True)
    return df

def mess_up_date(date_str, error_rate=0.1):
    if random.random() < error_rate:
        formats = [
            "%d/%m/%Y", "%m-%d-%Y", "%Y%m%d", 
            "Yesterday", "Tomorrow", str(int(random.random() * 1000000000))
        ]
        return date_str.strftime(random.choice(formats))
    return date_str.strftime("%Y-%m-%d")

def mess_up_email(email, error_rate=0.1):
    if random.random() < error_rate:
        errors = [
            email.replace(".com", ".con"), 
            email.replace("@", "@@"), 
            email.split("@")[0] + "@gmal.com", 
            "NULL"
        ]
        return random.choice(errors)
    return email

def mess_up_price(price, error_rate=0.1):
    if random.random() < error_rate:
        errors = [f"£{price}", f"{price} GBP", "One Hundred", f"{price * -1}", "N/A"]
        return random.choice(errors)
    return price

def inject_html(text, error_rate=0.05):
    if random.random() < error_rate:
        return f"<b>{text}</b>"
    return text

def inject_emoji(text, error_rate=0.05):
    if random.random() < error_rate:
        return f"{text}📱💻"
    return text