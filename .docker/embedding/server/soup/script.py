import os
import time
import shutil
import contextlib
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)

# ====== настройки ======
BASE = "https://www.profesia.cz"
LOGIN_URL = f"{BASE}/uchazec/prihlaseni"

EMAIL = os.getenv("GOOGLE_EMAIL", "ivan@example.com")
PASSWORD = os.getenv("GOOGLE_PASSWORD", "Ivan")  # лучше хранить в секретах

# каталог с профилем, чтобы хранить куки/сессии
PROFILE_DIR = Path(os.getenv("CHROME_PROFILE_DIR", "/app/chrome-profile"))

# где лежат pdf (смонтируй shared volume!)
UPLOADS_DIR_ENV = os.getenv("UPLOADS_DIR")  # напр.: /var/www/html/www/uploads
DEFAULT_UPLOADS_DIR = Path("/var/www/html/www/uploads")

DEBUG_DIR = Path("debug_profesia"); DEBUG_DIR.mkdir(exist_ok=True)


# ====== браузер ======
def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")  # на время первой авторизации можно закомментировать
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1440,1200")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    bin_path = shutil.which("chromium") or shutil.which("chromium-browser")
    assert bin_path, "Chromium не найден в контейнере"
    opts.binary_location = bin_path

    return webdriver.Chrome(options=opts, service=Service())


driver = make_driver()
wait = WebDriverWait(driver, 20)


# ====== утилиты ======
def snap(name: str):
    DEBUG_DIR.mkdir(exist_ok=True)
    driver.save_screenshot(str(DEBUG_DIR / f"{name}.png"))
    (DEBUG_DIR / f"{name}.html").write_text(driver.page_source, encoding="utf-8")


def wait_overlays_gone(extra_selectors=()):
    overlays = [
        ".MuiBackdrop-root", ".MuiDialog-root", ".MuiPopover-root",
        ".MuiModal-backdrop", ".loading, .spinner, [aria-busy='true']",
        "#onetrust-accept-btn-handler",
    ] + list(extra_selectors)
    for css in overlays:
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css)))
        except Exception:
            pass


def try_accept_cookies():
    for sel in [
        "#onetrust-accept-btn-handler",
        "button[aria-label='Accept all']",
        ".cookie-accept, .cookies-accept, .cc-allow"
    ]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
            return True
        except Exception:
            pass
    return False


def click_strong(el, *, try_js=True):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.1)
    wait_overlays_gone()

    try:
        ActionChains(driver).move_to_element(el).pause(0.05).click().perform()
        return True
    except ElementClickInterceptedException:
        rect = driver.execute_script("""
            const r = arguments[0].getBoundingClientRect();
            return {x: Math.floor(r.left + r.width/2), y: Math.floor(r.top + r.height/2)};
        """, el)
        over = driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);",
                                     rect["x"], rect["y"])
        try:
            oh = driver.execute_script("return arguments[0] && arguments[0].outerHTML;", over) or ""
        except Exception:
            oh = ""
        print(f"[diag] intercepted by: {oh[:200]}")
        if try_js:
            driver.execute_script("arguments[0].click();", el)
            return True
        raise


def switch_to_google_context(timeout=10):
    """Переключиться на новое окно/вкладку или iframe с accounts.google.*"""
    end = time.time() + timeout
    orig = set(driver.window_handles)
    # окно
    while time.time() < end:
        cur = set(driver.window_handles)
        new = list(cur - orig)
        if new:
            driver.switch_to.window(new[0])
            return "window"
        time.sleep(0.2)
    # iframe
    with contextlib.suppress(Exception):
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src,'accounts.google.')]"))
        )
        driver.switch_to.frame(iframe)
        return "frame"
    return None


def resolve_uploads_dir() -> Path:
    if UPLOADS_DIR_ENV:
        p = Path(UPLOADS_DIR_ENV).expanduser().resolve()
        if p.exists():
            return p
    if DEFAULT_UPLOADS_DIR.exists():
        return DEFAULT_UPLOADS_DIR.resolve()
    raise FileNotFoundError(
        "Каталог с PDF не найден. Смонтируй общий том и/или задай "
        "UPLOADS_DIR=/var/www/html/www/uploads"
    )


