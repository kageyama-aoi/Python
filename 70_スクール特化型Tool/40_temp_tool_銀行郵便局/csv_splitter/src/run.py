import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

# 進捗メッセージを受け取るコールバック（CLIはprint、GUIはキュー投入を渡す）
ProgressCallback = Callable[[str], None]


@dataclass
class SplitOptions:
    """分割の実行パラメータ。config.json と1対1に対応する。"""

    rows_per_file: int
    encoding: str
    has_header: bool = True
    delimiter: Optional[str] = None  # None = 自動判定

    @classmethod
    def from_config_file(cls, config_path: Path) -> "SplitOptions":
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(
            rows_per_file=config["rows_per_file"],
            encoding=config["encoding"],
            has_header=config.get("has_header", True),
            delimiter=config.get("delimiter") or None,
        )

    def validate(self) -> None:
        if not isinstance(self.rows_per_file, int) or self.rows_per_file <= 0:
            raise ValueError("rows_per_file は1以上の整数を指定してください")
        if not isinstance(self.has_header, bool):
            raise ValueError("has_header は true / false で指定してください")


@dataclass
class SplitResult:
    """1回の分割実行の結果。write_log がそのままログに書き出す。"""

    status: str
    started_at: datetime
    ended_at: datetime
    input_path: Path
    rows_per_file: int
    encoding: str
    delimiter: str
    has_header: bool
    total_rows: int
    output_summaries: list  # list[tuple[ファイル名, レコード数]]
    error_message: str = ""


def _detect_delimiter(path: Path, encoding: str, ext: str) -> str:
    candidates = {",": 0, "\t": 0, ";": 0}
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                for delim in candidates:
                    candidates[delim] += line.count(delim)
    except (OSError, UnicodeDecodeError, LookupError):
        pass  # 読めない場合は拡張子フォールバックに任せる（本読み込みで改めてエラーになる）
    best = max(candidates, key=lambda d: candidates[d])
    if candidates[best] > 0:
        return best
    return "," if ext.lower() == ".csv" else "\t"


def write_log(log_path: Path, result: SplitResult) -> None:
    delimiter_repr = "\\t" if result.delimiter == "\t" else result.delimiter
    lines = [
        "=== CSV Splitter Execution Log ===",
        f"status: {result.status}",
        f"started_at: {result.started_at.isoformat(timespec='seconds')}",
        f"ended_at: {result.ended_at.isoformat(timespec='seconds')}",
        f"input_file: {result.input_path}",
        f"rows_per_file: {result.rows_per_file}",
        f"encoding: {result.encoding}",
        f"delimiter: {delimiter_repr}",
        f"has_header: {result.has_header}",
        f"data_record_count: {result.total_rows}",
        f"created_file_count: {len(result.output_summaries)}",
        "created_files:",
    ]

    if result.output_summaries:
        for file_name, record_count in result.output_summaries:
            lines.append(f"- {file_name}: {record_count} records")
    else:
        lines.append("- (none)")

    if result.error_message:
        lines.append(f"error: {result.error_message}")

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_csv(
    input_path: Path,
    options: SplitOptions,
    *,
    output_dir: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    progress: Optional[ProgressCallback] = None,
) -> tuple[int, list[tuple[str, int]], Path]:
    """input_path を options.rows_per_file 行ごとに分割する。

    戻り値は (総データ件数, [(出力ファイル名, レコード数)], ログファイルパス)。
    エラー時も finally でログを必ず出力してから例外を再送出する。
    """
    started_at = datetime.now()
    output_dir = output_dir if output_dir is not None else OUTPUT_DIR
    log_dir = log_dir if log_dir is not None else LOG_DIR

    options.validate()
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    ext = input_path.suffix
    delimiter = options.delimiter or _detect_delimiter(input_path, options.encoding, ext)
    quoting = csv.QUOTE_ALL if delimiter == "," else csv.QUOTE_MINIMAL

    output_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)

    base_name = input_path.stem

    file_index = 0
    total_rows = 0
    rows_in_file = 0
    output_summaries: list[tuple[str, int]] = []
    status = "SUCCESS"
    error_message = ""

    outfile = None
    output_name = ""

    def _close_current_file():
        nonlocal outfile
        if outfile is not None:
            outfile.close()
            outfile = None
            output_summaries.append((output_name, rows_in_file))

    try:
        with open(input_path, "r", encoding=options.encoding, newline="") as infile:
            reader = csv.reader(infile, delimiter=delimiter)

            header = None
            if options.has_header:
                header = next(reader, None)

            for row in reader:
                if outfile is None:
                    file_index += 1
                    output_path = output_dir / f"{base_name}_split_{file_index:03}{ext}"
                    output_name = output_path.name
                    rows_in_file = 0
                    outfile = open(output_path, "w", encoding=options.encoding, newline="")
                    writer = csv.writer(outfile, delimiter=delimiter, quoting=quoting)
                    if header is not None:
                        writer.writerow(header)

                writer.writerow(row)
                total_rows += 1
                rows_in_file += 1

                if progress and total_rows % 10_000 == 0:
                    progress(f"  処理中: {total_rows:,} 行 ...")

                if rows_in_file >= options.rows_per_file:
                    _close_current_file()

            _close_current_file()

    except Exception as exc:
        status = "ERROR"
        error_message = str(exc)
        raise

    finally:
        if outfile is not None:
            outfile.close()

        log_path = log_dir / f"split_log_{started_at:%Y%m%d_%H%M%S}.log"
        write_log(
            log_path,
            SplitResult(
                status=status,
                started_at=started_at,
                ended_at=datetime.now(),
                input_path=input_path,
                rows_per_file=options.rows_per_file,
                encoding=options.encoding,
                delimiter=delimiter,
                has_header=options.has_header,
                total_rows=total_rows,
                output_summaries=output_summaries,
                error_message=error_message,
            ),
        )

    return total_rows, output_summaries, log_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python run.py <入力CSVファイルパス> [config.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else BASE_DIR / "config.json"

    options = SplitOptions.from_config_file(config_path)
    _total, _summaries, _log = split_csv(
        input_path, options, progress=lambda msg: print(msg, flush=True)
    )
    print("=================================")
    print("CSV分割 完了")
    print(f"入力ファイル : {input_path}")
    print(f"総データ件数 : {_total}")
    print(f"出力ファイル数 : {len(_summaries)}")
    print(f"出力フォルダ : {OUTPUT_DIR}")
    print(f"ログファイル : {_log}")
    print("=================================")
