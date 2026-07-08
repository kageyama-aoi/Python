"""
T10: pywebview + Tkinter 共存の動作検証スクリプト（サブプロセス方式）

pywebview はメインスレッドでのみ動作する制約があるため、
Tkinter から subprocess で別プロセスとして起動する方式を検証する。

実行後、以下を確認する:
  1. Tkinterウィンドウが表示されること
  2. ボタンを押すとpywebviewウィンドウが別プロセスで開くこと
  3. HTML内のボタンを押すとPythonメソッドが呼ばれること（コンソール出力）
"""
import os
import sys
import subprocess
import tkinter as tk


# ── pywebview プロセス側のエントリーポイント ──────────────────────────
DRAFTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "drafts")


def draft_path(date_iso: str) -> str:
    return os.path.join(DRAFTS_DIR, f"{date_iso}.json")


def load_draft(date_iso: str) -> list:
    """指定日付の下書きJSONを読み込む。なければ空リストを返す。"""
    import json
    path = draft_path(date_iso)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    return []


def run_webview():
    import json
    import datetime
    import webview

    today = datetime.date.today().isoformat()  # 例: "2026-03-30"
    draft_entries = load_draft(today)
    draft_json = json.dumps(draft_entries, ensure_ascii=False)

    html_path = os.path.join(os.path.dirname(__file__), "crowdlog_dur_input.html")
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    # HTML フラグメントを最低限のページとして包む
    HTML = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  :root {{
    --font-sans: 'Hiragino Sans', 'Yu Gothic', sans-serif;
    --color-text-primary: #1a1a1a;
    --color-text-secondary: #555;
    --color-text-tertiary: #999;
    --color-text-info: #1d6fa4;
    --color-text-danger: #c0392b;
    --color-background-primary: #fff;
    --color-background-secondary: #f5f5f5;
    --color-background-info: #e8f4fc;
    --color-border-primary: #888;
    --color-border-secondary: #ccc;
    --color-border-tertiary: #e0e0e0;
    --border-radius-md: 6px;
    --border-radius-lg: 10px;
  }}
  body {{ margin: 0; background: var(--color-background-primary); }}
</style>
</head>
<body>
{html_content}
<script>
  window.addEventListener('load', () => {{
    setDate('{today}');
    loadDraft({draft_json});
  }});
</script>
</body>
</html>"""

    class Api:
        def ping(self, message):
            print(f"[Python] ping受信: {message}", flush=True)
            return f"pong: {message}"

        def save_draft(self, payload):
            os.makedirs(DRAFTS_DIR, exist_ok=True)
            date_iso = payload.get("date", today)
            path = draft_path(date_iso)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"[Python] 下書き保存: {path}", flush=True)
            return "saved"

        def submit(self, payload):
            print(f"[Python] 登録して同期:\n{json.dumps(payload, ensure_ascii=False, indent=2)}", flush=True)
            return "submitted"

    api = Api()
    window = webview.create_window(
        title=f"工数入力 - {today}",
        html=HTML,
        width=680,
        height=700,
        js_api=api,
    )
    webview.start()


# ── Tkinter メインウィンドウ ──────────────────────────────────────────
def open_webview_subprocess():
    """pywebview を別プロセスで起動する"""
    subprocess.Popen(
        [sys.executable, __file__, "--webview"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )


def main():
    root = tk.Tk()
    root.title("Tkinter メインウィンドウ")
    root.geometry("300x150")

    label = tk.Label(root, text="Tkinterウィンドウです", font=("", 12))
    label.pack(pady=20)

    btn = tk.Button(
        root,
        text="工数入力UIを開く",
        command=open_webview_subprocess,
    )
    btn.pack()

    root.mainloop()


if __name__ == "__main__":
    if "--webview" in sys.argv:
        run_webview()
    else:
        main()
