#!/bin/bash
# Copilot CLI postToolUse hook
# cdk_*_stack.py が作成・編集されたときに README.md を自動更新する。
#
# 入力 JSON (stdin):
#   { "toolName": "create"|"edit", "toolArgs": "{\"path\":\"...\"}", ... }

set -e

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName')

# create / edit ツール以外は無視
if [ "$TOOL_NAME" != "create" ] && [ "$TOOL_NAME" != "edit" ]; then
  exit 0
fi

TOOL_ARGS=$(echo "$INPUT" | jq -r '.toolArgs')
FILE_PATH=$(echo "$TOOL_ARGS" | jq -r '.path')

# cdk_*_stack.py 以外は無視
if ! basename "$FILE_PATH" | grep -qE '^cdk_[a-z_]+_stack\.py$'; then
  exit 0
fi

if [ "$TOOL_NAME" = "create" ]; then
  python3 scripts/update_readme.py new "$FILE_PATH"
else
  python3 scripts/update_readme.py modified "$FILE_PATH"
fi
