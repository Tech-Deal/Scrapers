from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import psycopg2
import re
import json


def getProducts(url, driver):
    ignored_exceptions = [NoSuchElementException,
                          StaleElementReferenceException]
    products = list()
    product_driver = []
    print(url)
    xpathcode = '//div[@class="product-container"]'
    driver.get(url)
    while True:
        try:
            products_driver = WebDriverWait(driver, 5, ignored_exceptions=ignored_exceptions)\
                .until(EC.presence_of_all_elements_located((By.XPATH, xpathcode)))
        except TimeoutException:
            return list()
        for product_driver in products_driver:
            product = get_product_from_driver(product_driver)
            if product:
                products.append(product)
        try:
            nextBtn = driver.find_element_by_xpath(
                '//ul[contains(@class,"page-list")]//a[@rel="next"]')
            if nextBtn.get_attribute('class').find("disabled") != -1:
                return products
            nextBtn.click()
            time.sleep(3)
        except NoSuchElementException:
            return products
        except ElementNotInteractableException:
            return products


def getDriver():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(r'./chromedriver.exe', options=options)
    return driver


def get_product_from_driver(product_driver):
    product = dict()
    try:
        product['name'] = product_driver.find_element_by_xpath(
            './/h5[@class="product-title"]/a').text

        product['url'] = product_driver.find_element_by_xpath(
            './/h5[@class="product-title"]/a').get_attribute('href')

        price = product_driver.find_element_by_xpath(
            './/span[@class="price"]').text
        print(price)
        if not price:
            return False
        product['price'] = float(re.sub(r"[^0-9\.]", "", price))

        product['img'] = product_driver.find_element_by_xpath(
            './/img[contains(@class,"img")]').get_attribute('src')

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


def getLinks(driver):
    driver.get("https://www.tecnowow.mx/")
    links_driver = driver.find_elements_by_xpath(
        '//nav[contains(@class,"navbar-default")]//a')
    links = list()
    for link in links_driver:
        links.append(link.get_attribute('href'))
    return links


if __name__ == "__main__":
    driver = getDriver()
    links = getLinks(driver)
    for link in links:
        products = getProducts(link, driver)
        insertProducts(products)
