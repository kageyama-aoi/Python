import datetime
import random
import os
import glob
from src import config as cfg
from src import processor
from src import excel_writer
from src import data_loader

def cleanup_old_files():
    """過去の出力ファイルを削除する"""
    files_to_delete = glob.glob('output_summary_*.xlsx')
    files_to_delete.extend(glob.glob(str(cfg.OUTPUT_DIR / 'Summary_*.xlsx')))
    for file in files_to_delete:
        try:
            os.remove(file)
            print(f'ファイルが削除されました: {file}')
        except OSError as e:
            print(f'ファイル削除失敗: {file} - {e}')

def main():
    # 0. 準備
    cleanup_old_files()
    
    # 1. 設定の読み込み
    settings = data_loader.load_config()
    target_project = settings.get('target_project', '')
    target_employee = settings.get('target_employee', '')
    
    project_label = target_project if target_project else cfg.PROJECT_LABEL_DEFAULT
    employee_label = target_employee if target_employee else cfg.EMPLOYEE_LABEL_DEFAULT
    
    # パス設定
    now = datetime.datetime.now()
    random_number = random.randint(10000, 99999)
    temp_file01 = cfg.OUTPUT_DIR / f'Debug_Summary_{project_label}_{employee_label}_{now:%Y%m%d_%H%M%S}_{random_number}.xlsx'
    temp_file02 = cfg.OUTPUT_DIR / 'temp_intermediate.xlsx'
    
    # 最終成果物のファイル名：工数集計結果_案件名_氏名_YYYYMMDD.xlsx
    final_output = cfg.OUTPUT_DIR / f'工数集計結果_{project_label}_{employee_label}_{now:%Y%m%d}.xlsx'
    
    sheet_name_detail = 'Detailed Data'
    sheet_name_processed = 'Processed Data'
    sheet_name_monthly_summary = 'Monthly Summary'

    print(f"処理開始: {project_label} / {employee_label}")

    # 2. データの読み込みと加工
    df_raw = processor.load_and_filter_data(cfg.TIMESHEET_CSV_FILE, target_project, target_employee)
    df_processed = processor.process_details(df_raw)
    df_monthly = processor.aggregate_monthly(df_processed)
    df_bugs = data_loader.load_bugs_csv(cfg.TR_CSV_FILE)
    
    print(f'★要素数:{len(df_processed)}')

    # 3. 初期レポートの保存
    sheet_order = [
        (sheet_name_monthly_summary, df_monthly),
        (sheet_name_processed, df_processed),
        (sheet_name_detail, df_raw),
        ('TR', df_bugs)
    ]
    excel_writer.save_initial_report(temp_file01, sheet_order)
    
    # TRリストの更新
    excel_writer.save_initial_report(cfg.TR_LIST_FILE, [('TR', df_bugs)])

    # 4. 数式追加と中間保存
    excel_writer.add_formulas_and_save(df_processed, temp_file02, sheet_name_processed)

    # 5. シート抽出とスタイル適用
    excel_writer.extract_sheet_to_new_file(temp_file02, sheet_name_processed, final_output)
    excel_writer.apply_custom_styles(final_output)

    print(f'Excelブックが保存されました: {final_output}')

if __name__ == "__main__":
    main()