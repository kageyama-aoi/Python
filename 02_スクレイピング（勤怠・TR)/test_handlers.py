import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

# モック用にconfigをロードしておく
import config
# 新しい構造に合わせてダミー設定を入れる
config.CONF = {
    'common_defaults': {},
    'school_specific_defaults': {'cl': {}, 'tf': {}},
    
    'app': {'login': {'email': 'test', 'password': 'test'}},
    
    # 新しいCrowdLog設定
    'crowdlog_settings': {
        'selectors': {
            'login_email': 'email', 'login_password': 'pwd', 'login_button': 'btn',
            'download_button': '#dl'
        },
        'fields': {
            'StartDate': {'locator': 'from', 'type': 'text'},
            'EndDate': {'locator': 'to', 'type': 'text'}
        }
    },
    
    # 新しいTR共通設定
    'task_report_settings': {
        'fields': {
            'Project': {'locator': 'proj', 'type': 'text'},
            'Comments': {'locator': 'comm', 'type': 'text'}
        }
    },

    'templates': {'tf': {'comment_template_rendered': 'test_template'}}
}

from .src.handlers import CrowdLogHandler, TaskReportHandler
from .src.form_handler import FormAutomationHandler

class TestHandlers(unittest.TestCase):
    def setUp(self):
        self.mock_driver = MagicMock()

    def test_factory_logic(self):
        """FormAutomationHandlerが正しいハンドラを生成するか"""
        # Case 1: CrowdLog
        context_cl = {'schools_type': 'cl'}
        handler_wrapper = FormAutomationHandler(self.mock_driver, context_cl)
        self.assertIsInstance(handler_wrapper.handler, CrowdLogHandler)
        print("Factory Test (CL): OK")

        # Case 2: TaskReport
        context_tr = {'schools_type': 'tf'}
        handler_wrapper = FormAutomationHandler(self.mock_driver, context_tr)
        self.assertIsInstance(handler_wrapper.handler, TaskReportHandler)
        print("Factory Test (TR): OK")

    @patch('handlers.crowdlog_handler.browser_utils')
    def test_crowdlog_execution(self, mock_utils):
        """CrowdLogHandlerのexecuteフロー確認"""
        context = {'schools_type': 'cl'}
        handler = CrowdLogHandler(self.mock_driver, context)
        
        # 実行
        handler.execute()
        
        # 検証
        # ログインや入力が呼ばれたか。ここではエラーが出ないことを確認
        print("Execution Test (CrowdLogHandler): OK")

    @patch('handlers.task_report_handler.browser_utils')
    def test_task_report_execution(self, mock_utils):
        """TaskReportHandlerのexecuteフロー確認"""
        context = {'schools_type': 'tf', 'environment_name': 'UAT2'}
        handler = TaskReportHandler(self.mock_driver, context)
        
        # execute実行
        handler.execute()
        
        # 検証: input_textなどが呼ばれたか
        self.assertTrue(mock_utils.input_text.called)
        print("Execution Test (TaskReportHandler): OK")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)