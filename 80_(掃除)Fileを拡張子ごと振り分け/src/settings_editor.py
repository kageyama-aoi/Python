"""設定エディタ（config.ini を GUI から構造化編集する）サブウィンドウ。

タブ構成:
- 基本      … 対象フォルダ / ログフォルダ名
- 拡張子グループ … グループ一覧（左）＋選択グループの拡張子（右）
- 除外      … 除外ファイル名 / 除外拡張子

テキスト構文の手打ちをなくし、追加/削除/名前変更はボタン操作で行う。
未保存で閉じようとすると確認する。
"""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import theme
from .config_io import OrganizeConfig, default_config, save_config


def _norm_ext(value: str) -> str:
    """拡張子表記を正規化する（前後空白除去・小文字化・先頭ドット除去）。"""
    return value.strip().lower().lstrip(".")


def _split_input(text: str) -> list[str]:
    """カンマ / 空白区切りの入力を要素リストにする。"""
    return [part for chunk in text.split(",") for part in chunk.split() if part]


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
        self.config_path = Path(config_path)
        self.on_save = on_save

        # 編集用モデル（キャンセル時に元 config へ影響しないようコピー）
        self._groups: dict[str, list[str]] = {
            k: list(v) for k, v in config.extension_groups.items()
        }
        self._exclude_names: list[str] = sorted(config.exclude_filenames)
        self._exclude_exts: list[str] = sorted(config.exclude_extensions)
        self._dirty = False

        self.title("設定")
        self.geometry("620x560")
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        theme.style_titlebar(self)

        self.target_var = tk.StringVar(value=str(config.target_dir))
        self.log_name_var = tk.StringVar(value=config.log_dir_name)
        self.target_var.trace_add("write", lambda *_: self._mark_dirty())
        self.log_name_var.trace_add("write", lambda *_: self._mark_dirty())

        self._build_widgets()
        self._refresh_group_list()
        self._refresh_exclude_lists()
        self._update_save_state()

    # ------------------------------------------------------------------ build
    def _build_widgets(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(outer)
        nb.pack(fill=tk.BOTH, expand=True)
        self._build_basic_tab(nb)
        self._build_groups_tab(nb)
        self._build_exclude_tab(nb)

        ttk.Label(
            outer,
            text="※ config.ini は git 追跡対象です。保存すると変更が履歴に現れます。",
            style="Summary.TLabel",
            foreground="#9aa0a6",
            wraplength=560,
        ).pack(anchor="w", pady=(10, 6))

        btns = ttk.Frame(outer)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="既定に戻す", command=self._reset_to_default).pack(side=tk.LEFT)
        self.save_btn = ttk.Button(btns, text="保存", command=self._save)
        self.save_btn.pack(side=tk.RIGHT)
        ttk.Button(btns, text="キャンセル", command=self._on_close).pack(
            side=tk.RIGHT, padx=(0, 8)
        )

    def _build_basic_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="基本")
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="対象フォルダ (TargetDirectory)").grid(row=0, column=0, sticky="w")
        row = ttk.Frame(tab)
        row.grid(row=1, column=0, sticky="ew", pady=(2, 12))
        row.columnconfigure(0, weight=1)
        ttk.Entry(row, textvariable=self.target_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(row, text="参照…", command=self._browse).grid(row=0, column=1, padx=(8, 0))

        lrow = ttk.Frame(tab)
        lrow.grid(row=2, column=0, sticky="w")
        ttk.Label(lrow, text="ログフォルダ名 (LogDirectoryName)").pack(side=tk.LEFT)
        ttk.Entry(lrow, textvariable=self.log_name_var, width=18).pack(side=tk.LEFT, padx=(8, 0))

    def _build_groups_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="拡張子グループ")
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="グループ").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="このグループにまとめる拡張子").grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )

        self.group_list = tk.Listbox(tab, exportselection=False, activestyle="none")
        self.group_list.grid(row=1, column=0, sticky="nsew")
        self.group_list.bind("<<ListboxSelect>>", lambda _e: self._on_group_select())

        self.ext_list = tk.Listbox(tab, exportselection=False, activestyle="none")
        self.ext_list.grid(row=1, column=1, sticky="nsew", padx=(12, 0))

        gbtns = ttk.Frame(tab)
        gbtns.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(gbtns, text="追加", command=self._add_group).pack(side=tk.LEFT)
        ttk.Button(gbtns, text="名前変更", command=self._rename_group).pack(side=tk.LEFT, padx=4)
        ttk.Button(gbtns, text="削除", command=self._delete_group).pack(side=tk.LEFT)

        ebtns = ttk.Frame(tab)
        ebtns.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=(6, 0))
        self.ext_entry_var = tk.StringVar()
        ttk.Entry(ebtns, textvariable=self.ext_entry_var, width=14).pack(side=tk.LEFT)
        ttk.Button(ebtns, text="追加", command=self._add_ext).pack(side=tk.LEFT, padx=4)
        ttk.Button(ebtns, text="削除", command=self._remove_ext).pack(side=tk.LEFT)

    def _build_exclude_tab(self, nb: ttk.Notebook) -> None:
        tab = ttk.Frame(nb, padding=12)
        nb.add(tab, text="除外")
        tab.rowconfigure(1, weight=1)
        tab.rowconfigure(4, weight=1)
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="除外ファイル名（このファイル名は動かさない）").grid(
            row=0, column=0, sticky="w"
        )
        self.exc_name_list = tk.Listbox(tab, height=5, exportselection=False, activestyle="none")
        self.exc_name_list.grid(row=1, column=0, sticky="nsew")
        nrow = ttk.Frame(tab)
        nrow.grid(row=2, column=0, sticky="ew", pady=(6, 12))
        self.exc_name_var = tk.StringVar()
        ttk.Entry(nrow, textvariable=self.exc_name_var, width=22).pack(side=tk.LEFT)
        ttk.Button(nrow, text="追加", command=self._add_exc_name).pack(side=tk.LEFT, padx=4)
        ttk.Button(nrow, text="削除", command=self._remove_exc_name).pack(side=tk.LEFT)

        ttk.Label(tab, text="除外拡張子（この拡張子は動かさない）").grid(
            row=3, column=0, sticky="w"
        )
        self.exc_ext_list = tk.Listbox(tab, height=5, exportselection=False, activestyle="none")
        self.exc_ext_list.grid(row=4, column=0, sticky="nsew")
        xrow = ttk.Frame(tab)
        xrow.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        self.exc_ext_var = tk.StringVar()
        ttk.Entry(xrow, textvariable=self.exc_ext_var, width=14).pack(side=tk.LEFT)
        ttk.Button(xrow, text="追加", command=self._add_exc_ext).pack(side=tk.LEFT, padx=4)
        ttk.Button(xrow, text="削除", command=self._remove_exc_ext).pack(side=tk.LEFT)

    # -------------------------------------------------------------- list 更新
    def _selected(self, listbox: tk.Listbox) -> str | None:
        sel = listbox.curselection()
        return listbox.get(sel[0]) if sel else None

    def _refresh_group_list(self, select: str | None = None) -> None:
        self.group_list.delete(0, tk.END)
        for name in self._groups:
            self.group_list.insert(tk.END, name)
        names = list(self._groups)
        if select and select in names:
            idx = names.index(select)
        elif names:
            idx = 0
        else:
            idx = None
        if idx is not None:
            self.group_list.selection_set(idx)
        self._on_group_select()

    def _on_group_select(self) -> None:
        self.ext_list.delete(0, tk.END)
        name = self._selected(self.group_list)
        if name and name in self._groups:
            for ext in self._groups[name]:
                self.ext_list.insert(tk.END, ext)

    def _refresh_exclude_lists(self) -> None:
        for lb, items in (
            (self.exc_name_list, self._exclude_names),
            (self.exc_ext_list, self._exclude_exts),
        ):
            lb.delete(0, tk.END)
            for item in items:
                lb.insert(tk.END, item)

    # ---------------------------------------------------------- グループ操作
    def _add_group(self) -> None:
        name = simpledialog.askstring("グループ追加", "グループ名（移動先フォルダ名）:", parent=self)
        if not name:
            return
        name = name.strip().lower()
        if not name:
            return
        if name in self._groups:
            messagebox.showinfo("設定", f"グループ「{name}」は既にあります。", parent=self)
            return
        self._groups[name] = []
        self._mark_dirty()
        self._refresh_group_list(select=name)

    def _rename_group(self) -> None:
        old = self._selected(self.group_list)
        if not old:
            return
        name = simpledialog.askstring(
            "名前変更", "新しいグループ名:", initialvalue=old, parent=self
        )
        if not name:
            return
        name = name.strip().lower()
        if not name or name == old:
            return
        if name in self._groups:
            messagebox.showinfo("設定", f"グループ「{name}」は既にあります。", parent=self)
            return
        # 挿入順を保ったまま置き換える
        self._groups = {(name if k == old else k): v for k, v in self._groups.items()}
        self._mark_dirty()
        self._refresh_group_list(select=name)

    def _delete_group(self) -> None:
        name = self._selected(self.group_list)
        if not name:
            return
        if not messagebox.askyesno("設定", f"グループ「{name}」を削除しますか？", parent=self):
            return
        self._groups.pop(name, None)
        self._mark_dirty()
        self._refresh_group_list()

    def _add_ext(self) -> None:
        group = self._selected(self.group_list)
        if not group:
            messagebox.showinfo("設定", "先にグループを選んでください。", parent=self)
            return
        raw = _split_input(self.ext_entry_var.get())
        if not raw:
            return
        added = False
        for ext in (_norm_ext(x) for x in raw):
            if not ext or ext in self._groups[group]:
                continue
            owner = next((g for g, es in self._groups.items() if ext in es and g != group), None)
            if owner and not messagebox.askyesno(
                "設定",
                f"「{ext}」はグループ「{owner}」にあります。「{group}」へ移動しますか？",
                parent=self,
            ):
                continue
            if owner:
                self._groups[owner].remove(ext)
            if ext in self._exclude_exts:
                messagebox.showwarning(
                    "設定",
                    f"「{ext}」は除外拡張子にも入っています。振り分け時は除外が優先されます。",
                    parent=self,
                )
            self._groups[group].append(ext)
            added = True
        if added:
            self.ext_entry_var.set("")
            self._mark_dirty()
            self._refresh_group_list(select=group)

    def _remove_ext(self) -> None:
        group = self._selected(self.group_list)
        ext = self._selected(self.ext_list)
        if not group or not ext:
            return
        self._groups[group].remove(ext)
        self._mark_dirty()
        self._refresh_group_list(select=group)

    # -------------------------------------------------------------- 除外操作
    def _add_to(self, items: list[str], values: list[str]) -> bool:
        changed = False
        for value in values:
            if value and value not in items:
                items.append(value)
                changed = True
        items.sort()
        return changed

    def _add_exc_name(self) -> None:
        if self._add_to(self._exclude_names, _split_input(self.exc_name_var.get())):
            self.exc_name_var.set("")
            self._mark_dirty()
            self._refresh_exclude_lists()

    def _remove_exc_name(self) -> None:
        name = self._selected(self.exc_name_list)
        if name:
            self._exclude_names.remove(name)
            self._mark_dirty()
            self._refresh_exclude_lists()

    def _add_exc_ext(self) -> None:
        exts = [_norm_ext(x) for x in _split_input(self.exc_ext_var.get())]
        owners = {g for g, es in self._groups.items() for ext in exts if ext in es}
        if owners:
            messagebox.showwarning(
                "設定",
                "次のグループに属する拡張子を除外に追加します。除外が優先されます: "
                + " / ".join(sorted(owners)),
                parent=self,
            )
        if self._add_to(self._exclude_exts, exts):
            self.exc_ext_var.set("")
            self._mark_dirty()
            self._refresh_exclude_lists()

    def _remove_exc_ext(self) -> None:
        ext = self._selected(self.exc_ext_list)
        if ext:
            self._exclude_exts.remove(ext)
            self._mark_dirty()
            self._refresh_exclude_lists()

    # ------------------------------------------------------------- 保存 / 終了
    def _browse(self) -> None:
        initial = self.target_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(initialdir=initial, title="対象フォルダを選択")
        if chosen:
            self.target_var.set(chosen)

    def _reset_to_default(self) -> None:
        if not messagebox.askyesno(
            "設定",
            "拡張子グループと除外リストを初期状態に戻します（対象フォルダは変更しません）。",
            parent=self,
        ):
            return
        base = default_config()
        self._groups = {k: list(v) for k, v in base.extension_groups.items()}
        self._exclude_names = sorted(base.exclude_filenames)
        self._exclude_exts = sorted(base.exclude_extensions)
        self._mark_dirty()
        self._refresh_group_list()
        self._refresh_exclude_lists()

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._update_save_state()

    def _update_save_state(self) -> None:
        self.save_btn.configure(state=tk.NORMAL if self._dirty else tk.DISABLED)

    def _collect(self) -> OrganizeConfig:
        target = self.target_var.get().strip()
        if not target:
            raise ValueError("対象フォルダを入力してください。")
        groups = {name: list(exts) for name, exts in self._groups.items() if exts}
        return OrganizeConfig(
            target_dir=Path(target),
            log_dir_name=self.log_name_var.get().strip() or "logs",
            extension_groups=groups,
            exclude_filenames=set(self._exclude_names),
            exclude_extensions=set(self._exclude_exts),
        )

    def _save(self) -> None:
        try:
            new_config = self._collect()
        except ValueError as e:
            messagebox.showerror("設定", str(e), parent=self)
            return
        if not messagebox.askyesno(
            "設定", f"{self.config_path.name} を上書き保存します。よろしいですか？", parent=self
        ):
            return
        try:
            save_config(self.config_path, new_config)
        except OSError as e:
            messagebox.showerror("設定", f"保存に失敗しました:\n{e}", parent=self)
            return
        self._dirty = False
        self.on_save(new_config)
        self.destroy()

    def _on_close(self) -> None:
        if self._dirty and not messagebox.askyesno(
            "設定", "保存していない変更があります。破棄して閉じますか？", parent=self
        ):
            return
        self.destroy()
