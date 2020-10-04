from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import psycopg2
import re
import json


def getProducts(category, driver):
    ignored_exceptions = [NoSuchElementException,
                          StaleElementReferenceException]
    products = list()
    url = f"https://www.doto.com.mx/{category}"
    print(url)
    xpathcode = '//div[contains(@class,"product-item-wrapper")]'
    driver.get(url)
    while(True):
        products_driver = WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions)\
            .until(EC.presence_of_all_elements_located((By.XPATH, xpathcode)))
        #products_driver = driver.find_elements_by_xpath(xpathcode)
        for product_driver in products_driver:
            product = get_product_from_driver(product_driver)
            if product:
                products.append(product)
        try:
            nextBtn = driver.find_element_by_xpath(
                '//ul[@class="pages"]/li[@class="next"]')
            driver.execute_script("arguments[0].click();", nextBtn)
            time.sleep(1)
        except NoSuchElementException:
            return products


def getDriver():
    options = Options()
    #options.headless = True
    driver = webdriver.Chrome(r'./chromedriver.exe', options=options)
    return driver


def get_product_from_driver(product_driver):
    product = dict()
    try:
        product['name'] = product_driver.find_element_by_xpath(
            './/h5[@class="product-item-name"]/a').text

        product['url'] = product_driver.find_element_by_xpath(
            './/h5[@class="product-item-name"]/a').get_attribute('href')

        price = product_driver.find_element_by_xpath(
            './/div[@class="product-item-price"]/h6').text
        p = re.compile("(\$[0-9\.,]*)")
        price = p.findall(price)[0]
        product['price'] = float(re.sub(r"[^0-9\.]", "", price))

        product['img'] = product_driver.find_element_by_xpath(
            './/div[@class="normal_img"]/img').get_attribute('src')

        return product
    except NoSuchElementException:
        return False


def db():
    conn = psycopg2.connect(
        host="techdeal.ccp4vlnfh8p0.us-east-2.rds.amazonaws.com",
        database="techdata",
        user="techdeal",
        password="p4ss.sql")
    return conn


def insertProducts(products):
    conn = db()
    cur = conn.cursor()
    cur.executemany("""
    INSERT INTO public."Products" (name, price, url, image_url, store_id) 
    VALUES (%(name)s, %(price)s, %(url)s, %(img)s, 1)
    ON CONFLICT (url)
    DO UPDATE SET price = EXCLUDED.price
    """, products)
    print('added')
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":

    categories = ["audio", "celulares", "computo",
                  "gadgets", "gaming", "tablets", "tv-y-video"]
    driver = getDriver()
    for category in categories:
        products = getProducts(category, driver)
        insertProducts(products)
