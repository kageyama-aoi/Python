import logging
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.handlers.in_clause_generator import (
    build_in_clause,
    extract_user_names,
    load_table,
)
from src.handlers.input_resolver import resolve_input_csv, resolve_user_column

FILTER_CFG = {
    "user_column": "user_name",
    "status_column": "status",
    "status_value": "Active",
    "exclude_users": ["admin", "user_x"],
}

logger = logging.getLogger("test")


def _sample_df():
    return pd.DataFrame(
        {
            "user_name": ["zeta", "admin", "alpha", "user_x", "beta"],
            "status": ["Active", "Active", "Active", "Active", "Inactive"],
        }
    )


# ---- extract_user_names ----

def test_extract_user_names_filters_and_sorts():
    names = extract_user_names(_sample_df(), FILTER_CFG)
    assert names == ["alpha", "zeta"]


def test_extract_user_names_empty_exclude():
    cfg = {**FILTER_CFG, "exclude_users": None}
    names = extract_user_names(_sample_df(), cfg)
    assert names == ["admin", "alpha", "user_x", "zeta"]


def test_extract_user_names_without_status_column_skips_filter():
    df = pd.DataFrame({"user_name": ["b", "a", "admin"]})
    names = extract_user_names(df, FILTER_CFG, logger)
    assert names == ["a", "b"]  # statusフィルタなし・除外は効く


def test_extract_user_names_deduplicates():
    df = pd.DataFrame({"user_name": ["a", "b", "a", "a"]})
    names = extract_user_names(df, FILTER_CFG, logger)
    assert names == ["a", "b"]


def test_extract_user_names_column_override():
    df = pd.DataFrame({"login_id": ["b", "a"]})
    names = extract_user_names(df, FILTER_CFG, logger, user_column="login_id")
    assert names == ["a", "b"]


def test_extract_user_names_missing_user_column_raises():
    df = pd.DataFrame({"login": ["a"]})
    with pytest.raises(KeyError):
        extract_user_names(df, FILTER_CFG)


# ---- build_in_clause ----

def test_build_in_clause_basic():
    assert build_in_clause(["a", "b"]) == "('a', 'b')"


def test_build_in_clause_escapes_single_quote():
    assert build_in_clause(["o'brien"]) == "('o''brien')"


def test_build_in_clause_empty():
    assert build_in_clause([]) == "()"


def test_build_in_clause_with_in_prefix():
    assert build_in_clause(["a"], include_in_prefix=True) == "IN ('a')"


# ---- load_table ----

def test_load_table_csv(tmp_path):
    p = tmp_path / "users.csv"
    p.write_text("user_name,status\na,Active\n", encoding="utf-8")
    df = load_table(str(p))
    assert list(df.columns) == ["user_name", "status"]
    assert len(df) == 1


def test_load_table_pipe_text(tmp_path):
    p = tmp_path / "result.txt"
    p.write_text(
        "+-----------+--------+\n"
        "| user_name | status |\n"
        "+-----------+--------+\n"
        "| a         | Active |\n"
        "| b         | Active |\n"
        "+-----------+--------+\n",
        encoding="utf-8",
    )
    df = load_table(str(p))
    assert list(df.columns) == ["user_name", "status"]
    assert list(df["user_name"]) == ["a", "b"]


def test_load_table_plain_list(tmp_path):
    p = tmp_path / "list.txt"
    p.write_text("b\n\na\n", encoding="utf-8")
    df = load_table(str(p))
    assert list(df.columns) == ["value"]
    assert list(df["value"]) == ["b", "a"]


# ---- resolve_input_csv ----

def test_resolve_input_csv_from_argv(tmp_path):
    csv = tmp_path / "users.csv"
    csv.write_text("user_name,status\n", encoding="utf-8")
    path = resolve_input_csv(["main.py", str(csv)], {}, logger)
    assert path == str(csv)


def test_resolve_input_csv_argv_not_found():
    with pytest.raises(FileNotFoundError):
        resolve_input_csv(["main.py", "no_such_file.csv"], {}, logger)


# ---- resolve_user_column ----

def test_resolve_user_column_from_argv():
    col = resolve_user_column(["main.py", "f.csv", "login_id"],
                              ["login_id", "status"], FILTER_CFG, logger)
    assert col == "login_id"


def test_resolve_user_column_argv_not_found():
    with pytest.raises(KeyError):
        resolve_user_column(["main.py", "f.csv", "nope"],
                            ["login_id"], FILTER_CFG, logger)


def test_resolve_user_column_from_config():
    col = resolve_user_column(["main.py", "f.csv"],
                              ["user_name", "status"], FILTER_CFG, logger)
    assert col == "user_name"


def test_resolve_user_column_single_column_auto():
    col = resolve_user_column(["main.py", "f.csv"],
                              ["only_col"], FILTER_CFG, logger)
    assert col == "only_col"
