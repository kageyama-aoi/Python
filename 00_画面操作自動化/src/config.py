# VS code便利機能
# 一括コメントアウト
# Ctrl + /
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG
import yaml
from pathlib import Path

# グローバルな設定オブジェクト
CONF = {}

def load_config(config_path="config.yaml"):
    """
    config.yaml を読み込み、CONF グローバル変数に格納する。
    """
    global CONF
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            CONF.update(yaml.safe_load(f))
        
        # 動的に生成する文字列を処理
        # ENVIRONMENT_OPTIONS_STRING の生成
        if 'menus' in CONF and 'environment_list' in CONF['menus']:
            CONF['menus']['environment_options_string'] = "\n".join(
                f"{k}:{v}" for k, v in CONF['menus']['environment_list'].items()
            )
        
        # MENU_2_PROMPT の生成
        if 'menus' in CONF and 'menu_2_prompt' in CONF['menus']:
            CONF['menus']['menu_2_prompt'] = CONF['menus']['menu_2_prompt'].replace(
                "{{ENVIRONMENT_OPTIONS_STRING}}", CONF['menus']['environment_options_string']
            )

        # TF_COMMENT_TEMPLATE の生成
        if 'templates' in CONF and 'tf' in CONF['templates'] and 'comment_template' in CONF['templates']['tf']:
            tf_template = CONF['templates']['tf']['comment_template']
            tf_template = tf_template.replace("{{TF_DRIVE_URL}}", CONF['templates']['tf']['drive_url'])
            tf_template = tf_template.replace("{{TF_DESIGN_DOC_FOLDER_PATH}}", CONF['templates']['tf']['design_doc_folder_path'])
            tf_template = tf_template.replace("{{TF_SPEC_DOC_FILENAME}}", CONF['templates']['tf']['spec_doc_filename'])
            CONF['templates']['tf']['comment_template_rendered'] = tf_template

    except FileNotFoundError:
        print(f"Error: config file '{config_path}' not found.")
        # プログラムを終了するか、デフォルト値で続行するか選択
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        exit(1)


##################################
###ログ仕込み
##################################
def setup_logger(log_file_path, logger_name=__name__): # パラメータ名を log_file_path に変更して明確化
    logger = getLogger(logger_name)
    logger.setLevel(DEBUG)

    sh = StreamHandler()
    sh.setLevel(DEBUG)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    fh = FileHandler(log_file_path) #fh = file handler
    fh.setLevel(DEBUG)
    fh_formatter = Formatter('%(asctime)s - %(filename)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    return logger