"""pytest 共通設定。

app.py / md_store.py は「カレント＝プロジェクト直下」を前提に相対パス
（md/, html/）を使うため、import パス追加とカレント移動をここで行う。
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client
