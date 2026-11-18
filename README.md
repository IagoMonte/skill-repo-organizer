# skill-repo-organizer

Skill do Claude Code que prepara um repositório para o GitHub: decide o que vai para o remoto, remove comentários avulsos do código, troca dados reais por fictícios, audita segredos e refaz o histórico limpo.

- `SKILL.md`: fluxo e regras.
- `references/criterios.md`: critérios de publicação e organização.
- `scripts/audit.py`: auditoria só leitura (arquivos locais, segredos, comentários, histórico).
- `scripts/strip_comments.py` com `strip_php.php` e `strip_js.mjs`: remoção de comentários mantendo docstrings.
- `scripts/dev_branch.sh`: cria a branch `dev` local com o código bruto e bloqueia o push dela.
- `scripts/fresh_history.sh`: `main` novo com um commit.
- `scripts/sync_main.sh`: gera o `main` limpo a partir da `dev`.

Requisitos: Python 3, Git, PHP (para PHP/Blade) e Node com `acorn` e `vue/compiler-sfc` no repo alvo (para JS/Vue).

```bash
python scripts/audit.py <repo> --history
python scripts/strip_comments.py <repo> [--write] [--resolve-from <dir>]
scripts/dev_branch.sh <repo>
scripts/fresh_history.sh <repo> "mensagem"
scripts/sync_main.sh <repo> "mensagem"
```

Instalação: copie esta pasta para `~/.claude/skills/repo-organizer/`.
