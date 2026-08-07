import csv
import io
import sys
from pathlib import Path

# src/ の1つ上（プロジェクトルート）を基準にする。cwdに依存しないため、
# run.batから起動しても直接 `python src/csv_to_tsv.py` を実行しても同じ場所を指す。
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"

# 上位から順に試すエンコード。utf-8-sig は BOM付きUTF-8も無印UTF-8も両方読める。
_ENCODING_CANDIDATES = [
    ("utf-8-sig", "UTF-8"),
    ("cp932", "Shift-JIS"),
]


class CsvToTsvError(RuntimeError):
    """このスクリプトの、原因を人間向けに説明するエラー。"""


def _decode_with_fallback(path: Path) -> str:
    """UTF-8 → Shift-JIS の順でファイル全体のデコードを試みる。全滅したら原因を含めて例外を投げる。"""
    raw = path.read_bytes()
    errors = []
    for encoding, label in _ENCODING_CANDIDATES:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{label}: {exc}")
    detail = "\n".join(f"  - {e}" for e in errors)
    raise CsvToTsvError(
        f"'{path.name}' の文字コードを判別できませんでした（UTF-8 / Shift-JIS を試行）。\n"
        f"{detail}\n"
        f"→ CSVをUTF-8で保存し直してから再実行してください。"
    )


def convert_csv_to_tsv(csv_path: Path, output_dir: Path = OUTPUT_DIR) -> Path:
    """1つのCSVをTSVに変換し、出力先パスを返す。"""
    text = _decode_with_fallback(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = output_dir / csv_path.with_suffix(".tsv").name

    reader = csv.reader(io.StringIO(text))
    with tsv_path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile, delimiter="\t")
        for row in reader:
            writer.writerow(row)
    return tsv_path


def main() -> int:
    csv_files = sorted(INPUT_DIR.glob("*.csv"))
    if not csv_files:
        print(f"\nエラー: '{INPUT_DIR}/' にCSVファイルが見つかりませんでした。", file=sys.stderr)
        print(f"→ 変換したいCSVを '{INPUT_DIR}/' フォルダに置いてから再実行してください。", file=sys.stderr)
        return 1

    print(f"対象CSVファイル数: {len(csv_files)}")
    exit_code = 0
    for csv_path in csv_files:
        print(f"読み込み中: {csv_path.name}")
        try:
            tsv_path = convert_csv_to_tsv(csv_path)
            print(f"  変換完了: {tsv_path.name}")
        except CsvToTsvError as exc:
            print(f"  エラー: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
