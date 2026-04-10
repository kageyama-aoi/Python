import csv
import json
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"


def _detect_delimiter(path: Path, encoding: str, ext: str) -> str:
    candidates = {",": 0, "\t": 0, ";": 0}
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                for delim in candidates:
                    candidates[delim] += line.count(delim)
    except Exception:
        pass
    best = max(candidates, key=lambda d: candidates[d])
    if candidates[best] > 0:
        return best
    return "," if ext.lower() == ".csv" else "\t"


def write_log(
    log_path: Path,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    input_path: Path,
    rows_per_file: int,
    encoding: str,
    delimiter: str,
    has_header: bool,
    total_rows: int,
    output_summaries: list[tuple[str, int]],
    error_message: str = "",
) -> None:
    delimiter_repr = "\\t" if delimiter == "\t" else delimiter
    lines = [
        "=== CSV Splitter Execution Log ===",
        f"status: {status}",
        f"started_at: {started_at.isoformat(timespec='seconds')}",
        f"ended_at: {ended_at.isoformat(timespec='seconds')}",
        f"input_file: {input_path}",
        f"rows_per_file: {rows_per_file}",
        f"encoding: {encoding}",
        f"delimiter: {delimiter_repr}",
        f"has_header: {has_header}",
        f"data_record_count: {total_rows}",
        f"created_file_count: {len(output_summaries)}",
        "created_files:",
    ]

    if output_summaries:
        for file_name, record_count in output_summaries:
            lines.append(f"- {file_name}: {record_count} records")
    else:
        lines.append("- (none)")

    if error_message:
        lines.append(f"error: {error_message}")

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_csv(input_path: Path, config_path: Path) -> None:
    started_at = datetime.now()

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    rows_per_file = config["rows_per_file"]
    encoding = config["encoding"]
    has_header = config.get("has_header", True)
    ext = input_path.suffix
    delimiter = config.get("delimiter") or _detect_delimiter(input_path, encoding, ext)
    quoting = csv.QUOTE_ALL if delimiter == "," else csv.QUOTE_MINIMAL

    if not isinstance(rows_per_file, int) or rows_per_file <= 0:
        raise ValueError("rows_per_file は1以上の整数を指定してください")

    if not isinstance(has_header, bool):
        raise ValueError("has_header は true / false で指定してください")

    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    base_name = input_path.stem

    file_index = 1
    total_rows = 0
    current_file_records = 0
    output_summaries: list[tuple[str, int]] = []
    status = "SUCCESS"
    error_message = ""

    outfile = None

    try:
        with open(input_path, "r", encoding=encoding, newline="") as infile:
            reader = csv.reader(infile, delimiter=delimiter)

            header = None
            if has_header:
                header = next(reader, None)

            for row in reader:
                if current_file_records == 0:
                    if outfile:
                        output_summaries.append((output_file_name, prev_file_records))
                        outfile.close()

                    output_path = OUTPUT_DIR / f"{base_name}_split_{file_index:03}{ext}"
                    output_file_name = output_path.name

                    outfile = open(output_path, "w", encoding=encoding, newline="")
                    writer = csv.writer(outfile, delimiter=delimiter, quoting=quoting)

                    if has_header and header is not None:
                        writer.writerow(header)

                    file_index += 1

                writer.writerow(row)

                total_rows += 1
                current_file_records += 1

                if total_rows % 10_000 == 0:
                    print(f"  処理中: {total_rows:,} 行 ...", flush=True)

                if current_file_records >= rows_per_file:
                    prev_file_records = current_file_records
                    current_file_records = 0

            if outfile:
                output_summaries.append((output_file_name, current_file_records))
                outfile.close()
                outfile = None

    except Exception as exc:
        status = "ERROR"
        error_message = str(exc)
        raise

    finally:
        if outfile:
            outfile.close()

        ended_at = datetime.now()
        log_path = LOG_DIR / f"split_log_{started_at:%Y%m%d_%H%M%S}.log"

        write_log(
            log_path=log_path,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            input_path=input_path,
            rows_per_file=rows_per_file,
            encoding=encoding,
            delimiter=delimiter,
            has_header=has_header,
            total_rows=total_rows,
            output_summaries=output_summaries,
            error_message=error_message,
        )

    return total_rows, output_summaries, log_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python run.py <入力CSVファイルパス> [config.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else BASE_DIR / "config.json"

    _total, _summaries, _log = split_csv(input_path, config_path)
    print("=================================")
    print("CSV分割 完了")
    print(f"入力ファイル : {input_path}")
    print(f"総データ件数 : {_total}")
    print(f"出力ファイル数 : {len(_summaries)}")
    print(f"出力フォルダ : {OUTPUT_DIR}")
    print(f"ログファイル : {_log}")
    print("=================================")
