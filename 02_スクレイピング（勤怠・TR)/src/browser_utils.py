"""
Selenium WebDriverを用いたブラウザ操作のユーティリティモジュール。
要素の特定、テキスト入力、セレクトボックス操作などの基本的な機能を提供します。
"""
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


# ---------------------------------------------------------------------------
# 要素の取得
# ---------------------------------------------------------------------------

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


def find_elements(driver: webdriver.Remote, attribute: str, element: str) -> list:
    """
    指定された属性に基づいて複数のWeb要素を取得します。

    Returns:
        list[WebElement]: 一致した要素のリスト（0件の場合は空リスト）
    """
    if attribute == "css":
        return driver.find_elements(By.CSS_SELECTOR, element)
    if attribute == "tag":
        return driver.find_elements(By.TAG_NAME, element)
    if attribute == "name":
        return driver.find_elements(By.NAME, element)
    if attribute == "class name":
        return driver.find_elements(By.CLASS_NAME, element)
    return []


def find_child_elements(parent, attribute: str, element: str) -> list:
    """
    親要素配下の複数のWeb要素を取得します。

    Args:
        parent: 親となるWebElement
        attribute (str): 検索に使用する属性タイプ
        element (str): 検索する値

    Returns:
        list[WebElement]: 一致した子要素のリスト
    """
    if attribute == "tag":
        return parent.find_elements(By.TAG_NAME, element)
    if attribute == "css":
        return parent.find_elements(By.CSS_SELECTOR, element)
    if attribute == "name":
        return parent.find_elements(By.NAME, element)
    return []


def get_attribute(element, attribute_name: str) -> str:
    """
    Web要素の属性値を取得します。

    Args:
        element: 対象のWebElement
        attribute_name (str): 取得する属性名

    Returns:
        str: 属性値
    """
    return element.get_attribute(attribute_name)


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


# ---------------------------------------------------------------------------
# ページ遷移・待機
# ---------------------------------------------------------------------------

def wait_for_page_load(driver: webdriver.Remote, timeout: int = 30):
    """
    ページの読み込み完了（document.readyState == "complete"）を待ちます。

    Args:
        driver: Selenium WebDriverインスタンス
        timeout (int): 最大待機秒数（デフォルト30秒）
    """
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def navigate(driver: webdriver.Remote, url: str, timeout: int = 30):
    """
    指定URLに遷移し、ページ読み込み完了を待ちます。

    Args:
        driver: Selenium WebDriverインスタンス
        url (str): 遷移先URL
        timeout (int): 最大待機秒数（デフォルト30秒）
    """
    driver.get(url)
    wait_for_page_load(driver, timeout)


# ---------------------------------------------------------------------------
# 要素への操作
# ---------------------------------------------------------------------------

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


def prepend_text(driver: webdriver.Remote, attribute: str, element: str, text: str):
    """
    指定された要素の先頭にテキストを追記します。
    JavaScriptで一括セットするため、長文でも高速に動作します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
        text (str): 先頭に追記するテキスト
    """
    elem = find_element(driver, attribute, element)
    current = elem.get_attribute("value") or ""
    driver.execute_script("arguments[0].value = arguments[1];", elem, text + current)


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


def select_option_by_text(driver: webdriver.Remote, attribute: str, element: str, visible_text: str):
    """
    セレクトボックス（ドロップダウン）から表示テキストで値を選択します。
    YAMLに表示名をそのまま書きたい場合に使用します。

    Args:
        driver: Selenium WebDriverインスタンス
        attribute (str): 要素検索に使用する属性タイプ
        element (str): 要素検索に使用する値
        visible_text (str): 選択するオプションの表示テキスト
    """
    Select(find_element(driver, attribute, element)).select_by_visible_text(visible_text)


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


def input_text_by_script(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
    """
    JavaScriptを使用して指定された要素にテキストを入力します。
    通常のsend_keysが要素の非表示・非活性などで失敗する場合に使用します。
    """
    target_element = find_element(driver, attribute, element)
    driver.execute_script("arguments[0].value = arguments[1];", target_element, input_value)


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


# ---------------------------------------------------------------------------
# その他
# ---------------------------------------------------------------------------

def save_screenshot(driver: webdriver.Remote, path: str):
    """
    スクリーンショットを指定パスに保存します。

    Args:
        driver: Selenium WebDriverインスタンス
        path (str): 保存先ファイルパス
    """
    driver.save_screenshot(path)
