"""全Pythonツールを起動するGUIランチャー。

Python/ 配下を再帰的に走査し、launcher.json を持つツールを一覧表示して
ボタンで起動する。ツール側のコードには一切手を入れず、外付けの
launcher.json マニフェストだけを読む方式。

launcher.json の形式:
{
  "name": "表示名",
  "description": "一言説明",
  "actions": [
    {
      "label": "ボタンに表示するラベル",
      "kind": "gui" | "cli" | "server" | "generator",
      "entry": "run.bat",
      "open_after": "output/*.xlsx"   # generatorのみ。完了後に開く出力ファイルのglobパターン
      "note": "補足事項があれば"        # 任意。クリック時に案内ダイアログを表示
    }
  ]
}

favorites.json（このファイルと同じ場所に自動生成、gitignore対象）:
お気に入り登録したツールの相対パス一覧。ユーザーのローカル環境固有の状態。

設定編集（⚙設定ボタン）:
ツールディレクトリ直下に config.json または config.ini がある場合、⚙設定ボタンを
自動表示する。launcher.json への宣言は不要。押すと全キーをフォーム化した編集
ウィンドウが開く。JSONは元の型を保ったまま全体を書き戻し、INIは変更したキーの
行だけを置換してコメント・空行を保持する。
"""
import json
import os
import re
import subprocess
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import messagebox, ttk

from config_editors import ConfigEditorWindow, IniConfigEditorWindow
from theme import (
    BTN_SECONDARY,
    BTN_TERTIARY,
    HEADER_FONT,
    MUTED_FG,
    PATH_FONT,
    STATUS_FG,
    TAG_FONT,
    apply_theme,
    style_titlebar,
)

# テーマ・フォント・ボタン3段階スタイル・タイトルバー処理は theme.py に集約
# （sv-ttk / pywinstyles は theme.py 側で任意 import。未導入でも標準ttkで動作する）。
# 設定エディタ（config.json / config.ini）のウィンドウは config_editors.py。

ROOT_DIR = Path(__file__).resolve().parent.parent
FAVORITES_FILE = Path(__file__).resolve().parent / "favorites.json"

KIND_LABELS = {
    "gui": "GUI",
    "cli": "CLI",
    "server": "サーバー",
    "generator": "生成",
}

# ディレクトリ番号帯とカテゴリ名の対応（過去のリネームコミットの命名を踏襲）
CATEGORY_LABELS = {
    "10": "業務自動化",
    "20": "セレクタ抽出支援",
    "30": "データ変換",
    "40": "ドキュメント生成",
    "50": "ナレッジ管理",
    "60": "データ可視化",
    "70": "スクール特化業務",
    "80": "雑務ユーティリティ",
    "90": "ひな形",
}

_CATEGORY_PREFIX_RE = re.compile(r"^(\d)\d_")


def find_tools():
    """Python/ 配下の launcher.json を再帰的に探索する。"""
    tools = []
    for manifest_path in ROOT_DIR.rglob("launcher.json"):
        if "node_modules" in manifest_path.parts or ".git" in manifest_path.parts:
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        data["_dir"] = manifest_path.parent
        tools.append(data)
    tools.sort(key=lambda t: str(t["_dir"]))
    return tools


def get_category_key(tool_dir: Path) -> str:
    """ツールの所属カテゴリキー（10刻みで"10"など）を返す。該当なしは"99"。"""
    rel = tool_dir.relative_to(ROOT_DIR)
    m = _CATEGORY_PREFIX_RE.match(rel.parts[0])
    return (m.group(1) + "0") if m else "99"


def get_category_label(key: str) -> str:
    """カテゴリキーから表示用ラベル（例: "業務自動化（10番台）"）を返す。"""
    if key == "99":
        return "その他"
    return f"{CATEGORY_LABELS.get(key, key + '番台')}（{key}番台）"


def load_favorites() -> set:
    """お気に入り登録済みツールの相対パス集合を読み込む。"""
    if not FAVORITES_FILE.exists():
        return set()
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_favorites(favorites: set):
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(favorites), f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _cmd_c_line(entry_path: Path) -> str:
    """`cmd /c` に渡すコマンドラインを組み立てる。

    entryは絶対パスで渡す。日本語を含むフォルダ名では、相対パス+cwd指定の
    組み合わせだと cmd.exe が "run.bat" を見つけられないことがあるため。
    さらにパスに括弧 () を含む場合（例: "60_Data_Flow_Portal(データフロー書き出し)"）、
    単純に `cmd /c <path>` と渡すと cmd.exe が "(" 以降を別コマンドとして
    誤認識し「内部コマンドまたは外部コマンドとして認識されていません」と
    失敗する。`cmd /c ""<path>""` の二重引用符で囲むことでこれを回避する。
    """
    return f'cmd /c ""{entry_path}""'


