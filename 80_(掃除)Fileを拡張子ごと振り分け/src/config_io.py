"""config.ini の読み書き。

[Settings]        TargetDirectory / LogDirectoryName
[ExtensionGroups] グループ名 = カンマ区切り拡張子
[Exclude]         filenames / extensions

GUI の設定エディタからも編集できるよう、拡張子グループは
「グループ名 -> 拡張子リスト」（編集向き）と
「拡張子 -> グループ名」（振り分け時の逆引き）の両方を保持する。
"""
from __future__ import annotations

import configparser
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.ini"


def _split_csv(value: str) -> list[str]:
    """カンマ区切り文字列を、空要素を除いたリストにする。"""
    return [item for item in value.replace(" ", "").split(",") if item]


@dataclass
class OrganizeConfig:
    """振り分け設定一式。"""

    target_dir: Path
    log_dir_name: str = "logs"
    # 編集向きの表現（グループ名 -> 拡張子リスト、拡張子は小文字・ドットなし）
    extension_groups: dict[str, list[str]] = field(default_factory=dict)
    exclude_filenames: set[str] = field(default_factory=set)
    exclude_extensions: set[str] = field(default_factory=set)

    @property
    def extension_to_folder(self) -> dict[str, str]:
        """振り分け時の逆引き（拡張子 -> 移動先フォルダ名）。"""
        mapping: dict[str, str] = {}
        for folder_name, extensions in self.extension_groups.items():
            for ext in extensions:
                mapping[ext.lower()] = folder_name
        return mapping


def load_config(path: Path | None = None) -> OrganizeConfig:
    """config.ini を読み込んで OrganizeConfig を返す。"""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")

    if not parser.has_option("Settings", "TargetDirectory"):
        raise configparser.NoOptionError("TargetDirectory", "Settings")
    target_dir = Path(parser.get("Settings", "TargetDirectory").strip())
    log_dir_name = parser.get("Settings", "LogDirectoryName", fallback="logs").strip() or "logs"

    extension_groups: dict[str, list[str]] = {}
    if parser.has_section("ExtensionGroups"):
        for folder_name, extensions_str in parser.items("ExtensionGroups"):
            exts = [ext.lower() for ext in _split_csv(extensions_str)]
            if exts:
                extension_groups[folder_name] = exts

    exclude_filenames: set[str] = set()
    exclude_extensions: set[str] = set()
    if parser.has_section("Exclude"):
        exclude_filenames = set(_split_csv(parser.get("Exclude", "filenames", fallback="")))
        exclude_extensions = {
            ext.lower() for ext in _split_csv(parser.get("Exclude", "extensions", fallback=""))
        }

    return OrganizeConfig(
        target_dir=target_dir,
        log_dir_name=log_dir_name,
        extension_groups=extension_groups,
        exclude_filenames=exclude_filenames,
        exclude_extensions=exclude_extensions,
    )


def save_config(path: Path, cfg: OrganizeConfig) -> None:
    """OrganizeConfig を config.ini に書き戻す。

    注意: configparser はコメント行（';' 始まり）を保持しないため、
    保存すると既存のコメントは失われる。呼び出し側で確認を取ること。
    """
    parser = configparser.ConfigParser()
    parser["Settings"] = {
        "TargetDirectory": str(cfg.target_dir),
        "LogDirectoryName": cfg.log_dir_name,
    }
    parser["ExtensionGroups"] = {
        folder_name: ", ".join(exts) for folder_name, exts in cfg.extension_groups.items()
    }
    parser["Exclude"] = {
        "filenames": ", ".join(sorted(cfg.exclude_filenames)),
        "extensions": ", ".join(sorted(cfg.exclude_extensions)),
    }

    with open(path, "w", encoding="utf-8", newline="") as fp:
        parser.write(fp)
