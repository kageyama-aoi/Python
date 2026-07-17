"""名前付きプリセット（お気に入り設定）の読み書き。

presets.json は config/ に置く。実案件の名前が入り得るため gitignore 対象
（形式は config/presets.example.json を参照）。tkinter 非依存のロジック層。
"""
import json
from pathlib import Path
from typing import Optional

from run import SplitOptions

BASE_DIR = Path(__file__).parent.parent
PRESETS_PATH = BASE_DIR / "config" / "presets.json"


def load_presets(path: Optional[Path] = None) -> dict[str, dict]:
    """presets.json を読み込む。ファイルがなければ空の dict を返す。"""
    path = Path(path) if path is not None else PRESETS_PATH
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not all(isinstance(v, dict) for v in data.values()):
        raise ValueError(f"プリセットファイルの形式が不正です（{{\"名前\": {{設定}}}} 形式）: {path}")
    return data


def save_presets(presets: dict[str, dict], path: Optional[Path] = None) -> None:
    path = Path(path) if path is not None else PRESETS_PATH
    path.write_text(
        json.dumps(presets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def get_preset_options(name: str, path: Optional[Path] = None) -> SplitOptions:
    """プリセット名から SplitOptions を組み立てる。未登録なら KeyError。"""
    presets = load_presets(path)
    if name not in presets:
        available = "、".join(presets) if presets else "（登録なし）"
        raise KeyError(f"プリセット '{name}' が見つかりません。登録済み: {available}")
    preset = presets[name]
    return SplitOptions(
        rows_per_file=preset["rows_per_file"],
        encoding=preset["encoding"],
        has_header=preset.get("has_header", True),
        delimiter=preset.get("delimiter") or None,
    )
