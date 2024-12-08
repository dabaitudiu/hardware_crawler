from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")  # 启用无头模式
options.add_argument("--window-size=1920,1080")  # 设置窗口大小
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("chrome://gpu")
    print(driver.page_source)
finally:
    driver.quit()
