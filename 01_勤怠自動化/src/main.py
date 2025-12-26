"""
自動操作ツールのエントリーポイント。
ユーザー入力を受け付け、ブラウザを起動し、フォーム自動入力処理を実行します。
"""
import os
from selenium import webdriver
import datetime
import tkinter as tk
from tkinter import messagebox

import config
import browser_utils
import file_utils
from form_handler import FormAutomationHandler
import gui

# ログファイル名の設定
log_folder = '{0}.log'.format(datetime.date.today())

def main():
    # 設定ファイルの読み込み
    config.load_config("config/config.yaml")
    logger = config.setup_logger(log_folder)

    # GUIによるユーザー入力の取得
    user_select_school, environment_name = gui.get_user_input_gui()
    
    # ユーザーがキャンセルまたは閉じた場合
    if user_select_school is None:
        print("操作がキャンセルされました。")
        return

    # ブラウザの初期化
    driver = webdriver.Chrome()
    driver.set_window_size(1000, 1000) # CrowdLog用に少し広めに
    driver.implicitly_wait(10)
    
    try:
        print(f"DEBUG: Selected School Type: {user_select_school}") # Debug
        
        target_url = ""
        if user_select_school == 'cl':
            target_url = config.CONF['app']['url']
        else:
            # TR用のURLが設定にあればそれを使う、なければデフォルト(app.url)を使う
            # 現状configにないので、app.urlが使われるが、ここを分離ポイントとする
            target_url = config.CONF['app'].get('task_report_url', config.CONF['app']['url'])
        
        print(f"DEBUG: Navigating to {target_url}")
        driver.get(target_url)
        driver.implicitly_wait(3)
        
        # 初期アクション（タスクレポート系のみ）
        # TR用URLに直接飛んだ場合は、このボタンクリックは不要になるかもしれないが
        # 既存ロジック(app.urlが共通だった場合)のために残しておく
        if user_select_school != 'cl':
            # もしTR用URLが設定されていれば、このボタンクリックはスキップする判定を入れても良い
            # ここでは要素が存在する場合のみクリックするように変更して安全性を高める
            btn_selector = config.CONF['selectors']['new_bug_button_dom_attribute']
            if browser_utils.is_element_present(driver, "name", btn_selector):
                browser_utils.find_element(driver, "name", btn_selector).click()
            else:
                print(f"Warning: New bug button ({btn_selector}) not found on page.")

        # メイン処理：フォーム入力の実行
        context = {
            'schools_type': user_select_school,
            'environment_name': environment_name
        }
        form_handler = FormAutomationHandler(driver, context)
        form_handler.fill_form()

        # CrowdLogの場合、ファイルのダウンロード完了を待って移動
        if user_select_school == 'cl':
            # Windows標準のダウンロードフォルダ
            default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            target_dir = config.CONF['app'].get('download_dir', 'data/downloads/')
            
            moved_path = file_utils.move_latest_downloaded_file(default_download_dir, target_dir)
            
            if moved_path:
                msg = f'CSVのダウンロードと移動が完了しました！\n保存先: {moved_path}'
            else:
                msg = 'ダウンロードのタイムアウト、またはファイルが見つかりませんでした。'
        else:
            msg = '下書きを作成しました！'

        # 完了通知
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo('完了メッセージ', msg)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()