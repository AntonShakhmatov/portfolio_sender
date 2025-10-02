import json
import requests
import os, re, base64, time
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox") # важно для Docker
opts.add_argument("--disable-dev-shm-usage") # важно для Docker

opts.binary_location = "/usr/bin/chromium"

driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 20)

try:
    def fill_if_present(by, selector, value, *, clear=True):
        try:
            el = wait.until(EC.presence_of_element_located((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            if clear:
                try:
                    el.clear()
                except() /Exception:
                    el.send_keys(Keys.CONTROL + "a")
                    el.send_keys(Keys.DELETE)
            el.send_keys(value)
            return True
        except Exception:
            return False

    def click_if_present(by, selector):
        try:
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            return True
        except Exception:
            return False

    # ==== ЗАПОЛНЯЕМ ФОРМУ ====
    # Имя / Фамилия / Email / Телефон / Комментарий
    ok = fill_if_present(By.ID, "job_post_reply_firstname",  "Ivan")
    print("firstname:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_lastname",   "Ivanov")
    print("lastname:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_email",      "ivan@example.com")
    print("email:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_phone",      "+420 700 000 000")
    print("telefone:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_comment",    "Dobrý den, mám zájem o pozici. Přikládám CV.")
    print("text:", ok)

    # Ссылки: сопроводительное, CV, LinkedIn, личный сайт
    ok = fill_if_present(By.ID, "job_post_reply_coverletterlink", "https://pastebin.com/raw/....")
    print("coverlink:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_resumelink",      "https://example.com/cv.pdf")
    print("resumelink:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_linkedinlink",    "https://www.linkedin.com/in/ivany")
    print("linkedin:", ok)
    ok = fill_if_present(By.ID, "job_post_reply_personalweblink", "https://ivany.dev")
    print("personalweb:", ok)

    el = driver.find_element(By.ID, "job_post_reply_firstname")
    print("firstname value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "Ivan"

    el = driver.find_element(By.ID, "job_post_reply_lastname")
    print("lastname value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "Ivanov"

    el = driver.find_element(By.ID, "job_post_reply_email")
    print("email value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "ivan@example.com"

    el = driver.find_element(By.ID, "job_post_reply_phone")
    print("phone value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "+420 700 000 000"

    el = driver.find_element(By.ID, "job_post_reply_comment")
    print("text value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "Dobrý den, mám zájem o pozici. Přikládám CV."

    el = driver.find_element(By.ID, "job_post_reply_coverletterlink")
    print("coverletterlink value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "https://pastebin.com/raw/...."

    el = driver.find_element(By.ID, "job_post_reply_resumelink")
    print("resumelink value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "https://example.com/cv.pdf"

    el = driver.find_element(By.ID, "job_post_reply_linkedinlink")
    print("linkedinlink value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "https://www.linkedin.com/in/ivany"

    el = driver.find_element(By.ID, "job_post_reply_personalweblink")
    print("personalweblink value:", el.get_attribute("value"))
    assert el.get_attribute("value") == "https://ivany.dev"


    recaptcha = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".g-recaptcha")))
    sitekey = recaptcha.get_attribute("data-sitekey")

    print(f"[{i}] Перешли на вторую: {driver.current_url} (OK)")
except Exception as e:
    print(f"[{i}] Нет второй ссылки или ошибка перехода: {e}")

    # Если есть input[type=file] для загрузки файла (лучше, чем линк):
    # Укажи АБСОЛЮТНЫЙ путь внутри контейнера!
    try:
        UPLOADS_DIR = Path(__file__).resolve().parents[4] / "www" / "uploads"   # /var/www/html/www/uploads
        pdfs = sorted(UPLOADS_DIR.glob("*.pdf"))  # список Path
        if not pdfs:
            raise FileNotFoundError(f"Нет PDF в {UPLOADS_DIR}")

        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']#job_post_reply_resume")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
        file_input.send_keys(str(pdfs[0].resolve()))
    except Exception:
        pass

    # Чекбокс согласия
    try:
        consent = driver.find_element(By.ID, "job_post_reply_consent")
        if not consent.is_selected():
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", consent)
            consent.click()
    except Exception:
        # иногда клик надо делать по label:
        click_if_present(By.CSS_SELECTOR, "label[for='job_post_reply_consent']")

    # Captcha
    driverCaptcha = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    wait = WebDriverWait(driverCaptcha, 20)

    captcha_page_url = "https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php"
    driverCaptcha.get(captcha_page_url)

    solver = TwoCaptcha("5638079e4c935415104aa5e5e52d1925")
    response = solver.recaptcha(sitekey="{sitekey}", url=captcha_page_url)
    code = response['code']

    recaptcha_response_element = driverCaptcha.find_element(By.ID, 'g-recaptcha-response')
    driverCaptcha.execute_script(f'arguments[0].value = "{code}";', recaptcha_response_element)

    # Submit the form
    submit_btn = driverCaptcha.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_btn.click()

    # Pause the execution so you can see the screen after submission before closing the driver
    input("Press enter to continue")
    driverCaptcha.close()

    # Сабмит формы
    # Вариант 1: клик по кнопке
    if not click_if_present(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"):
        # Вариант 2: submit у формы
        try:
            form = driver.find_element(By.CSS_SELECTOR, "form")
            driver.execute_script("arguments[0].submit();", form)
        except Exception:
            pass

    # Подтверждаем, что отправка прошла (подбери селектор успеха или смену URL)
    try:
        prev = driver.current_url
        # Если при сабмите меняется URL:
        wait.until(EC.url_changes(prev))
    except Exception:
        # Или подождать появление сообщения об успехе
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success, .flash-success, .success")))
        except Exception:
            pass
    time.sleep(0.2)  # лёгкий троттлинг, чтоб не долбить сайт
finally:
    driver.quit()
