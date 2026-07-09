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
"""
import json
import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT_DIR = Path(__file__).resolve().parent.parent

KIND_LABELS = {
    "gui": "GUI",
    "cli": "CLI",
    "server": "サーバー",
    "generator": "生成",
}


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


def _cmd_c_line(entry_path: Path) -> str:
    """`cmd /c` に渡すコマンドラインを組み立てる。

    entryは絶対パスで渡す。日本語を含むフォルダ名では、相対パス+cwd指定の
    組み合わせだと cmd.exe が "run.bat" を見つけられないことがあるため。
    さらにパスに括弧 () を含む場合（例: "31_csv-excel-viewer(phpMyadmin)"）、
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


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python ツールランチャー")
        self.geometry("760x560")

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)

        self.body.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.build_tool_list()

    def build_tool_list(self):
        tools = find_tools()
        if not tools:
            ttk.Label(
                self.body, text="launcher.json を持つツールが見つかりませんでした。"
            ).pack(padx=16, pady=16)
            return

        for tool in tools:
            frame = ttk.LabelFrame(self.body, text=tool.get("name", tool["_dir"].name))
            frame.pack(fill="x", padx=10, pady=6)

            desc = tool.get("description", "")
            if desc:
                ttk.Label(frame, text=desc, wraplength=680, justify="left").pack(
                    anchor="w", padx=8, pady=(4, 2)
                )

            rel_dir = tool["_dir"].relative_to(ROOT_DIR)
            ttk.Label(frame, text=str(rel_dir), foreground="gray").pack(
                anchor="w", padx=8, pady=(0, 4)
            )

            btn_row = ttk.Frame(frame)
            btn_row.pack(anchor="w", padx=8, pady=(0, 8))

            for action in tool.get("actions", []):
                self.add_action_button(btn_row, tool["_dir"], action)

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

        btn = ttk.Button(parent, text=f"{label} [{kind_label}]", command=on_click)
        btn.pack(side="left", padx=(0, 6))

        ttk.Label(parent, textvariable=status_var, foreground="blue").pack(side="left")


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
