#!/usr/bin/env python3
"""
README.md を cdk_*_stack.py の変更に合わせて更新するスクリプト。

呼び出し方:
  1. Copilot CLI postToolUse フックから:
       python3 scripts/update_readme.py <status> <filepath>
       status: 'new' | 'modified'

  2. Git pre-commit フックから (引数なし):
       python3 scripts/update_readme.py
       git diff --cached の内容を読み取る
"""

import re
import subprocess
import sys
from pathlib import Path

README = Path("README.md")
STACK_FILE_RE = re.compile(r"^cdk_[a-z_]+_stack\.py$")
CLASS_RE = re.compile(r"class\s+(Cdk\w+Stack)\s*\(")

# '提供スタック一覧' テーブルの既存行にマッチ
TABLE_ROW_RE = re.compile(r"\| [^|]+ \| `cdk_[^|]+_stack\.py` \| [^|]+ \|")


def get_class_name(filepath: str) -> str:
    try:
        content = Path(filepath).read_text()
        m = CLASS_RE.search(content)
        return m.group(1) if m else Path(filepath).stem
    except FileNotFoundError:
        return Path(filepath).stem


def add_to_table(content: str, class_name: str, filename: str) -> str:
    """'提供スタック一覧' テーブルの末尾にプレースホルダー行を挿入する。"""
    new_row = f"| {class_name} | `{filename}` | *(要記載)* |"
    matches = list(TABLE_ROW_RE.finditer(content))
    if not matches:
        return content
    last = matches[-1]
    return content[: last.end()] + "\n" + new_row + content[last.end() :]


def add_detail_section(content: str, class_name: str, filename: str) -> str:
    """'## 削除' の直前にスケルトンの詳細セクションを追加する。"""
    skeleton = (
        f"\n### {class_name}\n\n"
        f"> *(作成されるリソースの説明を記載してください)*\n\n"
        f"- ファイル: `{filename}`\n"
    )
    marker = "\n## 削除"
    if marker in content:
        idx = content.index(marker)
        return content[:idx] + skeleton + content[idx:]
    return content + skeleton


def process_new_stack(content: str, filepath: str) -> tuple[str, bool]:
    """新規スタックファイルを処理する。(updated_content, was_changed) を返す。"""
    filename = Path(filepath).name
    class_name = get_class_name(filepath)

    if f"`{filename}`" in content:
        return content, False  # 既にドキュメント済み

    content = add_to_table(content, class_name, filename)
    content = add_detail_section(content, class_name, filename)
    print(
        f"[hook] README.md: '{class_name}' ({filename}) のプレースホルダーを追加しました。"
        f" リソースの説明を記載してください。"
    )
    return content, True


def process_modified_stack(filepath: str) -> None:
    """変更されたスタックファイルの処理 (手動更新を促すメッセージのみ)。"""
    filename = Path(filepath).name
    print(
        f"[hook] '{filename}' が変更されました。"
        f" スタックの内容が変わった場合は README.md を手動で更新してください。"
    )


# ---------------------------------------------------------------------------
# 呼び出しモード 1: Copilot CLI フックから直接呼び出し
# ---------------------------------------------------------------------------

def run_single(status: str, filepath: str) -> None:
    """単一ファイルを処理する (Copilot CLI フック用)。"""
    if not STACK_FILE_RE.match(Path(filepath).name):
        return

    if status == "new":
        content = README.read_text()
        content, changed = process_new_stack(content, filepath)
        if changed:
            README.write_text(content)
            print("[hook] README.md を更新しました。")
    elif status == "modified":
        process_modified_stack(filepath)


# ---------------------------------------------------------------------------
# 呼び出しモード 2: Git pre-commit フックから呼び出し
# ---------------------------------------------------------------------------

def run_from_git_staged() -> None:
    """git diff --cached を読んでスタックファイルを処理する (Git pre-commit 用)。"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True,
        text=True,
        check=True,
    )

    new_stacks: list[str] = []
    modified_stacks: list[str] = []

    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, filepath = parts[0].strip(), parts[1].strip()
        if not STACK_FILE_RE.match(Path(filepath).name):
            continue
        if status == "A":
            new_stacks.append(filepath)
        elif status == "M":
            modified_stacks.append(filepath)

    if not new_stacks and not modified_stacks:
        return

    for fp in modified_stacks:
        process_modified_stack(fp)

    if not new_stacks:
        return

    content = README.read_text()
    changed = False
    for fp in new_stacks:
        content, was_changed = process_new_stack(content, fp)
        changed = changed or was_changed

    if changed:
        README.write_text(content)
        subprocess.run(["git", "add", str(README)], check=True)
        print("[hook] README.md を更新してステージしました。")


# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) == 3:
        run_single(status=sys.argv[1], filepath=sys.argv[2])
    else:
        run_from_git_staged()


if __name__ == "__main__":
    main()
