
from selenium import webdriver
import datetime
import sys
from tkinter import messagebox
#Tkinterメッセージボックス利用時の空ウィンドウ削除のため
import tkinter as tk

#設定値ファイル
import config
import browser_utils
from form_handler import FormAutomationHandler

# 保存するファイル名を指定
log_folder = '{0}.log'.format(datetime.date.today())
# ログの初期設定を行う
logger = config.setup_logger(log_folder)

##################################
###ユーザー入力:対応種別
###ユーザー入力:環境名
##################################

# print(input_item.x)
print(config.MENU_1_PROMPT)
user_select_school = input()

environment_name = ""
if user_select_school == "up":
    print(config.MENU_2_PROMPT)
    upload_destination = input()
    environment_name = config.ENVIRONMENT_LIST[upload_destination]

##################################
#ドライバ設定
# seleniumバージョンUP対応 Driver引数不要
##################################
driver = webdriver.Chrome()
driver.set_window_size(700,1000)
driver.implicitly_wait(10) # seconds
driver.get(config.URL)
driver.implicitly_wait(3) # seconds
browser_utils.find_element(driver,"name",config.NEW_BUG_BUTTON_DOM_ATTRIBUTE).click()  


# ##################################
# ###メイン処理
# ##################################
i_InputIem = FormAutomationHandler(driver,user_select_school,environment_name)
i_InputIem.setItems()

#################
#  後処理:ポップアップ   
#################
#Tkinterのルートウィンドウを作成して非表示に
root = tk.Tk()
root.withdraw()

messagebox.showinfo('完了メッセージ','下書きを作成しました！')

# #driver.refresh()