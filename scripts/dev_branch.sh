#!/usr/bin/env bash
set -euo pipefail
repo="${1:?repo}"
cd "$repo"
if git rev-parse --verify -q HEAD >/dev/null; then
  git rev-parse --verify -q dev >/dev/null || git checkout -q -b dev
  git checkout -q dev
else
  git symbolic-ref HEAD refs/heads/dev
fi
git add -A
tam=$(git diff --cached --numstat | wc -l)
mb=$(git diff --cached --name-only -z | xargs -0 -r du -cm 2>/dev/null | tail -1 | cut -f1)
if [ "${FORCE:-0}" != 1 ] && { [ "${tam:-0}" -gt 400 ] || [ "${mb:-0}" -gt 20 ]; }; then
  git reset -q
  echo "snapshot grande demais (${tam} arquivos, ${mb} MB): revise o .gitignore ou rode com FORCE=1" >&2
  exit 1
fi
git diff --cached --quiet || git commit -q -m "Snapshot do código local antes da organização"
hook="$(git rev-parse --git-path hooks/pre-push)"
cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
while read -r local_ref local_sha remote_ref remote_sha; do
  if [ "$local_ref" = "refs/heads/dev" ] || [ "$remote_ref" = "refs/heads/dev" ]; then
    echo "bloqueado: a branch dev é só local e nunca vai para o remoto" >&2
    exit 1
  fi
done
exit 0
HOOK
chmod +x "$hook"
echo "ok: dev com $(git rev-list --count dev) commits; push de dev bloqueado em $hook"
