import os
import tkinter as tk
from tkinter import messagebox, ttk

from src import theme
from src.handlers import config_wizard, mapping_handler
from src.utils.fixed_format import REC_TYPE_LABELS

INSTRUCTION = (
    "仕様書の桁位置の表を貼り付けてください。1行に1項目、タブ区切りで\n"
    "「項目名  開始位置  文字数」（開始位置・文字数は1始まり）。\n"
    "例:  会員番号\t2\t16"
)

# 貼り付けタブのレコード種別（「データ」は必須、他は空でよい）
REC_TYPE_TABS = [("D", "データ"), ("H", "ヘッダー"), ("T", "トレーラー"), ("E", "エンドレコード")]


class ConfigWizardWindow(tk.Toplevel):
    """「新しいファイルに対応」ウィザード。桁位置の表を貼り付けて設定Excelを生成し、
    mapping.csv に登録して、そのまま変換まで実行する。"""

    def __init__(self, app, ctx):
        super().__init__(app)
        self.app = app
        self.ctx = ctx
        self.title("新しいファイルに対応")
        self.geometry("660x740")
        self.minsize(560, 600)
        self.transient(app)
        self.grab_set()
        theme.style_titlebar(self)

        self._paste_boxes = {}  # rec_key -> tk.Text
        self._build_widgets()
        self._reload_input_files()

    # ---- 画面構築 ----

    def _build_widgets(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        step1 = ttk.LabelFrame(outer, text="1. 対象の固定長ファイル", padding=10)
        step1.pack(fill="x")
        ttk.Label(step1, text="data/input/ 内のファイル:").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar()
        self.input_combo = ttk.Combobox(step1, textvariable=self.input_var, state="readonly", width=36)
        self.input_combo.grid(row=0, column=1, padx=(6, 0), sticky="w")
        self.input_combo.bind("<<ComboboxSelected>>", self._on_input_selected)

        ttk.Label(step1, text="設定ファイル名:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.config_name_var = tk.StringVar(value="config_")
        ttk.Entry(step1, textvariable=self.config_name_var, width=38).grid(
            row=1, column=1, padx=(6, 0), pady=(6, 0), sticky="w"
        )
        self.input_hint = ttk.Label(step1, text="", foreground=theme.WARN_FG)
        self.input_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        step2 = ttk.LabelFrame(outer, text="2. 桁位置の定義", padding=10)
        step2.pack(fill="x", pady=(10, 0))
        ttk.Label(step2, text=INSTRUCTION, justify="left").pack(anchor="w")
        ttk.Label(step2, text="※ ヘッダー/トレーラー/エンドレコードが無い形式なら「データ」だけでOK",
                  foreground=theme.MUTED_FG).pack(anchor="w", pady=(2, 6))

        nb = ttk.Notebook(step2)
        nb.pack(fill="x")
        for rec_key, label in REC_TYPE_TABS:
            tab = ttk.Frame(nb, padding=6)
            nb.add(tab, text=label)
            self._paste_boxes[rec_key] = self._make_paste_box(tab, height=8)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="プレビュー", style=theme.BTN_SECONDARY,
                   command=self._on_preview).pack(side="left")
        self.create_btn = ttk.Button(
            actions, text="作成して変換する", style=theme.BTN_PRIMARY,
            command=self._on_create, state="disabled",
        )
        self.create_btn.pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="閉じる", style=theme.BTN_TERTIARY,
                   command=self.destroy).pack(side="right")

        self.msg_var = tk.StringVar(value="「プレビュー」で内容を確認できます。")
        ttk.Label(outer, textvariable=self.msg_var, justify="left",
                  foreground=theme.MUTED_FG, wraplength=620).pack(anchor="w", pady=(8, 0))

        step3 = ttk.LabelFrame(outer, text="3. プレビュー", padding=10)
        step3.pack(fill="both", expand=True, pady=(6, 0))
        cols = ("type", "name", "start", "end", "length")
        self.tree = ttk.Treeview(step3, columns=cols, show="headings", height=6)
        for c, text, width in (
            ("type", "レコード種別", 90), ("name", "項目名", 160),
            ("start", "開始", 60), ("end", "終了", 60), ("length", "文字数", 60),
        ):
            self.tree.heading(c, text=text)
            self.tree.column(c, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def _make_paste_box(self, parent, height=6):
        box = tk.Text(parent, height=height, wrap="none", font=theme.LOG_FONT,
                      background=theme.LOG_BG, foreground=theme.LOG_FG,
                      insertbackground=theme.LOG_FG, relief="flat")
        box.pack(fill="x", pady=(2, 0))
        return box

    # ---- イベント ----

    def _reload_input_files(self):
        input_dir = self.ctx.dirs["input"]
        files = (
            sorted(f for f in os.listdir(input_dir)
                   if not f.startswith(".") and not f.startswith("~$"))
            if os.path.isdir(input_dir) else []
        )
        self.input_combo["values"] = files
        if not files:
            self.input_hint.configure(
                text="data/input/ にファイルがありません。先に対象ファイルを置いてください。"
            )
        else:
            self.input_hint.configure(text="")

    def _on_input_selected(self, event=None):
        selected = self.input_var.get()
        if selected:
            base = os.path.splitext(selected)[0]
            self.config_name_var.set(f"config_{base}")

    _MAX_SHOWN_ERRORS = 12

    def _collect(self):
        """全タブの貼り付け欄をパースして (fields_by_type, errors) を返す。"""
        fields_by_type = {}
        errors = []
        for rec_key, _ in REC_TYPE_TABS:
            text = self._paste_boxes[rec_key].get("1.0", "end").strip()
            if rec_key != "D" and not text:
                continue
            fields, errs = config_wizard.parse_field_spec(text)
            label = REC_TYPE_LABELS[rec_key]
            errors.extend(f"[{label}] {e}" for e in errs)
            if fields:
                fields_by_type[rec_key] = fields
        if len(errors) > self._MAX_SHOWN_ERRORS:
            hidden = len(errors) - self._MAX_SHOWN_ERRORS
            errors = errors[:self._MAX_SHOWN_ERRORS] + [f"... 他 {hidden} 件"]
        return fields_by_type, errors

    def _on_preview(self):
        self.tree.delete(*self.tree.get_children())
        fields_by_type, errors = self._collect()

        if errors:
            self.create_btn.configure(state="disabled")
            self.msg_var.set("修正が必要:\n" + "\n".join(errors))
            return

        for rec_key, _ in config_wizard.REC_TYPE_SHEETS:
            for f in fields_by_type.get(rec_key, []):
                self.tree.insert("", "end", values=(
                    REC_TYPE_LABELS[rec_key], f["name"],
                    f["start"], f["start"] + f["length"] - 1, f["length"],
                ))

        warns = config_wizard.validation_warnings(fields_by_type)
        if warns:
            self.msg_var.set("注意（このまま作成もできます）:\n" + "\n".join(warns))
        else:
            self.msg_var.set("問題は見つかりませんでした。「作成して変換する」で進めます。")
        self.create_btn.configure(state="normal")

    def _on_create(self):
        if self.app.is_running:
            messagebox.showinfo("実行中", "他の処理の完了後にもう一度お試しください。", parent=self)
            return

        input_file = self.input_var.get()
        if not input_file:
            messagebox.showwarning("未選択", "対象の固定長ファイルを選んでください。", parent=self)
            return

        fields_by_type, errors = self._collect()
        if errors:
            messagebox.showwarning("桁位置の定義エラー", "\n".join(errors), parent=self)
            return

        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showwarning("未入力", "設定ファイル名を入力してください。", parent=self)
            return
        if not config_name.endswith(".xlsx"):
            config_name += ".xlsx"

        configs_dir = self.ctx.dirs["configs"]
        os.makedirs(configs_dir, exist_ok=True)
        config_path = os.path.join(configs_dir, config_name)
        if os.path.exists(config_path) and not messagebox.askyesno(
            "上書き確認", f"{config_name} は既に存在します。上書きしますか？", parent=self,
        ):
            return

        try:
            config_wizard.build_config_excel(config_path, fields_by_type)
        except (ValueError, OSError) as exc:
            messagebox.showerror("設定Excelを作成できません", str(exc), parent=self)
            return

        keyword = os.path.splitext(input_file)[0]
        mapping_handler.add_mapping_entry(self.ctx, keyword, config_name)

        app = self.app
        app.logger.info(f"新規登録: {input_file} → {config_name}（変換を実行します）")
        self.destroy()
        app.after(0, lambda: app._run_action("to_excel"))
