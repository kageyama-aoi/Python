import unicodedata

from openpyxl.comments import Comment
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from src.utils.fixed_format import REC_TYPE_HEADER, REC_TYPE_TRAILER

HEADER_FILL = PatternFill(start_color="44546A", end_color="44546A", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)

# レコード種別ごとの行の背景色（データはExcelの既定色のまま）
ROW_FILLS = {
    REC_TYPE_HEADER: PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid"),
    REC_TYPE_TRAILER: PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid"),
}

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


def style_output_sheet(ws, df, field_rules, rec_type_col="レコード種別"):
    """ヘッダー行の書式・項目コメント、レコード種別ごとの行色、列幅自動調整をまとめて適用する

    field_rules: {項目名: [(レコード種別ラベル, {"start", "length"}), ...]}
    （同じ項目名がヘッダー/データ/トレーラーで異なる位置定義を持つことがあるため、リストで持つ）
    """
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        entries = field_rules.get(cell.value)
        if entries:
            cell.comment = Comment(_comment_text(entries), "Fixed2Excel")

    if rec_type_col in df.columns:
        for row_idx, rec_type in enumerate(df[rec_type_col], start=2):
            fill = ROW_FILLS.get(rec_type)
            if fill:
                for cell in ws[row_idx]:
                    cell.fill = fill

    for col_idx, col_name in enumerate(df.columns, start=1):
        letter = get_column_letter(col_idx)
        values = [str(col_name)] + [str(v) for v in df[col_name].fillna("")]
        max_width = max(_display_width(v) for v in values)
        ws.column_dimensions[letter].width = min(max_width + 2, MAX_COLUMN_WIDTH)
