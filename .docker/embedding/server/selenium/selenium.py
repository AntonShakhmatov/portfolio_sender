import os
from selenium import webdriver

REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", "http://selenium:4444")

opts = webdriver.ChromeOptions()
# можно добавить prefs/аргументы по желанию:
# opts.add_argument("--window-size=1400,900")

driver = webdriver.Remote(REMOTE_URL, options=opts)
driver.set_window_size(1400, 900)
driver.get("https://www.wikipedia.org/")
print("Title:", driver.title)

# теперь зайди на http://localhost:7900 и увидишь живое окно в noVNC
# (пароль пустой, просто нажми Connect)
driver.quit()
