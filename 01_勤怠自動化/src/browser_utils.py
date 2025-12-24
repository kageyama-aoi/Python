"""
Selenium WebDriverを用いたブラウザ操作のユーティリティモジュール。
要素の特定、テキスト入力、セレクトボックス操作などの基本的な機能を提供します。
"""
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.common.by import By

def find_element(driver: webdriver.Remote, attribute: str, element: str):
    """
    指定された属性に基づいてWeb要素を特定します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 検索に使用する属性タイプ ("name", "link text", "class name")
        element (str): 検索する値（ID、クラス名など）

    Returns:
        WebElement: 特定されたWeb要素
    """
    if attribute == "name":
        return driver.find_element(By.NAME, element)
    if attribute == "link text":
        return driver.find_element(By.LINK_TEXT, element)        
    if attribute == "class name":
        return driver.find_element(By.CLASS_NAME, element)   
    if attribute == "css":
        return driver.find_element(By.CSS_SELECTOR, element)

def input_text(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
    """
    指定された要素にテキストを入力します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
        input_value (str): 入力するテキスト
    """
    find_element(driver, attribute, element).send_keys(input_value)

def select_option(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
    """
    セレクトボックス（ドロップダウン）から指定された値を選択します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
        input_value (str): 選択するオプションのvalue属性値
    """
    Select(find_element(driver, attribute, element)).select_by_value(input_value)