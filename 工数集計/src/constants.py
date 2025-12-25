class InputCols:
    """入力CSV (timesheet.csv) の列名定義"""
    YEAR = "年"
    MONTH = "月"
    DAY = "日"
    EMPLOYEE_CODE = "社員コード"
    EMPLOYEE_NAME = "社員名"
    PROJECT_CODE = "プロジェクトコード"
    PROJECT_NAME = "プロジェクト名"
    MINUTES = "分"
    START_TIME = "開始時間"
    END_TIME = "終了時間"
    MEMO = "メモ"
    CLIENT_NAME = "取引先名"
    START_DATE = "開始日"
    PROCESS_1_CODE = "工程１:管理コード"
    PROCESS_1_NAME = "工程１:名称"

class InternalCols:
    """内部処理および出力Excelで使用する列名定義"""
    # 加工後の列名
    PJ_CODE = "PJコード"      # プロジェクトコード + 名称
    WORK_HOURS = "作業時間"   # 分 / 60
    MEMO_TYPE = "メモ_区分"
    MEMO_DETAIL = "メモ_詳細"
    
    # 集計用（数式で使用）
    SUM_EMPLOYEE = "集計_社員名"
    SUM_PJ = "集計_PJコード"
    SUM_HOURS = "集計_工数(h)"
    SUM_BLOCK = "集計_ブロック"
    SUM_HOURS_EXTRA = "集計_工数(h)_番外"
