import os

# アプリケーション設定
APP_TITLE = "セレクタ抽出ツール"
WINDOW_SIZE = "400x300"

# パス設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # プロジェクトルート
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "selector_log.txt")
JS_DIR = os.path.join(BASE_DIR, "js")
JS_FILE = os.path.join(JS_DIR, "injector.js")

# デフォルト値
DEFAULT_URL = "https://newculture.e-school.jp/beta/index.php"
DEFAULT_MODE = "popup"

# メッセージ
MSG_URL_EMPTY = "URLを入力してください"
