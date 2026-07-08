class InputCols:
    """入力CSV (timesheet.csv) の列名定義"""
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

class SheetNames:
    """Excelブック内のシート名定義"""
    MONTHLY_SUMMARY = 'Monthly Summary'
    PROCESSED = 'Processed Data'
    DETAIL = 'Detailed Data'
    TR = 'TR'


class StyleConfig:
    """apply_custom_styles() で使用する列位置・グループ定義"""
    # ヘッダー色塗り範囲（1始まり）
    HEADER_BLUE_COLS = range(1, 6)    # A〜E
    HEADER_GREEN_COLS = range(6, 15)  # F〜N
    # 全行色塗り列番号
    FILL_BLUE_COL_1 = 15  # O
    FILL_BLUE_COL_2 = 16  # P
    # 列幅自動調整から除外する列
    WIDTH_SKIP_COLS = {'C', 'E', 'O', 'J'}
    # 列グループ化（非表示）
    GROUP_1_START = 'F'
    GROUP_1_END = 'I'
    GROUP_2_START = 'J'
    GROUP_2_END = 'N'


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
