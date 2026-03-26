import tkinter as tk
from tkinter import ttk, messagebox
from config import config
from gui import gui_config_dialog

class SelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自動化ツール実行設定")
        self.root.geometry("500x550")

        # 戻り値を格納する変数
        self.result = (None, None, None) # (school_type, environment_name, keyword)
        self.is_submitted = False

        # 設定のロード
        self.menus = config.CONF.get('menus', {})
        self.modes = self.menus.get('modes', {})
        self.tr_options = self.menus.get('tr_options', [])
        # リスト形式になったenvironment_optionsを取得
        self.env_options = self.menus.get('environment_options', [])

        # 変数の初期化
        self.selected_mode = tk.StringVar(value="")
        self.selected_tr_type = tk.StringVar(value="")
        self.selected_env = tk.StringVar(value="")
        self.search_keyword = tk.StringVar(value="TEST_SEARCH")

        # GUI構築
        self._create_widgets()

    def _create_widgets(self):
        # --- メインモード選択エリア ---
        mode_frame = ttk.LabelFrame(self.root, text="1. モード選択", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=10)

        # CrowdLog (勤怠)
        cl_mode = self.modes.get('crowdlog', {})
        ttk.Radiobutton(
            mode_frame,
            text=cl_mode.get('label', 'CrowdLog'),
            variable=self.selected_mode,
            value=cl_mode.get('value', 'cl'),
            command=self._on_mode_change
        ).pack(anchor="w", pady=2)

        # Task Report (TR)
        tr_mode = self.modes.get('task_report', {})
        ttk.Radiobutton(
            mode_frame,
            text=tr_mode.get('label', 'Task Report'),
            variable=self.selected_mode,
            value=tr_mode.get('value', 'tr'),
            command=self._on_mode_change
        ).pack(anchor="w", pady=2)

        # --- TR詳細選択エリア ---
        self.tr_frame = ttk.LabelFrame(self.root, text="2. TR詳細設定", padding=10)
        self.tr_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # TR種別のリスト生成
        self.tr_radios = []
        self.env_combo = None

        for opt in self.tr_options:
            item_frame = ttk.Frame(self.tr_frame)
            item_frame.pack(fill="x", pady=2)

            rb = ttk.Radiobutton(
                item_frame,
                text=opt['label'],
                variable=self.selected_tr_type,
                value=opt['key'],
                command=self._on_tr_type_change
            )
            rb.pack(anchor="w")
            self.tr_radios.append(rb)

            if opt.get('requires_environment'):
                env_inner_frame = ttk.Frame(item_frame, padding=(25, 2, 0, 5))
                env_inner_frame.pack(fill="x")

                ttk.Label(env_inner_frame, text="対象環境:").pack(side="left")

                self.env_combo = ttk.Combobox(
                    env_inner_frame,
                    values=self.env_options,
                    state="disabled",
                    width=25
                )
                self.env_combo.pack(side="left", padx=5)
                if self.env_options:
                    default_idx = 0
                    if "UAT2" in self.env_options:
                        default_idx = self.env_options.index("UAT2")
                    self.env_combo.current(default_idx)

        # --- マージ依頼 (Shimamura) ---
        ttk.Separator(self.tr_frame, orient="horizontal").pack(fill="x", pady=8)

        merge_frame = ttk.Frame(self.tr_frame)
        merge_frame.pack(fill="x", pady=2)

        merge_rb = ttk.Radiobutton(
            merge_frame,
            text="マージ依頼 (Shimamura)",
            variable=self.selected_tr_type,
            value="search",
            command=self._on_tr_type_change
        )
        merge_rb.pack(anchor="w")
        self.tr_radios.append(merge_rb)

        keyword_inner_frame = ttk.Frame(merge_frame, padding=(25, 2, 0, 5))
        keyword_inner_frame.pack(fill="x")
        ttk.Label(keyword_inner_frame, text="キーワード:").pack(side="left")
        self.keyword_entry = ttk.Entry(keyword_inner_frame, textvariable=self.search_keyword, width=25, state="disabled")
        self.keyword_entry.pack(side="left", padx=5)

        # --- アクションボタン ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x", side="bottom")

        # 右から順に配置 (pack side=right)
        ttk.Button(btn_frame, text="終了", command=self.root.destroy).pack(side="right", padx=5)

        # 実行ボタン
        self.run_btn = ttk.Button(btn_frame, text="実行", command=self._on_submit)
        self.run_btn.pack(side="right", padx=5)

        # 設定編集ボタン (新規追加)
        self.edit_btn = ttk.Button(btn_frame, text="設定編集", command=self._open_config_editor)
        self.edit_btn.pack(side="right", padx=5)
        self.edit_btn.configure(state='disabled') # 初期は無効

        # 初期状態の設定
        self._on_mode_change()

    def _on_mode_change(self):
        """モード変更時のUI制御"""
        mode = self.selected_mode.get()
        print(f"Mode changed to: {mode}")

        if mode == 'tr':
            # TRモード: 詳細エリア有効化
            for rb in self.tr_radios:
                rb.configure(state='normal')
            self._on_tr_type_change()

        else:
            # 勤怠モードなど: 詳細エリア全体を無効化
            for rb in self.tr_radios:
                rb.configure(state='disabled')
            if self.env_combo:
                self.env_combo.configure(state='disabled')
            self.keyword_entry.configure(state='disabled')
            self.edit_btn.configure(state='disabled')

    def _on_tr_type_change(self):
        """TR種別変更時のUI制御"""
        if self.selected_mode.get() != 'tr':
            return

        current_tr_key = self.selected_tr_type.get()
        print(f"TR type changed to: {current_tr_key}")

        if current_tr_key == 'search':
            # マージ依頼: キーワード有効、env無効、設定編集無効
            self.keyword_entry.configure(state='normal')
            if self.env_combo:
                self.env_combo.configure(state='disabled')
            self.edit_btn.configure(state='disabled')
        else:
            # 通常TR: キーワード無効、設定編集有効
            self.keyword_entry.configure(state='disabled')
            self.edit_btn.configure(state='normal')
            selected_opt = next((opt for opt in self.tr_options if opt['key'] == current_tr_key), None)
            if selected_opt and selected_opt.get('requires_environment'):
                if self.env_combo:
                    self.env_combo.configure(state='readonly')
            else:
                if self.env_combo:
                    self.env_combo.configure(state='disabled')

    def _open_config_editor(self):
        """設定編集ダイアログを開く"""
        current_mode = self.selected_tr_type.get()
        if not current_mode:
            messagebox.showwarning("警告", "編集するTR種別を選択してください。")
            return
        gui_config_dialog.open_config_editor(self.root, current_mode)

    def _on_submit(self):
        """実行ボタン押下時の処理"""
        mode = self.selected_mode.get()

        if not mode:
            messagebox.showwarning("警告", "モードを選択してください。")
            return

        final_school_type = ""
        final_env_name = ""

        final_keyword = ""

        if mode == 'cl':
            final_school_type = 'cl'
        elif mode == 'tr':
            final_school_type = self.selected_tr_type.get()
            if not final_school_type:
                messagebox.showwarning("警告", "TRの詳細種別を選択してください。")
                return

            if final_school_type == 'search':
                final_keyword = self.search_keyword.get().strip()
                if not final_keyword:
                    messagebox.showwarning("警告", "検索キーワードを入力してください。")
                    return
            else:
                selected_opt = next((opt for opt in self.tr_options if opt['key'] == final_school_type), None)
                if selected_opt and selected_opt.get('requires_environment'):
                    if self.env_combo:
                        final_env_name = self.env_combo.get()

                    if not final_env_name:
                        messagebox.showwarning("警告", "対象環境を選択してください。")
                        return

        self.result = (final_school_type, final_env_name, final_keyword)
        self.is_submitted = True
        self.root.destroy()

def get_user_input_gui():
    """
    GUIを起動し、ユーザー選択結果を返します。
    """
    root = tk.Tk()
    app = SelectionApp(root)
    root.mainloop()

    if app.is_submitted:
        return app.result
    else:
        return None, None, None


def show_completion_message(msg: str):
    """
    処理完了をダイアログで通知します。

    Args:
        msg: 表示するメッセージ文字列
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo('完了メッセージ', msg)
