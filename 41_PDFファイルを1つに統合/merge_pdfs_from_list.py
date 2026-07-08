"""
title: 入力リストからPDFを結合
tags: pdf, cli
inputs: 入力リストtxt
outputs: 結合済みPDF
example: python merge_pdfs_from_list.py -l inputs.txt -o output\\merged.pdf
dependencies: pypdf
owner: kageyama
last_verified: 2026-02-04
"""

from __future__ import annotations

import argparse
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def read_list(list_file: Path) -> list[Path]:
    """入力リストtxtからPDFパスを読み込み、Pathの配列で返す。"""
    lines = [line.strip() for line in list_file.read_text(encoding="utf-8").splitlines()]
    paths = [Path(line) for line in lines if line and not line.startswith("#")]
    return paths


def merge_pdfs(inputs: list[Path], output: Path) -> None:
    """入力PDF群を結合し、指定の出力パスへ保存する。"""
    writer = PdfWriter()

    for pdf_path in inputs:
        if not pdf_path.exists():
            raise FileNotFoundError(f"見つかりません: {pdf_path}")

        reader = PdfReader(str(pdf_path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as e:
                raise RuntimeError(f"暗号化PDFのため結合できません: {pdf_path}") from e

        for page in reader.pages:
            writer.add_page(page)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as f:
        writer.write(f)


def main() -> None:
    """コマンドライン引数を解析してPDF結合を実行する。"""
    ap = argparse.ArgumentParser()
    ap.add_argument("-l", "--list", required=True, type=Path, help="入力リストtxt")
    ap.add_argument("-o", "--output", required=True, type=Path, help="出力PDF")
    args = ap.parse_args()

    inputs = read_list(args.list)
    if not inputs:
        raise ValueError("リストに入力PDFがありません")

    merge_pdfs(inputs, args.output)


if __name__ == "__main__":
    main()
