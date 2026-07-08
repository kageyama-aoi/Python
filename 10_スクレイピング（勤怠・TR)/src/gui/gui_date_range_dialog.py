import tkinter as tk
from tkinter import ttk
import datetime
import calendar


def ask_date_range() -> tuple:
    """
    CrowdLogダウンロード用の日付区間選択ダイアログを表示する。

    Returns:
        (start_date_str, end_date_str): "YYYY-MM-DD" 形式のタプル
        (None, None): キャンセル時
    """
    today = datetime.date.today()
    first_of_month = today.replace(day=1)
    last_day_num = calendar.monthrange(today.year, today.month)[1]
    last_of_month = today.replace(day=last_day_num)

    prev_last = first_of_month - datetime.timedelta(days=1)
    prev_first = prev_last.replace(day=1)

    result = [None, None]

    root = tk.Tk()
    root.title("ダウンロード期間の選択")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    selected = tk.IntVar(value=0)
    year_var = tk.IntVar(value=today.year)
    month_var = tk.IntVar(value=today.month)

    # _on_change がスピンボックスを参照するため先に作成しておく
    custom_frame = ttk.Frame(frame, padding=(20, 4, 0, 0))
    year_spin = ttk.Spinbox(custom_frame, from_=2020, to=2035, textvariable=year_var, width=6, state="disabled")
    month_spin = ttk.Spinbox(custom_frame, from_=1, to=12, textvariable=month_var, width=4, state="disabled")

    def _on_change():
        state = "normal" if selected.get() == 3 else "disabled"
        year_spin.configure(state=state)
        month_spin.configure(state=state)

    # ヘッダー
    ttk.Label(frame, text="ダウンロード期間を選択してください", font=("", 10, "bold")).pack(anchor="w", pady=(0, 12))

    # ラジオボタン（視覚的に上から順に配置）
    radio_labels = [
        f"今月  （{first_of_month.strftime('%Y/%m/%d')} ～ {last_of_month.strftime('%Y/%m/%d')}）",
        f"当月1日〜今日  （{first_of_month.strftime('%Y/%m/%d')} ～ {today.strftime('%Y/%m/%d')}）",
        f"先月  （{prev_first.strftime('%Y/%m/%d')} ～ {prev_last.strftime('%Y/%m/%d')}）",
        "月を指定する",
    ]
    for i, label in enumerate(radio_labels):
        ttk.Radiobutton(frame, text=label, variable=selected, value=i, command=_on_change).pack(anchor="w", pady=2)

    # 月指定サブフォーム（ラジオボタン直下）
    ttk.Label(custom_frame, text="年:").pack(side="left")
    year_spin.pack(side="left", padx=(4, 10))
    ttk.Label(custom_frame, text="月:").pack(side="left")
    month_spin.pack(side="left", padx=4)
    custom_frame.pack(anchor="w")

    def _on_ok():
        idx = selected.get()
        if idx == 0:
            result[0] = first_of_month.strftime("%Y-%m-%d")
            result[1] = last_of_month.strftime("%Y-%m-%d")
        elif idx == 1:
            result[0] = first_of_month.strftime("%Y-%m-%d")
            result[1] = today.strftime("%Y-%m-%d")
        elif idx == 2:
            result[0] = prev_first.strftime("%Y-%m-%d")
            result[1] = prev_last.strftime("%Y-%m-%d")
        else:
            y = year_var.get()
            m = month_var.get()
            first = datetime.date(y, m, 1)
            last_num = calendar.monthrange(y, m)[1]
            last = datetime.date(y, m, last_num)
            result[0] = first.strftime("%Y-%m-%d")
            result[1] = last.strftime("%Y-%m-%d")
        root.destroy()

    def _on_cancel():
        root.destroy()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(16, 0))
    ttk.Button(btn_frame, text="OK", command=_on_ok).pack(side="right")
    ttk.Button(btn_frame, text="キャンセル", command=_on_cancel).pack(side="right", padx=(0, 8))

    root.mainloop()
    return tuple(result)
