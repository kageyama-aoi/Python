"""
アプリケーションの設定管理およびロギング機能を提供するモジュール。
外部のYAML設定ファイル(config.yaml)を読み込み、グローバルな設定オブジェクトとして提供します。
"""
import os
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG
import yaml
from pathlib import Path
from dotenv import load_dotenv

# グローバルな設定オブジェクト（YAMLから読み込んだデータを保持）
CONF = {}

def load_config(config_path="config/config.yaml"):
    """
    指定されたYAML設定ファイルを読み込み、CONF グローバル変数に格納します。
    テンプレート内のプレースホルダー置換などの動的な処理もここで行います。
    また、.envファイルから環境変数を読み込み、機密情報を上書きします。

    Args:
        config_path (str): 設定ファイルのパス。デフォルトは "config/config.yaml"。
    """
    global CONF
    
    # .env ファイルの読み込み
    load_dotenv()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            CONF.update(yaml.safe_load(f))
        
        # --- 環境変数による上書き処理 ---
        # ログイン情報が環境変数にあれば、YAMLの設定を上書きする
        env_email = os.getenv("CROWDLOG_EMAIL")
        env_password = os.getenv("CROWDLOG_PASSWORD")

        if 'app' not in CONF:
            CONF['app'] = {}
        if 'login' not in CONF['app']:
            CONF['app']['login'] = {}

        if env_email:
            CONF['app']['login']['email'] = env_email
        if env_password:
            CONF['app']['login']['password'] = env_password

        # --- 動的な文字列生成処理 ---

        # 1. 環境リストの文字列表現生成 (ENVIRONMENT_OPTIONS_STRING)
        if 'menus' in CONF and 'environment_list' in CONF['menus']:
            CONF['menus']['environment_options_string'] = "\n".join(
                f"{k}:{v}" for k, v in CONF['menus']['environment_list'].items()
            )
        
        # 2. メニュープロンプト内のプレースホルダー置換 (MENU_2_PROMPT)
        if 'menus' in CONF and 'menu_2_prompt' in CONF['menus']:
            CONF['menus']['menu_2_prompt'] = CONF['menus']['menu_2_prompt'].replace(
                "{{ENVIRONMENT_OPTIONS_STRING}}", CONF['menus']['environment_options_string']
            )

        # 3. 特定テンプレートのレンダリング (TF_COMMENT_TEMPLATE)
        if 'templates' in CONF and 'tf' in CONF['templates'] and 'comment_template' in CONF['templates']['tf']:
            tf_config = CONF['templates']['tf']
            tf_template = tf_config['comment_template']
            # 各プレースホルダーを置換
            tf_template = tf_template.replace("{{TF_DRIVE_URL}}", tf_config.get('drive_url', ''))
            tf_template = tf_template.replace("{{TF_DESIGN_DOC_FOLDER_PATH}}", tf_config.get('design_doc_folder_path', ''))
            tf_template = tf_template.replace("{{TF_SPEC_DOC_FILENAME}}", tf_config.get('spec_doc_filename', ''))
            # レンダリング済み文字列として保存
            CONF['templates']['tf']['comment_template_rendered'] = tf_template

    except FileNotFoundError:
        print(f"Error: config file '{config_path}' not found.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        exit(1)

def setup_logger(log_file_path, logger_name=__name__):
    """
    ロガーの初期設定を行います。
    コンソール出力とファイル出力の両方を設定します。

    Args:
        log_file_path (str): ログファイルの出力先パス
        logger_name (str): ロガーの名前。通常は __name__ を使用。

    Returns:
        Logger: 設定済みのLoggerインスタンス
    """
    logger = getLogger(logger_name)
    logger.setLevel(DEBUG)

    # ストリームハンドラ（コンソール出力）の設定
    sh = StreamHandler()
    sh.setLevel(DEBUG)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # ファイルハンドラ（ファイル出力）の設定
    fh = FileHandler(log_file_path)
    fh.setLevel(DEBUG)
    fh_formatter = Formatter('%(asctime)s - %(filename)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    
    return logger