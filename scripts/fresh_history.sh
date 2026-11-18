#!/usr/bin/env bash
set -euo pipefail
repo="${1:?repo}"; msg="${2:?mensagem}"
cd "$repo"
tmp="limpo-$$"
git checkout -q --orphan "$tmp"
git rm -r --cached -q . 2>/dev/null || true
git add -A
indevido=$(git ls-files -ci --exclude-standard)
[ -z "$indevido" ] || { echo "rastreado mas ignorado:"; echo "$indevido"; exit 1; }
git commit -q -m "$msg"
git branch -D main -q 2>/dev/null || true
git branch -m main
echo "ok: $(git log --oneline | wc -l) commit, $(git ls-files | wc -l) arquivos. Refs origin/* antigas continuam até o push."
