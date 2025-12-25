import pandas as pd
from . import config as cfg

def load_and_filter_data(file_path, target_project=None, target_employee=None):
    """CSVを読み込み、プロジェクトと社員でフィルタリングする"""
    df = pd.read_csv(file_path, encoding=cfg.ENCODING)
    
    if target_project:
        df = df[df['取引先名'] == target_project]
    
    if target_employee:
        df = df[df['社員名'] == target_employee]
        
    return df

def process_details(df):
    """詳細データの加工（作業時間の計算、列の追加など）を行う"""
    df = df.copy()
    
    # 必要な列の定義
    columns_to_keep = [
        '社員コード', '社員名', 'プロジェクトコード', 'プロジェクト名',
        '開始日', '分', 'メモ', '工程１:管理コード', '工程１:名称', '開始時間', '終了時間', '取引先名'
    ]
    # 指定された列のみを保持（存在しない列がある場合は無視するように安全に処理）
    df = df[[c for c in columns_to_keep if c in df.columns]]

    # データの型変換と計算
    df['開始日'] = pd.to_datetime(df['開始日'])
    df['作業時間'] = (df['分'] / 60).round(2)
    df['PJコード'] = df['プロジェクトコード'] + ':' + df['プロジェクト名']
    
    # メモ関連の空列追加
    df['メモ_区分'] = None 
    df['メモ_詳細'] = None

    # 列の並び替えと不要な列の削除
    result_columns = [
        '社員コード', '社員名', 'PJコード', '開始日', '作業時間', 
        'メモ_詳細', 'メモ_区分', '工程１:管理コード', '工程１:名称', '開始時間', '終了時間', 'メモ'
    ]
    # 最終的に必要な列だけを選択して並び替える
    return df[[c for c in result_columns if c in df.columns]].sort_values(
        by=['社員名', 'PJコード', 'メモ', '開始日']
    ).reset_index(drop=True)

def aggregate_monthly(df):
    """月次集計を行う"""
    if df.empty:
        return pd.DataFrame()

    # 月単位で集計
    monthly_summary = df.groupby(
        ['社員名', 'PJコード', df['開始日'].dt.to_period('M')]
    ).agg({
        '作業時間': 'sum'
    }).reset_index()

    # 表示用に列を整理
    monthly_summary = monthly_summary.sort_values(
        by=['社員名', '作業時間', 'PJコード'],
        ascending=[True, False, True]
    ).reset_index(drop=True)
    
    return monthly_summary
