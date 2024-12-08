import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def extract_and_group_products_selenium(url):
    options = Options()
    options.headless = True
    options.add_argument('--disable-blink-features=AutomationControlled')

    # 自动下载和管理 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        soup = bs4.BeautifulSoup(driver.page_source, "html.parser")
        # 提取数据的代码保持不变
    finally:
        driver.quit()
