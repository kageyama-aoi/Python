"""主要ルートのスモークテスト（Issue #11）。

起動と主要動線（/, /kb/, /import）が 200 を返すことだけを確認する。
機能の細部はテストしない。
"""
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Markdown メタ編集" in res.get_data(as_text=True)


@pytest.mark.skipif(
    not (PROJECT_ROOT / "html" / "index.html").exists(),
    reason="html/index.html 未生成（python build.py 実行前）",
)
def test_kb_returns_200(client):
    res = client.get("/kb/")
    assert res.status_code == 200


def test_import_returns_200(client):
    res = client.get("/import")
    assert res.status_code == 200
    assert "プレーンテキスト取込" in res.get_data(as_text=True)


def test_api_items_returns_200(client):
    res = client.get("/api/items")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
