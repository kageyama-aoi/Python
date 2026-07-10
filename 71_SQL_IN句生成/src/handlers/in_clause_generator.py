"""CSVからユーザー名を抽出し、SQLのIN句テキストを生成するハンドラ。"""
import os

import pandas as pd


def extract_user_names(df: pd.DataFrame, filter_cfg: dict, logger=None) -> list:
    """条件（status一致・除外ユーザー）でフィルタし、ソート済みユーザー名リストを返す。

    status列がCSVに存在しない場合はフィルタをスキップする（汎用CSV対応）。
    """
    user_col = filter_cfg["user_column"]
    status_col = filter_cfg["status_column"]
    status_value = filter_cfg["status_value"]
    exclude_users = filter_cfg.get("exclude_users") or []

    if user_col not in df.columns:
        raise KeyError(
            f"列 '{user_col}' がCSVにありません（実際の列: {list(df.columns)}）。"
            f" config/main.yaml の filter.user_column を確認してください。"
        )

    if status_col in df.columns:
        df = df[df[status_col] == status_value]
    elif logger:
        logger.warning(
            f"列 '{status_col}' がないため statusフィルタをスキップします。"
        )

    filtered = df[~df[user_col].isin(exclude_users)]
    return sorted(filtered[user_col].astype(str))


def build_in_clause(names: list) -> str:
    """名前リストを ('a', 'b', ...) 形式のIN句文字列にする。

    値中のシングルクォートはSQL標準の '' にエスケープする。
    """
    if not names:
        return "()"
    escaped = [name.replace("'", "''") for name in names]
    return "('" + "', '".join(escaped) + "')"


def generate(config: dict, logger, csv_path: str) -> dict:
    """CSVを読み込みIN句を生成して txt/csv に書き出す。結果サマリを返す。"""
    input_cfg = config["input"]
    output_cfg = config["output"]

    df = pd.read_csv(csv_path, encoding=input_cfg.get("encoding", "utf-8"))
    logger.info(f"CSV読込: {csv_path} ({len(df)}行)")

    names = extract_user_names(df, config["filter"], logger)
    in_clause = build_in_clause(names)
    logger.info(f"抽出ユーザー数: {len(names)}")

    txt_path = output_cfg["txt_path"]
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(in_clause)
    logger.info(f"txt出力: {txt_path}")

    csv_path_out = output_cfg["csv_path"]
    os.makedirs(os.path.dirname(csv_path_out), exist_ok=True)
    df_output = pd.DataFrame({output_cfg["csv_header"]: [in_clause]})
    df_output.to_csv(csv_path_out, index=False, encoding="utf-8-sig")
    logger.info(f"csv出力: {csv_path_out}")

    return {"count": len(names), "txt_path": txt_path, "csv_path": csv_path_out}
