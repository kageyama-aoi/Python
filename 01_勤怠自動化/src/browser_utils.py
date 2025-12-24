"""
Selenium WebDriverを用いたブラウザ操作のユーティリティモジュール。
要素の特定、テキスト入力、セレクトボックス操作などの基本的な機能を提供します。
"""
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def find_element(driver: webdriver.Remote, attribute: str, element: str):
    """
    指定された属性に基づいてWeb要素を特定します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 検索に使用する属性タイプ ("name", "link text", "class name", "css", "tag")
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
    if attribute == "tag":
        return driver.find_element(By.TAG_NAME, element)

def is_element_present(driver: webdriver.Remote, attribute: str, element: str) -> bool:
    """
    指定された要素が存在するかどうかを確認します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値

    Returns:
        bool: 要素が存在すればTrue、存在しなければFalse
    """
    try:
        find_element(driver, attribute, element)
        return True
    except NoSuchElementException:
        return False

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

def click_element(driver: webdriver.Remote, attribute: str, element: str):
    """
    指定された要素をクリックします。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
    """
    find_element(driver, attribute, element).click()

def click_element_by_script(driver: webdriver.Remote, attribute: str, element: str):
    """
    JavaScriptを使用して指定された要素をクリックします。
    通常のクリックが要素被なり等で失敗する場合に使用します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
    """
    target_element = find_element(driver, attribute, element)
    driver.execute_script("arguments[0].click();", target_element)

def click_body(driver: webdriver.Remote):
    """
    bodyタグ（画面背景）をクリックします。
    ポップアップやドロップダウンを閉じるために使用します。
    """
    try:
        find_element(driver, "tag", "body").click()
    except Exception:
        # bodyクリックでのエラーは無視する（致命的ではないため）
        pass