#!/usr/bin/env python3
"""ドキュメント/スキルが名指しするファイルパス・識別子が実ソースに存在するか検査する。

ドリフト（コードを整理したのに、それを説明する README/ガイド/スキルが古い参照を
抱えたまま残る）を commit 時に気付ける状態にするための警告ツール。

使い方:
    python scripts/check_doc_refs.py            # 警告のみ表示（exit 0）
    python scripts/check_doc_refs.py --check    # 検出があれば exit 1（CI/フック昇格用）
    python scripts/check_doc_refs.py --docs     # **/docs/** も対象に含める（広めの掃除用）
    python scripts/check_doc_refs.py --skills   # ~/.claude/skills/ も追加検査（手動専用）
    python scripts/check_doc_refs.py --symbols  # 識別子参照(②)も検査する
    python scripts/check_doc_refs.py --quiet    # 検出0件のとき無出力

検査対象:
    既定 = 「いま何がどうなっているか」を説明する doc:
        - リポジトリ直下と各ツール直下の README.md / readme.md
        - すべての AGENTS.md / CLAUDE.md
        - 90_ひな形/ 配下の *.md（構成の正）
    --docs を付けると **/docs/** も対象（ただし状態行が「完了」「廃止」の
    plan/履歴 doc は凍結された記録なので自動でスキップ）。

検査内容:
    ① パス参照   バッククォート内 / Markdownリンク先の `src/...` `NN_フォルダ/...`
                 `*.py` 等が、doc のツールフォルダ基準 → リポジトリルート基準の
                 どちらでも解決できないものを報告。末尾 `:123` の行番号は無視。
    ② 識別子参照 (--symbols 時) `name(` `Class.method(` `def name` `class Name` が
                 リポジトリ内のいずれかの .py に定義されているか。警告は弱め。

除外:
    - フェンス済みコードブロック（``` ```）は走査しない（説明用途が多く誤検知源）。
    - 空白を含むトークン（コマンド行）、プレースホルダー記号（{x} <x> 〇〇 NN_ ...）。
    - scripts/check_doc_refs.ignore に1行1件で書いた参照（# 以降はコメント、glob可）。

標準ライブラリのみ。Python 3.10+。
"""
from __future__ import annotations

import argparse
import ast
import builtins
import fnmatch
import os
import re
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IGNORE_FILE = REPO_ROOT / "scripts" / "check_doc_refs.ignore"

# --- 走査から外すディレクトリ ------------------------------------------------

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules",
}
# 実データ・生成物が入るサブフォルダ（どのツール配下でも中身を見ない）
EXCLUDE_DIR_NAMES = {"input", "output", "temp", "logs", "downloads"}

# --- 参照とみなす拡張子・トップディレクトリ --------------------------------

REF_EXT = (
    ".py", ".md", ".json", ".bat", ".ps1", ".sh", ".yaml", ".yml",
    ".txt", ".ini", ".cfg", ".toml", ".html", ".css", ".js", ".mmd", ".csv",
)
KNOWN_TOP_SEGMENTS = {
    "src", "tests", "test", "config", "handlers", "utils", "docs", "scripts",
    "templates", "references", "fixtures", "evals",
}
NUMBERED_DIR_RE = re.compile(r"^\d{2}_")
STATUS_FROZEN_RE = re.compile(r"状態[:：].*(完了|廃止|アーカイブ|クローズ)")
# 「標準・規約そのもの」を説明する doc。汎用的な構成パスを大量に含み、
# 具体ツリーへの主張ではないので ① の実在検査から外す（人が正として保守する）。
CONVENTION_DOCS = {"00_project_standard.md", "DOC_SYNC.md"}

# --- プレースホルダー判定 --------------------------------------------------

