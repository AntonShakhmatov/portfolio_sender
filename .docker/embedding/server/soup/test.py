import shutil
import json
import requests
import undetected_chromedriver as uc
import os, re, base64, time
# import form # importing nearest py file-form.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
)


BASE = "https://www.profesia.cz"
LOGIN_URL = f"{BASE}/uchazec/prihlaseni"
PHP = f"{BASE}/prace/praha/?radius=radius30&search_anywhere=php&sort_by=relevance&page_num="
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8,ru;q=0.7",
}

# где лежат pdf (смонтируй shared volume!)
UPLOADS_DIR_ENV = os.getenv("UPLOADS_DIR")  # напр.: /var/www/html/www/uploads
DEFAULT_UPLOADS_DIR = Path("/var/www/html/www/uploads")

DEBUG_DIR = Path("debug_profesia"); DEBUG_DIR.mkdir(exist_ok=True)

remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
opts = Options()
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,900")
# на всякий случай явно укажем браузер
opts.set_capability("browserName", "chrome")

# opts = uc.ChromeOptions()
# opts.add_argument("--no-sandbox")
# opts.add_argument("--disable-dev-shm-usage")
# opts.add_argument("--disable-blink-features=AutomationControlled")
# opts.add_experimental_option("excludeSwitches", ["enable-automation"])
# opts.add_experimental_option("useAutomationExtension", False)


def txt(el):
    return el.get_text(strip=True) if el else ""

def safe_name_from_url(u: str, idx: int) -> str:
    p = urlparse(u)
    tail = (p.path or "/").rstrip("/").split("/")[-1] or "index"
    tail = re.sub(r"[^A-Za-z0-9._-]+", "_", tail)
    return f"{idx:03d}_{tail or 'page'}"

driver = webdriver.Remote(command_executor=remote_url, options=opts)

# driver = uc.Chrome(
#     options=opts,
#     browser_executable_path="/usr/bin/chromium",  # поменяйте на свой путь
#     headless=False,   # для отладки лучше с окном
# )
wait = WebDriverWait(driver, 20)

