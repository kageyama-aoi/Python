import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import json_to_tsv_rows as m


def test_flatten_with_levels_nested_dict():
    data = {"a": {"b": 1}, "c": 2}
    rows = m.flatten_with_levels(data)
    assert ["L0", "a", ""] in rows
    assert ["L1", "b", 1] in rows
    assert ["L0", "c", 2] in rows


def test_flatten_with_levels_none_becomes_empty_string():
    rows = m.flatten_with_levels({"a": None})
    assert rows == [["L0", "a", ""]]


def test_flatten_with_levels_top_level_list_is_comma_joined():
    # flatten_with_levels自身に「リスト」を渡した場合（トップレベルがリスト、または
    # 再帰呼び出しでリストが渡された場合）はカンマ区切り文字列になる。
    rows = m.flatten_with_levels(["x", "y", "z"], parent_key="tags")
    assert rows == [["L0", "tags", "x,y,z"]]


def test_flatten_with_levels_dict_value_that_is_a_list_is_kept_as_is():
    # 辞書の値がリストの場合はisinstance(v, dict)がFalseになりelse節に落ちるため、
    # カンマ結合されずリストオブジェクトのまま格納される（既存仕様。ここでは
    # 30番の刷新時に挙動を変えていないことを回帰確認する）。
    rows = m.flatten_with_levels({"tags": ["x", "y", "z"]})
    assert rows == [["L0", "tags", ["x", "y", "z"]]]


def test_find_latest_json_raises_when_empty(tmp_path):
    with pytest.raises(m.JsonToTsvError):
        m.find_latest_json(tmp_path)