PLACEHOLDER_SUBSTR = (
    "{", "}", "<", ">", "$", "%", "...", "〇", "○", "△", "□", "×", "＊",
    "path/to", "path\\to", "example.com", "your-", "yourname",
    "foo", "bar", "baz", "hoge", "fuga", "piyo", "xxx", "aaa",
    "nn_", "yyyy", "mmdd", "hhmm", "dummy_", "new_handler", "new.yaml",
    "newmode", "new_system", "new_mode",
    "example.", "/example", "ファイル名", "サンプル", "①", "②", "③", "⇒",
)

PY_BUILTINS = set(dir(builtins)) | {"self", "cls", "super"}
COMMON_WORDS = {
    "def", "class", "if", "for", "while", "return", "import", "from", "with",
    "try", "except", "finally", "lambda", "yield", "async", "await", "pass",
    "true", "false", "none", "null", "todo", "fixme", "note", "warning",
    "func", "function", "method", "value", "name", "data", "text", "path",
    "args", "kwargs", "params", "config", "result", "item", "key", "obj",
    "self", "this", "test", "main", "type", "list", "dict",
}

# --- ignore ファイル ------------------------------------------------------


def load_ignore_patterns() -> list[str]:
    if not IGNORE_FILE.exists():
        return []
    out: list[str] = []
    for raw in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line.replace("\\", "/"))
    return out


def is_ignored(token: str, patterns: list[str]) -> bool:
    norm = token.replace("\\", "/")
    for p in patterns:
        if norm == p or fnmatch.fnmatch(norm, p) or norm.endswith("/" + p):
            return True
    return False


# --- Markdown パース -----------------------------------------------------

FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
LINE_NO_SUFFIX_RE = re.compile(r":L?\d+(-L?\d+)?$")
TRAIL_PUNCT = "　、。，．・）)｣」』】>。,.:;”\"'`"
LEAD_REL_RE = re.compile(r"^\.[\\/]+")
MD_LINK_RE = re.compile(r"\]\(<?([^)>\s]+(?:\([^)]*\)[^)>\s]*)*)>?\)")
# 実体がユーザー環境で作られる／リポジトリ外を指すのが正しいプレフィックス
OUT_OF_REPO_PREFIXES = (".venv/", "venv/", "node_modules/", ".git/", "~/")
# 「ディレクトリの形」を示すだけで、ファイルの実在を主張しないトークン
STRUCTURAL_SEGMENTS = {
    "handlers", "utils", "src", "tests", "test", "config", "docs", "modes",
    "scripts", "data", "logs", "input", "output", "temp",
}


def default_doc_files(root: Path, include_docs: bool) -> list[Path]:
    docs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and d not in EXCLUDE_DIR_NAMES
        ]
        cur = Path(dirpath)
        rel_parts = cur.relative_to(root).parts
        depth = len(rel_parts)
        in_template_dir = bool(rel_parts) and rel_parts[0] == "90_ひな形"
        in_docs_dir = "docs" in rel_parts
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            low = fn.lower()
            keep = False
            if low in ("readme.md",) and depth <= 1:
                keep = True
            elif fn in ("AGENTS.md", "CLAUDE.md"):
                keep = True
            elif in_template_dir:
                keep = True
            elif include_docs and in_docs_dir:
                keep = True
            if keep:
                docs.append(cur / fn)
    return sorted(docs)


def is_frozen_plan(text: str) -> bool:
    head = "\n".join(text.splitlines()[:12])
    return bool(STATUS_FROZEN_RE.search(head))


def tool_root_for(doc: Path, root: Path) -> Path:
    try:
        parts = doc.relative_to(root).parts
    except ValueError:
        return root
    if parts and NUMBERED_DIR_RE.match(parts[0]):
        return root / parts[0]
    return root


def extract_candidates(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in INLINE_CODE_RE.finditer(line):
            out.append((i, m.group(1).strip()))
        for m in MD_LINK_RE.finditer(line):
            out.append((i, m.group(1).strip()))
    return out


# --- ソースの識別子インデックス ----------------------------------------


def build_symbol_index(root: Path) -> set[str]:
    names: set[str] = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                p = Path(dirpath) / fn
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8"),
                                     filename=str(p))
                except (SyntaxError, ValueError, UnicodeDecodeError, OSError):
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.ClassDef)):
                        names.add(node.name)
                    elif isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                names.add(t.id)
    return names


