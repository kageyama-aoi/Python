"""
自動操作ツールのエントリーポイント。
ユーザー入力を受け付け、ブラウザを起動し、フォーム自動入力処理を実行します。
"""
from selenium import webdriver
import datetime
import tkinter as tk
from tkinter import messagebox

import config
import browser_utils
from form_handler import FormAutomationHandler

# ログファイル名の設定
log_folder = '{0}.log'.format(datetime.date.today())

def get_user_input():
    """
    ユーザーからの入力を受け付け、実行に必要なパラメータを取得します。
    設定ファイル(config.yaml)で定義されたプロンプトを表示します。
    """
    print(config.CONF['menus']['menu_1_prompt'])
    user_select_school = input()

    environment_name = ""
    # "up" (更新依頼) の場合のみ、追加の環境選択を行う
    if user_select_school == "up":
        print(config.CONF['menus']['menu_2_prompt'])
        upload_destination = input()
        environment_name = config.CONF['menus']['environment_list'][upload_destination]
    return user_select_school, environment_name

def main():
    # 設定ファイルの読み込み
    config.load_config("config.yaml")
    logger = config.setup_logger(log_folder)

    user_select_school, environment_name = get_user_input()

    # ブラウザの初期化
    driver = webdriver.Chrome()
    driver.set_window_size(700, 1000)
    driver.implicitly_wait(10)
    
    try:
        driver.get(config.CONF['app']['url'])
        driver.implicitly_wait(3)
        
        # 初期アクション（新規作成ボタンのクリックなど）
        browser_utils.find_element(
            driver, 
            "name", 
            config.CONF['selectors']['new_bug_button_dom_attribute']
        ).click()

        # メイン処理：フォーム入力の実行
        context = {
            'schools_type': user_select_school,
            'environment_name': environment_name
        }
        form_handler = FormAutomationHandler(driver, context)
        form_handler.fill_form()

        # 完了通知
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo('完了メッセージ', '下書きを作成しました！')

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise e
    # finally ブロックで driver.quit() を呼ぶのが一般的だが、
    # 完了後もブラウザを開いたままにする要件と推測されるため省略

if __name__ == "__main__":
    main()