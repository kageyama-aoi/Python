"""ツール直下の config.json / config.ini をフォーム化して編集するサブウィンドウ。

ファイル書き戻しの中核（config.json の型ラウンドトリップ・config.ini の行置換）は
tkinter 非依存の純関数として切り出し、tests/test_config_editors.py で検証する。
壊れるとユーザーの設定ファイルを破損させる箇所のため、GUI から独立して守る。
"""
import configparser
import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from theme import (
    BTN_PRIMARY,
    BTN_SECONDARY,
    BTN_TERTIARY,
    MUTED_FG,
    TAG_FONT,
    UI_FONT_BOLD,
    style_titlebar,
)

# フォルダ参照ボタンを付ける対象キーの判定（例: root_dir, TargetDirectory, icon_folder）
PATH_KEY_RE = re.compile(r"(dir|path|folder)", re.IGNORECASE)

_SECTION_RE = re.compile(r"^\s*\[(.+?)\]")
_KEY_LINE_RE = re.compile(r"^(\s*)([^=:\s][^=:]*?)(\s*[=:]\s*)")


# ── 純ロジック（tkinter 非依存・テスト対象） ───────────────────────────

def describe_json_value(value):
    """config.json の値から (編集方式, フォーム初期値) を返す。

    bool は int のサブクラスなので int より先に判定する。
    """
    if isinstance(value, bool):
        return "bool", value
    if isinstance(value, str):
        return "str", value
    if isinstance(value, (int, float)):
        return "number", str(value)
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return "list_str", ", ".join(value)
    return "json", json.dumps(value, ensure_ascii=False)


def coerce_json_value(kind, raw, original):
    """編集方式に応じてフォーム入力を元の型へ戻す。

    変換できない入力は ValueError / json.JSONDecodeError を送出する（呼び出し側で表示）。
    number は元の値と同じ型（int / float）を保つ。
    """
    if kind == "bool":
        return bool(raw)
    if kind == "number":
        return type(original)(raw)
    if kind == "list_str":
        return [v.strip() for v in raw.split(",") if v.strip()]
    if kind == "json":
        return json.loads(raw)
    return raw


def replace_ini_value_line(lines, section, key, new_value):
    """指定セクション内のキー行を探し、値部分だけ書き換える。見つからなければ False。

    コメント行・空行・キーの記述順を保持するため、ファイル全体の書き直しではなく
    該当行だけを置換する（configparser で書き戻すとコメントが全て消えるため）。
    lines は splitlines(keepends=True) のリストで、その場で書き換える。
    """
    current_section = None
    for i, line in enumerate(lines):
        m = _SECTION_RE.match(line)
        if m:
            current_section = m.group(1)
            continue
        if current_section != section:
            continue
        stripped = line.lstrip()
        if not stripped or stripped.startswith((";", "#")):
            continue
        km = _KEY_LINE_RE.match(line)
        if km and km.group(2).strip() == key:
            newline = "\n" if line.endswith("\n") else ""
            lines[i] = f"{km.group(1)}{km.group(2)}{km.group(3)}{new_value}{newline}"
            return True
    return False


# ── GUI ───────────────────────────────────────────────────────────────

def _browse_dir_into_var(parent, var: tk.StringVar, fallback_dir: Path):
    """フォルダ選択ダイアログを開き、選択結果を入力欄の変数へ反映する。"""
    current = var.get()
    initial = current if Path(current).is_dir() else str(fallback_dir)
    selected = filedialog.askdirectory(parent=parent, initialdir=initial)
    if selected:
        var.set(selected)


class _BaseConfigEditorWindow(tk.Toplevel):
    """設定エディタ2種の共通の枠（タイトル・最小サイズ・保存/キャンセル行）。"""

    def __init__(self, master, config_path: Path, tool_name: str):
        super().__init__(master)
        self.title(f"⚙設定 - {tool_name}")
        self.config_path = config_path
        self.minsize(480, 120)
        self.transient(master)
        style_titlebar(self)

    def _add_save_cancel_row(self):
        btn_row = ttk.Frame(self)
        btn_row.pack(pady=(6, 12))
        ttk.Button(btn_row, text="保存して閉じる", style=BTN_PRIMARY, command=self._save).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(btn_row, text="キャンセル", style=BTN_SECONDARY, command=self.destroy).pack(
            side="left"
        )

    def _save(self):  # pragma: no cover - サブクラスで実装
        raise NotImplementedError