# --- パス判定 ---------------------------------------------------------


def clean_token(tok: str) -> str:
    tok = tok.strip().strip("`").strip().lstrip("!")
    tok = LINE_NO_SUFFIX_RE.sub("", tok)
    tok = tok.rstrip(TRAIL_PUNCT).strip().rstrip("/\\")
    return tok


def looks_like_path(tok: str) -> bool:
    if not tok or " " in tok or "\t" in tok:
        return False
    if "/" not in tok and "\\" not in tok:
        return False
    norm = LEAD_REL_RE.sub("", tok.replace("\\", "/"))
    low = norm.lower()
    if low.startswith(OUT_OF_REPO_PREFIXES):
        return False
    segs = [s for s in norm.split("/") if s]
    if len(segs) < 2:
        return False
    has_ext = low.endswith(REF_EXT)
    # 拡張子なしで末尾がディレクトリ名 → 「構成の形」の説明。実在検査しない
    if not has_ext and segs[-1].lower() in STRUCTURAL_SEGMENTS:
        return False
    if has_ext:
        return True
    if segs[0] in KNOWN_TOP_SEGMENTS:
        return True
    if any(NUMBERED_DIR_RE.match(s) for s in segs):
        return True
    return False


def is_placeholder(tok: str) -> bool:
    low = tok.lower()
    return any(s in low for s in PLACEHOLDER_SUBSTR)


def resolve_path(tok: str, doc: Path, root: Path) -> bool:
    rel = LEAD_REL_RE.sub("", tok.replace("\\", "/"))
    if not rel:
        return True
    troot = tool_root_for(doc, root)
    candidates = [root / rel, troot / rel, doc.parent / rel]
    has_glob = any(c in rel for c in "*?[")
    for base in candidates:
        try:
            if has_glob:
                if base.parent.exists() and any(base.parent.glob(base.name)):
                    return True
            elif base.exists():
                return True
        except OSError:
            continue
    # サブツールを束ねるフォルダ（33_/60_ 等）はツール直下1階層も見る
    if not has_glob and troot != root:
        try:
            if any((sub / rel).exists()
                   for sub in troot.iterdir() if sub.is_dir()):
                return True
        except OSError:
            pass
    return False


# --- 識別子判定 ------------------------------------------------------

