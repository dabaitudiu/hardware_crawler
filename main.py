import time
from collections import defaultdict

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def extract_and_group_products_selenium(url):
    # 配置 Selenium 选项
    options = Options()
    options.headless = True  # 无头模式
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # 自动管理 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 打开目标页面
        driver.get(url)
        time.sleep(5)  # 等待页面加载完成

        # 获取页面内容
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 查找所有商品
        products = soup.find_all("div", class_="s-result-item")

        # 定义关键词分组
        keywords = ["9400", "12100", "12400", "12600", "12700", "12900", "13100", "13600", "13700", "14100", "14600",
                    "14700", "14900", "4100", "4500", "4600", "5500", "5600", "5700", "5800", "5900", "5950", "7500",
                    "7600", "7700", "7800", "7950", "8500", "8600", "8700", "9600", "9700", "9800", "9900"]
        grouped_products = defaultdict(list)

        # 提取商品信息并分组
        for product in products:
            # 提取商品标题
            title_tag = product.select_one("h2.a-size-base-plus span")
            title = title_tag.get_text(strip=True) if title_tag else "unknown_title"

            # 提取商品价格
            price_tag = product.select_one("span.a-offscreen")
            price = float(price_tag.get_text(strip=True).replace("S$", "").replace(",", "")) if price_tag else None

            # 提取商品链接
            link_tag = product.select_one("a.a-link-normal")
            link = f"https://www.amazon.sg{link_tag['href']}" if link_tag else None

            if title and price and link:
                # 查找匹配的关键词
                matched_keyword = "Other"
                for keyword in keywords:
                    if keyword in title:
                        matched_keyword = keyword
                        break

                # 将商品加入对应分组
                grouped_products[matched_keyword].append({
                    "title": title,
                    "link": link,
                    "price": price,
                })

        # 对每个分组内的商品按价格排序
        for key in grouped_products:
            grouped_products[key].sort(key=lambda x: x["price"])

        return grouped_products

    finally:
        # 确保退出浏览器
        driver.quit()


if __name__ == "__main__":
    url = "https://www.amazon.sg/s?k=cpu"  # 替换为实际页面URL
    grouped_products = extract_and_group_products_selenium(url)

    # 输出结果
    for group, products in grouped_products.items():
        print(f"分组: {group}")
        for product in products:
            print(f"  商品名称: {product['title']}, 价格: S${product['price']:.2f}, 链接: {product['link']}")
        print()
