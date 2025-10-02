# selkit_refactored.py
import os, re, time
from dataclasses import dataclass
from selenium import webdriver
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
)
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException

# ---- Заголовки по умолчанию
HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome  /58.0.3029.110 Safari/537.3",
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8,ru;q=0.7",
}   

remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
opts = Options()
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,900")
opts.set_capability("browserName", "chrome")

def txt(el):
    return el.get_text(strip=True) if el else ""

def safe_name_from_url(u: str, idx: int) -> str:
    p = urlparse(u)
    tail = (p.path or "/").rstrip("/").split("/")[-1] or "index"
    tail = re.sub(r"[^A-Za-z0-9._-]+", "_", tail)
    return f"{idx:03d}_{tail or 'page'}"

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
        # el.send_keys(value)
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

            highlight(el, True)
            try:
                el.click()
            except ElementClickInterceptedException:
                if js_fallback:
                    driver.execute_script("arguments[0].click();", el)
                else:
                    raise
            finally:
                highlight(el, False)
                # time.sleep(15)
            return True

        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"[skip] не нашли/не кликнули по локатору ({by}, {value}): {e}")
            return False
    

driver = webdriver.Remote(command_executor=remote_url, options=opts)
driver.implicitly_wait(10)

wait = WebDriverWait(driver, 25)