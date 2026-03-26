"""
config.py のユニットテスト。
ブラウザ不要・ファイルI/Oのみ。
"""
import textwrap
import pytest
from config import config


# ===========================================================================
# _deep_merge
# ===========================================================================

class Test辞書ディープマージ:
    def test_トップレベルキーがマージされる(self):
        base = {"a": 1, "b": 2}
        update = {"b": 99, "c": 3}
        config._deep_merge(base, update)
        assert base == {"a": 1, "b": 99, "c": 3}

    def test_ネスト辞書は上書きでなくマージされる(self):
        base = {"app": {"email": "old@example.com", "timeout": 30}}
        update = {"app": {"email": "new@example.com"}}
        config._deep_merge(base, update)
        assert base["app"]["email"] == "new@example.com"
        assert base["app"]["timeout"] == 30  # 指定外のキーは残る

    def test_dict以外の値は上書きされる(self):
        base = {"list": [1, 2, 3]}
        update = {"list": [4, 5]}
        config._deep_merge(base, update)
        assert base["list"] == [4, 5]

    def test_baseにないキーが追加される(self):
        base = {"a": 1}
        update = {"b": {"c": 2}}
        config._deep_merge(base, update)
        assert base["b"] == {"c": 2}

    def test_updateが空ならbaseは変化しない(self):
        base = {"a": 1}
        config._deep_merge(base, {})
        assert base == {"a": 1}


# ===========================================================================
# load_config
# ===========================================================================

class Test設定ファイルの読み込み:
    def test_main_yamlのトップレベルキーが読み込まれる(self, project_root):
        config.load_config("config/main.yaml")
        assert "app" in config.CONF
        assert "menus" in config.CONF
        assert "masters" in config.CONF

    def test_tr_optionsがリストとして読み込まれる(self, project_root):
        config.load_config("config/main.yaml")
        tr_options = config.CONF["menus"]["tr_options"]
        assert isinstance(tr_options, list)
        keys = [opt["key"] for opt in tr_options]
        assert "h" in keys
        assert "y" in keys

    def test_modesフォルダのYAMLがメインにマージされる(self, project_root):
        config.load_config("config/main.yaml")
        defaults = config.CONF.get("school_specific_defaults", {})
        assert "h" in defaults
        assert defaults["h"]["Project"] == "SMMs001PH"

    def test_metaにYAMLファイルパスが記録される(self, project_root):
        config.load_config("config/main.yaml")
        meta_files = config.CONF.get("_meta", {}).get("files", {})
        assert "h" in meta_files
        assert "shimamura.yaml" in meta_files["h"]

    def test_存在しない設定ファイルはSystemExitになる(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            config.load_config("nonexistent.yaml")

    def test_リロード時に古いデータが消える(self, project_root):
        config.load_config("config/main.yaml")
        config.CONF["__test_marker__"] = True
        config.load_config("config/main.yaml")
        assert "__test_marker__" not in config.CONF

    def test_environment_optionsがリストで読み込まれる(self, project_root):
        config.load_config("config/main.yaml")
        env_opts = config.CONF["menus"]["environment_options"]
        assert "UAT2" in env_opts

    def test_masters_schools_projectsが読み込まれる(self, project_root):
        config.load_config("config/main.yaml")
        sp = config.CONF["masters"]["schools_projects"]
        assert "shimamura" in sp
        assert "SMMs001PH" in sp["shimamura"]


# ===========================================================================
# _apply_env_overrides
# ===========================================================================

class Test環境変数による上書き:
    def test_CROWDLOG_EMAILでメールアドレスが上書きされる(self, project_root, monkeypatch):
        monkeypatch.setenv("CROWDLOG_EMAIL", "env_user@example.com")
        config.load_config("config/main.yaml")
        assert config.CONF["app"]["login"]["email"] == "env_user@example.com"

    def test_CROWDLOG_PASSWORDでパスワードが上書きされる(self, project_root, monkeypatch):
        monkeypatch.setenv("CROWDLOG_PASSWORD", "secret123")
        config.load_config("config/main.yaml")
        assert config.CONF["app"]["login"]["password"] == "secret123"

    def test_環境変数なしはYAMLの値が使われる(self, project_root, monkeypatch):
        monkeypatch.delenv("CROWDLOG_EMAIL", raising=False)
        monkeypatch.delenv("CROWDLOG_PASSWORD", raising=False)
        # load_dotenv() が .env を再ロードしないようにモック
        monkeypatch.setattr("config.config.load_dotenv", lambda: None)
        config.load_config("config/main.yaml")
        assert config.CONF["app"]["login"]["email"] == "test@example.com"


# ===========================================================================
# _render_templates
# ===========================================================================

class TestTframeテンプレートレンダリング:
    def test_プレースホルダーが値に置換される(self, project_root, tmp_path):
        tf_yaml = textwrap.dedent("""\
            templates:
              tf:
                drive_url: "https://drive.example.com"
                design_doc_folder_path: "/path/to/docs"
                spec_doc_filename: "spec.xlsx"
                comment_template: |
                  URL: {{TF_DRIVE_URL}}
                  Folder: {{TF_DESIGN_DOC_FOLDER_PATH}}
                  File: {{TF_SPEC_DOC_FILENAME}}
        """)
        (tmp_path / "config" / "modes" / "tframe.yaml").write_text(tf_yaml, encoding="utf-8")
        config.load_config("config/main.yaml")

        rendered = config.CONF["templates"]["tf"]["comment_template_rendered"]
        assert "https://drive.example.com" in rendered
        assert "/path/to/docs" in rendered
        assert "spec.xlsx" in rendered
        assert "{{TF_DRIVE_URL}}" not in rendered

    def test_templates設定なしでもエラーにならない(self, project_root):
        config.load_config("config/main.yaml")
        assert "templates" not in config.CONF
