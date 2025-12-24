#設定値ファイル
import config as conf
import browser_utils

class FormAutomationHandler:

    # コンストラクタ
    def __init__(self, driver, context: dict):
        self.driver = driver
        self.schools_type = context.get('schools_type')
        self.environment_name = context.get('environment_name')

    def fill_form(self):
        #####################################
        #  設定値（ユーザーインプット依存）   ##
        #####################################
        #設定値（スクール）

        # logger.info("入力開始:" + Schools)

        #################
        #  画面入力値設定
        #################

        field_names = list(conf.CONF['fields']['tr_field_mappings'].keys())
        Two_dimensional_dict = {}
        for index, field_name in enumerate(field_names):
            field_info = conf.CONF['fields']['tr_field_mappings'][field_name]
            # SCHOOL_SPECIFIC_DEFAULTS は YAML の値を直接使う
            value_from_defaults = conf.CONF['school_specific_defaults'][self.schools_type][index]
            
            # TF_COMMENT_TEMPLATE を使用する tf の場合のみ特別処理 (YAMLでレンダリング済みを使う)
            if self.schools_type == 'tf' and field_name == 'Comments':
                Two_dimensional_dict[field_name] = {
                    'locator': field_info['locator'],
                    'type': field_info['type'],
                    'value': conf.CONF['templates']['tf']['comment_template_rendered']
                }
            else:
                Two_dimensional_dict[field_name] = {
                    'locator': field_info['locator'],
                    'type': field_info['type'],
                    'value': value_from_defaults
                }

        
        keys_to_update = ['Comments', 'Title', 'Category']
        for key in keys_to_update:
            # 既にレンダリング済みの 'tf' の Comments は更新しない
            if not (self.schools_type == 'tf' and key == 'Comments'):
                Two_dimensional_dict[key]['value'] = Two_dimensional_dict[key]['value'].replace("[KANKYOUMEI]", self.environment_name)
                
        print(Two_dimensional_dict)

        #################
        #  画面入力   ##
        #################

        for dom_key,val in Two_dimensional_dict.items():
            #引数まとめ
            # attributeは現状'name'固定とする。必要に応じて'TR_FIELD_MAPPINGS'に'find_by'などの属性を追加することも検討。
            common_dom_args = (self.driver,'name',val["locator"],val["value"])

            if val["type"] == "text":
                browser_utils.input_text(*common_dom_args)
            elif val["type"] == "select":
                browser_utils.select_option(*common_dom_args)

