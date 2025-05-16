import os
import glob
import pandas as pd
from datetime import datetime, timedelta
import pytz

chunks = sorted(glob.glob("tmp/chunk_*.pkl"))
if not chunks:
    print("No chunks found in tmp/")
    exit(1)

dataframes = [pd.read_pickle(chunk) for chunk in chunks]
merged_df = pd.concat(dataframes, ignore_index=True)

# --- Determine Dates Automatically ---
berlin = pytz.timezone('Europe/Berlin')
today = datetime.now(berlin)
first_of_current_month = today.replace(day=1)
last_month = first_of_current_month - timedelta(days=1)
first_of_last_month = last_month.replace(day=1)
target_month = first_of_last_month.month
target_year = first_of_last_month.year

filename = f"{target_month:02d}.{target_year}_RG.pkl"

os.makedirs("raw_data", exist_ok=True)
merged_df.to_pickle(f"raw_data/{filename}")
print(f"Saved merged file to raw_data/{filename}")