def run_fire_and_forget(tool_dir: Path, entry: str):
    """GUI/CLI/サーバー系: 起動したら結果を待たない。"""
    subprocess.Popen(
        _cmd_c_line(tool_dir / entry),
        cwd=str(tool_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def run_generator(
    widget: tk.Widget, tool_dir: Path, entry: str, open_after: str, status_var: tk.StringVar
):
    """生成系: 完了を待ってから対象ファイルを開く。GUIが固まらないよう別スレッドで実行。

    Tkinter変数はメインスレッド以外から更新すると不安定になるため、
    widget.after() でメインスレッドのイベントループに処理を戻す。
    """

    def worker():
        widget.after(0, lambda: status_var.set("実行中..."))
        try:
            subprocess.run(_cmd_c_line(tool_dir / entry), cwd=str(tool_dir))
        except Exception as exc:
            # 注意: run.bat が pause を含む場合、Python側の異常終了(exit code != 0)は
            # pause自体の終了コード(0)に上書きされるため、ここでは検知できない。
            # ここで捕捉できるのは subprocess.run 自体が例外を送出するケース
            # （cmd.exe が見つからない等）に限られる。
            widget.after(
                0,
                lambda: messagebox.showerror(
                    "実行エラー", f"{entry} の実行中にエラーが発生しました:\n{exc}"
                ),
            )
            return
        finally:
            widget.after(0, lambda: status_var.set(""))

        if not open_after:
            return

        candidates = sorted(
            tool_dir.glob(open_after),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            os.startfile(str(candidates[0]))
        else:
            widget.after(
                0,
                lambda: messagebox.showwarning(
                    "生成物が見つかりません",
                    f"'{open_after}' に一致するファイルが見つかりませんでした。",
                ),
            )

    threading.Thread(target=worker, daemon=True).start()



class CollapsibleSection(ttk.Frame):
    """クリックで開閉できるセクション。見出しをクリックすると中身の表示/非表示を切り替える。"""

    def __init__(self, parent, title, expanded=True):
        super().__init__(parent)
        self._expanded = expanded
        self._title = title

        header = ttk.Frame(self)
        header.pack(fill="x")

        self.toggle_label = ttk.Label(
            header, text=self._arrow(), width=2, font=HEADER_FONT, cursor="hand2"
        )
        self.toggle_label.pack(side="left")
        self.title_label = ttk.Label(
            header, text=title, font=HEADER_FONT, cursor="hand2"
        )
        self.title_label.pack(side="left", padx=(2, 0))

        self.toggle_label.bind("<Button-1>", lambda e: self.toggle())
        self.title_label.bind("<Button-1>", lambda e: self.toggle())

        self.body = ttk.Frame(self)
        if expanded:
            self.body.pack(fill="x", padx=(18, 0), pady=(2, 0))

    def _arrow(self):
        return "▼" if self._expanded else "▶"

    def toggle(self):
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.toggle_label.config(text=self._arrow())
        if expanded:
            self.body.pack(fill="x", padx=(18, 0), pady=(2, 0))
        else:
            self.body.pack_forget()


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python ツールランチャー")
        self.geometry("820x640")
        self.minsize(600, 400)

        self.style = apply_theme(self)

        self.favorites = load_favorites()

        # ── 検索バー（固定・スクロールしない） ──
        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", padx=10, pady=(8, 4))
        ttk.Label(search_bar, text="検索:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filter())
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(
            search_bar, text="クリア", style=BTN_TERTIARY, command=lambda: self.search_var.set("")
        ).pack(side="left")

        # ── スクロール可能な本体 ──
        canvas_bg = self.style.lookup("TFrame", "background") or self.cget("background")
        canvas = tk.Canvas(self, highlightthickness=0, background=canvas_bg)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)

        self.body.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        body_window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        # canvas幅にbodyを追従させる。これがないと説明文のwraplengthをウィンドウ幅に
        # 連動させても、body自体の実効幅が古いまま残り折り返しがズレる。
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(body_window, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ホイールスクロールはポインタが本体上にある間だけ有効にする。bind_all にすると
        # 設定エディタ等の子ウィンドウでホイールを回しても裏の親ランチャーが動いてしまう。
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # フィルタ対象の登録簿。(検索用テキスト, ツールのFrame, 所属セクション) のタプルを
        # 登録順（=表示したい順）に保持する。
        self._entries = []
        self._sections = []

        self.build_tool_list()
        style_titlebar(self)

    def build_tool_list(self):
        for w in self.body.winfo_children():
            w.destroy()
        self._entries = []
        self._sections = []

        tools = find_tools()
        if not tools:
            ttk.Label(
                self.body, text="launcher.json を持つツールが見つかりませんでした。"
            ).pack(padx=16, pady=16)
            return

        fav_tools = [
            t for t in tools if str(t["_dir"].relative_to(ROOT_DIR)) in self.favorites
        ]
        if fav_tools:
            fav_section = CollapsibleSection(
                self.body, f"★ お気に入り（{len(fav_tools)}）", expanded=True
            )
            fav_section.pack(fill="x", padx=6, pady=(6, 2))
            self._sections.append(fav_section)
            for tool in fav_tools:
                self.add_tool_frame(fav_section.body, tool, fav_section)

        grouped = defaultdict(list)
        for tool in tools:
            grouped[get_category_key(tool["_dir"])].append(tool)

        for key in sorted(grouped.keys()):
            cat_tools = grouped[key]
            section = CollapsibleSection(
                self.body, f"{get_category_label(key)}（{len(cat_tools)}）", expanded=True
            )
            section.pack(fill="x", padx=6, pady=2)
            self._sections.append(section)
            for tool in cat_tools:
                self.add_tool_frame(section.body, tool, section)

        self.apply_filter()

    def add_tool_frame(self, parent, tool, section):
        name = tool.get("name", tool["_dir"].name)
        desc = tool.get("description", "")
        rel_dir = tool["_dir"].relative_to(ROOT_DIR)
        rel_str = str(rel_dir)

        frame = ttk.LabelFrame(parent, text=name)
        frame.pack(fill="x", padx=4, pady=4)

        # 補助ボタン（☆・⚙設定）と説明文を1行に収める。別行にすると見出しとの間に
        # ボタン高さぶんの縦空白が空いてしまうため、説明文をこの行の左側に流し込む（#160）。
        top_row = ttk.Frame(frame)
        top_row.pack(fill="x", padx=8, pady=(2, 2))

        is_fav = rel_str in self.favorites
        ttk.Button(
            top_row,
            text="★" if is_fav else "☆",
            width=3,
            style=BTN_TERTIARY,
            command=lambda: self.toggle_favorite(rel_str),
        ).pack(side="right")

        for config_name, editor_cls in (
            ("config.json", ConfigEditorWindow),
            ("config.ini", IniConfigEditorWindow),
        ):
            config_path = tool["_dir"] / config_name
            if config_path.exists():
                ttk.Button(
                    top_row,
                    text="⚙設定",
                    width=7,
                    style=BTN_TERTIARY,
                    command=lambda p=config_path, n=name, c=editor_cls: c(self, p, n),
                ).pack(side="right", padx=(0, 4))
                break

        if desc:
            desc_label = ttk.Label(top_row, text=desc, justify="left")
            desc_label.pack(side="left", fill="x", expand=True)
            # ウィンドウ幅に折り返しを追従させる（固定値だとリサイズ時にズレるため）。
            desc_label.bind(
                "<Configure>", lambda e, w=desc_label: w.configure(wraplength=max(200, e.width))
            )

        ttk.Label(frame, text=rel_str, font=PATH_FONT, foreground=MUTED_FG).pack(
            anchor="w", padx=8, pady=(0, 4)
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(anchor="w", padx=8, pady=(0, 8))

        for action in tool.get("actions", []):
            self.add_action_button(btn_row, tool["_dir"], action)

        category_label = get_category_label(get_category_key(tool["_dir"]))
        search_text = " ".join([name, desc, rel_str, category_label]).lower()
        self._entries.append((search_text, frame, section))

    def add_action_button(self, parent, tool_dir: Path, action: dict):
        kind = action.get("kind", "")
        label = action.get("label", action.get("entry", "実行"))
        kind_label = KIND_LABELS.get(kind, kind)
        status_var = tk.StringVar(value="")

        def on_click():
            entry = action["entry"]
            if kind == "generator":
                run_generator(parent, tool_dir, entry, action.get("open_after", ""), status_var)
            else:
                run_fire_and_forget(tool_dir, entry)
            if action.get("note"):
                messagebox.showinfo(label, action["note"])

        action_box = ttk.Frame(parent)
        action_box.pack(side="left", padx=(0, 10))

        btn = ttk.Button(action_box, text=label, style=BTN_SECONDARY, command=on_click)
        btn.pack(side="left")
        if kind_label:
            ttk.Label(action_box, text=kind_label, font=TAG_FONT, foreground=MUTED_FG).pack(
                side="left", padx=(4, 0)
            )

        ttk.Label(parent, textvariable=status_var, foreground=STATUS_FG).pack(side="left")

    def toggle_favorite(self, rel_str: str):
        if rel_str in self.favorites:
            self.favorites.discard(rel_str)
        else:
            self.favorites.add(rel_str)
        save_favorites(self.favorites)
        self.build_tool_list()

    def apply_filter(self):
        """検索クエリに応じてツール・セクションの表示/非表示を切り替える。

        pack_forget() したウィジェットを再度 pack() すると、その時点で
        「最後に追加された扱い」になり表示順が崩れるため、対象を毎回
        forget してから登録順（self._entries / self._sections の順）で
        packし直すことで順序を保つ。
        """
        query = self.search_var.get().strip().lower()

        by_section = defaultdict(list)
        for search_text, frame, section in self._entries:
            by_section[id(section)].append((search_text, frame))

        for section in self._sections:
            section.pack_forget()
            items = by_section.get(id(section), [])
            any_match = False
            for search_text, frame in items:
                frame.pack_forget()
                if (not query) or (query in search_text):
                    frame.pack(fill="x", padx=4, pady=4)
                    any_match = True
            if items and (not query or any_match):
                section.pack(fill="x", padx=6, pady=2)
                if query:
                    section.set_expanded(True)


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
