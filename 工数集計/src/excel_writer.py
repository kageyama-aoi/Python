import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
import pandas as pd
from . import config as cfg

def save_initial_report(temp_file_path, sheet_data_list):
    """
    初期データをExcelに保存する
    sheet_data_list: [(sheet_name, dataframe), ...]
    """
    with pd.ExcelWriter(temp_file_path, engine='xlsxwriter') as writer:
        for sheet_name, df in sheet_data_list:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def add_formulas_and_save(df, output_path, sheet_name):
    """
    データフレームにExcel数式を追加して保存し、D列を値として確定させる
    """
    sum_name_label = '集計_社員名'
    sum_pj_label = '集計_PJコード'
    sum_time_label = '集計_工数(h)'
    sum_block1_label = '集計_ブロック'
    sum_time_block1_label = '集計_工数(h)_番外'
    
    labels = [sum_name_label, sum_pj_label, sum_time_label, sum_block1_label, sum_time_block1_label]

    # 列の挿入
    for i, label in enumerate(labels):
        df.insert(i, label, '')

    # 列番号の特定
    col_num = {
        '社員名': None, 'PJコード': None, '作業時間': None, 
        sum_name_label: None, sum_pj_label: None, sum_time_label: None, 
        'メモ_区分': None, 'メモ_詳細': None, 'メモ': None
    }
    for col in df.columns:
        if col in col_num:
            col_num[col] = df.columns.get_loc(col) + 1

    if not all(col_num.values()):
        # ログ出力などは呼び出し元で行うか、ここで例外を出す
        raise ValueError("必要なヘッダーが見つかりませんでした。")

    # 列レターの取得
    column_sagyou = get_column_letter(col_num['作業時間'])
    column_syainmei = get_column_letter(col_num['社員名'])
    column_pjcode = get_column_letter(col_num['PJコード'])
    column_memo = get_column_letter(col_num['メモ'])
    column_memo_kubun = get_column_letter(col_num['メモ_区分'])
    keyword_syain = get_column_letter(col_num[sum_name_label])
    keyword_pj = get_column_letter(col_num[sum_pj_label])
    
    one_line_ago_syainmmei_value = ''
    one_line_ago_pjcode_value = ''
    
    # 行ごと処理
    for index, row in df.iterrows():
        syainmmei_value = row['社員名']
        pjcode_value = row['PJコード']
        excel_row = index + 2

        # 数式の埋め込み
        df.at[index, 'メモ_区分'] = f'=IFERROR(LEFT({column_memo}{excel_row}, FIND(",", {column_memo}{excel_row}) - 1), "-")'
        df.at[index, 'メモ_詳細'] = f'=IFERROR(MID({column_memo}{excel_row}, FIND(",", {column_memo}{excel_row}) + 1, LEN({column_memo}{excel_row}) - FIND(",", {column_memo}{excel_row})), {column_memo}{excel_row})'
        df.at[index, '工程１:名称'] = row['メモ_区分']
        df.at[index, '集計_ブロック'] = f'={column_memo_kubun}{excel_row}'
        df.at[index, sum_name_label] = syainmmei_value
        df.at[index, sum_pj_label] = pjcode_value
        df.at[index, sum_time_block1_label] = f"=SUMIFS({column_sagyou}:{column_sagyou}, {column_syainmei}:{column_syainmei}, {keyword_syain}{excel_row}, {column_pjcode}:{column_pjcode}, {keyword_pj}{excel_row}, {column_memo_kubun}:{column_memo_kubun}, {column_memo_kubun}{excel_row})"  

        if syainmmei_value == one_line_ago_syainmmei_value and pjcode_value == one_line_ago_pjcode_value:
            continue
        
        df.at[index, sum_time_label] = f"=SUMIFS({column_sagyou}:{column_sagyou}, {column_syainmei}:{column_syainmei}, {keyword_syain}{excel_row}, {column_pjcode}:{column_pjcode}, {keyword_pj}{excel_row})"  
        
        one_line_ago_syainmmei_value = syainmmei_value
        one_line_ago_pjcode_value = pjcode_value

    # 一旦保存
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
    # 再読み込みして調整
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    # D列を値のみにする処理（既存ロジックを継承）
    for row in range(1, ws.max_row + 1):
        ws[f'D{row}'] = ws[f'D{row}'].value
        
    wb.save(output_path)

def extract_sheet_to_new_file(input_path, sheet_name, output_path):
    """指定されたシートを新しいExcelファイルとして抽出する"""
    wb = openpyxl.load_workbook(input_path)
    new_wb = openpyxl.Workbook()
    new_ws = new_wb.active
    
    if sheet_name not in wb.sheetnames:
        return
        
    ws = wb[sheet_name]

    for row in ws.iter_rows(values_only=True):
        new_ws.append(row)

    new_ws.title = sheet_name
    if 'Sheet' in new_wb.sheetnames:
        new_wb.remove(new_wb['Sheet'])

    new_wb.save(output_path)

def apply_custom_styles(file_path):
    """Excelシートにスタイル（固定、背景色、列幅、グループ化）を適用する"""
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    
    sheet.freeze_panes = 'A2'
    
    fill_green = PatternFill(start_color=cfg.COLOR_RIGHT_GREEN, end_color=cfg.COLOR_RIGHT_GREEN, fill_type='solid')
    fill_blue = PatternFill(start_color=cfg.COLOR_RIGHT_BLUE, end_color=cfg.COLOR_RIGHT_BLUE, fill_type='solid')
    
    # ヘッダー背景色
    for i in range(1, 6):
        sheet.cell(row=1, column=i).fill = fill_blue
    for i in range(6, 15):
        sheet.cell(row=1, column=i).fill = fill_green

    # 特定列の背景色
    for i in range(1, 200):
        sheet.cell(row=i, column=15).fill = fill_blue
        sheet.cell(row=i, column=16).fill = fill_blue

    # 列幅の自動調整（一部除外）
    for col in sheet.columns:
        column_letter = get_column_letter(col[0].column)
        if column_letter not in ['C','E','O','J']:
            max_length = max((len(str(cell.value)) for cell in col if cell.value is not None), default=0)
            adjusted_width = (max_length + 2) * 1.1
            sheet.column_dimensions[column_letter].width = adjusted_width

    # 列グループ化
    sheet.column_dimensions.group('F', 'I', hidden=True)
    sheet.column_dimensions.group('J', 'N', hidden=True)

    wb.save(file_path)
