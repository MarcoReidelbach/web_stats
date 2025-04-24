import pandas as pd
from datetime import datetime, timedelta
import os

# Load remove list
try:
    with open("remove", "r", encoding="utf-8") as f:
        Remove = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Warning: 'remove' not found. No users will be removed.")
    Remove = []

start_date = datetime.strptime("01.04.2025", "%d.%m.%Y")
end_date = datetime.strptime("30.04.2025", "%d.%m.%Y")

results = []

# Loop through month
for i in range((end_date - start_date).days + 1):
    date_old = start_date + timedelta(days=i)
    date_new = date_old + timedelta(days=1)

    str_old = date_old.strftime("%d.%m.%Y")
    str_new = date_new.strftime("%d.%m.%Y")

    file_old = f"raw_data_test/{str_old}.pkl"
    file_new = f"raw_data_test/{str_new}.pkl"

    if not (os.path.exists(file_old) and os.path.exists(file_new)):
        continue

    dold = pd.read_pickle(file_old)
    dnew = pd.read_pickle(file_new)

    dold = dold[(dold['User Name'] != 'Not Defined') & (dold['User ID'] != 'Not Defined')]
    dnew = dnew[(dnew['User Name'] != 'Not Defined') & (dnew['User ID'] != 'Not Defined')]

    dold['Number of Posts'] = dold['Number of Posts'].astype(str).str.replace('.', '', regex=False).astype(int)
    dnew['Number of Posts'] = dnew['Number of Posts'].astype(str).str.replace('.', '', regex=False).astype(int)

    post_change = pd.merge(
        dnew[['User ID', 'User Name', 'Number of Posts']].rename(columns={'Number of Posts': 'NoP_new', 'User Name': 'User Name new'}),
        dold[['User ID', 'User Name', 'Number of Posts']].rename(columns={'Number of Posts': 'NoP_old', 'User Name': 'User Name old'}),
        on='User ID', how='outer'
    )
    post_change['NoP_old'] = post_change['NoP_old'].fillna(0)
    post_change['NoP_new'] = post_change['NoP_new'].fillna(0)
    post_change = post_change.eval('Change = NoP_new - NoP_old').sort_values('Change', ascending=False).reset_index(drop=True)

    post_change = post_change[~post_change['User ID'].isin(Remove)].reset_index(drop=True)

    if not post_change.empty:
        top_change = post_change['Change'].max()
        top_users = post_change[post_change['Change'] == top_change]['User Name new'].tolist()
        user_names = ", ".join(top_users)
        result = f"{str_old} - {user_names} ({int(top_change)})"
        results.append(result)

# Output all results
for r in results:
    print(r)

