
from selenium import webdriver
import datetime
import sys
from tkinter import messagebox
import tkinter as tk

#設定値ファイル
import config
import browser_utils
from form_handler import FormAutomationHandler

# ログの初期設定を行う
log_folder = '{0}.log'.format(datetime.date.today())

def get_user_input():
    """ユーザーからの入力（学校選択と環境名）を取得する関数"""
    print(config.CONF['menus']['menu_1_prompt'])
    user_select_school = input()

    environment_name = ""
    if user_select_school == "up":
        print(config.CONF['menus']['menu_2_prompt'])
        upload_destination = input()
        environment_name = config.CONF['menus']['environment_list'][upload_destination]
    return user_select_school, environment_name

def main():
    config.load_config("config.yaml") # config.yaml を読み込む
    logger = config.setup_logger(log_folder) # logger の初期化は config.load_config の後に行う

    user_select_school, environment_name = get_user_input()

    ##################################
    #ドライバ設定
    # seleniumバージョンUP対応 Driver引数不要
    ##################################
    driver = webdriver.Chrome()
    driver.set_window_size(700,1000)
    driver.implicitly_wait(10) # seconds
    driver.get(config.CONF['app']['url'])
    driver.implicitly_wait(3) # seconds
    browser_utils.find_element(driver,"name",config.CONF['selectors']['new_bug_button_dom_attribute']).click()  

    # ##################################
    # ###メイン処理
    # ##################################
    context = {
        'schools_type': user_select_school,
        'environment_name': environment_name
    }
    form_handler = FormAutomationHandler(driver, context)
    form_handler.fill_form()

    #################
    #  後処理:ポップアップ   
    #################
    #Tkinterのルートウィンドウを作成して非表示に
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo('完了メッセージ','下書きを作成しました！')

    # #driver.refresh()

if __name__ == "__main__":
    main()