import pandas as pd
from . import config as cfg
from .constants import InputCols as IC


def _prompt_choice(label, options, default):
    """番号選択プロンプトを表示し、選択された値を返す。0 は空文字（全件）を意味する。"""
    print(f"\n--- {label} を選択してください ---")
    print("  0: 全て（絞り込みなし）")
    for i, opt in enumerate(options, start=1):
        marker = " ← 現在の設定" if opt == default else ""
        print(f"  {i}: {opt}{marker}")

    default_prompt = f"（Enter で '{default}' を使用）" if default else "（Enter で 0: 全て を選択）"
    while True:
        raw = input(f"番号を入力 {default_prompt}: ").strip()

        if raw == "":
            return default  # Enter → デフォルト値をそのまま使用

        if not raw.isdigit():
            print("  ※ 数字を入力してください。")
            continue

        idx = int(raw)
        if idx == 0:
            return ""
        if 1 <= idx <= len(options):
            return options[idx - 1]
        print(f"  ※ 1〜{len(options)} または 0 を入力してください。")


def select_target(timesheet_path, default_project="", default_employee=""):
    """
    タイムシートCSVから取引先・社員一覧を読み込み、
    インタラクティブに対象を選択して (project, employee) を返す。
    """
    df = pd.read_csv(timesheet_path, encoding=cfg.ENCODING,
                     usecols=[IC.CLIENT_NAME, IC.EMPLOYEE_NAME])

    projects = sorted(df[IC.CLIENT_NAME].dropna().unique().tolist())
    project = _prompt_choice("取引先（プロジェクト）", projects, default_project)

    # プロジェクトが絞られている場合は社員も絞る
    if project:
        employee_df = df[df[IC.CLIENT_NAME] == project]
    else:
        employee_df = df
    employees = sorted(employee_df[IC.EMPLOYEE_NAME].dropna().unique().tolist())
    employee = _prompt_choice("社員名", employees, default_employee)

    return project, employee
