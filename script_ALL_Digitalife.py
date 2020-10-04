from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import psycopg2
import re
import json


def getProducts(categoryId, driver):
    """
        Returns a list<dict> that contains all the products of a category
    """

    products = list()
    url = f"https://www.digitalife.com.mx/productos/idCategoria/{categoryId}"
    print(url)
    xpathcode = '//div[@class = "productoInfoBloq"]'
    driver.get(url)
    while True:
        products_driver = driver.find_elements_by_xpath(xpathcode)
        for product_driver in products_driver:
            products.append(get_product_from_driver(product_driver))
        try:
            driver.find_element_by_xpath('//a[@rel="next"]').click()
        except ElementClickInterceptedException:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            driver.find_element_by_xpath('//a[@rel="next"]').click()
        except NoSuchElementException:
            return products


def getDriver():
    """
        Initializes the Selenium driver
    """

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(r'./chromedriver.exe', options=options)
    return driver


def get_product_from_driver(product_driver):
    """
        Returns a dict from a WebElement 
    """

    product = dict()
    product['name'] = product_driver.find_element_by_xpath(
        './/span[@class="tituloHighlight"]').text

    url = product['url'] = product_driver.find_element_by_xpath(
        './a').get_attribute('href')

    p = re.compile('/([0-9]+)$')
    product['id'] = int(p.findall(url)[0])

    price = product_driver.find_element_by_xpath(
        './/div[contains(@class,"precioFlag")]').text
    product['price'] = float(re.sub(r"[^0-9\.]", "", price))

    img = product_driver.find_element_by_xpath('.//div[contains(@id,"img")]')
    img = img.value_of_css_property('background-image')
    product['img'] = img[5:-2]
    return product


def db():
    """
        creates an instance of the db driver
    """

    conn = psycopg2.connect(
        host="techdeal.ccp4vlnfh8p0.us-east-2.rds.amazonaws.com",
        database="techdata",
        user="techdeal",
        password="p4ss.sql")
    return conn


def insertProducts(products):
    """
        Inserts a list of products into the db
    """

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
    idCategories = [569, 1, 3, 609, 140, 2, 251,
                    250, 254, 252, 253, 259, 257, 256]
    driver = getDriver()
    for categoryId in idCategories:
        products = getProducts(categoryId, driver)
        insertProducts(products)