def attach_portfolio_pdf():
    """Открыть зону CV и прикрепить первый pdf."""
    # твой xpath на «раскрыть/добавить файл»
    open_zone = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//*[@id='job-application-form-cv-section']/div/div[2]/div/div/div/"
        "div[1]/div/div[2]/div/div[2]/div/div/div[1]/p[1]/a"
    )))
    click_strong(open_zone)

    # найти file input в секции CV
    file_input = None
    for css in [
        "#job-application-form-cv-section input[type='file']#job_post_reply_coverletterlink",
        "#job-application-form-cv-section input[type='file']#job_post_reply_resume",
        "#job-application-form-cv-section input[type='file'][name='job_post_reply[coverletterlink]']",
        "#job-application-form-cv-section input[type='file']",
    ]:
        try:
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
            break
        except TimeoutException:
            continue
    if not file_input:
        raise NoSuchElementException("Не найден <input type='file'> (проверь разметку/селектор).")

    uploads = resolve_uploads_dir()
    pdfs = sorted(uploads.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"В {uploads} нет *.pdf")
    file_path = str(pdfs[0].resolve())
    print("Прикрепляем:", file_path)

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
    try:
        file_input.send_keys(file_path)
    except ElementNotInteractableException:
        driver.execute_script("""
            const el = arguments[0];
            el.style.visibility='visible';
            el.style.display='block';
            el.style.opacity='1';
            el.removeAttribute('hidden');
            el.removeAttribute('disabled');
        """, file_input)
        file_input.send_keys(file_path)

    driver.execute_script("""
        const el = arguments[0];
        el.dispatchEvent(new Event('input',  {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    """, file_input)
    print("file_input.value:", file_input.get_attribute("value"))


# ====== основной поток ======
try:
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    try_accept_cookies()
    wait_overlays_gone(extra_selectors=[".MuiSkeleton-root", "[data-testid='loading']"])

    # — найти/кликнуть кнопку входа через Google —
    # сначала пробуем точный data-testid
    google_btn = None
    cand = driver.find_elements(By.CSS_SELECTOR, '[data-testid="social-login-button"]')
    print(f"[diag] social-login-button in main: {len(cand)}")
    if cand:
        for el in cand:
            blob = " ".join([
                (el.text or ""),
                (el.get_attribute("aria-label") or ""),
                (el.get_attribute("outerHTML") or "")
            ]).lower()
            if "google" in blob:
                google_btn = el
                break
        if not google_btn:
            google_btn = cand[0]

    # если не нашли — попробуем другие варианты
    if not google_btn:
        for by, sel in [
            (By.XPATH, "//button[contains(@class,'social') and contains(.,'Google')]"),
            (By.XPATH, "//*[self::button or self::a][contains(.,'Google')]"),
            (By.CSS_SELECTOR, "[data-provider='google'], a[href*='google']"),
        ]:
            try:
                el = wait.until(EC.element_to_be_clickable((by, sel)))
                google_btn = el
                break
            except Exception:
                continue

    if not google_btn:
        # может быть внутри iframe
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"[diag] iframes: {len(frames)}")
        for fr in frames:
            with contextlib.suppress(Exception):
                driver.switch_to.frame(fr)
                el = driver.find_element(By.CSS_SELECTOR, '[data-testid="social-login-button"]')
                google_btn = el
                driver.switch_to.default_content()
                break
            driver.switch_to.default_content()

    if not google_btn:
        snap("no_google_button")
        raise TimeoutException("Google login button not found")

    click_strong(google_btn)

    # — переключиться в окно/iframe Google и ввести учетные данные —
    ctx = switch_to_google_context(timeout=8)
    if ctx:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='identifierId']"))).clear()
        driver.find_element(By.XPATH, "//*[@id='identifierId']").send_keys(EMAIL)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='identifierNext']/div/button"))).click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='password']/div[1]/div/div[1]/input"))).clear()
        driver.find_element(By.XPATH, "//*[@id='password']/div[1]/div/div[1]/input").send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='passwordNext']/div/button"))).click()

        # вернуться в основное
        with contextlib.suppress(Exception):
            driver.switch_to.default_content()
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        print("prihlaseni probehlo uspesne")
    else:
        print("[warn] не появилось окно/iframe Google. Возможно, уже залогинены, или другая форма входа.")

    # ===== здесь ты уже (в идеале) залогинен и можешь идти на страницу отклика =====
    # пример: клик по блоку загрузки CV и отправка файла
    try:
        # иногда страница входа редиректит сразу к анкете — тогда просто вызываем attach_portfolio_pdf()
        attach_portfolio_pdf()

        # пример клика по кнопке «Дальше/Отправить» (проверь XPATH под свой DOM)
        submit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "/html/body/div[1]/div/div/main/job-application-form-primary-information-content//div/div/form/div[2]/button"
        )))
        click_strong(submit_btn)
    except Exception as e:
        print(f"[info] форма отклика не найдена/не на этой странице: {e}")

except Exception as e:
    print(f"[FATAL] {type(e).__name__}: {e}")
    snap("fatal")
finally:
    # оставь драйвер открытым, если смотришь руками; иначе закрывай
    driver.quit()