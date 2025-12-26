import tkinter as tk
from tkinter import ttk, messagebox
import config

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
        self.env_combo = None # 後で参照できるように初期化

        for opt in self.tr_options:
            # 各選択肢をラップするフレーム（レイアウト調整用）
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

            # 'requires_environment' フラグがある場合、その直下に環境選択エリアを配置
            if opt.get('requires_environment'):
                env_inner_frame = ttk.Frame(item_frame, padding=(25, 2, 0, 5)) # インデント
                env_inner_frame.pack(fill="x")
                
                ttk.Label(env_inner_frame, text="対象環境:").pack(side="left")
                
                # 環境リストをそのまま設定
                self.env_combo = ttk.Combobox(
                    env_inner_frame, 
                    values=self.env_options, 
                    state="disabled", 
                    width=25
                )
                self.env_combo.pack(side="left", padx=5)
                # デフォルト設定（あれば）
                if self.env_options:
                    # 'UAT2' があればそれを、なければ先頭を選択
                    default_idx = 0
                    if "UAT2" in self.env_options:
                        default_idx = self.env_options.index("UAT2")
                    self.env_combo.current(default_idx)

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
        print(f"Mode changed to: {mode}")
        
        if mode == 'tr':
            # TRモード: 詳細エリアのラジオボタンを有効化
            for rb in self.tr_radios:
                rb.configure(state='normal')
            self._on_tr_type_change() # 環境プルダウンの状態更新

        else:
            # 勤怠モードなど: 詳細エリアを無効化
            for rb in self.tr_radios:
                rb.configure(state='disabled')
            if self.env_combo:
                self.env_combo.configure(state='disabled')

    def _on_tr_type_change(self):
        """TR種別変更時のUI制御"""
        if self.selected_mode.get() != 'tr':
            return

        current_tr_key = self.selected_tr_type.get()
        print(f"TR type changed to: {current_tr_key}")
        
        # 選択されたオプションの設定を取得
        selected_opt = next((opt for opt in self.tr_options if opt['key'] == current_tr_key), None)
        
        # 環境選択が必要なオプションが選ばれているか
        if selected_opt and selected_opt.get('requires_environment'):
            if self.env_combo:
                self.env_combo.configure(state='readonly') # 編集不可、選択のみ
        else:
            if self.env_combo:
                self.env_combo.configure(state='disabled')

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
                # 以前のような split 処理は不要。値をそのまま取得
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