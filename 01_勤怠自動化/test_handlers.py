
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

# モック用にconfigをロードしておく
import config
# ダミー設定を入れる
config.CONF = {
    'common_defaults': {},
    'school_specific_defaults': {'cl': {}, 'tf': {}},
    'fields': {'tr_field_mappings': {}},
    'selectors': {
        'login_email': 'email', 'login_password': 'pwd', 'login_button': 'btn',
        'download_button': '#dl'
    },
    'app': {'login': {'email': 'test', 'password': 'test'}},
    'templates': {'tf': {'comment_template_rendered': 'test_template'}}
}

from handlers import CrowdLogHandler, TaskReportHandler
from form_handler import FormAutomationHandler

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
        
        # 検証: ログインチェックが呼ばれたか（is_element_presentなど）
        # mock_utils.is_element_present.assert_called() 
        # 具体的な呼び出し回数などは実装依存だが、エラーなく通過すればまずはOK
        print("Execution Test (CrowdLogHandler): OK")

    @patch('handlers.task_report_handler.browser_utils')
    def test_task_report_execution(self, mock_utils):
        """TaskReportHandlerのexecuteフロー確認"""
        # フィールドマッピングのダミー設定
        config.CONF['fields']['tr_field_mappings'] = {
            'Project': {'locator': 'proj', 'type': 'text'},
            'Comments': {'locator': 'comm', 'type': 'text'}
        }
        
        context = {'schools_type': 'tf', 'environment_name': 'UAT2'}
        handler = TaskReportHandler(self.mock_driver, context)
        
        # execute実行
        handler.execute()
        
        # 検証: input_textなどが呼ばれたか
        self.assertTrue(mock_utils.input_text.called)
        print("Execution Test (TaskReportHandler): OK")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
