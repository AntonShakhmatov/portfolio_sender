import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

BASE = "https://prace.cz/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8,ru;q=0.7",
}

def txt(el):
    return el.get_text(strip=True) if el else ""

results = []

url = f"https://www.pracezarohem.cz/nabidky/@50.064570475009,14.442584331308?keywords=Program%C3%A1tor&sort=distance"
resp = requests.get(url, headers=HEADERS, timeout=20)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

for div in soup.find_all("div", class_="pl-md-0 pr-md-0 col"):
    title = div.select_one("h2")
    address = div.select_one("p.typography-body-undefined-text-regular.mb-2.advert-address")
    far_away = div.select_one("p.typography-body-undefined-text-regular.mb-0")
    condition = div.select_one("p.typography-body-undefined-text-regular.mb-0.advert-age-group")

    results.append({
        'title': txt(title),
        'address': txt(address),
        'far_away': txt(far_away),
        'condition': txt(condition)
    })

# Selenium
opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox") # важно в Docker
opts.add_argument("--disable-dev-shm-usage") # важно в Docker

driver = webdriver.Crome(options=opts)
wait = WebDriverWait(driver, 20)

try:
    for i, item in enumerate(results, 1):
        driver.get(item["url"])
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        item["landed_url"] = driver.current_url
        item["page_title"] = driver.title
        item["snippet"] = driver.find_element(By.TAG_NAME, "body").text[:500].replace("\n", " ")
        print(f"[{i}] {item['title']!r} -> {item['landed_url']}")
finally:
    driver.quit()

out_path = "pracezarohem.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Сохранено {len(results)} записей в {out_path}")
        
