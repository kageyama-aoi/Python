#設定値ファイル
import constants as var
import element_utils

class task_report_input_handler:

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

        Two_dimensional_dict = {
        var.TR_FIELDS[index]: dict(attribut_name = var.TR_HTML_ATTRIBUTES[index],value=values)
        for index, values in enumerate(var.SCHOOL_SPECIFIC_DEFAULTS[self.schools_type])
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
            common_dom_args = (self.driver,'name',val["attribut_name"],val["value"])

            #「コメント」欄の場合
            # if dom_key in ("Comments") : 
            #     FuncElement.send(*common_dom_args) 
            #     continue
            
            # 入力除外項目
            # if dom_key in ("Category") : continue
            
            # 値を直入力
            if dom_key in ("Project","Title","Comments","Category") : 
                element_utils.input_text(*common_dom_args) 
                continue

            element_utils.select_option(*common_dom_args) 

