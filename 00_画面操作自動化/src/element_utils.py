# バージョンUP対応(2023-09-06)
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.common.by import By

#エレメント設定
def set(driver,attribute,element):
    if attribute == "name":
        return driver.find_element(By.NAME,element)
    if attribute == "link text":
        return driver.find_element(By.NAME,element)        
    if attribute == "class name":
        return driver.find_elements(By.CLASS_NAME,element)   

#エレメントへ入力
def send(driver,attribute,element,input_value):
    set(driver,attribute,element).send_keys(input_value)

#エレメント選択
def select(driver,attribute,element,input_value):
    Select(set(driver,attribute,element)).select_by_value(input_value)