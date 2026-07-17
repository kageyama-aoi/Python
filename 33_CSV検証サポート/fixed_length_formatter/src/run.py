"""固定長レコードファイル（改行なし）に、指定バイト数ごとの改行を付与するツール。

バイナリストリームで処理するため巨大ファイルでもメモリを消費しない。
CLI エントリポイントを兼ねる（ランチャーからは subprocess で呼ばれる）。
"""
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = DATA_DIR / "logs"

ProgressCallback = Callable[[str], None]

_BOM = b"\xef\xbb\xbf"
_NEWLINES = {"crlf": b"\r\n", "lf": b"\n"}
_CHUNK_BYTES = 1024 * 1024  # 1MBずつ読む


@dataclass
class FormatOptions:
    """変換の実行パラメータ。config.json と1対1に対応する。"""
    record_bytes: int
    newline: str = "crlf"      # "crlf" | "lf"
    encoding: str = "cp932"    # 先頭レコードの境界チェックに使う（変換自体はバイナリ）

    @classmethod
    def from_config_file(cls, path: Path) -> "FormatOptions":
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(
            record_bytes=config.get("record_bytes", 120),
            newline=config.get("newline", "crlf"),
            encoding=config.get("encoding", "cp932"),
        )

    def validate(self) -> None:
        if not isinstance(self.record_bytes, int) or self.record_bytes < 1:
            raise ValueError("record_bytes は1以上の整数で指定してください")
        if self.newline not in _NEWLINES:
            raise ValueError(f"newline は {'/'.join(_NEWLINES)} のいずれかで指定してください")


@dataclass
class FormatResult:
    """変換の実行結果。"""
    input_path: Path
    output_path: Optional[Path] = None
    log_path: Optional[Path] = None
    total_records: int = 0
    tail_bytes: int = 0          # 末尾の半端レコードのバイト数（0なら割り切れた）
    bom_skipped: bool = False
    boundary_ok: Optional[bool] = None  # 先頭レコードが encoding で正しくデコードできたか
    warnings: list = field(default_factory=list)


def _write_log(log_dir: Path, options: FormatOptions, result: FormatResult,
               started_at: datetime, error: Optional[BaseException]) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"format_log_{started_at:%Y%m%d_%H%M%S}.log"
    lines = [
        f"started_at: {started_at:%Y-%m-%d %H:%M:%S}",
        f"finished_at: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"input: {result.input_path}",
        f"record_bytes: {options.record_bytes}",
        f"newline: {options.newline}",
        f"encoding(check): {options.encoding}",
        f"total_records: {result.total_records}",
        f"tail_bytes: {result.tail_bytes}",
        f"bom_skipped: {result.bom_skipped}",
        f"boundary_ok: {result.boundary_ok}",
        f"output: {result.output_path}",
    ]
    for warning in result.warnings:
        lines.append(f"WARNING: {warning}")
    if error is not None:
        lines.append(f"ERROR: {error}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path


def format_fixed_length(
    input_path: Path,
    options: FormatOptions,
    *,
    output_dir: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    progress: Optional[ProgressCallback] = None,
) -> FormatResult:
    """input_path を record_bytes ごとに改行して出力する。

    出力は output_dir/<stem>_<日時>/<stem>_formatted<ext>（実行ごとサブディレクトリ）。
    エラー時もログは必ず出力する。
    """
    options.validate()
    output_dir = output_dir if output_dir is not None else OUTPUT_DIR
    log_dir = log_dir if log_dir is not None else LOG_DIR
    started_at = datetime.now()
    result = FormatResult(input_path=input_path)
    error: Optional[BaseException] = None

    n = options.record_bytes
    nl = _NEWLINES[options.newline]
    stem = input_path.stem
    ext = input_path.suffix or ".txt"
    run_dir = output_dir / f"{stem}_{started_at:%Y%m%d_%H%M%S}"
    first_record: Optional[bytes] = None

    try:
        with open(input_path, "rb") as fin:
            head = fin.read(len(_BOM))
            if head == _BOM:
                result.bom_skipped = True
                result.warnings.append("先頭のUTF-8 BOM(EF BB BF)を読み飛ばしました")
                buf = b""
            else:
                buf = head

            run_dir.mkdir(parents=True, exist_ok=True)
            result.output_path = run_dir / f"{stem}_formatted{ext}"
            with open(result.output_path, "wb") as fout:
                while True:
                    chunk = fin.read(_CHUNK_BYTES)
                    buf += chunk
                    usable = len(buf) - len(buf) % n  # レコード境界までの長さ
                    for i in range(0, usable, n):
                        record = buf[i:i + n]
                        if first_record is None:
                            first_record = record
                        fout.write(record)
                        fout.write(nl)
                        result.total_records += 1
                        if progress and result.total_records % 100_000 == 0:
                            progress(f"{result.total_records:,} レコード処理...")
                    buf = buf[usable:]  # 半端は次のchunkと連結して処理する
                    if not chunk:       # EOF: 残った半端レコードも出力して警告
                        if buf:
                            result.tail_bytes = len(buf)
                            fout.write(buf)
                            fout.write(nl)
                            result.warnings.append(
                                f"末尾に {len(buf)} バイトの半端レコードがあります"
                                f"（record_bytes={n} で割り切れません）")
                        break

        # 境界チェック: 先頭レコードが指定エンコーディングで丸ごとデコードできるか
        if first_record is not None:
            try:
                first_record.decode(options.encoding)
                result.boundary_ok = True
            except (UnicodeDecodeError, LookupError):
                result.boundary_ok = False
                result.warnings.append(
                    f"先頭レコードが {options.encoding} でデコードできません。"
                    "record_bytes がファイル仕様と合っていない可能性があります")
    except BaseException as exc:
        error = exc
        raise
    finally:
        result.log_path = _write_log(log_dir, options, result, started_at, error)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="改行なしの固定長レコードファイルに、指定バイト数ごとの改行を付与する")
    parser.add_argument("input", help="入力ファイルパス（固定長・改行なし）")
    parser.add_argument("config", nargs="?", default=None,
                        help="config.json のパス（省略時は config/config.json）")
    parser.add_argument("--record-bytes", type=int, metavar="N",
                        help="1レコードのバイト数（config.json より優先）")
    parser.add_argument("--newline", choices=list(_NEWLINES),
                        help="出力の改行コード（config.json より優先）")
    parser.add_argument("--encoding", metavar="ENC",
                        help="境界チェック用エンコーディング（config.json より優先）")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else CONFIG_DIR / "config.json"
    if config_path.exists():
        options = FormatOptions.from_config_file(config_path)
    else:
        options = FormatOptions(record_bytes=120)
    if args.record_bytes is not None:
        options.record_bytes = args.record_bytes
    if args.newline is not None:
        options.newline = args.newline
    if args.encoding is not None:
        options.encoding = args.encoding

    try:
        result = format_fixed_length(
            Path(args.input), options,
            progress=lambda msg: print(msg, flush=True))
    except (OSError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    print("=================================")
    print("固定長→改行付与 完了")
    print(f"入力ファイル : {args.input}")
    print(f"レコード長 : {options.record_bytes} バイト")
    print(f"総レコード数 : {result.total_records}")
    for warning in result.warnings:
        print(f"警告 : {warning}")
    print(f"出力ファイル : {result.output_path}")
    print(f"ログファイル : {result.log_path}")
