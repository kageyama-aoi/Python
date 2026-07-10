"""CSV/テキストから値を抽出し、SQLのIN句テキストを生成するハンドラ。"""
import os

import pandas as pd


def load_table(path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """入力ファイルをDataFrameとして読み込む。

    - .csv: 通常のCSVとして読む
    - それ以外: テキストとして読む
      - パイプ区切り（SQLクライアントの表形式出力）は1行目をヘッダーとして表に変換
      - それ以外は1行1値のリストとして単一列 'value' に変換
    """
    _, ext = os.path.splitext(path)
    if ext.lower() == ".csv":
        return pd.read_csv(path, encoding=encoding)

    with open(path, "r", encoding=encoding) as f:
        lines = [line.strip() for line in f]
    # 罫線行（+---+）と空行を除く
    lines = [l for l in lines if l and not l.startswith("+") and not set(l) <= {"-", " "}]

    pipe_lines = [l for l in lines if "|" in l]
    if pipe_lines:
        rows = [[cell.strip() for cell in l.strip("|").split("|")] for l in pipe_lines]
        header, *data = rows
        return pd.DataFrame(data, columns=header)

    return pd.DataFrame({"value": lines})


def extract_user_names(df: pd.DataFrame, filter_cfg: dict, logger=None,
                       user_column: str = None) -> list:
    """条件（status一致・除外ユーザー）でフィルタし、重複除去・ソート済みの値リストを返す。

    status列が存在しない場合はフィルタをスキップする（汎用CSV対応）。
    user_column を指定すると config の filter.user_column より優先される。
    """
    user_col = user_column or filter_cfg["user_column"]
    status_col = filter_cfg["status_column"]
    status_value = filter_cfg["status_value"]
    exclude_users = filter_cfg.get("exclude_users") or []

    if user_col not in df.columns:
        raise KeyError(
            f"列 '{user_col}' がありません（実際の列: {list(df.columns)}）。"
        )

    if status_col in df.columns:
        df = df[df[status_col] == status_value]
    elif logger:
        logger.warning(
            f"列 '{status_col}' がないため statusフィルタをスキップします。"
        )

    filtered = df[~df[user_col].isin(exclude_users)]
    return sorted(set(filtered[user_col].astype(str)))


def build_in_clause(names: list, include_in_prefix: bool = False) -> str:
    """名前リストを ('a', 'b', ...) 形式のIN句文字列にする。

    値中のシングルクォートはSQL標準の '' にエスケープする。
    include_in_prefix=True で "IN (...)" 形式にする。
    """
    if not names:
        body = "()"
    else:
        escaped = [name.replace("'", "''") for name in names]
        body = "('" + "', '".join(escaped) + "')"
    return f"IN {body}" if include_in_prefix else body


def generate(config: dict, logger, df: pd.DataFrame, user_column: str) -> dict:
    """DataFrameからIN句を生成して txt/csv に書き出す。結果サマリを返す。"""
    output_cfg = config["output"]

    names = extract_user_names(df, config["filter"], logger, user_column)
    in_clause = build_in_clause(names, output_cfg.get("include_in_prefix", False))
    logger.info(f"抽出件数: {len(names)}")

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
