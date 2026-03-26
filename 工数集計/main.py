import datetime
import os
import glob
from src import config as cfg
from src import processor
from src import excel_writer
from src import data_loader
from src import selector
from src.constants import SheetNames as SN

def cleanup_old_files():
    """過去の出力ファイルを削除する"""
    files_to_delete = glob.glob(str(cfg.OUTPUT_DIR / 'temp_*.xlsx'))
    files_to_delete.extend(glob.glob(str(cfg.OUTPUT_DIR / '工数集計結果_*.xlsx')))
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
    target_project = settings.get(cfg.CONFIG_KEY_PROJECT, '')
    target_employee = settings.get(cfg.CONFIG_KEY_EMPLOYEE, '')

    # 未設定の場合はインタラクティブ選択
    if not target_project or not target_employee:
        target_project, target_employee = selector.select_target(
            cfg.TIMESHEET_CSV_FILE,
            default_project=target_project,
            default_employee=target_employee,
        )
        # 選択結果を config.json に保存して次回のデフォルトとする
        settings[cfg.CONFIG_KEY_PROJECT] = target_project
        settings[cfg.CONFIG_KEY_EMPLOYEE] = target_employee
        data_loader.save_config(settings)

    project_label = target_project if target_project else cfg.PROJECT_LABEL_DEFAULT
    employee_label = target_employee if target_employee else cfg.EMPLOYEE_LABEL_DEFAULT
    
    # パス設定
    now = datetime.datetime.now()
    temp_file01 = cfg.OUTPUT_DIR / f'temp_summary_{project_label}_{employee_label}_{now:%Y%m%d_%H%M%S}.xlsx'
    temp_file02 = cfg.OUTPUT_DIR / 'temp_intermediate.xlsx'
    
    # 最終成果物のファイル名：工数集計結果_案件名_氏名_YYYYMMDD.xlsx
    final_output = cfg.OUTPUT_DIR / f'工数集計結果_{project_label}_{employee_label}_{now:%Y%m%d}.xlsx'
    
    print(f"処理開始: {project_label} / {employee_label}")

    # 2. データの読み込みと加工
    df_raw = processor.load_and_filter_data(cfg.TIMESHEET_CSV_FILE, target_project, target_employee)
    df_processed = processor.process_details(df_raw)
    df_monthly = processor.aggregate_monthly(df_processed)
    df_bugs = data_loader.load_bugs_csv(cfg.TR_CSV_FILE)

    print(f'★要素数:{len(df_processed)}')

    # 3. 初期レポートの保存
    sheet_order = [
        (SN.MONTHLY_SUMMARY, df_monthly),
        (SN.PROCESSED, df_processed),
        (SN.DETAIL, df_raw),
        (SN.TR, df_bugs)
    ]
    excel_writer.save_initial_report(temp_file01, sheet_order)

    # TRリストの更新
    excel_writer.save_initial_report(cfg.TR_LIST_FILE, [(SN.TR, df_bugs)])

    # 4. 数式追加と中間保存
    excel_writer.add_formulas_and_save(df_processed, temp_file02, SN.PROCESSED)

    # 5. シート抽出とスタイル適用
    excel_writer.extract_sheet_to_new_file(temp_file02, SN.PROCESSED, final_output)
    excel_writer.apply_custom_styles(final_output)

    # 6. 中間ファイルの削除
    for temp_file in [temp_file01, temp_file02]:
        try:
            if temp_file.exists():
                os.remove(temp_file)
        except OSError as e:
            print(f'中間ファイル削除失敗: {temp_file} - {e}')

    print(f'Excelブックが保存されました: {final_output}')

if __name__ == "__main__":
    main()