try:
    time.sleep(5)
    driver.get(LOGIN_URL)

    def js_events(el):
        driver.execute_script("""
        const el = arguments[0];
        el.dispatchEvent(new Event('input',  {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        """, el)

    def highlight(el, on=True):
        driver.execute_script("arguments[0].style.outline = arguments[1];",
                            el, "3px solid #ff9800" if on else "")

    def fire_events(el):
        driver.execute_script("""
            const el = arguments[0];
            el.dispatchEvent(new Event('input',  {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
        """, el)
    
    def type_slow(el, text, delay=0.06, clear=True):
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()
        if clear:
            try:
                el.clear()
            except Exception:
                el.send_keys(Keys.CONTROL, "a"); el.send_keys(Keys.DELETE)
        highlight(el, True)
        for ch in text:
            el.send_keys(ch)
            time.sleep(delay)
        highlight(el, False)
        fire_events(el)

    def fill(by, selector, value, clear=True):
        try:
            el = wait.until(EC.presence_of_element_located((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            if clear:
                try:
                    el.clear()
                except Exception:
                    el.send_keys(Keys.CONTROL, "a"); el.send_keys(Keys.DELETE)
            js_events(el)
            type_slow(el, value, delay=0.08, clear=clear)
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
        
    el = fill(By.ID, "user-email", "xshakhmatov@gmail.com")            
    if el:
        # 1) сохранить HTML только этого поля
        name = safe_name_from_url(driver.current_url, 1) + "_2nd"
        Path("pages/html2").mkdir(parents=True, exist_ok=True)
        el_html_path = f"pages/html2/{name}_firstname_el.html"
        with open(el_html_path, "w", encoding="utf-8") as f:
            f.write(el.get_attribute("outerHTML"))
        val_path = f"pages/html2/{name}_firstname_value.txt"
        with open(val_path, "w", encoding="utf-8") as f:
            f.write(el.get_attribute("value") or "")
        driver.set_window_size(1400, 900)
        # driver.get(el_html_path)
    else:
        print("[warn] Поле #user-email не найдено")
    
    def highlight(driver, el, on=True):
        try:
            driver.execute_script(
                "arguments[0].style.outline = arguments[1];",
                el,
                "2px solid magenta" if on else ""
            )
        except Exception:
            pass

    def find_and_click(by, value, timeout=20, js_fallback=True, center=True):
        """
        Ищет элемент по (by, value) и кликает. Возвращает True/False.
        Пример вызова:
            find_and_click(By.XPATH, "//button[contains(., 'pokračovat')]")
            find_and_click(By.CSS_SELECTOR, ".MuiButtonBase-root.MuiButton-root.button-block")
        """
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            if center:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

            highlight(driver, el, True)
            try:
                el.click()
            except ElementClickInterceptedException:
                if js_fallback:
                    driver.execute_script("arguments[0].click();", el)
                else:
                    raise
            finally:
                highlight(driver, el, False)
                # time.sleep(15)
            return True

        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"[skip] не нашли/не кликнули по локатору ({by}, {value}): {e}")
            return False
        
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )

    time.sleep(2)

    el = fill(By.ID, "user-password", "1195286F")
    if el:
        # 1) сохранить HTML только этого поля
        password = safe_name_from_url(driver.current_url, 1) + "_2nd"
        Path("pages/html2").mkdir(parents=True, exist_ok=True)
        el_html_path = f"pages/html2/{name}_password_el.html"
        with open(el_html_path, "w", encoding="utf-8") as f:
            f.write(el.get_attribute("outerHTML"))
        val_path = f"pages/html2/{name}_password_value.txt"
        with open(val_path, "w", encoding="utf-8") as f:
            f.write(el.get_attribute("value") or "")
        driver.set_window_size(1400, 900)
        # time.sleep(15)
    else:
        print("[warn] Поле #user-password не найдено")

    time.sleep(3)

    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    time.sleep(6)
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    time.sleep(3)
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    time.sleep(3)
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    time.sleep(1)
    find_and_click(
        By.XPATH,
        "//form//button[@type='submit' and not(@aria-disabled='true')][.//text()[normalize-space()='Pokračovat']]"
    )
    time.sleep(25)

    # def click_until_navigated(
    #     by, locator,
    #     pause=5,              # пауза между попытками (сериями кликов)
    #     timeout=1300,         # общий лимит
    #     per_try_wait=5,       # ожидание навигации после серии кликов
    #     success_pred=None,    # функция-признак следующей страницы
    #     clicks_per_try=5,     # СКОЛЬКО кликов сделать в одной попытке
    #     inter_click_pause=0.2,# пауза между кликами в серии
    #     quick_check=0.8,      # короткое ожидание перехода после каждого клика
    #     per_click_wait=2      # сколько ждать кликабельность на каждый клик
    # ):
    #     import time
    #     t0 = time.time()
    #     while True:
    #         start_url = driver.current_url

    #         # серия из N кликов
    #         for i in range(clicks_per_try):
    #             # пробуем кликнуть (быстро)
    #             find_and_click(by, locator, timeout=per_click_wait, js_fallback=True, center=True)

    #             # после каждого клика — короткая проверка «а вдруг уже ушли»
    #             try:
    #                 WebDriverWait(driver, quick_check).until(
    #                     lambda d: d.current_url != start_url or (success_pred(d) if success_pred else False)
    #                 )
    #                 return True
    #             except TimeoutException:
    #                 pass

    #             time.sleep(inter_click_pause)

    #         # если серия не дала перехода — подождём подольше результат серии
    #         try:
    #             WebDriverWait(driver, per_try_wait).until(
    #                 lambda d: d.current_url != start_url or (success_pred(d) if success_pred else False)
    #             )
    #             return True
    #         except TimeoutException:
    #             pass

    #         # общий таймаут
    #         if time.time() - t0 > timeout:
    #             return False

    #         time.sleep(pause)

    # # --- использование под «Pokračovat» ---

    # POKRA = "//form//button[@type='submit' and not(@aria-disabled='true')][normalize-space()='Pokračovat']"

    # def next_page_ready(drv):
    #     return bool(drv.find_elements(
    #         By.XPATH,
    #         "//label[normalize-space()='Pozice']/following::input[1] | "
    #         "//input[@placeholder='Pozice' or @aria-label='Pozice' or @name='position'] | "
    #         "//form//button[@type='submit' and normalize-space()='Vyhledat']"
    #     ))

    # ok = click_until_navigated(
    #     By.XPATH, POKRA,
    #     pause=5,
    #     timeout=1300,
    #     per_try_wait=5,
    #     success_pred=next_page_ready,
    #     clicks_per_try=5,        # 5 кликов за попытку
    #     inter_click_pause=0.2,   # короткая пауза между кликами
    #     quick_check=0.8,         # быстрый чек после каждого
    #     per_click_wait=2         # не тратить много времени на каждый клик
    # )

    # def nav_js(url):
    #     driver.execute_script("window.location.href = arguments[0];", url)

    # if not ok:
    #     print("Не удалось перейти на следующую страницу после «Pokračovat»")
    # else:
    #     nav_js(f"{PHP}1")
    # time.sleep(15)

    # result = []
    # # проход по страницам с вакансиями
    # for page in range(1, 2):
    #     url = f"{PHP}{page}"
    #     driver.get(url)
    #     wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    #     time.sleep(2)
    #     name = safe_name_from_url(driver.current_url, page)
    #     html_path = f"pages/html2/{name}.html"
    #     Path("pages/html2").mkdir(parents=True, exist_ok=True)
    #     with open(html_path, "w", encoding="utf-8") as f:
    #         f.write(driver.page_source)

    #     soup = BeautifulSoup(driver.page_source, "html.parser")
    #     items = soup.select(".job-offer-item")
    #     print(f"[{page}] {len(items)} items on {url}")
    #     for i, item in enumerate(items, start=1):
    #         title_el = item.select_one("a.offer-company-logo-link")
    #         company_el = item.select_one(".employer")
    #         location_el = item.select_one(".job-location")
    #         detail_url = urljoin(BASE, title_el["href"]) if title_el else None
    #         result.append({
    #             "title": txt(title_el),
    #             "company": txt(company_el),
    #             "location": txt(location_el),
    #             "detail_url": detail_url,
    #         })
    # time.sleep(5)
    
    # try:
    #     for i, item in enumerate(result,1):
    #         if not item["detail_url"]:
    #             continue
    #         driver.get(item["detail_url"])
    #         wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    #         item["detail_url"] = driver.current_url
    #         time.sleep(2)

    #         try:
    #             second_link = wait.until(
    #                 EC.element_to_be_clickable((By.CSS_SELECTOR, "div.text-center a[href]"))
    #             )

    #             second_href = second_link.get_attribute("href")
    #             if not second_href.startswith("http"):
    #                 second_href = urljoin(BASE, second_href)
    #             prev = driver.current_url
    #             driver.get(second_href)
    #             wait.until(EC.url_changes(prev))
    #             wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    #             item["second_url"] = driver.current_url
    #             print(f"[{i}] OK: {item['detail_url']} -> {item['second_url']}")
    #         except Exception:
    #             item["second_url"] = None
    #             print(f"[{i}] Нет второй ссылки. Не унывайте, пацаны {item['detail_url']}")
    # finally:
    #     driver.quit()
finally:
    driver.quit()
