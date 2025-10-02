import shutil
import json
import requests
import os, re, base64, time
# import form # importing nearest py file-form.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException

BASE = "https://www.jobstack.it"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8,ru;q=0.7",
}


def make_driver():
    remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
    opts = Options()
    # критически важные флаги для Docker
    # opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,1024")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_argument("--disable-software-rasterizer")
    # найдём бинарник chromium
    bin_path = shutil.which("chromium") or shutil.which("chromium-browser")
    assert bin_path, "Chromium не найден в контейнере"
    opts.binary_location = bin_path

    # drv = webdriver.Chrome(options=opts, service=Service())  # Selenium Manager сам подберёт драйвер
    drv = webdriver.Remote(command_executor=remote_url, options=opts)
    return drv

# создаём драйвер и проверяем, что он реально живой
driver = make_driver()
wait = WebDriverWait(driver, 20)

def txt(el):
    return el.get_text(strip=True) if el else ""

def safe_name_from_url(u: str, idx: int) -> str:
    p = urlparse(u)
    tail = (p.path or "/").rstrip("/").split("/")[-1] or "index"
    tail = re.sub(r"[^A-Za-z0-9._-]+", "_", tail)
    return f"{idx:03d}_{tail or 'page'}"

results = []
# BS сбор ссылок и данных о предлагаймой работе
for page in range(1, 4):
    url = f"{BASE}/it-jobs/php-developer/praha?page={page}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for li in soup.find_all("li", class_="jobposts-item"):
        title = li.select_one("h3")
        list = li.select_one("span.custom-profile-label.custom-profile-label--lower.custom-profile-label--with-icon")
        level = li.select_one("span.custom-profile-label.custom-profile-label--primary.custom-profile-label--dotted.custom-profile-label--lower")
        firma = li.select_one("span.icon.icon--cp-building-07-secondary.mr-5")
        address = li.select_one("span.icon.icon--cp-pin-gray")
        salary = li.select_one("span.jobposts-item_salary.icontext")
        link_el  = li.select_one("a[href]")

        href = link_el.get("href") if link_el else None
        abs_url = urljoin(BASE, href) if href else ""

        results.append({
            'title': txt(title),
            'list': txt(list),
            'level': txt(level),
            'firma': txt(firma),
            'address': txt(address),
            'salary': txt(salary),
            "url": abs_url,
            "page": page,
        })

# Запись данных в json файл
out_path = "jobstackit.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Сохранено {len(results)} записей в {out_path}")

# Selenium
os.makedirs("pages/html", exist_ok=True)
os.makedirs("pages/html2", exist_ok=True)
os.makedirs("pages/png", exist_ok=True)

remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
opts = Options()
# opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox") # важно для Docker
opts.add_argument("--disable-dev-shm-usage") # важно для Docker


# opts.binary_location = "/usr/bin/chromium"

# driver = webdriver.Chrome(options=opts)
driver = webdriver.Remote(command_executor=remote_url, options=opts)
wait = WebDriverWait(driver, 20)

