import shutil
import json
import requests
import undetected_chromedriver as uc
import os, re, base64, time
# import form # importing nearest py file-form.
from bs4 import BeautifulSoup
from selkit import *
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
)

BASE = "https://pracezarohem.cz"


try:
    time.sleep(5)
    driver.get(BASE)
    el = wait.until(EC.element_to_be_clickable((By.ID, "professions")))
    el.click()
    time.sleep(2)

    el = fill(By.CSS_SELECTOR, "input#professions", "PHP")    
    driver.switch_to.active_element.send_keys(Keys.ARROW_DOWN)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    if el:
        print("professions filled")
    else:
        print("[warn] Поле #professions не найдено")

    time.sleep(3)

    try:
        find_and_click(
            By.XPATH,
            "/html/body/div[1]/div/header/div[2]/div/div/div/form/div/button",
        )
    except Exception as e:
        print("[warn] Не удалось кликнуть по кнопке 'NABÍDEK':", e)
    time.sleep(10)

    # Praha, okres Praha, Praha
    el = fill(By.CSS_SELECTOR, "input#location", "Praha")  
    time.sleep(2)
    # driver.switch_to.active_element.send_keys(Keys.ARROW_DOWN)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    if el:
        print("location filled")
    else:
        print("[warn] Поле #location не найдено")

    time.sleep(3)

    driver.switch_to.active_element.send_keys(Keys.ESCAPE)

    try:
        find_and_click(
            By.XPATH,
            "/html/body/div[1]/div/header/div[2]/div/div/div/form/div/button",
        )
    except Exception as e:
        print("[warn] Не удалось кликнуть по кнопке 'NABÍDEK':", e)
    time.sleep(5)
    

    results_url = driver.current_url

    def get_job_hrefs(limit=None):
        """
        Собирает href'ы вакансий со страницы результатов.
        limit: если нужно ограничить количество на прогон.
        """
        # кликабельный <a>, внутри которого H2 с нужными классами
        links = driver.find_elements(By.CSS_SELECTOR, "a:has(h2.typography-heading-small-text.mb-3)")
        hrefs = []
        seen = set()
        for a in links:
            try:
                href = a.get_attribute("href")
                if href and href not in seen:
                    hrefs.append(href)
                    seen.add(href)
            except StaleElementReferenceException:
                continue
            if limit and len(hrefs) >= limit:
                break
        return hrefs

    def wait_thanks_or_timeout(timeout=12):
        try:
            WebDriverWait(driver, timeout).until(EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Děkujeme') or contains(., 'Dekuji') or contains(., 'Odesláno') or contains(., 'děkujeme')]")),
                EC.url_matches(r".*(dekuji|thank|success|odeslano).*")
            ))
        except TimeoutException:
            pass

    # --- вспомогательные функции для отклика (твои, слегка уплотнил) ---
    def make_visible(el):
        driver.execute_script("""
            const el = arguments[0];
            el.style.visibility='visible';
            el.style.display='block';
            el.style.opacity='1';
            el.style.width='1px';
            el.style.height='1px';
            el.style.position='fixed';
            el.style.left='0';
            el.style.top='0';
            el.style.zIndex='2147483647';
            el.removeAttribute('hidden');
            el.removeAttribute('disabled');
        """, el)

    def find_uploads_dir() -> Path | None:
        tried = []
        env = os.getenv("UPLOADS_DIR")
        if env:
            p = Path(env).expanduser(); tried.append(p)
            if p.exists(): print("[uploads] using env:", p); return p.resolve()
        for cand in [Path("../shared/uploads"), Path("www/uploads"), Path("/app/shared/uploads")]:
            tried.append(cand)
            if cand.exists(): print("[uploads] using:", cand.resolve()); return cand.resolve()
        print("[uploads] tried:", [str(x) for x in tried]); return None

    def all_file_inputs():
        # основной документ
        for el in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
            yield (None, el)
        # ифреймы
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for fr in frames:
            try:
                driver.switch_to.frame(fr)
                for el in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                    yield (fr, el)
            except Exception:
                pass
            finally:
                driver.switch_to.default_content()

    def attach_file(pattern="*.pdf") -> bool:
        uploads_dir = find_uploads_dir()
        if not uploads_dir:
            print("[skip] uploads dir not found"); return False
        files = sorted(uploads_dir.glob(pattern))
        if not files:
            print(f"[skip] no files matching {pattern} in {uploads_dir}"); return False
        file_path = str(files[0].resolve())
        print("Прикрепляем:", file_path)

        # не обязательно, но помогаем скроллом в зону
        try:
            dz = driver.find_element(By.CSS_SELECTOR, ".FileUploaderInput__dropZone, [class*='dropZone'], [data-testid*='drop']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dz)
        except Exception:
            pass

        # приоритетные селекторы
        preferred = [
            "input[type='file']#fileUploaderInput",
            "input[type='file'][name='attachments']",
            "input[type='file'][name*='attachment']",
            "input[type='file'][accept*='pdf']",
        ]
        file_inputs = []
        for sel in preferred:
            file_inputs.extend(driver.find_elements(By.CSS_SELECTOR, sel))
        if not file_inputs:
            for fr, el in all_file_inputs():
                file_inputs.append((fr, el))
        else:
            file_inputs = [(None, el) for el in file_inputs]

        if not file_inputs:
            print("[skip] file input not found anywhere"); return False

        for fr, el in file_inputs:
            try:
                if fr is not None:
                    driver.switch_to.frame(fr)
                make_visible(el)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.send_keys(file_path)  # ключевой шаг — БЕЗ кликов
                driver.execute_script("""
                    const el = arguments[0];
                    el.dispatchEvent(new Event('input',  {bubbles:true}));
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                """, el)
                val = el.get_attribute("value") or ""
                if val:
                    print("file_input.value:", val)
                    if fr is not None:
                        driver.switch_to.default_content()
                    return True
            except Exception as e:
                if fr is not None:
                    driver.switch_to.default_content()
                print("[try next input] reason:", type(e).__name__, str(e)[:160])
        return False

    # --- 2) отклик на конкретную вакансию в новой вкладке ---
    def complete_proposal(href):
        # открыть в новой вкладке
        driver.execute_script("window.open(arguments[0], '_blank');", href)
        driver.switch_to.window(driver.window_handles[-1])

        # кнопка «Odpovědět na nabídku»
        try:
            find_and_click(By.XPATH, "//a[contains(., 'Odpovědět na nabídku') or contains(., 'Odpovedět') or contains(., 'Odpovědět')]")
        except Exception as e:
            print("[warn] Кнопка отклика не найдена:", e)

        time.sleep(2)

        # загрузка файла
        ok = attach_file("*.pdf")
        print("upload ok?", ok)

        # заполнение формы
        try:
            el = fill(By.CSS_SELECTOR, "textarea", "Ahoj, mám zájem o tuto pozici. Děkuji.")
            print("textarea filled" if el else "[warn] textarea not found")

            el = fill(By.CSS_SELECTOR, "input#name", "Anton");      print("name filled" if el else "[warn] #name not found")
            el = fill(By.CSS_SELECTOR, "input#surname", "Shakhmatov"); print("surname filled" if el else "[warn] #surname not found")

            el = fill(By.CSS_SELECTOR, "select#prefix", "+420")
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            print("prefix filled" if el else "[warn] #prefix not found")

            el = fill(By.CSS_SELECTOR, "input#phone", "773694287"); print("phone filled" if el else "[warn] #phone not found")
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            driver.switch_to.active_element.send_keys(Keys.BACKSPACE)
            el = fill(By.CSS_SELECTOR, "input#email", "xshakhmatov@gmail.com"); print("email filled" if el else "[warn] #email not found")

            # отметить все чекбоксы согласий (если их несколько)
            for cb in driver.find_elements(By.CSS_SELECTOR, "input.CheckboxField__input"):
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
                    if not cb.is_selected():
                        driver.execute_script("arguments[0].click();", cb)
                except Exception:
                    pass

            # отправка формы
            # sent = False
            # for xp in [
            #     "//button[not(@disabled) and (contains(., 'Odeslat') or contains(., 'Odpovědět'))]",
            #     "//input[@type='submit' and not(@disabled)]",
            #     "//button[@type='submit' and not(@disabled)]"
            # ]:
            #     try:
            #         btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xp)))
            #         driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            #         driver.execute_script("arguments[0].click();", btn)
            #         sent = True
            #         break
            #     except Exception:
            #         continue
            # print("form sent clicked?" , sent)

            # wait_thanks_or_timeout(12)

        except Exception as e:
            print("[warn] заполнение/отправка формы:", e)

        # закрыть вкладку и вернуться к результатам
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # убедиться, что список на месте (или восстановить по URL)
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a:has(h2.typography-heading-small-text.mb-3)"))
            )
        except TimeoutException:
            driver.get(results_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a:has(h2.typography-heading-small-text.mb-3)"))
            )

    # --- 3) основной прогон по вакансиям на странице ---
    job_hrefs = get_job_hrefs(limit=None)  # например limit=5, чтобы не улететь по всем
    print("found jobs:", len(job_hrefs))

    processed = []
    for href in job_hrefs:
        try:
            complete_proposal(href)
            processed.append(href)
            # небольшая пауза между откликами, чтоб не выглядеть как бот
            time.sleep(2)
        except Exception as e:
            print("[warn] ошибка на вакансии:", href, e)
            # вернуться на список, если выбило
            try:
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                driver.get(results_url)

    print("processed:", len(processed))

    time.sleep(9)
finally:
    driver.quit()