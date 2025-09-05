import pandas as pd
import datetime
import random
import json
import logging

# 定数の定義
ENCODING = 'cp932'
PROJECT_LABEL_DEFAULT = "全案件"
EMPLOYEE_LABEL_DEFAULT = "全社員"
OUTPUT_DIR = './output/'
INPUT_DIR = './input/'
CONFIG_FILE = 'config.json'
TR_LIST_FILE = 'tr_list.xlsx'
TR_CSV_FILE = 'bugs.csv'
TIMESHEET_CSV_FILE = 'timesheet.csv'
SHEET_NAME_DETAIL = 'Detailed Data'
SHEET_NAME_PROCESSED = 'Processed Data'
SHEET_NAME_MONTHLY_SUMMARY = 'Monthly Summary'

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_timesheet_data(file_path, encoding='cp932'):
    """タイムシートデータを読み込む。"""
    try:
        employee_data = pd.read_csv(file_path, encoding=encoding)
    except FileNotFoundError:
        logging.error(f"ファイルが見つかりません: {file_path}")
        return None
    except Exception as e:
        logging.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return None
    return employee_data

def filter_timesheet_data(df, target_project, target_employee):
    """タイムシートデータをプロジェクトと従業員でフィルタリングする。"""
    if target_project:
        df_filtered = df[df['取引先名'] == target_project]
    else:
        df_filtered = df.copy()
    if target_employee:
        df_filtered = df_filtered[df_filtered['社員名'] == target_employee]
    return df_filtered

def select_columns(df, columns_to_keep):
    """必要な列のみを選択する。"""
    df_filtered = df[columns_to_keep]
    return df_filtered

def process_timesheet_data(df):
    """タイムシートデータを加工し、必要なデータを作成する。"""
    df['開始日'] = pd.to_datetime(df['開始日'])
    df['作業時間'] = (df['分'] / 60).round(2)
    df['PJコード'] = df['プロジェクトコード'] + ':' + df['プロジェクト名']
    df['メモ_区分'] = None
    df['メモ_詳細'] = None
    return df

def sort_timesheet_data(df, sort_key):
    """タイムシートデータのソートを行う。"""
    df_filtered_sorted = df[sort_key].sort_values(
        by=['社員名', 'PJコード', 'メモ', '開始日'],
        ascending=[True, True, True, True]
    ).reset_index(drop=True)
    return df_filtered_sorted

def summarize_monthly_data(df):
    """タイムシートデータを月別に集計する。"""
    monthly_summary_by_name = df.groupby(
        ['社員名', 'PJコード', df['開始日'].dt.to_period('M')]
    ).agg({
        '作業時間': 'sum'
    }).reset_index()

    columns_to_keep_month_summary = ['社員名', 'PJコード', '作業時間', '開始日']
    monthly_summary_sorted = monthly_summary_by_name[columns_to_keep_month_summary].sort_values(
        by=['社員名', '作業時間', 'PJコード'],
        ascending=[True, False, True]
    ).reset_index(drop=True)
    return monthly_summary_sorted

def save_data_to_excel(data_dict, output_file):
    """データをExcelファイルに保存する。"""
    try:
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        logging.error(f"Excelファイルの書き込み中にエラーが発生しました: {e}")

def process_timesheet(file_path, input_tr_csv, target_project, target_employee, temp_file01):
    """タイムシートデータを処理し、フィルタリングと集計を行い、Excelファイルに保存する。"""

    # 1. データの読み込み
    employee_data = read_timesheet_data(file_path)
    if employee_data is None:
        logging.error(f'csvファイルの取得に失敗したため、終了します。')
        return None, None, None

    # 2. データのフィルタリング
    df_filtered = filter_timesheet_data(employee_data, target_project, target_employee)

    # 3. データの必要な列の選択
    columns_to_keep = [
        '社員コード', '社員名', 'プロジェクトコード', 'プロジェクト名',
        '開始日', '分', 'メモ', '工程１:管理コード', '工程１:名称', '開始時間', '終了時間', '取引先名'
    ]
    df_filtered = select_columns(df_filtered, columns_to_keep)

    # 4. 不要になったデータは削除する。
    del employee_data

    # 5. データの加工
    df_filtered = process_timesheet_data(df_filtered)

    # 6. 列の追加と不要な列を削除
    columns_to_keep_sorted = [
        '社員コード', '社員名', 'PJコード',
        '開始日', '作業時間', 'メモ', 'メモ_区分', 'メモ_詳細', '工程１:管理コード', '工程１:名称', '開始時間', '終了時間'
    ]
    df_filtered_sorted = select_columns(df_filtered, columns_to_keep_sorted)

    # 7. データのソート
    df_filtered_sorted = sort_timesheet_data(df_filtered_sorted, columns_to_keep_sorted)

    # 8. 月別集計
    monthly_summary_sorted = summarize_monthly_data(df_filtered_sorted)

    # 9. Excelファイルに保存
    sheet_order = {
        SHEET_NAME_MONTHLY_SUMMARY: monthly_summary_sorted,
        SHEET_NAME_PROCESSED: df_filtered_sorted,
        SHEET_NAME_DETAIL: df_filtered,
        'TR': pd.read_csv(input_tr_csv)
    }
    save_data_to_excel(sheet_order, temp_file01)

    # 10 TR情報の保存
    try:
        with pd.ExcelWriter(TR_LIST_FILE, engine='xlsxwriter') as writer:
            pd.read_csv(input_tr_csv).to_excel(writer, sheet_name='TR', index=False)
    except FileNotFoundError:
        logging.error(f"ファイルが見つかりません: {input_tr_csv}")
    except Exception as e:
        logging.error(f"ファイルの書き込み中にエラーが発生しました: {e}")

    return temp_file01, TR_LIST_FILE, df_filtered_sorted
