"""
T10: pywebview + Tkinter 共存の動作検証スクリプト（サブプロセス方式）

pywebview はメインスレッドでのみ動作する制約があるため、
Tkinter から subprocess で別プロセスとして起動する方式を検証する。

実行後、以下を確認する:
  1. Tkinterウィンドウが表示されること
  2. ボタンを押すとpywebviewウィンドウが別プロセスで開くこと
  3. HTML内のボタンを押すとPythonメソッドが呼ばれること（コンソール出力）
"""
import sys
import subprocess
import tkinter as tk


# ── pywebview プロセス側のエントリーポイント ──────────────────────────
def run_webview():
    import webview

    HTML = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: sans-serif; padding: 2rem; }
        button { padding: 8px 20px; font-size: 14px; cursor: pointer; }
        #result { margin-top: 1rem; color: green; font-size: 14px; }
      </style>
    </head>
    <body>
      <h2>pywebview 疎通テスト</h2>
      <p>ボタンを押してPythonメソッドを呼び出します。</p>
      <button onclick="callPython()">Python に ping を送る</button>
      <div id="result"></div>
      <script>
        async function callPython() {
          const result = await window.pywebview.api.ping('こんにちは from JS');
          document.getElementById('result').textContent = '応答: ' + result;
        }
      </script>
    </body>
    </html>
    """

    class Api:
        def ping(self, message):
            print(f"[Python] ping受信: {message}", flush=True)
            return f"pong: {message}"

    api = Api()
    window = webview.create_window(
        title="pywebview テスト（サブプロセス）",
        html=HTML,
        width=500,
        height=350,
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
