"""
フォーム入力処理を管理するハンドラモジュール。
src/handlers/ 配下のクラスに処理を委譲します。
"""
from handlers import CrowdLogHandler, TaskReportHandler

class FormAutomationHandler:
    """
    フォーム自動入力の実行を担うクラス（ラッパー）。
    コンテキストに応じて適切なハンドラを選択し、実行します。
    """

    def __init__(self, driver, context: dict):
        """
        Args:
            driver: Selenium WebDriverインスタンス
            context (dict): 実行に必要なパラメータ（schools_type, environment_nameなど）を含む辞書
        """
        self.driver = driver
        self.context = context
        self.handler = self._create_handler()

    def _create_handler(self):
        """
        school_type に応じて適切なハンドラインスタンスを生成して返します。
        """
        school_type = self.context.get('schools_type')
        
        if school_type == 'cl':
            return CrowdLogHandler(self.driver, self.context)
        else:
            # cl以外は全てタスクレポートとして扱う
            return TaskReportHandler(self.driver, self.context)

    def fill_form(self):
        """
        選択されたハンドラの実行メソッドを呼び出します。
        """
        if self.handler:
            self.handler.execute()
        else:
            print("Error: No handler created.")