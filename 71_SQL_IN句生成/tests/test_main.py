import logging
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.handlers.in_clause_generator import build_in_clause, extract_user_names
from src.handlers.input_resolver import resolve_input_csv

FILTER_CFG = {
    "user_column": "user_name",
    "status_column": "status",
    "status_value": "Active",
    "exclude_users": ["admin", "shima00485"],
}

logger = logging.getLogger("test")


def _sample_df():
    return pd.DataFrame(
        {
            "user_name": ["zeta", "admin", "alpha", "shima00485", "beta"],
            "status": ["Active", "Active", "Active", "Active", "Inactive"],
        }
    )


def test_extract_user_names_filters_and_sorts():
    names = extract_user_names(_sample_df(), FILTER_CFG)
    assert names == ["alpha", "zeta"]


def test_extract_user_names_empty_exclude():
    cfg = {**FILTER_CFG, "exclude_users": None}
    names = extract_user_names(_sample_df(), cfg)
    assert names == ["admin", "alpha", "shima00485", "zeta"]


def test_extract_user_names_without_status_column_skips_filter():
    df = pd.DataFrame({"user_name": ["b", "a", "admin"]})
    names = extract_user_names(df, FILTER_CFG, logger)
    assert names == ["a", "b"]  # statusフィルタなし・除外は効く


def test_extract_user_names_missing_user_column_raises():
    df = pd.DataFrame({"login": ["a"]})
    with pytest.raises(KeyError):
        extract_user_names(df, FILTER_CFG)


def test_build_in_clause_basic():
    assert build_in_clause(["a", "b"]) == "('a', 'b')"


def test_build_in_clause_escapes_single_quote():
    assert build_in_clause(["o'brien"]) == "('o''brien')"


def test_build_in_clause_empty():
    assert build_in_clause([]) == "()"


def test_resolve_input_csv_from_argv(tmp_path):
    csv = tmp_path / "users.csv"
    csv.write_text("user_name,status\n", encoding="utf-8")
    path = resolve_input_csv(["main.py", str(csv)], {}, logger)
    assert path == str(csv)


def test_resolve_input_csv_argv_not_found():
    with pytest.raises(FileNotFoundError):
        resolve_input_csv(["main.py", "no_such_file.csv"], {}, logger)
