# 03 Tkinter GUI 開発

## IT新人向け

### GUI って何？

GUI（グラフィカルユーザーインタフェース）は、
ボタンや入力欄などを使って操作できる画面のことです。
コマンドラインで `python main.py` と打つ代わりに、
マウスでクリックして操作できます。

### Tkinter とは

Python に最初から付属している GUI ライブラリです。
`pip install` 不要で使えます。

```python
import tkinter as tk
root = tk.Tk()          # ウィンドウを作る
root.title("タイトル")   # ウィンドウのタイトルを設定
root.mainloop()         # 画面を表示し続ける（閉じるまでここで待機）
```

### このプロジェクトの画面構成

```
┌─────────────────────────────────┐
│ 1. モード選択                     │ ← mode_frame (LabelFrame)
│  ○ CrowdLog                      │
│  ○ Task Report                   │
├─────────────────────────────────┤
│ 2. TR詳細設定                     │ ← tr_frame (LabelFrame)
│  ○ 標準                           │
│  ○ Yamaha                         │
│  ○ ...                            │
├─────────────────────────────────┤
│ [＋ パターン追加] [設定編集] [実行] [終了] │ ← btn_frame
└─────────────────────────────────┘
```

### ウィジェットって何？

画面に表示される「部品」のことです。

| ウィジェット | 説明 | 使用箇所 |
|---|---|---|
| `ttk.Radiobutton` | ラジオボタン（1つだけ選択） | モード選択・TR種別選択 |
| `ttk.Button` | ボタン | 実行・設定編集など |
| `ttk.Combobox` | ドロップダウン | 環境選択・パターン追加の Schools |
| `ttk.Entry` | 1行テキスト入力 | キーワード入力 |
| `tk.Text` | 複数行テキスト入力 | Comments 入力 |
| `ttk.LabelFrame` | 枠（グループ化） | モード選択エリア全体 |

---

## 中級者向け

### レイアウト管理：pack の使い方

Tkinter にはレイアウト管理が 3 種類あります（`pack`, `grid`, `place`）。
このプロジェクトでは **`pack`** と **`grid`** を使い分けています。

**`pack`（縦・横に積み上げる）**

```python
# gui.py: ボタンは右から順に積み上げ
ttk.Button(btn_frame, text="終了").pack(side="right", padx=5)
ttk.Button(btn_frame, text="実行").pack(side="right", padx=5)
ttk.Button(btn_frame, text="設定編集").pack(side="right", padx=5)
# → [設定編集] [実行] [終了] の順に右寄りで並ぶ
```

**`grid`（表形式に配置する）**

```python
# gui_add_pattern_dialog.py: ラベル・入力欄を表形式に並べる
ttk.Label(form_frame, text="キー*").grid(row=0, column=0, sticky="w")
ttk.Entry(form_frame, textvariable=key_var).grid(row=0, column=1)
ttk.Label(form_frame, text="半角英数字").grid(row=0, column=2)
```

`pack` と `grid` を **同じフレーム内で混在させてはいけません**（エラーになります）。

### イベント駆動プログラミング

GUI はユーザーの操作を「待つ」プログラムです。

```python
# ラジオボタンが変わったら _on_mode_change を呼ぶ
ttk.Radiobutton(
    mode_frame,
    variable=self.selected_mode,
    value="tr",
    command=self._on_mode_change  # ← ここでコールバックを登録
)
```

`command=` に関数を渡すと、ボタンが押されたとき自動で呼ばれます。
`root.mainloop()` が「ユーザーが何かするまでここで待つ」ループです。

### StringVar によるデータバインディング

```python
self.selected_mode = tk.StringVar(value="")

# ラジオボタンに紐付ける
ttk.Radiobutton(variable=self.selected_mode, value="cl")  # 選ぶと "cl" がセット
ttk.Radiobutton(variable=self.selected_mode, value="tr")  # 選ぶと "tr" がセット

# コード側から取得
mode = self.selected_mode.get()  # "cl" または "tr"
```

`StringVar` はウィジェットと値を繋ぐ「橋」です。
直接変数に代入するのではなく、`.get()` / `.set()` で操作します。

### モーダルダイアログ

```python
# gui_add_pattern_dialog.py
dialog = tk.Toplevel(parent)
dialog.grab_set()  # ← これがポイント
```

`grab_set()` を呼ぶと、ダイアログが閉じるまで **親ウィンドウを操作できなくなります**（モーダル）。
保存操作の途中で別の操作をされるのを防ぎます。

### GUIの動的再描画（_refresh_tr_options）

パターン追加後にGUIを再描画するには、既存ウィジェットを全消去して再生成します。

```python
def _refresh_tr_options(self):
    # 全ウィジェットを消す
    for widget in self.tr_frame.winfo_children():
        widget.destroy()

    # 最新の config から再生成
    self.tr_options = config.CONF.get('menus', {}).get('tr_options', [])
    for opt in self.tr_options:
        rb = ttk.Radiobutton(self.tr_frame, text=opt['label'], ...)
        rb.pack()
```

アプリを再起動せずに新パターンが反映される仕組みです。

---

## 上級者向け

### OOP による GUI 設計

`SelectionApp` クラスは **GUI と状態を1つにまとめた設計** です。

```python
class SelectionApp:
    def __init__(self, root):
        self.result = (None, None, None)  # 戻り値（状態）
        self.is_submitted = False
        self._create_widgets()            # 画面構築

    def _on_mode_change(self):    # イベントハンドラ（内部ロジック）
    def _on_tr_type_change(self): # イベントハンドラ
    def _on_submit(self):         # 確定処理
```

この構造の利点：
- `self.result` で実行後の結果を外から取得できる
- メソッド名に `_` がついているものは「外から直接呼ばない」という慣習

### GUI から値を受け取るパターン

```python
# main.py 側
def get_user_input_gui():
    root = tk.Tk()
    app = SelectionApp(root)
    root.mainloop()           # ← ウィンドウが閉じるまでここで止まる

    if app.is_submitted:
        return app.result     # ← 閉じた後に結果を取り出す
    else:
        return None, None, None
```

`mainloop()` は同期的にブロックするため、
**ウィンドウが閉じた後** に `app.result` を取得できます。
非同期（async/await）にすると複雑になるため、このシンプルな方式が適切です。

### コールバックによる疎結合

パターン追加ダイアログは `on_saved_callback` を受け取ります。

```python
# gui.py（呼び出し側）
def _open_add_pattern_dialog(self):
    gui_add_pattern_dialog.open_add_pattern_dialog(
        self.root,
        self._refresh_tr_options  # ← コールバックを渡す
    )

# gui_add_pattern_dialog.py（ダイアログ側）
def open_add_pattern_dialog(parent, on_saved_callback):
    def save():
        manager.add_pattern(...)
        dialog.destroy()
        on_saved_callback()  # ← 保存後に親に通知
```

ダイアログは「保存後に何をするか」を知りません。
親から渡された関数を呼ぶだけです。これを **依存性の注入（DI）** と呼びます。
ダイアログが `gui.py` を直接 import しないため、循環依存が防がれています。

### Tkinter の制約と対策

**スレッド制約**：Tkinter は**メインスレッドでのみ** GUI を操作できます。

```python
# NG: 別スレッドから直接 GUI を触る
import threading
def background_task():
    self.label.config(text="完了")  # クラッシュの原因

# OK: after() でメインスレッドにスケジュール
def background_task():
    self.root.after(0, lambda: self.label.config(text="完了"))
```

本プロジェクトではブラウザ操作中に GUI を操作しないため問題になりませんが、
プログレスバーを出したい場合は `threading + queue` が必要になります。
