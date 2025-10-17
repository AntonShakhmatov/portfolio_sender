import shutil
import json
import requests
import undetected_chromedriver as uc
import google.generativeai as genai
import sqlite3 as sq
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
from sql.req import *

GEMINI_API_KEY="<API_HERE>"

BASE = 'https://www.reedglobal.cz/'

response = requests.get(BASE)

soup = BeautifulSoup(response.content, "html.parser")

main_element = soup.select_one(".bg-white")

main_html = str(main_element)