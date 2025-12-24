#設定値ファイル
import config as var
import browser_utils

class FormAutomationHandler:

    # コンストラクタ
    def __init__(self, driver,schools_type,environment_name):
        self.driver = driver
        self.schools_type = schools_type
        self.environment_name = environment_name

    def setItems(self):
        #####################################
        #  設定値（ユーザーインプット依存）   ##
        #####################################
        #設定値（スクール）

        # logger.info("入力開始:" + Schools)

        #################
        #  画面入力値設定
        #################

        field_names = list(var.TR_FIELD_MAPPINGS.keys())
        Two_dimensional_dict = {}
        for index, field_name in enumerate(field_names):
            field_info = var.TR_FIELD_MAPPINGS[field_name]
            Two_dimensional_dict[field_name] = {
                'locator': field_info['locator'],
                'type': field_info['type'],
                'value': var.SCHOOL_SPECIFIC_DEFAULTS[self.schools_type][index]
            }

        
        keys_to_update = ['Comments', 'Title', 'Category']
        for key in keys_to_update:
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

