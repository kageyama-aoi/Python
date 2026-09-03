import os
import tkinter as tk
from tkinter import messagebox, ttk

from src import theme
from src.handlers import mapping_handler


class MappingEditorWindow(tk.Toplevel):
    """mapping.csvの登録内容を一覧表示し、input/configをプルダウンで選んで追加・削除する編集画面"""

    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.title("mapping.csv 編集")
        self.geometry("580x520")
        self.transient(parent)
        theme.style_titlebar(self)

        self._build_widgets()
        self.refresh()

    def _build_widgets(self):
        columns = ("keyword", "config", "note")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self.tree.heading("keyword", text="判定キーワード")
        self.tree.heading("config", text="設定ファイル名")
        self.tree.heading("note", text="備考")
        self.tree.column("keyword", width=140)
        self.tree.column("config", width=220)
        self.tree.column("note", width=140)
        self.tree.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill="x", padx=10)
        self.scan_btn = ttk.Button(
            btn_bar, text="inputをスキャンして候補追加", command=self._on_scan_inputs
        )
        self.scan_btn.pack(side="left")
        self.delete_btn = ttk.Button(btn_bar, text="選択行を削除", command=self._on_delete)
        self.delete_btn.pack(side="right")

        form_frame = ttk.LabelFrame(self, text="新規登録", padding=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="inputファイル:").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar()
        self.input_combo = ttk.Combobox(form_frame, textvariable=self.input_var, state="readonly", width=32)
        self.input_combo.grid(row=0, column=1, padx=(6, 0), sticky="w")
        self.input_combo.bind("<<ComboboxSelected>>", self._on_input_selected)

        ttk.Label(form_frame, text="キーワード:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.keyword_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.keyword_var, width=34).grid(
            row=1, column=1, padx=(6, 0), pady=(6, 0), sticky="w"
        )

        ttk.Label(form_frame, text="適用Config:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.config_var = tk.StringVar()
        self.config_combo = ttk.Combobox(form_frame, textvariable=self.config_var, state="readonly", width=32)
        self.config_combo.grid(row=2, column=1, padx=(6, 0), pady=(6, 0), sticky="w")

        self.register_btn = ttk.Button(form_frame, text="登録", command=self._on_register)
        self.register_btn.grid(row=3, column=1, sticky="e", pady=(10, 0))

    def set_locked(self, locked):
        """メイン画面でバックグラウンド処理が走っている間、このウィンドウからのmapping.csv
        書き込みを止める（同時書き込みによる上書き事故を防ぐ）"""
        state = "disabled" if locked else "readonly"
        self.input_combo.configure(state=state)
        self.config_combo.configure(state=state)
        self.register_btn.configure(state="disabled" if locked else "normal")
        self.delete_btn.configure(state="disabled" if locked else "normal")
        self.scan_btn.configure(state="disabled" if locked else "normal")

    def _reload_file_lists(self):
        dirs = self.ctx.dirs
        input_dir = dirs["input"]
        configs_dir = dirs["configs"]
        mapping_name = os.path.basename(self.ctx.mapping_csv)

        input_files = (
            sorted(f for f in os.listdir(input_dir) if not f.startswith(".") and not f.startswith("~$"))
            if os.path.isdir(input_dir)
            else []
        )
        config_files = (
            sorted(
                f for f in os.listdir(configs_dir)
                if f.endswith((".xlsx", ".csv")) and f != mapping_name and not f.startswith("~$")
            )
            if os.path.isdir(configs_dir)
            else []
        )

        self.input_combo["values"] = input_files
        self.config_combo["values"] = config_files

    def _on_input_selected(self, event=None):
        selected = self.input_var.get()
        if selected:
            self.keyword_var.set(os.path.splitext(selected)[0])

    def _on_register(self):
        keyword = self.keyword_var.get().strip()
        config_name = self.config_var.get().strip()
        if not keyword or not config_name:
            messagebox.showwarning(
                "入力不足", "キーワードと適用Configの両方を指定してください。", parent=self
            )
            return

        # 既存キーワードへの登録はadd_mapping_entry内で無言のまま置き換わる（バックアップは作られるが
        # 画面上は何も変わって見えない）ため、割り当てが変わる場合はここで一度確認を挟む。
        existing_config = mapping_handler.find_existing_config(self.ctx, keyword)
        if existing_config is not None and existing_config != config_name:
            if not messagebox.askyesno(
                "上書き確認",
                f"キーワード '{keyword}' は既に登録されています。\n"
                f"適用Config: {existing_config} → {config_name}\n\n"
                "登録済みの設定を上書きしますか？",
                parent=self,
            ):
                return

        mapping_handler.add_mapping_entry(self.ctx, keyword, config_name)
        self.refresh()

    def _on_scan_inputs(self):
        """data/input の新規ファイル名から未登録のキーワード候補を追記する
        （設定ファイル名は要手動確認。旧「mapping.csv 更新」ボタン相当）。"""
        added = mapping_handler.build_or_update_mapping(self.ctx)
        self.refresh()
        if added:
            messagebox.showinfo(
                "候補を追加しました",
                f"{added}件の候補を追加しました。設定ファイル名（適用Config）は一覧で確認・修正してください。",
                parent=self,
            )
        else:
            messagebox.showinfo("候補なし", "未登録の新規ファイルはありませんでした。", parent=self)

    def _on_delete(self):
        selection = self.tree.selection()
        if not selection:
            return
        keyword = self.tree.item(selection[0])["values"][0]
        if not messagebox.askyesno("削除確認", f"'{keyword}' の登録を削除しますか？", parent=self):
            return
        mapping_handler.remove_mapping_entry(self.ctx, str(keyword))
        self.refresh()

    def refresh(self):
        """一覧・プルダウン候補を読み直す（外部のバックグラウンド処理完了後の再同期にも使う）"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        df_map = mapping_handler.load_mapping(self.ctx)
        columns = self.ctx.mapping_columns
        keyword_col = columns["keyword"]
        config_col = columns["config_name"]
        note_col = columns.get("note", "備考")

        for _, row in df_map.iterrows():
            note_val = row[note_col] if note_col in df_map.columns else ""
            self.tree.insert("", "end", values=(row[keyword_col], row[config_col], note_val))

        self._reload_file_lists()
