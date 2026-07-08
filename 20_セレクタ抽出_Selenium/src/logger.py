import os
from datetime import datetime
from . import config

class Logger:
    """ログ出力を管理するクラス"""

    @staticmethod
    def setup():
        """ログディレクトリの作成"""
        os.makedirs(config.LOG_DIR, exist_ok=True)

    @staticmethod
    def log(message: str, timestamped: bool = True):
        """
        ログファイルにメッセージを追記する
        
        Args:
            message (str): 記録するメッセージ
            timestamped (bool): タイムスタンプを付与するかどうか
        """
        Logger.setup() # 念のため存在確認
        
        entry = message
        if timestamped:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{ts}] {message}"
        
        try:
            with open(config.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            print(f"ログ保存エラー: {e}")

    @staticmethod
    def write_separator(char="-", length=40):
        """区切り線を出力する"""
        Logger.log(char * length, timestamped=False)

    @staticmethod
    def log_session_start(url: str):
        """セッション開始時のヘッダーを出力"""
        Logger.log("", timestamped=False) # 空行
        Logger.write_separator("=", 60)
        Logger.log(f"セッション開始")
        Logger.log(f"初期URL: {url}")
        Logger.write_separator("=", 60)

    @staticmethod
    def log_page_transition(url: str):
        """ページ遷移時の情報を出力"""
        Logger.log("", timestamped=False)
        Logger.write_separator("-", 40)
        Logger.log(f"ページ移動: {url}")
        Logger.write_separator("-", 40)

# 簡易テスト用
if __name__ == "__main__":
    print(f"Logging to: {config.LOG_FILE}")
    Logger.log("Test log entry from independent module.")
    Logger.log_session_start("http://test.com")
