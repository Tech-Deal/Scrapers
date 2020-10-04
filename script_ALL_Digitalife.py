from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import psycopg2
import re
import json


def getProducts(id, driver):
    products = list()
    url = f"https://www.digitalife.com.mx/productos/idCategoria/{id}"
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
            #print('algo bloquea')
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            driver.find_element_by_xpath('//a[@rel="next"]').click()
        except NoSuchElementException:
            # print("fin")
            return products


def getDriver():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(r'./chromedriver.exe', options=options)
    return driver


def get_product_from_driver(product_driver):
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
    conn = psycopg2.connect(
        host="techdeal.ccp4vlnfh8p0.us-east-2.rds.amazonaws.com",
        database="techdata",
        user="techdeal",
        password="p4ss.sql")
    return conn


def insertProducts(products):
    conn = db()
    cur = conn.cursor()
    for product in products:
        cur.execute(
            'SELECT id FROM public."Products" WHERE url = %s', (product['url'],))
        p = cur.fetchone()
        if p is None:
            cur.execute(
                'INSERT INTO public."Products" (name, price, url, image_url, store_id) '
                'VALUES (%(name)s, %(price)s, %(url)s, %(img)s, 1) ',
                product
            )
        else:
            cur.execute(
                'UPDATE public."Products" '
                'SET price = %s WHERE id = %s ',
                (product['price'],p[0])
            )
    print('added')
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    idCategories = [569, 569, 1, 3, 609, 140, 2, 251,
                    250, 254, 252, 253, 259, 257, 256]
    driver = getDriver()
    for id in idCategories:
        products = getProducts(id, driver)
        insertProducts(products)
