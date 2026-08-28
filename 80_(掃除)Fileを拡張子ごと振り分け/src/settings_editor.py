"""設定エディタ（config.ini を GUI から編集する）サブウィンドウ。"""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import theme
from .config_io import OrganizeConfig, save_config


def _groups_to_text(groups: dict[str, list[str]]) -> str:
    return "\n".join(f"{name} = {', '.join(exts)}" for name, exts in groups.items())


def _text_to_groups(text: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if "=" not in line:
            raise ValueError(f"'グループ名 = 拡張子, ...' の形式で記述してください: {raw}")
        name, _, exts_str = line.partition("=")
        name = name.strip()
        exts = [e.strip().lower().lstrip(".") for e in exts_str.split(",") if e.strip()]
        if name and exts:
            groups[name] = exts
    return groups


def _csv_to_set(text: str, *, lower: bool = False) -> set[str]:
    items = (part.strip() for part in text.replace("\n", ",").split(","))
    return {(item.lower() if lower else item) for item in items if item}


class SettingsEditor(tk.Toplevel):
    """config.ini の各項目を編集して保存する。"""

    def __init__(
        self,
        master: tk.Misc,
        config: OrganizeConfig,
        config_path: Path,
        on_save: Callable[[OrganizeConfig], None],
    ):
        super().__init__(master)
        self.config = config
        self.config_path = Path(config_path)
        self.on_save = on_save

        self.title("設定")
        self.geometry("560x560")
        self.transient(master)
        theme.style_titlebar(self)

        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=2)
        frame.rowconfigure(5, weight=1)
        frame.rowconfigure(7, weight=1)

        # 対象フォルダ
        ttk.Label(frame, text="対象フォルダ (TargetDirectory)").grid(row=0, column=0, sticky="w")
        folder_row = ttk.Frame(frame)
        folder_row.grid(row=1, column=0, sticky="ew", pady=(2, 10))
        folder_row.columnconfigure(0, weight=1)
        self.target_var = tk.StringVar(value=str(self.config.target_dir))
        ttk.Entry(folder_row, textvariable=self.target_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(folder_row, text="参照…", command=self._browse).grid(
            row=0, column=1, padx=(8, 0)
        )

        # ログフォルダ名
        log_row = ttk.Frame(frame)
        log_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(log_row, text="ログフォルダ名 (LogDirectoryName)").pack(side=tk.LEFT)
        self.log_name_var = tk.StringVar(value=self.config.log_dir_name)
        ttk.Entry(log_row, textvariable=self.log_name_var, width=18).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        # 拡張子グループ
        ttk.Label(
            frame, text="拡張子グループ（1行1グループ: グループ名 = jpg, png, ...）"
        ).grid(row=3, column=0, sticky="sw", pady=(10, 2))
        self.groups_text = tk.Text(frame, height=8, wrap=tk.NONE, font=theme.MONO_FONT)
        self.groups_text.grid(row=4, column=0, sticky="nsew")
        self.groups_text.insert("1.0", _groups_to_text(self.config.extension_groups))

        # 除外ファイル名
        ttk.Label(frame, text="除外ファイル名（カンマ区切り）").grid(
            row=5, column=0, sticky="sw", pady=(10, 2)
        )
        self.exclude_names_text = tk.Text(frame, height=3, wrap=tk.WORD, font=theme.MONO_FONT)
        self.exclude_names_text.grid(row=6, column=0, sticky="nsew")
        self.exclude_names_text.insert("1.0", ", ".join(sorted(self.config.exclude_filenames)))

        # 除外拡張子
        ttk.Label(frame, text="除外拡張子（カンマ区切り）").grid(
            row=7, column=0, sticky="sw", pady=(10, 2)
        )
        self.exclude_exts_text = tk.Text(frame, height=3, wrap=tk.WORD, font=theme.MONO_FONT)
        self.exclude_exts_text.grid(row=8, column=0, sticky="nsew")
        self.exclude_exts_text.insert("1.0", ", ".join(sorted(self.config.exclude_extensions)))

        # 注記
        ttk.Label(
            frame,
            text="※ 保存すると config.ini のコメント行は失われます（git 追跡対象のため変更は履歴に出ます）。",
            style="Summary.TLabel",
            foreground="#9aa0a6",
            wraplength=520,
        ).grid(row=9, column=0, sticky="w", pady=(10, 6))

        # ボタン
        btns = ttk.Frame(frame)
        btns.grid(row=10, column=0, sticky="e")
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btns, text="保存", command=self._save).pack(side=tk.RIGHT)

    def _browse(self) -> None:
        initial = self.target_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(initialdir=initial, title="対象フォルダを選択")
        if chosen:
            self.target_var.set(chosen)

    def _collect(self) -> OrganizeConfig:
        target = self.target_var.get().strip()
        if not target:
            raise ValueError("対象フォルダを入力してください。")
        groups = _text_to_groups(self.groups_text.get("1.0", tk.END))
        return OrganizeConfig(
            target_dir=Path(target),
            log_dir_name=self.log_name_var.get().strip() or "logs",
            extension_groups=groups,
            exclude_filenames=_csv_to_set(self.exclude_names_text.get("1.0", tk.END)),
            exclude_extensions=_csv_to_set(
                self.exclude_exts_text.get("1.0", tk.END), lower=True
            ),
        )

    def _save(self) -> None:
        try:
            new_config = self._collect()
        except ValueError as e:
            messagebox.showerror("設定", str(e), parent=self)
            return
        if not messagebox.askyesno(
            "設定",
            f"{self.config_path.name} を上書き保存します。\n"
            "既存のコメント行は失われます。よろしいですか？",
            parent=self,
        ):
            return
        try:
            save_config(self.config_path, new_config)
        except OSError as e:
            messagebox.showerror("設定", f"保存に失敗しました:\n{e}", parent=self)
            return
        self.on_save(new_config)
        self.destroy()
