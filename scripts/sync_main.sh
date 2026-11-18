#!/usr/bin/env bash
set -euo pipefail
repo="${1:?repo}"; msg="${2:?mensagem}"
here="$(cd "$(dirname "$0")" && pwd)"
cd "$repo"
git checkout -q dev
[ -z "$(git status --porcelain)" ] || { echo "dev tem alterações sem commit: commite antes"; exit 1; }
voltar() {
  if [ "$(git branch --show-current)" = main ]; then
    git reset -q --hard HEAD
    git checkout -q -f dev
    echo "falhou: main não foi alterado e o HEAD voltou para a dev" >&2
  fi
}
git checkout -q main
trap voltar ERR
git rm -rq --cached .
git checkout dev -- .
git checkout main -- .gitignore README.md 2>/dev/null || true
git ls-files -ci --exclude-standard -z | xargs -0 -r git rm -q --cached
git add -A
python "$here/strip_comments.py" "$repo" ${RESOLVE_FROM:+--resolve-from "$RESOLVE_FROM"} --write
git add -A
if python "$here/audit.py" "$repo"; then
  git diff --cached --quiet && echo "main já está igual à dev limpa" || git commit -q -m "$msg"
  git checkout -q dev
  echo "ok: main atualizado localmente, HEAD de volta na dev. Nada foi enviado."
else
  echo "auditoria falhou: main NÃO foi commitado; resolva os achados" >&2
  git checkout -q dev 2>/dev/null || true
  exit 1
fi
