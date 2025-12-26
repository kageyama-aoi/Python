"""
アプリケーションの設定管理およびロギング機能を提供するモジュール。
外部のYAML設定ファイル(config/main.yaml および config/modes/*.yaml)を読み込み、
グローバルな設定オブジェクトとして提供します。
"""
import os
import glob
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG
import yaml
from dotenv import load_dotenv

# グローバルな設定オブジェクト（YAMLから読み込んだデータを保持）
CONF = {}

def _deep_merge(base_dict, update_dict):
    """
    辞書を再帰的にマージするヘルパー関数。
    base_dict を破壊的に更新します。
    """
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            _deep_merge(base_dict[key], value)
        else:
            base_dict[key] = value

def load_config(config_path="config/main.yaml"):
    """
    指定されたYAML設定ファイルを読み込み、CONF グローバル変数に格納します。
    config/modes/ 配下のYAMLファイルも自動的に読み込み、マージします。
    """
    global CONF
    # 再読み込み時のために初期化
    CONF.clear()
    
    # メタデータ格納用の辞書を初期化
    CONF['_meta'] = {'files': {}}
    
    load_dotenv()

    try:
        # 1. Main Config の読み込み
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Main config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            CONF.update(yaml.safe_load(f))
        
        # Main Configに _meta が上書きされている場合は復元
        if '_meta' not in CONF: CONF['_meta'] = {'files': {}}

        # 2. Modes Configs の読み込み (config/modes/ 配下を再帰的に探索)
        config_dir = os.path.dirname(config_path)
        modes_dir = os.path.join(config_dir, "modes")
        
        if os.path.exists(modes_dir):
            # modes/**/*.yaml を全て取得
            mode_files = glob.glob(os.path.join(modes_dir, "**", "*.yaml"), recursive=True)
            
            for file_path in mode_files:
                # print(f"Loading mode config: {file_path}") # Debug
                with open(file_path, "r", encoding="utf-8") as f:
                    sub_conf = yaml.safe_load(f)
                    if sub_conf:
                        _deep_merge(CONF, sub_conf)
                        
                        # school_specific_defaults のキーがどのファイルにあるか記録
                        if 'school_specific_defaults' in sub_conf:
                            for key in sub_conf['school_specific_defaults']:
                                CONF['_meta']['files'][key] = file_path

        # 3. 環境変数による上書き
        _apply_env_overrides()

        # 4. テンプレートのレンダリング
        _render_templates()

    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

def _apply_env_overrides():
    """環境変数でログイン情報などを上書きします。"""
    env_email = os.getenv("CROWDLOG_EMAIL")
    env_password = os.getenv("CROWDLOG_PASSWORD")

    if 'app' not in CONF: CONF['app'] = {}
    if 'login' not in CONF['app']: CONF['app']['login'] = {}

    if env_email: CONF['app']['login']['email'] = env_email
    if env_password: CONF['app']['login']['password'] = env_password

def _render_templates():
    """テンプレート文字列内の変数を置換して、レンダリング済み文字列を生成します。"""
    # Tframe Comment Template Rendering
    # templatesキーがマージされている前提
    if 'templates' in CONF and 'tf' in CONF['templates'] and 'comment_template' in CONF['templates']['tf']:
        tf_config = CONF['templates']['tf']
        tf_template = tf_config['comment_template']
        
        # 各プレースホルダーを置換
        tf_template = tf_template.replace("{{TF_DRIVE_URL}}", tf_config.get('drive_url', ''))
        tf_template = tf_template.replace("{{TF_DESIGN_DOC_FOLDER_PATH}}", tf_config.get('design_doc_folder_path', ''))
        tf_template = tf_template.replace("{{TF_SPEC_DOC_FILENAME}}", tf_config.get('spec_doc_filename', ''))
        
        # レンダリング済み文字列として保存
        CONF['templates']['tf']['comment_template_rendered'] = tf_template

def setup_logger(log_file_path, logger_name=__name__):
    """ロガーの初期設定を行います。"""
    logger = getLogger(logger_name)
    logger.setLevel(DEBUG)

    sh = StreamHandler()
    sh.setLevel(DEBUG)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    fh = FileHandler(log_file_path)
    fh.setLevel(DEBUG)
    fh_formatter = Formatter('%(asctime)s - %(filename)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    
    return logger