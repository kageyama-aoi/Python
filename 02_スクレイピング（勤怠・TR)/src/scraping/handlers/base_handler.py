from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver

class BaseHandler(ABC):
    """
    全ての自動化ハンドラの基底クラス。
    """
    def __init__(self, driver: WebDriver, context: dict):
        """
        Args:
            driver: Selenium WebDriverインスタンス
            context: 実行に必要なコンテキスト情報（設定値など）
        """
        self.driver = driver
        self.context = context

    @abstractmethod
    def execute(self):
        """
        自動化処理を実行する抽象メソッド。
        サブクラスで具体的な処理を実装してください。
        """
        pass
