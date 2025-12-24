"""
フォーム入力処理を管理するハンドラモジュール。
設定ファイルに基づいて入力データを構築し、ブラウザ操作ユーティリティを用いて実際の入力を行います。
"""
import config as conf
import browser_utils

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

    def fill_form(self):
        """
        設定に基づいて入力データを準備し、フォームへの入力を実行します。
        """
        
        # 1. 入力データの構築
        field_names = list(conf.CONF['fields']['tr_field_mappings'].keys())
        input_data = {} # 変数名を Two_dimensional_dict から input_data に変更して可読性向上

        for index, field_name in enumerate(field_names):
            field_info = conf.CONF['fields']['tr_field_mappings'][field_name]
            # YAMLからデフォルト値を取得
            value_from_defaults = conf.CONF['school_specific_defaults'][self.schools_type][index]
            
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
                    'value': value_from_defaults
                }

        # 2. 変数の置換（テンプレート処理）
        # 特定のフィールドに含まれるプレースホルダー（例: [KANKYOUMEI]）を実際の値に置換
        keys_to_update = ['Comments', 'Title', 'Category']
        for key in keys_to_update:
            # 既にレンダリング済みの特殊ケース以外を対象とする
            if not (self.schools_type == 'tf' and key == 'Comments'):
                input_data[key]['value'] = input_data[key]['value'].replace("[KANKYOUMEI]", self.environment_name)
                
        # デバッグ用出力
        print(input_data)

        # 3. ブラウザ操作の実行
        for dom_key, val in input_data.items():
            # 現在は 'name' 属性での検索に固定。必要に応じて config で検索属性を指定可能に拡張を検討。
            common_dom_args = (self.driver, 'name', val["locator"], val["value"])

            if val["type"] == "text":
                browser_utils.input_text(*common_dom_args)
            elif val["type"] == "select":
                browser_utils.select_option(*common_dom_args)

