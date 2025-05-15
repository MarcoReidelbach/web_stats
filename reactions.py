from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz

# --- Load 'Remove' List ---
try:
    with open("remove", "r", encoding="utf-8") as f:
        Remove = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Warning: 'remove' not found. No users will be removed.")
    Remove = []

# Get login info from environment variables
username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")

# --- Determine Dates Automatically ---
berlin = pytz.timezone('Europe/Berlin')
today = datetime.now(berlin)
first_of_current_month = today.replace(day=1)
last_month = first_of_current_month - timedelta(days=1)
first_of_last_month = last_month.replace(day=1)
target_month = first_of_last_month.month
target_year = first_of_last_month.year

# --- Load Pickles ---
data_old = first_of_last_month.strftime("%d.%m.%Y")
data_new = first_of_current_month.strftime("%d.%m.%Y")
dold = pd.read_pickle(f"raw_data/{data_old}.pkl")
dnew = pd.read_pickle(f"raw_data/{data_new}.pkl")

# --- Filter out 'Not Defined' Users ---
dold = dold[(dold['User Name'] != 'Not Defined') & (dold['User ID'] != 'Not Defined')]
dnew = dnew[(dnew['User Name'] != 'Not Defined') & (dnew['User ID'] != 'Not Defined')]

# --- Convert columns to int ---
for df in [dold, dnew]:
    df['Number of Posts'] = df['Number of Posts'].astype(str).str.replace('.', '', regex=False).astype(int)
    df['Number of Reactions'] = df['Number of Reactions'].astype(str).str.replace('.', '', regex=False).astype(int)
    df['Number of Trophies'] = df['Number of Trophies'].astype(str).str.replace('.', '', regex=False).astype(int)

# --- Compute reaction change ---
reaction_change = pd.merge(
    dnew[['User ID', 'User Name', 'Number of Reactions']].rename(columns={
        'Number of Reactions': 'NoR_new',
        'User Name': 'User Name new'
    }),
    dold[['User ID', 'User Name', 'Number of Reactions']].rename(columns={
        'Number of Reactions': 'NoR_old',
        'User Name': 'User Name old'
    }),
    on='User ID',
    how='outer'
)

reaction_change['NoR_old'] = reaction_change['NoR_old'].fillna(0).astype(int)
reaction_change['NoR_new'] = reaction_change['NoR_new'].fillna(0).astype(int)
reaction_change['Change'] = reaction_change['NoR_new'] - reaction_change['NoR_old']
reaction_change = reaction_change[~reaction_change['User ID'].isin(Remove)]

# --- Limit to top 100 by Change ---
reaction_change = reaction_change.sort_values('Change', ascending=False).head(1).reset_index(drop=True)

# Instantiate options
opts = Options()
opts.add_argument("--headless")  # Run headless on GitHub Actions
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

# Set the location of the webdriver
service = Service("/usr/bin/chromedriver")

# Instantiate a webdriver
driver = webdriver.Chrome(options=opts, service=service)
driver.set_window_size(1920, 1080)

# Load the HTML page
driver.get("https://www.moonsault.de/login")
time.sleep(10)

# Accept cookies if banner appears
try:
    driver.find_element("id", "cmpbntyestxt").click()
except:
    pass

# Login
driver.find_element("id", "username").send_keys(username)
driver.find_element("id", "password").send_keys(password)
driver.find_element(By.XPATH, "//input[@value='Absenden']").click()

# Go to members list page
max_attempts = 5
for attempt in range(max_attempts):
    try:
        driver.get("https://www.moonsault.de/members-list/?pageNo=1&sortField=activityPoints&sortOrder=DESC")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav.pagination"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        break  # Exit loop if successful
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(10)  # Wait before retrying
else:
    driver.save_screenshot("fail.png")
    raise Exception("Failed to load members list page after multiple attempts.")

# Initialize lists
usr_name, usr_id, reactions_given = [], [], []

for _, row in reaction_change.iterrows():
    print(row['User Name new'])
    profile_url = f'https://www.moonsault.de/user/{row["User ID"]}/#likes' 

    if profile_url:
        print(profile_url)
        try:    
            # Load user profile page
            driver.get(profile_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
    
            try:
                # Wait for the 'Vergebene Reaktionen' button to be present
                given_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-like-type="given"]'))
                )
    
                # Click only if not already active
                if "active" not in given_button.get_attribute("class"):
                    driver.execute_script("arguments[0].click();", given_button)
                else:
                    print("Already on 'Vergebene Reaktionen' tab.")
    
                # Now parse the updated HTML content
                soup = BeautifulSoup(driver.page_source, 'html.parser')
    
                # Initialize reaction count
                seen_reaction = set()
                reactions_count = 0
                search = True
    
                while search == True:
                    # Find all reactions currently loaded on the page
                    reactions = driver.find_elements(By.CSS_SELECTOR, "li > div.box48")
            
                    # Check each reaction
                    for reaction in reactions:
                        # Skip if not an actual "reaction"
                        info_text = reaction.find_element(By.CSS_SELECTOR, ".containerHeadline > div").text
                        if "reagiert" not in info_text:
                            continue
                        # Extract the date from the <time> tag
                        time_tag = reaction.find_element(By.CSS_SELECTOR, "time.datetime")
                        datetime_str = time_tag.get_attribute("datetime")
                
                        if datetime_str in seen_reaction:
                            continue
    
                        # Convert the date to a datetime object for comparison
                        reaction_date = datetime.fromisoformat(datetime_str)
                        
                        # Check if the reaction is in the target month and year
                        if reaction_date.month == target_month and reaction_date.year == target_year:
                            seen_reaction.add(datetime_str)
                            reactions_count += 1
                        # If reactions are older than the target month, stop loading more
                        elif reaction_date.year < target_year or (reaction_date.year == target_year and reaction_date.month < target_month):
                            # We can stop if we've reached older reactions (stop here)
                            search = False
                            print(f"Stopping search - Reached reactions from {reaction_date.strftime('%b %Y')}")
                            break
            
                    # Check if the "Weitere Reaktionen" button is present
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        button = driver.find_element(By.CSS_SELECTOR, "li.likeListMore.showMore > button.small")
                        button.click()
                    except Exception as e:
                        break
    
            except Exception as e:
                print("Failed to click or load 'Vergebene Reaktionen' tab:", e)
                seen_reaction = set()
                soup = BeautifulSoup(driver.page_source, 'html.parser')  # still try to parse what you can
    
        finally:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
    else:
        seen_reaction = set()
    
    reactions_given.append(len(seen_reaction) if seen_reaction else '-')

# Save to file
os.makedirs("raw_data", exist_ok=True)
data = pd.DataFrame({
    'User ID': row["User ID"],
    'User Name': row["User Name new"],
    'Given Reaction': reactions_given
})
data.to_pickle(f"raw_data/{target_month:02d}.{target_year}_RG.pkl")
