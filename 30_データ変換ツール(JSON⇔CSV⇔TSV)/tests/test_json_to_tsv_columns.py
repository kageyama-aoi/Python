import json
import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import json_to_tsv_columns as m


# ---- extract_paths / split_path ----

def test_extract_paths_dict_and_list():
    data = {"a": {"b": 1}, "c": [10, 20]}
    paths = m.extract_paths(data)
    assert ("a.b", 1) in paths
    assert ("c[0]", 10) in paths
    assert ("c[1]", 20) in paths


def test_split_path():
    assert m.split_path("courses[0].conditions[1].note") == [
        "courses", "[0]", "conditions", "[1]", "note"
    ]


def test_split_path_no_array_index():
    assert m.split_path("meta.input_month") == ["meta", "input_month"]


# ---- build_tsv_with_levels（→ 省略） ----

def test_build_tsv_with_levels_abbreviates_repeated_segments():
    data = {
        "courses": [
            {"conditions": [{"type": "a", "value": 10}, {"type": "b", "value": 20}]},
        ]
    }
    paths = m.extract_paths(data)
    tsv = m.build_tsv_with_levels(paths, leaf_like_keys=["value"])
    lines = tsv.split("\n")
    # Level1行: courses[0] が2回連続するので2つ目は矢印になる
    assert lines[0].split("\t").count("→") >= 1


def test_build_tsv_with_levels_leaf_like_keys_not_abbreviated():
    # 同じキー名(value)が連続しても、leaf_like_keysに含まれていれば矢印にしない
    data = {"a": {"value": 1}, "b": {"value": 2}}
    paths = m.extract_paths(data)
    tsv = m.build_tsv_with_levels(paths, leaf_like_keys=["value"])
    key_row = tsv.split("\n")[-2]  # 値行の1つ手前がキー名行
    assert "→" not in key_row


# ---- load_leaf_like_keys ----

def test_load_leaf_like_keys_returns_config_values(tmp_path, monkeypatch):
    config_path = tmp_path / "leaf_like_keys.json"
    config_path.write_text(json.dumps({"leaf_like_keys": ["foo", "bar"]}), encoding="utf-8")
    monkeypatch.setattr(m, "LEAF_LIKE_KEYS_CONFIG", config_path)
    assert m.load_leaf_like_keys() == ["foo", "bar"]


def test_load_leaf_like_keys_falls_back_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "LEAF_LIKE_KEYS_CONFIG", tmp_path / "does_not_exist.json")
    assert m.load_leaf_like_keys() == m.DEFAULT_LEAF_LIKE_KEYS


def test_load_leaf_like_keys_falls_back_when_invalid_json(tmp_path, monkeypatch):
    config_path = tmp_path / "leaf_like_keys.json"
    config_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(m, "LEAF_LIKE_KEYS_CONFIG", config_path)
    assert m.load_leaf_like_keys() == m.DEFAULT_LEAF_LIKE_KEYS


# ---- find_latest_json ----

def test_find_latest_json_raises_when_empty(tmp_path):
    with pytest.raises(m.JsonToTsvError):
        m.find_latest_json(tmp_path)


def test_find_latest_json_picks_most_recent(tmp_path):
    import time
    old = tmp_path / "old.json"
    old.write_text("{}", encoding="utf-8")
    time.sleep(0.01)
    new = tmp_path / "new.json"
    new.write_text("{}", encoding="utf-8")
    assert m.find_latest_json(tmp_path) == new


# ---- save_with_timestamp ----

def test_save_with_timestamp_creates_file(tmp_path):
    out_path = m.save_with_timestamp("a\tb\n1\t2", output_dir=tmp_path)
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == "a\tb\n1\t2"
    assert out_path.name.startswith("output_")