CALL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\($")
ATTR_CALL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.([A-Za-z_][A-Za-z0-9_]*)\s*\($")
DEF_RE = re.compile(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


def symbol_name(tok: str) -> str | None:
    tok = tok.strip().rstrip(TRAIL_PUNCT)
    for rx in (CALL_RE, ATTR_CALL_RE, DEF_RE):
        m = rx.match(tok)
        if m:
            return m.group(1)
    return None


def is_meaningful_symbol(name: str) -> bool:
    if len(name) < 4 or name.startswith("_"):
        return False
    low = name.lower()
    if low in COMMON_WORDS or name in PY_BUILTINS or low in PY_BUILTINS:
        return False
    return bool(re.search(r"[a-z]", name)) or "_" in name


# --- スキャン --------------------------------------------------------


def scan_repo_docs(root: Path, ignore: list[str], symbols: set[str] | None,
                   include_docs: bool):
    path_hits: list[tuple[Path, int, str]] = []
    sym_hits: list[tuple[Path, int, str]] = []
    for doc in default_doc_files(root, include_docs):
        text = doc.read_text(encoding="utf-8", errors="replace")
        if is_frozen_plan(text):
            continue
        skip_paths = doc.name in CONVENTION_DOCS
        for lineno, raw in extract_candidates(text):
            tok = clean_token(raw)
            if not tok or is_ignored(tok, ignore) or is_placeholder(tok):
                continue
            if looks_like_path(tok):
                if not skip_paths and not resolve_path(tok, doc, root):
                    path_hits.append((doc, lineno, tok))
                continue
            if symbols is not None:
                name = symbol_name(raw.strip())
                if name and is_meaningful_symbol(name) and name not in symbols:
                    sym_hits.append((doc, lineno, raw.strip()))
    return path_hits, sym_hits


SKILLS_LINE_RE = re.compile(r"Tools[\\/]Python[\\/]([^\s`'\"）、。]+)")
SKILL_SKIP_DIR_RE = re.compile(r"(-workspace$|^evals$|^iteration-\d)")


def scan_skills(root: Path, ignore: list[str]):
    home_skills = Path.home() / ".claude" / "skills"
    hits: list[tuple[Path, int, str]] = []
    if not home_skills.exists():
        return hits, home_skills
    for dirpath, dirnames, filenames in os.walk(home_skills):
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and not SKILL_SKIP_DIR_RE.search(d)
        ]
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            p = Path(dirpath) / fn
            text = p.read_text(encoding="utf-8", errors="replace")
            in_fence = False
            for i, line in enumerate(text.splitlines(), start=1):
                if FENCE_RE.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for m in SKILLS_LINE_RE.finditer(line):
                    rel = clean_token(m.group(1).split("`")[0])
                    if not rel or is_ignored(rel, ignore) or is_placeholder(rel):
                        continue
                    target = root / rel.replace("\\", "/")
                    has_glob = any(c in rel for c in "*?[")
                    try:
                        ok = (target.parent.exists()
                              and any(target.parent.glob(target.name))
                              ) if has_glob else target.exists()
                    except OSError:
                        ok = False
                    if not ok:
                        hits.append((p, i, rel))
    return hits, home_skills


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="検出があれば exit 1")
    ap.add_argument("--docs", action="store_true",
                    help="**/docs/** も対象に含める")
    ap.add_argument("--skills", action="store_true",
                    help="~/.claude/skills/ の Tools\\Python 参照も検査")
    ap.add_argument("--symbols", action="store_true",
                    help="識別子参照(②)も検査する")
    ap.add_argument("--quiet", action="store_true",
                    help="検出0件なら何も出力しない")
    args = ap.parse_args(argv)

    ignore = load_ignore_patterns()
    symbols = build_symbol_index(REPO_ROOT) if args.symbols else None

    path_hits, sym_hits = scan_repo_docs(REPO_ROOT, ignore, symbols, args.docs)
    skill_hits: list[tuple[Path, int, str]] = []
    skills_root = None
    if args.skills:
        skill_hits, skills_root = scan_skills(REPO_ROOT, ignore)

    total = len(path_hits) + len(sym_hits) + len(skill_hits)

    if total == 0:
        if not args.quiet:
            print("check_doc_refs: 参照ドリフトは検出されませんでした。")
        return 0

    print("=" * 70)
    print("check_doc_refs: ドキュメントの参照ずれ候補")
    print("=" * 70)

    if path_hits:
        print(f"\n■ ① パス参照が解決できない  ({len(path_hits)} 件)")
        for doc, ln, tok in path_hits:
            print(f"  {rel(doc, REPO_ROOT)}:{ln}  ->  {tok}")

    if sym_hits:
        print(f"\n■ ② .py に定義が無い識別子  ({len(sym_hits)} 件・弱い警告)")
        for doc, ln, tok in sym_hits:
            print(f"  {rel(doc, REPO_ROOT)}:{ln}  ->  {tok}")

    if args.skills:
        if skill_hits:
            print(f"\n■ skills → リポジトリ参照が解決できない  ({len(skill_hits)} 件)")
            for doc, ln, tok in skill_hits:
                print(f"  {rel(doc, skills_root)}:{ln}  ->  Tools/Python/{tok}")
        else:
            print("\n■ skills: Tools\\Python 参照のずれは検出されませんでした。")

    print()
    print(f"合計 {total} 件。意図的な参照は scripts/check_doc_refs.ignore に追記してください。")
    print("（既定は警告のみ。--check を付けると exit 1 になります）")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
