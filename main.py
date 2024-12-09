import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 初始化日志记录器
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format='%(asctime)s [%(levelname)s] %(message)s',  # 日志格式：时间戳 + 日志级别 + 消息
    handlers=[
        logging.FileHandler("crawler.log", mode="w", encoding="utf-8"),  # 写入日志文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

KEYWORDS_MAP = {
    "cpu": ["9400", "12100", "12400", "12600", "12700", "12900", "13100", "13600", "13700", "14100", "14600",
            "14700", "14900", "4100", "4500", "4600", "5500", "5600", "5700", "5800", "5900", "5950", "7500",
            "7600", "7700", "7800", "7950", "8500", "8600", "8700", "9600", "9700", "9800", "9900"],
    "gpu": ["A380", "A750", "A770", "580", "1660", "3050", "3060", "3070", "3080", "3090", "4060", "4070", "4080",
            "4090", "5700", "6500", "6600", "6650", "6950", "7600", "7700", "7800", "7900"],
    "motherboard": ["H610", "B760", "Z790", "A320", "B450", "B550", "B650", "X670"]
}


# 并行检索
def parallel_retrieve():
    logging.info("启动并行检索")

    # 最大并行线程数（根据 CPU 核心数或任务数量调整）
    max_workers = 4

    # 创建线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        futures = {
            executor.submit(retrieve_once, product_name, KEYWORDS_MAP[product_name]): product_name
            for product_name in KEYWORDS_MAP
        }

        # 收集结果
        all_results = {}
        for future in as_completed(futures):
            product_name = futures[future]
            try:
                result = future.result()
                all_results.update(result)
                logging.info(f"成功完成检索: {product_name}")
            except Exception as e:
                logging.error(f"检索 {product_name} 时出错: {e}")

    logging.info("并行检索完成")
    return all_results


def sequential_retrieve():
    for k in KEYWORDS_MAP:
        retrieve_once(k, KEYWORDS_MAP[k])


def retrieve_once(product_name, possible_products):
    sub_task_start_time = time.time()
    url = f"https://www.amazon.sg/s?k={product_name}"
    logging.info("启动爬取程序")

    # 配置 Selenium 选项
    options = Options()
    options.add_argument("--headless=new")  # 启用无头模式
    options.add_argument("--disable-gpu")  # 禁用 GPU 渲染
    options.add_argument("--window-size=1920,1080")  # 设置窗口大小
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 初始化 WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        logging.info(f"打开页面: {url}")
        driver.get(url)

        # 等待商品列表加载完成
        start_time = time.time()
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.s-result-item"))
            )
            logging.info(f"页面加载完成，用时: {1000 * (time.time() - start_time):.2f}ms, 开始解析内容...")
        except Exception as e:
            logging.error(f"页面加载超时: {e}")
            return {}

        # 获取页面内容
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("div", class_="s-result-item")
        total_products = len(products)
        logging.info(f"找到 {total_products} 个结果")

        # 定义关键词分组队列
        grouped_products = {possible_product: [] for possible_product in possible_products}
        grouped_products["Other"] = []  # 用于存储没有匹配到关键词的商品

        # 提取商品信息并直接分类
        for index, product in enumerate(products, start=1):
            try:
                # 提取商品标题
                title_tag = product.select_one("h2.a-size-base-plus span")
                title = title_tag.get_text(strip=True) if title_tag else "unknown_title"

                # 提取商品价格
                price_tag = product.select_one("span.a-offscreen")
                price = (
                    float(price_tag.get_text(strip=True).replace("S$", "").replace(",", ""))
                    if price_tag else None
                )

                # asin
                asin = product.get("data-asin", "unknown_asin")

                # 提取商品链接
                link_tag = product.select_one("a.a-link-normal")
                link = f"https://www.amazon.sg{link_tag['href']}" if link_tag else None

                # 跳过无价格的商品
                if price is None:
                    continue

                if title and link:
                    # 查找匹配的关键词并直接分类
                    matched_product = next(
                        (possible_product for possible_product in possible_products if possible_product in title),
                        "Other")
                    grouped_products[matched_product].append({
                        "title": title,
                        "link": link,
                        "price": price,
                    })

                # 打印进度日志
                logging.info(f"处理结果 {index}/{total_products}: {title} - S${price:.2f}")

            except Exception as e:
                logging.error(f"处理结果 {index} 时出错: {e}")

        logging.info("商品处理完成，返回结果")

        # 输出结果
        for group, products in grouped_products.items():
            logging.info(f"分组: {group}")
            for product in products:
                logging.info(
                    f"  商品名称: {product['title']}, id: {asin},  价格: S${product['price']:.2f}, 链接: {product['link']}")

        logging.info(f"{product_name}子任务总耗时: {time.time() - sub_task_start_time :.2f}s")

        return grouped_products

    except Exception as e:
        logging.error(f"爬取过程中出现错误: {e}")
        raise
    finally:
        logging.info("关闭浏览器")
        driver.quit()


if __name__ == "__main__":
    program_start_time = time.time()

    try:
        parallel_retrieve()
    except Exception as e:
        logging.error(f"程序运行失败: {e}")

    logging.info(f"爬虫任务总耗时: {time.time() - program_start_time:.2f}s")