try:
    for i, item in enumerate(results, 1):
        if not item["url"]:
            continue
        driver.get(item["url"])

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        item["detail_url"] = driver.current_url

        # Вторая ссылка после перехода
        try:
            second_link = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.text-center.pt-15 a[href]"))
            )
            second_href = second_link.get_attribute("href")
            if not second_href.startswith("https"):
                second_href = urljoin(BASE, second_href)
            prev = driver.current_url
            driver.get(second_href)  # или second_link.click()

            wait.until(EC.url_changes(prev))
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            item["second_url"] = driver.current_url
            print(f"[{i}] OK: {item['detail_url']} -> {item['second_url']}")
        except Exception:
            item["second_url"] = None
            print(f"[{i}] Нет второй ссылки. Не унывайте, пацаны")
        
        try:
            second_url = item.get("second_url")
            if not second_url:
                raise RuntimeError("Ссылка отсутствует, ну ты чо?")

            prev = driver.current_url
            driver.get(second_url)

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # wait.until(EC.url_changes(prev))  # опционально, если точно меняется URL

            # сохраняем HTML второй страницы
            name = safe_name_from_url(driver.current_url, i) + "_2nd"
            html_path = f"pages/html/{name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            item["second_saved_html"] = name

            # 0) (опционально) закрыть куки-баннер, если мешает
            def try_accept_cookies():
                for sel in [
                    "#onetrust-accept-btn-handler",
                    "button[aria-label='Accept all']",
                    ".cookie-accept, .cookies-accept, .cc-allow",
                ]:
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, sel)
                        driver.execute_script("arguments[0].click();", btn)
                        break
                    except Exception:
                        pass

            try_accept_cookies()

            # 1) ждём, пока DOM прогрузится; если формы нет — просто пропустим
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            def js_events(el):
                driver.execute_script("""
                const el = arguments[0];
                el.dispatchEvent(new Event('input',  {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
                """, el)


            def fill(by, selector, value, clear=True):
                try:
                    el = wait.until(EC.presence_of_element_located((by, selector)))
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    if clear:
                        try:
                            el.clear()
                        except Exception:
                            el.send_keys(Keys.CONTROL, "a"); el.send_keys(Keys.DELETE)
                    el.send_keys(value)
                    js_events(el)
                    # верификация
                    actual = el.get_attribute("value") or el.text or ""
                    print(f"{selector} -> {actual!r}")
                    driver.execute_script("""
                    const el = arguments[0];
                    el.dispatchEvent(new Event('input',  {bubbles:true}));
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                    """, el)
                    return el
                except Exception as e:
                    print(f"[skip] нет поля {selector}: {e}")
                    return None

            # 2) если на странице есть reCAPTCHA — просто игнорируем её (не трогаем)
            # (форма часто всё равно доступна; если нет — заполнение просто пропустится)
            # has_captcha = bool(driver.find_elements(By.CSS_SELECTOR, ".g-recaptcha, iframe[src*='recaptcha']"))
            # print("reCAPTCHA:", has_captcha)

            # 3) заполняем поля по твоим id
            # fill(By.ID, "job_post_reply_firstname",  "Ivan")
            el = fill(By.ID, "job_post_reply_firstname", "Ivan")            
            if el:
                # 1) сохранить HTML только этого поля
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path("pages/html2").mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_firstname_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_firstname_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")

                # # 2) при желании — сохранить значение поля
                # val_path = f"pages/html2/{name}_firstname_value.txt"
                # with open(val_path, "w", encoding="utf-8") as f:
                #     f.write(el.get_attribute("value") or "")

                # # 3) или сохранить всю страницу
                # page_html_path = f"pages/html2/{name}_page.html"
                # with open(page_html_path, "w", encoding="utf-8") as f:
                #     f.write(driver.page_source)
            else:
                print("[warn] Поле #job_post_reply_firstname не найдено")

            # fill(By.ID, "job_post_reply_lastname",   "Ivanov")
            el = fill(By.ID, "job_post_reply_lastname", "Ivanov")            
            if el:
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path('pages/html2').mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_lastname_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_lastname_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")


            # fill(By.ID, "job_post_reply_email",      "ivan@example.com")
            el = fill(By.ID, "job_post_reply_email", "ivan@example.com")            
            if el:
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path('pages/html2').mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_email_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_email_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")

            # fill(By.ID, "job_post_reply_phone",      "+420700000000")
            el = fill(By.ID, "job_post_reply_phone", "+420700000000")            
            if el:
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path('pages/html2').mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_phone_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_phone_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")

            # fill(By.ID, "job_post_reply_comment",    "Dobrý den, mám zájem o pozici. Přikládám CV.")
            el = fill(By.ID, "job_post_reply_comment", "Dobrý den, mám zájem o pozici. Přikládám CV.")            
            if el:
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path('pages/html2').mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_reply_comment_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_reply_comment_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")

            el = fill(By.ID, "job_post_reply_personalweblink", "https://github.com/IvanIvanov?tab=repositories")
            if el:
                name = safe_name_from_url(driver.current_url, i) + "_2nd"
                Path('pages/html2').mkdir(parents=True, exist_ok=True)
                el_html_path = f"pages/html2/{name}_github_personalweblink_el.html"
                with open(el_html_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("outerHTML"))
                val_path = f"pages/html2/{name}_reply_comment_value.txt"
                with open(val_path, "w", encoding="utf-8") as f:
                    f.write(el.get_attribute("value") or "")

            try:
                driver.find_element(By.XPATH,
                    ".//*[contains(text(), 'Souhlasím se všeobecnými obchodními podmínkami')]"
                ).click()
                break
            except NoSuchElementException as e:
                print('Retry in 1 second')
                time.sleep(1)
            else:
                raise e

            # 4) прикрепить файл «Vložit průvodní dopis» (НЕ кликаем кнопки, только send_keys на input[type=file])

            def find_uploads_dir() -> Path | None:
                # 1) приоритет — переменная окружения
                env = os.getenv("UPLOADS_DIR")
                if env:
                    p = Path(env).expanduser().resolve()
                    if p.exists():
                        return p

                # 2) ищем вверх по дереву ближайшую папку www/uploads
                here = Path(__file__).resolve()
                for base in [here] + list(here.parents):
                    cand = (base / "www" / "uploads")
                    if cand.exists():
                        return cand.resolve()


                # 3) хардкод на случай стандартного пути в контейнере
                fallback = Path("/var/www/html/www/uploads")
                if fallback.exists():
                    return fallback.resolve()

                return None

            def attach_coverletter():
                try:
                    uploads_dir = find_uploads_dir()
                    if not uploads_dir:
                        print("[skip] не нашли каталог www/uploads (ни вверх по дереву, ни в /var/www/html/www/uploads). " 
                            "Можно задать UPLOADS_DIR=/abs/path/to/uploads")
                        return False

                    pdfs = sorted(uploads_dir.glob("*.pdf"))
                    print("Uploads dir:", uploads_dir, "PDFs:", [p.name for p in pdfs])
                    if not pdfs:
                        print(f"[skip] нет *.pdf в {uploads_dir}")
                        return False

                    file_path = pdfs[0].resolve()
                    print("Прикрепляем:", file_path)

                    # найдём сам <input type="file">
                    selectors = [
                        "input[type='file']#job_post_reply_resumelink",
                        "input[type='file'][name='job_post_reply[resumelink]']",
                        "input[type='file']",
                    ]
                    file_input = None
                    for sel in selectors:
                        try:
                            file_input = driver.find_element(By.CSS_SELECTOR, sel)
                            print("Найден инпут:", sel)
                            break
                        except NoSuchElementException:
                            continue
                    if not file_input:
                        print("[skip] не найден <input type='file'>")
                        return False

                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
                    try:
                        file_input.send_keys(str(file_path))
                    except ElementNotInteractableException:
                        # делаем скрытый инпут видимым и пробуем снова
                        driver.execute_script("""
                            const el = arguments[0];
                            el.style.visibility='visible';
                            el.style.display='block';
                            el.style.opacity='1';
                            el.removeAttribute('hidden');
                            el.removeAttribute('disabled');
                        """, file_input)
                        file_input.send_keys(str(file_path))

                    # триггерим события
                    driver.execute_script("""
                        const el = arguments[0];
                        el.dispatchEvent(new Event('input',  {bubbles:true}));
                        el.dispatchEvent(new Event('change', {bubbles:true}));
                    """, file_input)

                    val = file_input.get_attribute("value") or ""
                    print("file_input.value:", val)
                    return bool(val)
                except Exception as e:
                    import traceback
                    print(f"[skip] файл не прикреплён: {e}")
                    traceback.print_exc()
                    return False
        
            # 5) НИКАКИХ сабмитов и взаимодействий с reCAPTCHA
            # (при желании можно сохранить скрин/HTML для проверки)
            # driver.save_screenshot("debug/filled.png")
            # with open("debug/filled.html","w",encoding="utf-8") as f: f.write(driver.page_source)


            # for div in soup.find_all("div", class_="job_post_reply_firstname"):
            #     name = div.select_one("input#job_post_reply_firstname")
            #     email = div.select_one("input#job_post_reply_email")
            #     lastname = div.select_one("input#job_post_reply_lastname")
            #     phone = div.select_one("input#job_post_reply_phone")
            #     text = div.select_one("textarea#job_post_reply_comment")
            #     input_file = div.select_one("input#job_post_reply_coverletterlink")
            #     cv = div.select_one("input#job_post_reply_resumelink")
            #     linkedin = div.select_one("input#job_post_reply_linkedinlink")
            #     web = div.select_one("input#job_post_reply_personalweblink")
            #     checkbox = div.select_one("input#job_post_reply_consent")

            #     results.append({
            #         'name': txt(name),
            #         'email': txt(email),
            #         'lastname': txt(lastname),
            #         'phone': txt(phone),
            #         'text': txt(text),
            #         'input_file': input_file,
            #         'cv': cv,
            #         'linkedin': txt(linkedin),
            #         'web': txt(web),
            #         'checkbox': checkbox,
            #     })

            # fill_present function
            # fill_present function end    
                
            print(f"[{i}] Перешли на вторую: {driver.current_url} (OK)")
        except Exception as e:
            print(f"[{i}] Нет второй ссылки или ошибка перехода: {e}")

        out_path = "jobstackit2.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # # PNG #Использовать потом для презентации позиции в чат-боте
        png_path = f"pages/png/{name}.png"
        driver.save_screenshot(png_path)
        item["saved_png"] = png_path

        # print(f"[{i}] {item['title']!r} -> {item['landed_url']}  (OK)")
        time.sleep(0.2)  # лёгкий троттлинг, чтоб не долбить сайт
finally:
    driver.quit()
