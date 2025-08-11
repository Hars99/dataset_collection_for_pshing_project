import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ==== CONFIG ====
PHISH_LIMIT = 100   # number of phishing sites to fetch
LEGIT_LIMIT = 100   # number of legit sites to fetch
OUTPUT_DIR = "dataset"

os.makedirs(f"{OUTPUT_DIR}/phishing", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/legit", exist_ok=True)

labels_file = os.path.join(OUTPUT_DIR, "labels.csv")

# ==== CHROME OPTIONS ====
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

# ==== FETCH PHISHING URLS ====
print("[*] Fetching phishing URLs...")
phish_data = requests.get("https://data.phishtank.com/data/online-valid.json").json()
phish_urls = [entry["url"] for entry in phish_data[:PHISH_LIMIT]]

# ==== FETCH LEGIT URLS ====
print("[*] Fetching legit URLs...")
tranco_csv = requests.get("https://tranco-list.eu/top-1m.csv").text.splitlines()
legit_urls = []
for row in csv.reader(tranco_csv):
    legit_urls.append("https://" + row[1])
    if len(legit_urls) >= LEGIT_LIMIT:
        break

# ==== SCREENSHOT FUNCTION ====
def capture(url, folder, label):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        time.sleep(2)
        
        # Save screenshot
        filename_base = url.replace("https://","").replace("http://","").replace("/", "_")
        screenshot_path = os.path.join(folder, f"{filename_base}.png")
        driver.save_screenshot(screenshot_path)
        
        # Save HTML
        html_path = os.path.join(folder, f"{filename_base}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Save to labels
        with open(labels_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([url, label])
        
        driver.quit()
        print(f"✅ {url}")
    except Exception as e:
        print(f"❌ {url} - {e}")

# ==== INIT LABELS FILE ====
with open(labels_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["url", "label"])  # label: 1 = phishing, 0 = legit

# ==== RUN PHISHING CAPTURE ====
for url in phish_urls:
    capture(url, f"{OUTPUT_DIR}/phishing", 1)

# ==== RUN LEGIT CAPTURE ====
for url in legit_urls:
    capture(url, f"{OUTPUT_DIR}/legit", 0)

print("[*] Dataset collection complete!")
