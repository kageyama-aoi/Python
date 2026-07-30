import unicodedata

import pandas as pd
from openpyxl.comments import Comment
from openpyxl.styles import Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.utils.fixed_format import REC_TYPE_END, REC_TYPE_HEADER, REC_TYPE_TRAILER

# 区切り列の見出し文字列（表示上は空白。列ごとに空白の個数を変えて一意な列名にする）
SEPARATOR_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
SEPARATOR_WIDTH = 3

HEADER_FILL = PatternFill(start_color="44546A", end_color="44546A", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)

# レコード種別ごとの行の背景色（データはExcelの既定色のまま）
ROW_FILLS = {
    REC_TYPE_HEADER: PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid"),
    REC_TYPE_TRAILER: PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid"),
    REC_TYPE_END: PatternFill(start_color="E2D9F3", end_color="E2D9F3", fill_type="solid"),
}

THIN_SIDE = Side(style="thin", color="B7B7B7")
CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)

# 同じレコード種別が連続する行/列をグループ化する際の最小連続数（1つだけの折りたたみは無意味なので対象外）
MIN_GROUP_SIZE = 2

MAX_COLUMN_WIDTH = 60


def _display_width(text):
    """全角文字を2、半角文字を1として表示幅を概算する"""
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def _comment_text(entries):
    """項目コメントを組み立てる。同じ列名がレコード種別をまたいで別定義を持つ場合は種別ごとに併記する"""
    if len(entries) == 1:
        _, rule = entries[0]
        return f"開始位置:{rule['start'] + 1} 文字数:{rule['length']}"
    return "\n".join(
        f"{label}: 開始位置:{rule['start'] + 1} 文字数:{rule['length']}" for label, rule in entries
    )


def _group_contiguous_ranges(types, start_index):
    """typesの値が連続する区間を求める（start_indexから採番、1-indexed）

    Noneは常に区切りとして扱い、グループに含めない（行番号・区分等、種別を持たない列向け）。
    戻り値: [(開始, 終了), ...]（MIN_GROUP_SIZE未満の連続は対象外）
    """
    ranges = []
    run_start = None
    prev = None
    idx = start_index
    for t in types:
        if t != prev:
            if run_start is not None and idx - run_start >= MIN_GROUP_SIZE:
                ranges.append((run_start, idx - 1))
            run_start = idx if t is not None else None
            prev = t
        idx += 1
    if run_start is not None and idx - run_start >= MIN_GROUP_SIZE:
        ranges.append((run_start, idx - 1))
    return ranges


def _group_row_ranges(rec_types):
    """レコード種別が連続している行範囲を求める（1-indexed, データ部分は start=2 から）"""
    return _group_contiguous_ranges(rec_types, start_index=2)


def _column_type(name, field_rules):
    """列名からレコード種別ラベルを引く（field_rulesに無い列はNone）。同じ項目名が複数の
    レコード種別にまたがる場合は、先頭の種別で代表させる。"""
    entries = field_rules.get(name)
    return entries[0][0] if entries else None


def is_separator_column(name):
    """insert_group_separatorsが挿入した空白の区切り列かどうか"""
    return isinstance(name, str) and name != "" and name.strip() == ""


def insert_group_separators(df, field_rules):
    """レコード種別が切り替わる境目に空白の区切り列を挿入したDataFrameを返す

    項目列同士が隙間なく隣接していると、Excelのアウトライン機能は種別ごとに独立した
    折りたたみグループを作れず、全体が1つの範囲に融合してしまう。区切り列を挟むことで
    ヘッダー/データ/トレーラーの各ブロックを個別に開閉できるようにする。
    行番号・区分・レコード種別などfield_rulesに無い列と最初のブロックの間には挿入しない
    （種別ブロック同士が切り替わる境目にのみ挿入する）。
    """
    columns = list(df.columns)
    types = [_column_type(name, field_rules) for name in columns]

    new_order = []
    sep_count = 0
    prev_type = None
    for name, t in zip(columns, types):
        if t is not None and prev_type is not None and t != prev_type:
            sep_count += 1
            new_order.append(" " * sep_count)  # 空白のみ・列ごとに個数を変えて一意にする
        new_order.append(name)
        prev_type = t

    result = pd.DataFrame(index=df.index)
    for col in new_order:
        result[col] = df[col] if col in df.columns else ""
    return result


def _group_column_ranges(columns, field_rules):
    """項目が属するレコード種別ごとに連続する列範囲を求める（1-indexed）

    行番号・区分・レコード種別・区切り列のように field_rules に定義のない列は区切りとして扱う。
    """
    types = [_column_type(name, field_rules) for name in columns]
    return _group_contiguous_ranges(types, start_index=1)


def style_output_sheet(ws, df, field_rules, rec_type_col="レコード種別"):
    """ヘッダー行の書式・項目コメント、レコード種別ごとの行色・行/列グループ化、罫線、列幅自動調整をまとめて適用する

    field_rules: {項目名: [(レコード種別ラベル, {"start", "length"}), ...]}
    （同じ項目名がヘッダー/データ/トレーラーで異なる位置定義を持つことがあるため、リストで持つ）
    """
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.border = CELL_BORDER
        entries = field_rules.get(cell.value)
        if entries:
            cell.comment = Comment(_comment_text(entries), "Fixed2Excel")

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.border = CELL_BORDER

    if rec_type_col in df.columns:
        rec_types = list(df[rec_type_col])

        for row_idx, rec_type in enumerate(rec_types, start=2):
            fill = ROW_FILLS.get(rec_type)
            if fill:
                for cell in ws[row_idx]:
                    cell.fill = fill

        # 同じレコード種別が連続するデータ部を折りたたみ可能なグループにする（Excelのアウトライン機能）
        for start_row, end_row in _group_row_ranges(rec_types):
            for row_idx in range(start_row, end_row + 1):
                ws.row_dimensions[row_idx].outlineLevel = 1

    for col_idx, col_name in enumerate(df.columns, start=1):
        letter = get_column_letter(col_idx)
        if is_separator_column(col_name):
            ws.column_dimensions[letter].width = SEPARATOR_WIDTH
            for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
                for cell in row:
                    cell.fill = SEPARATOR_FILL
            continue
        values = [str(col_name)] + [str(v) for v in df[col_name].fillna("")]
        max_width = max(_display_width(v) for v in values)
        ws.column_dimensions[letter].width = min(max_width + 2, MAX_COLUMN_WIDTH)

    # レコード種別ごとに連続する項目列を折りたたみ可能なグループにする（Excelのアウトライン機能）
    for start_col, end_col in _group_column_ranges(df.columns, field_rules):
        for col_idx in range(start_col, end_col + 1):
            ws.column_dimensions[get_column_letter(col_idx)].outlineLevel = 1
