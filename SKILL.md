---
name: repo-organizer
description: Organiza um repositório para o GitHub do Iago: decide o que vai para o remoto e o que fica local, remove comentários avulsos do código (só docstring), troca dados reais por fictícios, audita segredos e infra, cria README com modo dev e refaz o histórico do git limpo. Use quando o usuário pedir para "organizar o repo", "preparar para subir no GitHub", "limpar o histórico", "auditar antes do push" ou ao criar repo novo.
---

# repo-organizer: preparar um repo para o GitHub

Critérios completos e a lista do que vai e do que não vai: `references/criterios.md`. Leia antes de agir.

## Regras que não se negociam
1. **Nada de push, force push ou delete de branch remota sem o usuário mandar naquela conversa.** Prepare tudo local e pare.
2. **Branch `dev` local, nunca enviada.** Antes de qualquer mudança, todo o código local (inclusive o não commitado) vira commit na `dev` (`scripts/dev_branch.sh`). A `dev` guarda o código bruto, com comentários e notas; é onde se trabalha no dia a dia. O hook `pre-push` bloqueia qualquer push de `dev`. Só o `main`, limpo, vai para o GitHub. Mantenha também o backup em bundle e tar fora do repo, porque apagar a pasta `.git` leva a `dev` junto.
3. **Código sem comentário avulso.** No máximo docstring (`/** */`). Comentário de IA chama atenção de atacante.
4. **Baseline de testes antes e depois.** Rode a suíte antes de tocar em nada. Depois da limpeza, o resultado tem de ser idêntico. Falha que já existia é reportada, não corrigida às escondidas.
5. **Nada de dado real de cliente** (CNPJ, razão social, e-mail, telefone, IP interno) em fixtures. Troque por fictício válido, sem colidir com os que já existem.
6. **Visibilidade privada por padrão.**

## Fluxo
1. **Reconhecer:** `git status`, remotos, branches, tamanho do histórico, o que já está rastreado. Ler `references/criterios.md`.
2. **Auditar (só leitura):** `python scripts/audit.py <repo> --history`. Lista arquivos que deveriam ficar locais, segredo/IP/host, comentários e achados no histórico.
3. **Criar a `dev`** (`scripts/dev_branch.sh <repo>`, recusa snapshot acima de 400 arquivos ou 20 MB sem `FORCE=1`: revise o `.gitignore`), **backup** (regra 2) e **baseline de testes** (regra 4).
4. **Limpar a árvore:**
   - `python scripts/strip_comments.py <repo>` (dry-run) e depois `--write`. PHP/Blade usam o tokenizador do PHP; JS/Vue/CSS usam `acorn` e `vue/compiler-sfc` do próprio repo; Python usa `tokenize`; Shell remove só linhas inteiras de comentário. O shebang nunca é tocado (`--resolve-from <dir com node_modules>` quando o repo não tem). Mantém docblocks e diretivas de ferramenta (`eslint`, `@ts-`, `@phpstan`, `@vite-ignore`, `/*!` de licença).
   - Trocar dados reais por fictícios (regra 5) e rodar a suíte de novo. Se os testes ordenam por nome, escolha nomes novos que preservem a ordem alfabética relativa. Proteja nomes de cidade ("São Paulo") e valores derivados do nome (login, slug, senha de seed) ao trocar em massa; confira com busca case-insensitive e rode também o e2e quando houver.
   - `.gitignore` conforme o critério; README com **modo dev** (requisitos, comandos, portas, testes) sem IP, usuário, credencial, deploy ou CI.
5. **Rodar `scripts/audit.py <repo>` até dar `limpo`.**
6. **Gerar o `main` limpo:**
   - Primeira vez, histórico novo (só se o usuário pediu): `scripts/fresh_history.sh <repo> "mensagem"` cria `main` com um commit a partir da árvore limpa.
   - Depois disso, a cada ciclo: commite na `dev` e rode `scripts/sync_main.sh <repo> "mensagem"` (`RESOLVE_FROM=<dir com node_modules>` se o repo não tiver `acorn`). Ele copia a árvore da `dev` para o `main`, tira comentários, aplica o `.gitignore` do `main`, roda a auditoria e só commita se der `limpo`. O HEAD volta para a `dev`. Se a `dev` não mudou, o `main` fica igual.
7. **Parar e relatar:** o que mudou, contagens, resultado dos testes antes e depois, caminho dos backups. O force push (`git push --force-with-lease origin main`, e apagar branches de sessão como `claude/*`) só quando o usuário mandar.

## Armadilhas já vividas
- `git add -A` na criação da `dev` pega tudo que está solto (logs, prints, pastas de validação). Por isso a trava de tamanho; ajuste o `.gitignore` da `dev` antes de usar `FORCE=1`.
- Trocar de branch troca os arquivos no disco: README e docs que só existem no `main` somem na `dev`, e o código bruto volta ao trocar para `dev`. Os arquivos ignorados pelo `main` (scripts, notas) ficam no disco.
- `git rm -r --cached .` precisa rodar *depois* do `checkout --orphan` e o resultado deve ser conferido com `git ls-files -ci --exclude-standard` e `git ls-files`: arquivo ignorado pode continuar no índice.
- Ao trocar dado por fictício com `sed` global, não reaproveite um valor que já existe em outro teste: duas entidades passam a colidir. Gere valores novos e restaure o arquivo do git se errar.
- Remover `*.md` do `.gitignore` expõe notas soltas: use `/*.md` + `!/README.md`.
- `autocrlf` no Windows gera avisos de LF/CRLF; são inofensivos.
