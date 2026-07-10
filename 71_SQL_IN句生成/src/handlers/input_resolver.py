"""入力CSVパスの決定（引数 → ファイル選択ダイアログ → キャンセルで中断）。"""
import os


class InputCancelled(Exception):
    """ユーザーがファイル選択をキャンセルした。"""


def resolve_input_csv(argv: list, input_cfg: dict, logger) -> str:
    """入力CSVのパスを決定する。

    優先順位:
    1. コマンドライン引数（run.batへのドラッグ&ドロップを含む）
    2. tkinterのファイル選択ダイアログ（初期フォルダは config の dialog_initial_dir）
    """
    if len(argv) > 1:
        path = argv[1]
        if not os.path.exists(path):
            raise FileNotFoundError(f"指定されたCSVが見つかりません: {path}")
        logger.info(f"入力CSV（引数指定）: {path}")
        return path

    path = _ask_csv_path(input_cfg.get("dialog_initial_dir", "data/input"))
    if not path:
        raise InputCancelled("ファイル選択がキャンセルされました。処理を中断します。")
    logger.info(f"入力CSV（ダイアログ選択）: {path}")
    return path


def _ask_csv_path(initial_dir: str) -> str:
    """ファイル選択ダイアログを開き、選ばれたパスを返す（キャンセル時は空文字）。"""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # ランチャー経由でも背面に隠れないように
    try:
        return filedialog.askopenfilename(
            title="IN句を生成するCSVを選択してください",
            initialdir=initial_dir if os.path.isdir(initial_dir) else ".",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
        )
    finally:
        root.destroy()
