"""
config_manager.py のユニットテスト。
ブラウザ不要・ファイルI/Oのみ。
add_pattern() を中心にテスト（機能①: GUIからTRパターン追加）。
"""
import os
import pytest
import yaml

from config import config
from config.config_manager import ConfigManager


def _load_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ===========================================================================
# add_pattern
# ===========================================================================

class Testパターン新規追加:

    def test_パターンYAMLファイルが作成される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH", "Title": "TEST", "Comments": ""},
        )
        assert (project_root / "config" / "modes" / "task_report" / "abc.yaml").exists()

    def test_作成YAMLがschool_specific_defaults形式になっている(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        data = _load_yaml(project_root / "config" / "modes" / "task_report" / "abc.yaml")
        assert "school_specific_defaults" in data
        assert "abc" in data["school_specific_defaults"]
        assert data["school_specific_defaults"]["abc"]["Project"] == "SMMs001PH"

    def test_空フィールドはYAMLに書き込まれない(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH", "Title": "", "Comments": ""},
        )
        data = _load_yaml(project_root / "config" / "modes" / "task_report" / "abc.yaml")
        fields = data["school_specific_defaults"]["abc"]
        assert "Title" not in fields
        assert "Comments" not in fields

    def test_main_yamlのtr_optionsに新エントリが追記される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        main_data = _load_yaml(project_root / "config" / "main.yaml")
        keys = [opt["key"] for opt in main_data["menus"]["tr_options"]]
        assert "abc" in keys

    def test_labelがmain_yamlに正しく保存される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件テスト", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        main_data = _load_yaml(project_root / "config" / "main.yaml")
        entry = next(opt for opt in main_data["menus"]["tr_options"] if opt["key"] == "abc")
        assert entry["label"] == "ABC案件テスト"

    def test_requires_environment_trueがmain_yamlに保存される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=True,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        main_data = _load_yaml(project_root / "config" / "main.yaml")
        entry = next(opt for opt in main_data["menus"]["tr_options"] if opt["key"] == "abc")
        assert entry.get("requires_environment") is True

    def test_requires_environment_falseはmain_yamlに書き込まれない(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        main_data = _load_yaml(project_root / "config" / "main.yaml")
        entry = next(opt for opt in main_data["menus"]["tr_options"] if opt["key"] == "abc")
        assert "requires_environment" not in entry

    def test_既存キーの重複追加はValueErrorになる(self, project_root):
        config.load_config("config/main.yaml")
        with pytest.raises(ValueError, match="既に存在"):
            ConfigManager().add_pattern(
                key="h",  # main.yaml に既存のキー
                label="重複テスト", requires_environment=False,
                fields={"Schools": "shimamura", "Project": "SMMs001PH"},
            )

    def test_追加後にconfig_CONFが最新化される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        keys = [opt["key"] for opt in config.CONF.get("menus", {}).get("tr_options", [])]
        assert "abc" in keys

    def test_追加後も既存のtr_optionsが消えない(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().add_pattern(
            key="abc", label="ABC案件", requires_environment=False,
            fields={"Schools": "shimamura", "Project": "SMMs001PH"},
        )
        main_data = _load_yaml(project_root / "config" / "main.yaml")
        keys = [opt["key"] for opt in main_data["menus"]["tr_options"]]
        assert "h" in keys, "既存の 'h' エントリが消えている"
        assert "y" in keys, "既存の 'y' エントリが消えている"


# ===========================================================================
# save_setting
# ===========================================================================

class Test設定値の保存:

    def test_指定フィールドの値がYAMLファイルに書き込まれる(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().save_setting("h", {"Title": "新しいタイトル"})
        data = _load_yaml(project_root / "config" / "modes" / "task_report" / "shimamura.yaml")
        assert data["school_specific_defaults"]["h"]["Title"] == "新しいタイトル"

    def test_指定外のキーは上書きされない(self, project_root):
        config.load_config("config/main.yaml")
        original_project = config.CONF["school_specific_defaults"]["h"]["Project"]
        ConfigManager().save_setting("h", {"Title": "新しいタイトル"})
        data = _load_yaml(project_root / "config" / "modes" / "task_report" / "shimamura.yaml")
        assert data["school_specific_defaults"]["h"]["Project"] == original_project

    def test_保存後にconfig_CONFが更新される(self, project_root):
        config.load_config("config/main.yaml")
        ConfigManager().save_setting("h", {"Title": "リロードテスト"})
        assert config.CONF["school_specific_defaults"]["h"]["Title"] == "リロードテスト"

    def test_存在しないモードキーはエラーになる(self, project_root):
        config.load_config("config/main.yaml")
        with pytest.raises((FileNotFoundError, KeyError)):
            ConfigManager().save_setting("zzz_nonexistent", {"Title": "fail"})


# ===========================================================================
# load_for_edit
# ===========================================================================

class Test編集用設定読み込み:

    def test_有効なキーで辞書が返る(self, project_root):
        config.load_config("config/main.yaml")
        data, _ = ConfigManager().load_for_edit("h")
        assert data is not None
        assert isinstance(data, dict)

    def test_ファイルパスも合わせて返される(self, project_root):
        config.load_config("config/main.yaml")
        _, file_path = ConfigManager().load_for_edit("h")
        assert file_path is not None
        assert os.path.exists(file_path)

    def test_存在しないキーはNoneが返る(self, project_root):
        config.load_config("config/main.yaml")
        data, _ = ConfigManager().load_for_edit("zzz_unknown")
        assert data is None

    def test_返された辞書に正しいフィールドが含まれる(self, project_root):
        config.load_config("config/main.yaml")
        data, _ = ConfigManager().load_for_edit("h")
        assert "Project" in data
        assert data["Project"] == "SMMs001PH"
