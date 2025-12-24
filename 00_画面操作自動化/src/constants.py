# VS code便利機能
# 一括コメントアウト
# Ctrl + /
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG

###########################
#  接続
###########################
# URL="http://demo.technopian.com/smsbugreport/bugfix.php?"
# 2024/8/7~
URL="https://taskreport.e-school.jp/bugfix.php"
DRIVER="c:/driver/chromedriver.exe"

###########################
#  HTML属性値
###########################
#-----初期画面------------
NEW_BUG_BUTTON_DOM_ATTRIBUTE = "goindex"


# #コメント内容設定--------
# Kaigou1="\n" # COMMENT_SEPARATOR を使用するため不要
DEFAULT_KAIHATU_COMMENT = "" # 未使用の可能性があるため、確認を推奨
DEFAULT_TYOUSA_COMMENT = ""  # 未使用の可能性があるため、確認を推奨
# Comme_Menu2="" # 下で直接定義するため不要

# コメント1:作業内容確認
COMMENT_SEPARATOR = "\n"
_MENU_1_LINES = [
    "今回の対象は？次の選択肢の中から入力してください",
    "------------------------------------------------------",
    "h:標準~",
    "y:Yamaha",
    "tf:Tframe",
    "s:Shimamura(本番サポート)~",
    "t:Shimamura_SMBCPOS追加開発",
    "up:Shimamura_UAT_UP依頼",
    "sm:Shimamura_mysql対応",
    "------------------------------------------------------"
]
MENU_1_PROMPT = COMMENT_SEPARATOR.join(_MENU_1_LINES)

#コメント2:対象環境の設定
ENVIRONMENT_LIST = {
    "t": "trainigGCP",
    "u": "UAT2",
    "st": "smbcpos_training",
    "su": "smbcpos_uat"
}
ENVIRONMENT_OPTIONS_STRING = COMMENT_SEPARATOR.join(f"{k}:{v}" for k, v in ENVIRONMENT_LIST.items())

_MENU_2_LINES = [
    "UP依頼対象環境は？次の選択肢の中から入力してください",
    "------------------------------------------------------",
    ENVIRONMENT_OPTIONS_STRING,
    "------------------------------------------------------"
]
MENU_2_PROMPT = COMMENT_SEPARATOR.join(_MENU_2_LINES)

###########################
#  TR設定値(改良)
###########################
# 入力欄（TR依存）
TR_FIELD_MAPPINGS = [
    ['Schools', "who_edit"],
    ['Project', "project"],
    ['Priority', "priority_edit"],
    ['Uploader', "uploader_edit"],
    ['Category', "where_edit"],
    ['Title', "what_edit"],
    ['Owner', "owned_edit"],
    ['Comments', "comments"]
]
# アンパック、Zip関数
TR_FIELDS, TR_HTML_ATTRIBUTES = zip(*TR_FIELD_MAPPINGS)

# 入力値(共通値)
DEFAULT_USER = 'kageyama'
DEFAULT_PRIORITY = 'Critical' # 'Critical', 'Serious' など

# 入力値(専用値:リリース)
UP_REQUEST_CATEGORY_TEMPLATE = "[KANKYOUMEI]環境_更新依頼"
UP_REQUEST_TITLE_TEMPLATE = "[KANKYOUMEI]環境_更新依頼"
UP_REQUEST_COMMENT_TEMPLATE = "下記のTRに紐づくschoolmngの資材を[KANKYOUMEI]環境へUPをお願いします。(TOTAL8)\r\nXXXXX\r\nXXXXX\r\nXXXXX\r\n\r\n今回事前事後対応がありま、、、"

# 入力値(専用値:リリース)
TF_DRIVE_URL = "https://drive.google.com/drive/folders/1H5jEButNwT_J55h7B4B6V7lqjHfvr-Ti"
TF_DESIGN_DOC_FOLDER_PATH = "002.Customer(Tframe)/001.JP_Document/002.Culture/01.詳細設計書/☆★43.謝礼合計(shareiTotal)"
TF_SPEC_DOC_FILENAME = "43-50.講師謝礼明細（個人）_【CultureT】_20250519.xlsx"
TF_COMMENT_TEMPLATE = f"保存URL:\r\n{TF_DRIVE_URL}\r\n\r\n日本語仕様書フォルダ：\r\n{TF_DESIGN_DOC_FOLDER_PATH}\r\n\r\n仕様書：\r\n{TF_SPEC_DOC_FILENAME}"

# 配列作成
# S_DEFAULTS は TR_FIELDS の順序に対応:
# ['Schools', 'Project', 'Priority', 'Uploader', 'Category', 'Title', 'Owner', 'Comments']
S_DEFAULTS = ["shimamura", "SMMs001PH", DEFAULT_PRIORITY, DEFAULT_USER, "-", "(UATxxx)-----(shimaXXs)", DEFAULT_USER, "sc"]
TF_DEFAULTS = ["tframe", "TCNz004PH", "Serious", DEFAULT_USER, "種別 機能番号", "【Culture】機能名", DEFAULT_USER, TF_COMMENT_TEMPLATE]
T_DEFAULTS = ["shimamura", "SMMN003PH", DEFAULT_PRIORITY, DEFAULT_USER, "-", "(UATxxx)-----(SMBCPOS21s)", DEFAULT_USER, "tc"]
Y_DEFAULTS = ["yamaha", "YMHs001PH", DEFAULT_PRIORITY, DEFAULT_USER, "-", "(Redminexxx)-----(GXX)", DEFAULT_USER, "yc"]
H_DEFAULTS = ["shimamura", "SMMs001PH", DEFAULT_PRIORITY, DEFAULT_USER, "-", "(UATxxx)-----(shimaXXs)", DEFAULT_USER, "hc"]
UP_REQUEST_DEFAULTS = [
    "shimamura",
    "",  # Project
    DEFAULT_PRIORITY,
    DEFAULT_USER,
    UP_REQUEST_CATEGORY_TEMPLATE,
    UP_REQUEST_TITLE_TEMPLATE,
    DEFAULT_USER,
    UP_REQUEST_COMMENT_TEMPLATE
]
SM_DEFAULTS = ["shimamura", "TCNz007PH", DEFAULT_PRIORITY, DEFAULT_USER, "-", "(MySQLVerUP対応)-----", DEFAULT_USER, "sc"]

SCHOOL_SPECIFIC_DEFAULTS = {
    "s": S_DEFAULTS,
    "y": Y_DEFAULTS,
    "tf": TF_DEFAULTS,
    "h": H_DEFAULTS,
    "t": T_DEFAULTS,
    "up": UP_REQUEST_DEFAULTS,
    "sm": SM_DEFAULTS
}

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