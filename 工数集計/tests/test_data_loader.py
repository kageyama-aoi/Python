import pytest
import json
from unittest.mock import patch
from src import data_loader
from src import config as cfg


class TestLoadConfig:

    def test_load_config_returns_dict(self, sample_config_json):
        """config.jsonを辞書として読み込む"""
        with patch.object(cfg, 'CONFIG_FILE', sample_config_json):
            result = data_loader.load_config()
        assert isinstance(result, dict)
        assert result["target_project"] == "顧客A"
        assert result["target_employee"] == "山田太郎"

    def test_load_config_empty_values(self, tmp_path):
        """空の設定ファイルを読み込む"""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({}), encoding='utf-8')
        with patch.object(cfg, 'CONFIG_FILE', config_path):
            result = data_loader.load_config()
        assert result == {}


class TestLoadConfigErrors:

    def test_missing_config_exits_with_message(self, tmp_path, capsys):
        """config.json が存在しない場合に SystemExit とメッセージが出る（RF-16）"""
        missing = tmp_path / "no_config.json"
        with patch.object(cfg, 'CONFIG_FILE', missing):
            with pytest.raises(SystemExit):
                data_loader.load_config()
        captured = capsys.readouterr()
        assert "config.json" in captured.out


class TestLoadBugsCsv:

    def test_load_bugs_csv(self, sample_bugs_csv):
        """バグCSVを読み込む"""
        result = data_loader.load_bugs_csv(sample_bugs_csv)
        assert len(result) == 2
        assert "ID" in result.columns
        assert result.iloc[0]["ID"] == "BUG-001"
