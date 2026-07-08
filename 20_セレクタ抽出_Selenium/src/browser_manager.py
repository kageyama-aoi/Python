from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from . import config
from .logger import Logger

class BrowserManager:
    """Seleniumブラウザの起動と制御を行うクラス"""

    def __init__(self, mode: str = "popup", initial_url: str = "about:blank", prevent_navigation: bool = True):
        self.mode = mode
        self.initial_url = initial_url
        self.prevent_navigation = prevent_navigation
        self.driver = None
        self.is_running = False

    def load_js_script(self) -> str:
        """JavaScriptファイルを読み込み、設定値を埋め込む"""
        if not os.path.exists(config.JS_FILE):
            print(f"Error: {config.JS_FILE} が見つかりません。")
            return ""
        
        try:
            with open(config.JS_FILE, "r", encoding="utf-8") as f:
                js = f.read()
            
            # Python側の設定をJSの定数として埋め込む
            config_script = (
                f"const MODE = '{self.mode}';\n"
                f"const PREVENT_NAVIGATION = {'true' if self.prevent_navigation else 'false'};\n"
            )
            return config_script + js
        except Exception as e:
            print(f"JS読み込みエラー: {e}")
            return ""

    def start(self):
        """ブラウザを起動し、監視ループを開始する"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        
        # ログモードの場合のみコンソールログを取得できるようにする
        if self.mode == "log":
            options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.initial_url)
            self.is_running = True
            
            if self.mode == "log":
                Logger.log_session_start(self.initial_url)

            print(f"ブラウザ起動: モード={self.mode}, URL={self.initial_url}")
            print("終了するにはブラウザを閉じるか、コンソールでCtrl+Cを押してください。")

            self._monitor_loop()

        except Exception as e:
            print(f"ブラウザ起動中にエラーが発生しました: {e}")
        finally:
            self.stop()

    def stop(self):
        """ブラウザを終了する"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.driver = None
        self.is_running = False
        print("ブラウザを終了しました。")

    def _monitor_loop(self):
        """ブラウザの状態を監視し、ページ遷移時のスクリプト再注入やログ収集を行う"""
        last_url = ""
        script = self.load_js_script()

        try:
            while self.is_running:
                # ブラウザが閉じられたかチェック
                try:
                    current_url = self.driver.current_url
                except:
                    break

                # URLが変わった（ページ遷移した）場合、または初回
                if current_url != last_url:
                    if self.mode == "log" and last_url != "": 
                        Logger.log_page_transition(current_url)

                    try:
                        # bodyタグが読み込まれるまで待機
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(("tag name", "body"))
                        )
                        # スクリプト注入
                        self.driver.execute_script(script)
                    except Exception as e:
                        # 読み込み中のエラーは無視してリトライ
                        pass
                    
                    last_url = current_url

                # ログモードの場合はログを収集
                if self.mode == "log":
                    self._collect_browser_logs()

                time.sleep(1) 

        except KeyboardInterrupt:
            pass

    def _collect_browser_logs(self):
        """ブラウザのコンソールログを収集し、ファイルに保存する"""
        try:
            logs = self.driver.get_log("browser")
            for entry in logs:
                message = entry.get("message", "")
                if "TAG:" in message:
                    content = message.split("TAG:")[-1].strip()
                    # 引用符などが混ざる場合があるので整形
                    if content.endswith('"'):
                        content = content[:-1]
                    
                    Logger.log(content)
                    print(f"Log: {content}")
        except Exception:
            pass

# テスト用
if __name__ == "__main__":
    # テスト実行時はポップアップモードでGoogleを開く
    manager = BrowserManager(mode="popup", initial_url="https://www.google.com")
    manager.start()
