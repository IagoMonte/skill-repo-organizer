# Critérios

## 1. O que vai para o GitHub

**Vai:**
- Código-fonte, testes, lockfiles, configs de build e lint.
- `.env.example` só com chaves, sem valores reais.
- `README.md` e documentação básica (o que é, como rodar em dev, estrutura, estrutura de dados).
- `LICENSE` quando o repo é público.
- `.github/workflows/`: é código e precisa estar no repo para rodar.

**Fica só local (sempre no `.gitignore`):**
- `.env*` (exceto `.env.example`), chaves, tokens, certificados, dumps de banco, `*.sqlite`.
- `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/`, `skills-lock.json`.
- Planos e notas de trabalho (`plano.md`, `notas.md`, `diario.md` e similares).
- Documentação de CI/CD e de deploy.
- Scripts de ambiente: `*.ps1`, `*.cmd`, `*.sh` de deploy, túnel e dev. As instruções de dev vão no README.
- Logs, prints (`shots/`), notas de IA (`men-ai/`), pastas de validação, backups, dados reais de cliente.

## 2. Código

- Sem comentário avulso. Só docstring (`/** */`).
- Sem dado real em fixtures: CNPJ, razão social, e-mail, telefone, IP interno trocados por fictícios.
- Nada de IP, host, usuário SSH, e-mail corporativo ou credencial escrito em arquivo, nem no histórico.

## 3. Visibilidade

- Privado por padrão. Projeto com cliente, produção ou banco é sempre privado.
- Público só passando em três testes: sem dado de cliente, sem infra própria nos arquivos nem no histórico, e faz sentido como portfólio ou ferramenta.

## 4. Organização

- Nome: manter os existentes. Repo novo em `kebab-case`; skills em `skill-*`.
- Branches: `dev` é **local e nunca vai para o remoto** (código bruto, commits livres, push bloqueado por hook). `main` é a versão limpa, derivada da `dev`, e é a que sobe e vira produção. Releases por tag `vX.Y.Z` no `main`.
- Raiz mínima: `README.md`, `.gitignore`, `.env.example`, `.github/workflows/`.
- Segredos só em GitHub Secrets.
- Estrutura de dados entra como documentação (`docs/`).

## 5. Histórico

- Refeito com um commit quando houve vazamento, dado real ou comentário no passado.
- A `dev` local é a rede de segurança; bundle e tar da árvore ficam fora do repo como segunda cópia. Force push só por ordem explícita.
