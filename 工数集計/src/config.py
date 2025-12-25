from pathlib import Path

# 基本ディレクトリの設定
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / 'input'
OUTPUT_DIR = BASE_DIR / 'output'

# ファイルパスの設定
CONFIG_FILE = BASE_DIR / 'config.json'
TR_CSV_FILE = INPUT_DIR / 'bugs.csv'
TIMESHEET_CSV_FILE = INPUT_DIR / 'timesheet.csv'
TR_LIST_FILE = OUTPUT_DIR / 'tr_list.xlsx'

# エンコーディング
ENCODING_CP932 = 'cp932'
ENCODING_UTF8 = 'utf-8'
ENCODING = ENCODING_CP932  # デフォルト（後方互換用）

# デフォルトラベル
PROJECT_LABEL_DEFAULT = "全案件"
EMPLOYEE_LABEL_DEFAULT = "全社員"

# Excel用カラーコード
COLOR_RIGHT_GREEN = '009999'
COLOR_RIGHT_BLUE = 'B8CCE4'
