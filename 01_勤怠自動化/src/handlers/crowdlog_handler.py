import datetime
import calendar
import time
import config as conf
import browser_utils
from .base_handler import BaseHandler

class CrowdLogHandler(BaseHandler):
    """
    CrowdLogの工数実績ダウンロード処理を担当するハンドラ。
    """

    def execute(self):
        """
        ログインチェック、日付入力、ダウンロード実行を行います。
        """
        self._perform_login_if_needed()
        
        # 入力データの構築
        merged_settings = conf.CONF['common_defaults'].copy()
        specific_settings = conf.CONF['school_specific_defaults'].get('cl', {})
        merged_settings.update(specific_settings)

        # 動的な日付の置換
        first_day, last_day = self._get_dynamic_dates()
        if 'StartDate' in merged_settings:
            merged_settings['StartDate'] = merged_settings['StartDate'].replace("{{DYNAMIC_START_DATE}}", first_day)
        if 'EndDate' in merged_settings:
            merged_settings['EndDate'] = merged_settings['EndDate'].replace("{{DYNAMIC_END_DATE}}", last_day)

        # フィールド入力処理
        field_names = ['StartDate', 'EndDate']
        for field_name in field_names:
            if field_name not in conf.CONF['fields']['tr_field_mappings']:
                continue
                
            field_info = conf.CONF['fields']['tr_field_mappings'][field_name]
            value = merged_settings.get(field_name, "")
            
            browser_utils.input_text(self.driver, 'name', field_info['locator'], value)

        # ダウンロードボタン押下処理
        self._click_download_button()

    def _get_dynamic_dates(self):
        """今月の初日と末日を計算して返します。"""
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day = today.replace(day=last_day_num)
        return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")

    def _perform_login_if_needed(self):
        """ログイン画面が表示されている場合、ログイン処理を実行します。"""
        email_selector = conf.CONF['selectors']['login_email']
        
        if browser_utils.is_element_present(self.driver, 'name', email_selector):
            print("Login page detected. Performing login...")
            
            email = conf.CONF['app']['login']['email']
            password = conf.CONF['app']['login']['password']
            
            browser_utils.input_text(self.driver, 'name', conf.CONF['selectors']['login_email'], email)
            browser_utils.input_text(self.driver, 'name', conf.CONF['selectors']['login_password'], password)
            
            login_btn_selector = conf.CONF['selectors']['login_button']
            browser_utils.click_element(self.driver, 'css', login_btn_selector)
            
            time.sleep(3)

    def _click_download_button(self):
        """ダウンロードボタンをクリックします。"""
        # ポップアップなどを閉じるためにbodyをクリック
        browser_utils.click_body(self.driver)
        time.sleep(1)

        print("Clicking download button...")
        download_btn_selector = conf.CONF['selectors']['download_button']
        
        try:
            browser_utils.click_element(self.driver, 'css', download_btn_selector)
        except Exception as e:
            print(f"Normal click failed: {e}. Trying JavaScript click.")
            browser_utils.click_element_by_script(self.driver, 'css', download_btn_selector)
