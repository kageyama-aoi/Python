"""
フォーム入力処理を管理するハンドラモジュール。
設定ファイルに基づいて入力データを構築し、ブラウザ操作ユーティリティを用いて実際の入力を行います。
"""
import config as conf
import browser_utils
import datetime
import calendar
import time
from selenium.common.exceptions import NoSuchElementException

class FormAutomationHandler:
    """
    フォーム自動入力の実行を担うクラス。
    """

    def __init__(self, driver, context: dict):
        """
        Args:
            driver: Selenium WebDriverインスタンス
            context (dict): 実行に必要なパラメータ（schools_type, environment_nameなど）を含む辞書
        """
        self.driver = driver
        self.schools_type = context.get('schools_type')
        self.environment_name = context.get('environment_name')

    def _get_dynamic_dates(self):
        """
        今月の初日と末日を計算して返します。
        Returns:
            tuple: (first_day_str, last_day_str) 形式は YYYY-MM-DD
        """
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day = today.replace(day=last_day_num)
        return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")

    def _perform_login_if_needed(self):
        """
        ログイン画面が表示されている場合、ログイン処理を実行します。
        CrowdLog用。
        """
        try:
            # ログイン画面の識別（メールアドレス入力欄があるか）
            email_selector = conf.CONF['selectors']['login_email']
            browser_utils.find_element(self.driver, 'name', email_selector)
            
            print("Login page detected. Performing login...")
            
            # ログイン情報の取得
            email = conf.CONF['app']['login']['email']
            password = conf.CONF['app']['login']['password']
            
            # 入力と送信
            browser_utils.input_text(self.driver, 'name', conf.CONF['selectors']['login_email'], email)
            browser_utils.input_text(self.driver, 'name', conf.CONF['selectors']['login_password'], password)
            
            login_btn_selector = conf.CONF['selectors']['login_button']
            browser_utils.find_element(self.driver, 'css', login_btn_selector).click()
            
            # ログイン後の遷移待ち
            time.sleep(3)
            
        except NoSuchElementException:
            # ログイン画面ではないと判断し、何もしない
            pass

    def fill_form(self):
        """
        設定に基づいて入力データを準備し、フォームへの入力を実行します。
        """
        
        # CrowdLogの場合、まずログインチェックを行う
        if self.schools_type == 'cl':
            self._perform_login_if_needed()

        # 1. 入力データの構築
        # 共通のデフォルト値をベースにする
        merged_settings = conf.CONF['common_defaults'].copy()
        
        # 個別の設定があればマージ（上書き）する
        specific_settings = conf.CONF['school_specific_defaults'].get(self.schools_type, {})
        merged_settings.update(specific_settings)

        # 動的な日付の置換
        if self.schools_type == 'cl':
            first_day, last_day = self._get_dynamic_dates()
            if 'StartDate' in merged_settings:
                merged_settings['StartDate'] = merged_settings['StartDate'].replace("{{DYNAMIC_START_DATE}}", first_day)
            if 'EndDate' in merged_settings:
                merged_settings['EndDate'] = merged_settings['EndDate'].replace("{{DYNAMIC_END_DATE}}", last_day)

        field_names = list(conf.CONF['fields']['tr_field_mappings'].keys())
        input_data = {}

        for field_name in field_names:
            # その schools_type で必要なフィールドのみを対象とする
            # タスクレポート用とCrowdLog用でフィールドが分かれているため
            if self.schools_type == 'cl' and field_name not in ['StartDate', 'EndDate']:
                continue
            if self.schools_type != 'cl' and field_name in ['StartDate', 'EndDate']:
                continue

            field_info = conf.CONF['fields']['tr_field_mappings'][field_name]
            
            # マージ済みの設定から値を取得
            current_value = merged_settings.get(field_name, "")
            
            # 特殊ケース: 'tf' タイプの 'Comments' フィールドは、YAML側でレンダリング済みのテンプレートを使用
            if self.schools_type == 'tf' and field_name == 'Comments':
                input_data[field_name] = {
                    'locator': field_info['locator'],
                    'type': field_info['type'],
                    'value': conf.CONF['templates']['tf']['comment_template_rendered']
                }
            else:
                input_data[field_name] = {
                    'locator': field_info['locator'],
                    'type': field_info['type'],
                    'value': current_value
                }

        # 2. 変数の置換（テンプレート処理）
        # 特定のフィールドに含まれるプレースホルダー（例: [KANKYOUMEI]）を実際の値に置換
        keys_to_update = ['Comments', 'Title', 'Category']
        for key in keys_to_update:
            # 既にレンダリング済みの特殊ケース以外を対象とする
            if not (self.schools_type == 'tf' and key == 'Comments'):
                if key in input_data: # キーが存在することを確認
                     input_data[key]['value'] = input_data[key]['value'].replace("[KANKYOUMEI]", self.environment_name)
                
        # デバッグ用出力
        print(f"Input Data: {input_data}")

        # 3. ブラウザ操作の実行
        for dom_key, val in input_data.items():
            # 現在は 'name' 属性での検索に固定。
            common_dom_args = (self.driver, 'name', val["locator"], val["value"])

            if val["type"] == "text":
                browser_utils.input_text(*common_dom_args)
                # DatePickerが表示される可能性があるため、入力後にEscキーを送るなどの対策も有効だが
                # ここでは後続の処理でBodyクリック等を行う
            elif val["type"] == "select":
                browser_utils.select_option(*common_dom_args)

        # CrowdLogの場合、ダウンロードボタンをクリック
        if self.schools_type == 'cl':
            # DatePickerなどのポップアップを閉じるために、無害な要素（bodyなど）をクリック
            try:
                self.driver.find_element(browser_utils.By.TAG_NAME, 'body').click()
                time.sleep(1) # アニメーション待ち
            except Exception:
                pass

            print("Clicking download button...")
            download_btn_selector = conf.CONF['selectors']['download_button']
            
            try:
                # 通常のクリックを試行
                browser_utils.find_element(self.driver, 'css', download_btn_selector).click()
            except Exception as e:
                print(f"Normal click failed: {e}. Trying JavaScript click.")
                # JavaScriptで強制クリック
                element = browser_utils.find_element(self.driver, 'css', download_btn_selector)
                self.driver.execute_script("arguments[0].click();", element)

