# バージョンUP対応(2023-09-06)
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.common.by import By

#エレメント設定
def find_element(driver: webdriver.Remote, attribute: str, element: str):
    if attribute == "name":
        return driver.find_element(By.NAME, element)
    if attribute == "link text":
        return driver.find_element(By.LINK_TEXT, element)        
    if attribute == "class name":
        return driver.find_element(By.CLASS_NAME, element)   

#エレメントへ入力
def input_text(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
    find_element(driver, attribute, element).send_keys(input_value)

#エレメント選択
def select_option(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
    Select(find_element(driver, attribute, element)).select_by_value(input_value)