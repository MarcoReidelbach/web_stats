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
from datetime import datetime
import pytz

# Get login info from environment variables
username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")

# Get today's date in German time
berlin = pytz.timezone('Europe/Berlin')
query_day = datetime.now(berlin).strftime('%d.%m.%Y')

# Instantiate options
opts = Options()
opts.add_argument("--headless")  # Run headless on GitHub Actions
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

# Set the location of the webdriver
service = Service("/usr/bin/chromedriver")

# Instantiate a webdriver
driver = webdriver.Chrome(options=opts, service=service)

# Load the HTML page
driver.get("https://www.moonsault.de/login")
time.sleep(10)

# Accept cookies if banner appears
try:
    driver.find_element("id", "cmpwelcomebtnyes").click()
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

# Get Number of Pages
pages = int(re.search('data-pages="(.+?)"', str(soup.find("nav", {"class": "pagination"}))).group(1))

# Initialize lists
usr_name, usr_id, post_no, reac_no, troph_no = [], [], [], [], []

# Scrape user data
for page_no in range(pages):
    page = f"https://www.moonsault.de/members-list/?pageNo={page_no+1}&sortField=activityPoints&sortOrder=DESC"
    driver.get(page)
    soup = BeautifulSoup(driver.page_source)
    plain = [str(e) for e in soup.find_all("dl", {"class": "plain inlineDataList small"})]
    for entry in plain:
        # Username and ID
        usr_name.append(re.search('aria-label="Beiträge von (.+?)"', entry).group(1) if re.search('aria-label="Beiträge von (.+?)"', entry) else 'Not Defined')
        usr_id.append(re.search('data-user-id="(.+?)"', entry).group(1) if re.search('data-user-id="(.+?)"', entry) else 'Not Defined')

        # Posts
        post_opt_a = re.search('Beiträge</a></dt>\n<dd>(.+?)</dd>', entry)
        post_opt_b = re.search('Beiträge</dt>\n<dd>(.+?)</dd>', entry)
        a = int(post_opt_a.group(1).replace('.', '')) if post_opt_a else 0
        b = int(post_opt_b.group(1).replace('.', '')) if post_opt_b else 0
        post_no.append(str(max(a, b)))

        # Reactions
        reac_opt_a = re.search('Reaktionen</a></dt>\n<dd>(.+?)</dd>', entry)
        reac_opt_b = re.search('Reaktionen</dt>\n<dd>(.+?)</dd>', entry)
        a = int(reac_opt_a.group(1).replace('.', '')) if reac_opt_a else 0
        b = int(reac_opt_b.group(1).replace('.', '')) if reac_opt_b else 0
        reac_no.append(str(max(a, b)))

        # Trophies
        troph_opt_a = re.search('Trophäen</a></dt>\n<dd>(.+?)</dd>', entry)
        troph_opt_b = re.search('Trophäen</dt>\n<dd>(.+?)</dd>', entry)
        a = int(troph_opt_a.group(1).replace('.', '')) if troph_opt_a else 0
        b = int(troph_opt_b.group(1).replace('.', '')) if troph_opt_b else 0
        troph_no.append(str(max(a, b)))

# Save to file
os.makedirs("raw_data", exist_ok=True)
data = pd.DataFrame({
    'User ID': usr_id,
    'User Name': usr_name,
    'Number of Posts': post_no,
    'Number of Reactions': reac_no,
    'Number of Trophies': troph_no
})
data.to_pickle(f"raw_data/{query_day}.pkl")

