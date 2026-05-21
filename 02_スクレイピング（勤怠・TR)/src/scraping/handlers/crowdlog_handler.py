import time
from config import config as conf
from scraping import browser_utils
from gui.gui_date_range_dialog import ask_date_range
from .base_handler import BaseHandler


class UserCancelledError(Exception):
    """ユーザーが日付選択をキャンセルした場合に発生する例外。"""
    pass


class CrowdLogHandler(BaseHandler):
    """
    CrowdLogの工数実績ダウンロード処理を担当するハンドラ。
    """

    def _get_settings(self):
        return conf.CONF.get('crowdlog_settings', {})

    def execute(self):
        """
        日付区間選択 → ログインチェック → 日付入力 → ダウンロード実行を行います。
        """
        start_date, end_date = ask_date_range()
        if start_date is None:
            raise UserCancelledError("日付選択がキャンセルされました。")

        cl_settings = self._get_settings()
        self._perform_login_if_needed(cl_settings)

        # 入力データの構築
        merged_settings = conf.CONF['common_defaults'].copy()
        specific_settings = conf.CONF['school_specific_defaults'].get('cl', {})
        merged_settings.update(specific_settings)

        # ダイアログで選んだ日付を反映
        if 'StartDate' in merged_settings:
            merged_settings['StartDate'] = merged_settings['StartDate'].replace("{{DYNAMIC_START_DATE}}", start_date)
        if 'EndDate' in merged_settings:
            merged_settings['EndDate'] = merged_settings['EndDate'].replace("{{DYNAMIC_END_DATE}}", end_date)

        # フィールド入力処理
        fields_def = cl_settings.get('fields', {})
        for field_name, field_info in fields_def.items():
            value = merged_settings.get(field_name, "")
            browser_utils.input_text(self.driver, 'name', field_info['locator'], value)

        # ダウンロードボタン押下処理
        self._click_download_button(cl_settings)

    def _perform_login_if_needed(self, cl_settings):
        """ログイン画面が表示されている場合、ログイン処理を実行します。"""
        selectors = cl_settings.get('selectors', {})
        email_selector = selectors.get('login_email')

        if not email_selector: return

        if browser_utils.is_element_present(self.driver, 'name', email_selector):
            print("Login page detected. Performing login...")

            email = conf.CONF['app']['login']['email']
            password = conf.CONF['app']['login']['password']

            browser_utils.input_text(self.driver, 'name', selectors['login_email'], email)
            browser_utils.input_text(self.driver, 'name', selectors['login_password'], password)

            login_btn_selector = selectors['login_button']
            browser_utils.click_element(self.driver, 'css', login_btn_selector)

            time.sleep(3)

    def _click_download_button(self, cl_settings):
        """ダウンロードボタンをクリックします。"""
        browser_utils.click_body(self.driver)
        time.sleep(1)

        print("Clicking download button...")
        download_btn_selector = cl_settings.get('selectors', {}).get('download_button')

        try:
            browser_utils.click_element(self.driver, 'css', download_btn_selector)
        except Exception as e:
            print(f"Normal click failed: {e}. Trying JavaScript click.")
            browser_utils.click_element_by_script(self.driver, 'css', download_btn_selector)
