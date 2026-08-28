"""振り分けのコアロジック。

「計画（build_plan）」と「実行（execute_plan）」を分離している。
build_plan はファイルシステムを一切変更しない純粋関数で、GUI のドライラン
プレビューと実行の両方がこの計画を使う。
"""
from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config_io import OrganizeConfig

NO_EXTENSION_FOLDER = "no_extension"

# action の種類
ACTION_MOVE = "move"      # そのままの名前で移動
ACTION_RENAME = "rename"  # 同名衝突のため連番を付けて移動
ACTION_SKIP = "skip"      # 移動しない（除外・ログフォルダ・サブフォルダ等）

LogFn = Callable[[str, str], None]  # (message, level) -> None


@dataclass
class PlannedMove:
    """1 アイテムに対する処理計画。"""

    source: Path
    action: str
    dest_dir: Path | None = None
    dest_name: str | None = None
    reason: str = ""
    creates_dir: bool = False

    @property
    def dest_path(self) -> Path | None:
        if self.dest_dir is None or self.dest_name is None:
            return None
        return self.dest_dir / self.dest_name


@dataclass
class ExecuteResult:
    """実行結果の集計。"""

    moved: int = 0
    renamed: int = 0
    skipped: int = 0
    failed: int = 0
    created_dirs: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.moved + self.renamed


def _extension_of(path: Path) -> str:
    """先頭ドットを除いた小文字の拡張子（無ければ空文字）。"""
    return path.suffix[1:].lower()


def _destination_folder_name(extension: str, extension_to_folder: dict[str, str]) -> str:
    if extension in extension_to_folder:
        return extension_to_folder[extension]
    return extension if extension else NO_EXTENSION_FOLDER


def _resolve_name(
    stem: str,
    suffix: str,
    dest_dir: Path,
    claimed: set[str],
) -> tuple[str, bool]:
    """移動先での最終ファイル名を決める。

    dest_dir に既に存在する名前と、同じ計画内で先に割り当てた名前（claimed）の
    両方と衝突しないよう連番を付ける。戻り値は (name, renamed?)。
    """
    candidate = f"{stem}{suffix}"
    if candidate.lower() not in claimed and not (dest_dir / candidate).exists():
        return candidate, False

    counter = 1
    while True:
        counter += 1
        candidate = f"{stem}_{counter}{suffix}"
        if candidate.lower() not in claimed and not (dest_dir / candidate).exists():
            return candidate, True


def build_plan(target_dir: Path, cfg: OrganizeConfig) -> list[PlannedMove]:
    """target_dir 直下の各アイテムに対する処理計画を作る（副作用なし）。"""
    target_dir = Path(target_dir)
    log_dir = target_dir / cfg.log_dir_name
    extension_to_folder = cfg.extension_to_folder

    plan: list[PlannedMove] = []
    # 移動先フォルダごとに「割り当て済みファイル名（小文字）」を追跡する
    claimed_names: dict[Path, set[str]] = {}
    # この計画で新規作成されるフォルダ
    dirs_to_create: set[Path] = set()

    for source_path in sorted(target_dir.iterdir()):
        if source_path == log_dir:
            plan.append(PlannedMove(source_path, ACTION_SKIP, reason="ログフォルダ"))
            continue
        if not source_path.is_file():
            plan.append(PlannedMove(source_path, ACTION_SKIP, reason="フォルダ"))
            continue
        if source_path.name in cfg.exclude_filenames:
            plan.append(PlannedMove(source_path, ACTION_SKIP, reason="除外ファイル名"))
            continue

        extension = _extension_of(source_path)
        if extension in cfg.exclude_extensions:
            plan.append(
                PlannedMove(source_path, ACTION_SKIP, reason=f"除外拡張子 (.{extension})")
            )
            continue

        folder_name = _destination_folder_name(extension, extension_to_folder)
        dest_dir = target_dir / folder_name
        claimed = claimed_names.setdefault(dest_dir, set())

        dest_name, renamed = _resolve_name(
            source_path.stem, source_path.suffix, dest_dir, claimed
        )
        claimed.add(dest_name.lower())

        creates_dir = not dest_dir.exists() and dest_dir not in dirs_to_create
        if creates_dir:
            dirs_to_create.add(dest_dir)

        plan.append(
            PlannedMove(
                source=source_path,
                action=ACTION_RENAME if renamed else ACTION_MOVE,
                dest_dir=dest_dir,
                dest_name=dest_name,
                reason="",
                creates_dir=creates_dir,
            )
        )

    return plan


def _noop_log(message: str, level: str) -> None:  # pragma: no cover - default
    pass


def execute_plan(plan: list[PlannedMove], on_log: LogFn | None = None) -> ExecuteResult:
    """build_plan の結果を実際に適用する。"""
    log = on_log or _noop_log
    result = ExecuteResult()

    for item in plan:
        if item.action == ACTION_SKIP:
            result.skipped += 1
            log(f"スキップ: {item.source.name} ({item.reason})", "info")
            continue

        dest_dir = item.dest_dir
        dest_path = item.dest_path
        assert dest_dir is not None and dest_path is not None  # SKIP 以外は必ずある

        if not dest_dir.exists():
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                result.created_dirs.append(dest_dir.name)
                log(f"フォルダ作成: {dest_dir.name}", "info")
            except OSError as e:
                result.failed += 1
                log(f"フォルダ作成失敗: {dest_dir.name} - {e}", "error")
                continue

        try:
            shutil.move(str(item.source), str(dest_path))
        except (OSError, shutil.Error) as e:
            result.failed += 1
            log(f"移動失敗: {item.source.name} - {e}", "error")
            continue

        if item.action == ACTION_RENAME:
            result.renamed += 1
            log(f"移動(改名): {item.source.name} -> {dest_path.name} ({dest_dir.name})", "info")
        else:
            result.moved += 1
            log(f"移動: {item.source.name} -> ({dest_dir.name})", "info")

    return result


def setup_file_logging(log_dir: Path) -> Path:
    """CLI 用: log_dir に sort_log_*.txt を作り、logging を設定する。"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / f"sort_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_file_path
