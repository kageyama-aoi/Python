"""入力ファイル・対象列名の決定（引数 → ダイアログ → キャンセルで中断）。"""
import os


class InputCancelled(Exception):
    """ユーザーが選択をキャンセルした。"""


def resolve_input_csv(argv: list, input_cfg: dict, logger) -> str:
    """入力ファイルのパスを決定する。

    優先順位:
    1. コマンドライン第1引数（run.batへのドラッグ&ドロップを含む）
    2. tkinterのファイル選択ダイアログ（初期フォルダは config の dialog_initial_dir）
    """
    if len(argv) > 1:
        path = argv[1]
        if not os.path.exists(path):
            raise FileNotFoundError(f"指定されたファイルが見つかりません: {path}")
        logger.info(f"入力ファイル（引数指定）: {path}")
        return path

    path = _ask_file_path(input_cfg.get("dialog_initial_dir", "data/input"))
    if not path:
        raise InputCancelled("ファイル選択がキャンセルされました。処理を中断します。")
    logger.info(f"入力ファイル（ダイアログ選択）: {path}")
    return path


def resolve_user_column(argv: list, columns: list, filter_cfg: dict, logger) -> str:
    """IN句にする対象列名を決定する。

    優先順位:
    1. コマンドライン第2引数
    2. config の filter.user_column（実在する場合のみ）
    3. 列が1つだけならそれを自動選択
    4. 列名選択ダイアログ（キャンセルで中断）
    """
    if len(argv) > 2:
        col = argv[2]
        if col not in columns:
            raise KeyError(f"列 '{col}' がありません（実際の列: {columns}）。")
        logger.info(f"対象列（引数指定）: {col}")
        return col

    cfg_col = filter_cfg.get("user_column")
    if cfg_col and cfg_col in columns:
        logger.info(f"対象列（config）: {cfg_col}")
        return cfg_col

    if len(columns) == 1:
        logger.info(f"対象列（単一列を自動選択）: {columns[0]}")
        return columns[0]

    col = _ask_column(columns)
    if not col:
        raise InputCancelled("列の選択がキャンセルされました。処理を中断します。")
    logger.info(f"対象列（ダイアログ選択）: {col}")
    return col


def _ask_file_path(initial_dir: str) -> str:
    """ファイル選択ダイアログを開き、選ばれたパスを返す（キャンセル時は空文字）。"""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # ランチャー経由でも背面に隠れないように
    try:
        return filedialog.askopenfilename(
            title="IN句を生成するファイルを選択してください",
            initialdir=initial_dir if os.path.isdir(initial_dir) else ".",
            filetypes=[
                ("CSV/テキスト", "*.csv;*.txt"),
                ("すべてのファイル", "*.*"),
            ],
        )
    finally:
        root.destroy()


def _ask_column(columns: list) -> str:
    """列名選択ダイアログを開き、選ばれた列名を返す（キャンセル時は空文字）。"""
    import tkinter as tk

    result = {"value": ""}

    root = tk.Tk()
    root.title("IN句にする列を選択")
    root.attributes("-topmost", True)

    tk.Label(root, text="IN句にする列を選んでください:").pack(padx=10, pady=(10, 4))

    listbox = tk.Listbox(root, height=min(len(columns), 15), exportselection=False)
    for col in columns:
        listbox.insert(tk.END, col)
    listbox.selection_set(0)
    listbox.pack(fill=tk.BOTH, expand=True, padx=10)

    def on_ok(event=None):
        selection = listbox.curselection()
        if selection:
            result["value"] = columns[selection[0]]
        root.destroy()

    listbox.bind("<Double-Button-1>", on_ok)
    tk.Button(root, text="OK", command=on_ok, width=10).pack(pady=8)

    root.mainloop()
    return result["value"]