class ConfigEditorWindow(_BaseConfigEditorWindow):
    """config.json の全キーを自動フォーム化して編集・保存するサブウィンドウ。

    型ごとの編集方式:
    - bool            → チェックボックス
    - str / int / float → 1行入力（キー名に dir/path/folder を含む文字列値は
                          フォルダ参照ボタン付き）
    - list（全要素が文字列）→ カンマ区切りの1行入力
    - dict などその他  → JSON文字列として編集
    保存時は元の型へ変換して書き戻す。変換できない入力はエラー表示して中断する。
    """

    def __init__(self, master, config_path: Path, tool_name: str):
        super().__init__(master, config_path, tool_name)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            messagebox.showerror(
                "読み込みエラー", f"{config_path.name} を読み込めませんでした:\n{exc}",
                parent=master,
            )
            self.destroy()
            return
        if not isinstance(self.data, dict):
            messagebox.showerror(
                "読み込みエラー",
                f"{config_path.name} のトップレベルがオブジェクトではないため編集できません。",
                parent=master,
            )
            self.destroy()
            return

        # (キー, 編集方式, 入力変数) のリスト。保存時にここから値を復元する。
        self._fields = []
        self._build_form()
        self.grab_set()

    def _build_form(self):
        form = ttk.Frame(self)
        form.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        form.columnconfigure(1, weight=1)

        for row, (key, value) in enumerate(self.data.items()):
            ttk.Label(form, text=key).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3
            )
            kind, text = describe_json_value(value)
            if kind == "bool":
                var = tk.BooleanVar(value=text)
                ttk.Checkbutton(form, variable=var).grid(row=row, column=1, sticky="w", pady=3)
                self._fields.append((key, "bool", var))
                continue

            var = tk.StringVar(value=text)
            entry = ttk.Entry(form, textvariable=var, width=48)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            if kind == "str" and PATH_KEY_RE.search(key):
                ttk.Button(
                    form, text="参照...", style=BTN_TERTIARY,
                    command=lambda v=var: self._browse_dir(v),
                ).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
            self._fields.append((key, kind, var))

        hint = ttk.Label(
            self,
            text="リストはカンマ区切り、辞書はJSON形式で編集します。",
            font=TAG_FONT,
            foreground=MUTED_FG,
        )
        hint.pack(anchor="w", padx=12)

        self._add_save_cancel_row()

    def _browse_dir(self, var: tk.StringVar):
        _browse_dir_into_var(self, var, self.config_path.parent)

    def _save(self):
        new_data = dict(self.data)
        for key, kind, var in self._fields:
            try:
                new_data[key] = coerce_json_value(kind, var.get(), self.data[key])
            except (ValueError, json.JSONDecodeError) as exc:
                messagebox.showerror(
                    "入力エラー", f"'{key}' の値を変換できません:\n{exc}", parent=self
                )
                return

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as exc:
            messagebox.showerror(
                "保存エラー", f"{self.config_path.name} に保存できませんでした:\n{exc}",
                parent=self,
            )
            return
        self.destroy()


class IniConfigEditorWindow(_BaseConfigEditorWindow):
    """config.ini をセクションごとにフォーム化して編集・保存するサブウィンドウ。

    INIの値はすべて文字列として編集する。保存はファイル全体の書き直しではなく
    変更されたキーの行だけを置換する方式で、コメント行・空行・キーの記述順を
    保持する（configparserで書き戻すとコメントが全て消えるため）。
    複数行にまたがる値（継続行）は行置換で壊れるため編集不可として表示する。
    """

    def __init__(self, master, config_path: Path, tool_name: str):
        super().__init__(master, config_path, tool_name)

        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str  # キーの大文字小文字を保持する
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                parser.read_file(f)
        except (configparser.Error, OSError, UnicodeDecodeError) as exc:
            messagebox.showerror(
                "読み込みエラー", f"{config_path.name} を読み込めませんでした:\n{exc}",
                parent=master,
            )
            self.destroy()
            return

        # (セクション, キー, 入力変数, 元の値) のリスト。保存時に差分だけ書き込む。
        self._fields = []
        self._build_form(parser)
        self.grab_set()

    def _build_form(self, parser: configparser.ConfigParser):
        form = ttk.Frame(self)
        form.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        form.columnconfigure(1, weight=1)

        row = 0
        for section in parser.sections():
            ttk.Label(form, text=f"[{section}]", font=UI_FONT_BOLD).grid(
                row=row, column=0, columnspan=2, sticky="w",
                pady=(8 if row else 0, 2),
            )
            row += 1
            for key, value in parser.items(section):
                ttk.Label(form, text=key).grid(
                    row=row, column=0, sticky="w", padx=(12, 10), pady=3
                )
                var = tk.StringVar(value=value)
                entry = ttk.Entry(form, textvariable=var, width=48)
                entry.grid(row=row, column=1, sticky="ew", pady=3)
                if "\n" in value:
                    entry.config(state="disabled")
                    ttk.Label(
                        form, text="(複数行値のため編集不可)", font=TAG_FONT, foreground=MUTED_FG
                    ).grid(row=row, column=2, sticky="w", padx=(6, 0))
                elif PATH_KEY_RE.search(key):
                    ttk.Button(
                        form, text="参照...", style=BTN_TERTIARY,
                        command=lambda v=var: _browse_dir_into_var(
                            self, v, self.config_path.parent
                        ),
                    ).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
                self._fields.append((section, key, var, value))
                row += 1

        self._add_save_cancel_row()

    def _save(self):
        try:
            lines = self.config_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError) as exc:
            messagebox.showerror(
                "保存エラー", f"{self.config_path.name} を読み直せませんでした:\n{exc}",
                parent=self,
            )
            return

        changed = False
        for section, key, var, original in self._fields:
            new_value = var.get()
            if new_value == original:
                continue
            if "\n" in new_value:
                messagebox.showerror(
                    "入力エラー", f"'{key}' に改行は入力できません。", parent=self
                )
                return
            if not replace_ini_value_line(lines, section, key, new_value):
                messagebox.showerror(
                    "保存エラー",
                    f"[{section}] の '{key}' の行が見つからず、保存を中断しました。\n"
                    f"{self.config_path.name} を直接確認してください。",
                    parent=self,
                )
                return
            changed = True

        if changed:
            try:
                self.config_path.write_text("".join(lines), encoding="utf-8")
            except OSError as exc:
                messagebox.showerror(
                    "保存エラー",
                    f"{self.config_path.name} に保存できませんでした:\n{exc}",
                    parent=self,
                )
                return
        self.destroy()
