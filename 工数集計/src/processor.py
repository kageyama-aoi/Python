

import pandas as pd
from . import config as cfg
from .constants import InputCols as IC, InternalCols as RC

def load_and_filter_data(file_path, target_project=None, target_employee=None):
    """CSVを読み込み、プロジェクトと社員でフィルタリングする"""
    df = pd.read_csv(file_path, encoding=cfg.ENCODING)
    
    if target_project:
        df = df[df[IC.CLIENT_NAME] == target_project]
    
    if target_employee:
        df = df[df[IC.EMPLOYEE_NAME] == target_employee]
        
    return df

def process_details(df):
    """詳細データの加工（作業時間の計算、列の追加など）を行う"""
    df = df.copy()
    
    # 必要な列の定義
    columns_to_keep = [
        IC.EMPLOYEE_CODE, IC.EMPLOYEE_NAME, IC.PROJECT_CODE, IC.PROJECT_NAME,
        IC.START_DATE, IC.MINUTES, IC.MEMO, IC.PROCESS_1_CODE, IC.PROCESS_1_NAME,
        IC.START_TIME, IC.END_TIME, IC.CLIENT_NAME
    ]
    # 指定された列のみを保持（存在しない列がある場合は無視するように安全に処理）
    df = df[[c for c in columns_to_keep if c in df.columns]]

    # データの型変換と計算
    df[IC.START_DATE] = pd.to_datetime(df[IC.START_DATE])
    df[RC.WORK_HOURS] = (df[IC.MINUTES] / 60).round(2)
    df[RC.PJ_CODE] = df[IC.PROJECT_CODE] + ':' + df[IC.PROJECT_NAME]
    
    # メモ関連の空列追加
    df[RC.MEMO_TYPE] = None 
    df[RC.MEMO_DETAIL] = None

    # 列の並び替えと不要な列の削除
    result_columns = [
        IC.EMPLOYEE_CODE, IC.EMPLOYEE_NAME, RC.PJ_CODE, IC.START_DATE, RC.WORK_HOURS, 
        RC.MEMO_DETAIL, RC.MEMO_TYPE, IC.PROCESS_1_CODE, IC.PROCESS_1_NAME, 
        IC.START_TIME, IC.END_TIME, IC.MEMO
    ]
    # 最終的に必要な列だけを選択して並び替える
    return df[[c for c in result_columns if c in df.columns]].sort_values(
        by=[IC.EMPLOYEE_NAME, RC.PJ_CODE, IC.MEMO, IC.START_DATE]
    ).reset_index(drop=True)

def aggregate_monthly(df):
    """月次集計を行う"""
    if df.empty:
        return pd.DataFrame()

    # 月単位で集計
    monthly_summary = df.groupby(
        [IC.EMPLOYEE_NAME, RC.PJ_CODE, df[IC.START_DATE].dt.to_period('M')]
    ).agg({
        RC.WORK_HOURS: 'sum'
    }).reset_index()

    # 表示用に列を整理
    monthly_summary = monthly_summary.sort_values(
        by=[IC.EMPLOYEE_NAME, RC.WORK_HOURS, RC.PJ_CODE],
        ascending=[True, False, True]
    ).reset_index(drop=True)
    
    return monthly_summary
