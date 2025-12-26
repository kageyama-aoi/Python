import tkinter as tk
from tkinter import ttk, messagebox
import config

class SelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自動化ツール実行設定")
        self.root.geometry("500x500")

        # 戻り値を格納する変数
        self.result = (None, None) # (school_type, environment_name)
        self.is_submitted = False

        # 設定のロード
        self.menus = config.CONF.get('menus', {})
        self.modes = self.menus.get('modes', {})
        self.tr_options = self.menus.get('tr_options', [])
        self.env_options = self.menus.get('environment_options', {})

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
        for opt in self.tr_options:
            rb = ttk.Radiobutton(
                self.tr_frame,
                text=opt['label'],
                variable=self.selected_tr_type,
                value=opt['key'],
                command=self._on_tr_type_change
            )
            rb.pack(anchor="w", pady=1)
            self.tr_radios.append(rb)

        # --- 環境選択エリア ---
        env_frame = ttk.Frame(self.tr_frame, padding=(0, 10, 0, 0))
        env_frame.pack(fill="x")
        
        ttk.Label(env_frame, text="対象環境:").pack(side="left")
        
        # 環境リストの作成 (表示用: "key: value")
        self.env_values = [f"{k}: {v}" for k, v in self.env_options.items()]
        self.env_combo = ttk.Combobox(env_frame, values=self.env_values, state="disabled", width=30)
        self.env_combo.pack(side="left", padx=5)

        # --- アクションボタン ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="実行", command=self._on_submit).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="終了", command=self.root.destroy).pack(side="right", padx=5)

        # 初期状態の設定
        self._on_mode_change()

    def _on_mode_change(self):
        """モード変更時のUI制御"""
        mode = self.selected_mode.get()
        print(f"Mode changed to: {mode}") # Debug
        
        if mode == 'tr':
            # TRモード: 詳細エリアのラジオボタンを有効化
            for rb in self.tr_radios:
                rb.configure(state='normal')
            
            # TR詳細が未選択なら、最初のものをデフォルトで選択しておくと親切かもしれない
            # if not self.selected_tr_type.get() and self.tr_radios:
            #     self.selected_tr_type.set(self.tr_options[0]['key'])
            
            # 現在のTR詳細選択状態に合わせて環境プルダウンの状態を更新
            self._on_tr_type_change()

        else:
            # 勤怠モード(cl)など: 詳細エリアを無効化
            for rb in self.tr_radios:
                rb.configure(state='disabled')
            self.env_combo.configure(state='disabled')

    def _on_tr_type_change(self):
        """TR種別変更時のUI制御"""
        # 現在TRモードでなければ何もしない（無効化処理は _on_mode_change で実施済）
        if self.selected_mode.get() != 'tr':
            return

        current_tr_key = self.selected_tr_type.get()
        print(f"TR type changed to: {current_tr_key}") # Debug
        
        # 選択されたオプションの設定を取得
        selected_opt = next((opt for opt in self.tr_options if opt['key'] == current_tr_key), None)
        
        if selected_opt and selected_opt.get('requires_environment'):
            self.env_combo.configure(state='readonly')
        else:
            self.env_combo.configure(state='disabled')
            self.env_combo.set("") # 無効化時にクリア

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
            
            # 環境が必要かチェック
            selected_opt = next((opt for opt in self.tr_options if opt['key'] == final_school_type), None)
            if selected_opt and selected_opt.get('requires_environment'):
                env_val = self.env_combo.get()
                if not env_val:
                    messagebox.showwarning("警告", "対象環境を選択してください。")
                    return
                # "k: v" 形式から v (環境名) を抽出する必要があるが、
                # 既存ロジックは config.CONF['menus']['environment_list'][key] で取得していた。
                # ここでは値をそのまま渡すか、キーを渡すか。
                # form_handler.py は context['environment_name'] をそのまま使う。
                # Comboboxの値は "t: trainingGCP" のような形式。
                # ここから "trainingGCP" 部分を取り出すか、単純に選択値を渡すか。
                # 既存ロジックに合わせて "trainingGCP" (値部分) を渡すのが適切そう。
                final_env_name = env_val.split(": ", 1)[1] if ": " in env_val else env_val

        self.result = (final_school_type, final_env_name)
        self.is_submitted = True
        self.root.destroy()

def get_user_input_gui():
    """
    GUIを起動し、ユーザー選択結果を返します。
    Returns:
        tuple: (school_type, environment_name)
    """
    root = tk.Tk()
    app = SelectionApp(root)
    root.mainloop()
    
    if app.is_submitted:
        return app.result
    else:
        # ウィンドウを閉じた場合などは終了とみなす
        return None, None
