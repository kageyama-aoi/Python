import sys
from .constants import InputCols as IC

# タイムシートCSVに必須の列
_REQUIRED_TIMESHEET_COLS = [
    IC.EMPLOYEE_CODE, IC.EMPLOYEE_NAME,
    IC.PROJECT_CODE, IC.PROJECT_NAME,
    IC.MINUTES, IC.START_DATE, IC.MEMO,
    IC.CLIENT_NAME, IC.START_TIME, IC.END_TIME,
    IC.PROCESS_1_CODE, IC.PROCESS_1_NAME,
]


def validate_timesheet_columns(df):
    """タイムシートDataFrameに必要な列が揃っているか検証する"""
    missing = [col for col in _REQUIRED_TIMESHEET_COLS if col not in df.columns]
    if missing:
        print("エラー: timesheet.csv に必要な列が見つかりません。以下の列を確認してください：")
        for col in missing:
            print(f"  - {col}")
        sys.exit(1)
