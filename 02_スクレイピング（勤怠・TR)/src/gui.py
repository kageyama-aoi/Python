import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import config
from config_manager import ConfigManager

class SelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自動化ツール実行設定")
        self.root.geometry("500x550")

        # 戻り値を格納する変数
        self.result = (None, None) # (school_type, environment_name)
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
            self.edit_btn.configure(state='normal') # 編集ボタン有効化

        else:
            # 勤怠モードなど: 詳細エリア無効化
            for rb in self.tr_radios:
                rb.configure(state='disabled')
            if self.env_combo:
                self.env_combo.configure(state='disabled')
            self.edit_btn.configure(state='disabled') # 編集ボタン無効化

    def _on_tr_type_change(self):
        """TR種別変更時のUI制御"""
        if self.selected_mode.get() != 'tr':
            return

        current_tr_key = self.selected_tr_type.get()
        print(f"TR type changed to: {current_tr_key}")
        
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

        manager = ConfigManager()
        data, file_path = manager.load_for_edit(current_mode)
        
        if not data:
            messagebox.showerror("エラー", f"設定データが見つかりません。\nMode: {current_mode}")
            return

        # サブウィンドウ作成
        editor = tk.Toplevel(self.root)
        editor.title(f"設定編集: {current_mode}")
        editor.geometry("600x600")

        # ファイルパス表示
        ttk.Label(editor, text=f"File: {file_path}", font=("", 8)).pack(anchor="w", padx=10, pady=5)

        # フォーム生成用エリア (スクロール付き)
        canvas = tk.Canvas(editor)
        scrollbar = ttk.Scrollbar(editor, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Canvas配置 (下のアクションボタンエリアのためにpack)
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.place(relx=1, rely=0, relheight=1, anchor="ne") # 簡易的な配置

        entries = {} # {key: widget}
        row = 0
        
        # データのキーごとにウィジェット作成
        for key, value in data.items():
            ttk.Label(scroll_frame, text=key, font=("", 10, "bold")).grid(row=row, column=0, sticky="nw", padx=10, pady=5)
            
            val_str = str(value) if value is not None else ""
            
            # 長いテキストや改行を含む場合はTextウィジェット、それ以外はEntry
            if len(val_str) > 50 or "\n" in val_str:
                txt = scrolledtext.ScrolledText(scroll_frame, height=5, width=50)
                txt.insert("1.0", val_str)
                txt.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
                entries[key] = txt
            else:
                ent = ttk.Entry(scroll_frame, width=50)
                ent.insert(0, val_str)
                ent.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
                entries[key] = ent
            
            row += 1

        # 保存ボタンエリア
        action_frame = ttk.Frame(editor, padding=10)
        action_frame.pack(side="bottom", fill="x")

        def save():
            new_values = {}
            for k, widget in entries.items():
                if isinstance(widget, ttk.Entry):
                    new_values[k] = widget.get()
                else: # ScrolledText
                    new_values[k] = widget.get("1.0", "end-1c") # 末尾の改行を除く
            
            try:
                manager.save_setting(current_mode, new_values)
                messagebox.showinfo("成功", "設定を保存しました。")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("保存エラー", str(e))

        ttk.Button(action_frame, text="保存", command=save).pack(side="right", padx=5)
        ttk.Button(action_frame, text="キャンセル", command=editor.destroy).pack(side="right", padx=5)

    def _on_submit(self):
        """実行ボタン押下時の処理"""
        mode = self.selected_mode.get()
        
        if not mode:
            messagebox.showwarning("警告", "モードを選択してください。")
            return

        final_school_type = ""
        final_env_name = ""

        if mode == 'cl':
            final_school_type = 'cl'
        elif mode == 'tr':
            final_school_type = self.selected_tr_type.get()
            if not final_school_type:
                messagebox.showwarning("警告", "TRの詳細種別を選択してください。")
                return
            
            selected_opt = next((opt for opt in self.tr_options if opt['key'] == final_school_type), None)
            if selected_opt and selected_opt.get('requires_environment'):
                if self.env_combo:
                    final_env_name = self.env_combo.get()
                
                if not final_env_name:
                    messagebox.showwarning("警告", "対象環境を選択してください。")
                    return

        self.result = (final_school_type, final_env_name)
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
        return None, None
