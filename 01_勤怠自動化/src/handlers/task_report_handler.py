import config as conf
import browser_utils
from .base_handler import BaseHandler

class TaskReportHandler(BaseHandler):
    """
    タスクレポート（TR）のフォーム入力処理を担当するハンドラ。
    """

    def execute(self):
        """
        設定に基づいて入力データを構築し、フォームへの入力を実行します。
        """
        school_type = self.context.get('schools_type')
        environment_name = self.context.get('environment_name', '')

        # 1. 入力データの構築
        merged_settings = conf.CONF['common_defaults'].copy()
        specific_settings = conf.CONF['school_specific_defaults'].get(school_type, {})
        merged_settings.update(specific_settings)

        field_names = list(conf.CONF['fields']['tr_field_mappings'].keys())
        input_data = {}

        # 除外するフィールド（CrowdLog用）
        excluded_fields = ['StartDate', 'EndDate']

        for field_name in field_names:
            if field_name in excluded_fields:
                continue

            field_info = conf.CONF['fields']['tr_field_mappings'][field_name]
            current_value = merged_settings.get(field_name, "")
            
            # 特殊ケース: 'tf' タイプの 'Comments' フィールド
            if school_type == 'tf' and field_name == 'Comments':
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

        # 2. 変数の置換（環境名など）
        keys_to_update = ['Comments', 'Title', 'Category']
        for key in keys_to_update:
            if not (school_type == 'tf' and key == 'Comments'):
                if key in input_data and input_data[key]['value']:
                     input_data[key]['value'] = input_data[key]['value'].replace("[KANKYOUMEI]", environment_name)
        
        # デバッグ用出力
        print(f"Input Data for {school_type}: {input_data}")

        # 3. ブラウザ操作の実行
        for dom_key, val in input_data.items():
            common_dom_args = (self.driver, 'name', val["locator"], val["value"])

            if val["type"] == "text":
                browser_utils.input_text(*common_dom_args)
            elif val["type"] == "select":
                browser_utils.select_option(*common_dom_args)
