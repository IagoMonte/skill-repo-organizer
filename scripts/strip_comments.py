#!/usr/bin/env python3
"""Remove comentários avulsos do código de um repositório, mantendo só docstrings.

Uso: python strip_comments.py <repo> [--write] [--resolve-from <dir com node_modules>]
Sem --write apenas relata (dry-run). Arquivos: git ls-files + não rastreados não ignorados.
PHP/Blade: tokenizador do PHP. JS/Vue/CSS: acorn + vue/compiler-sfc do próprio repo alvo.
Python: tokenize. Shell: linhas inteiras de comentário, sem tocar o shebang.
"""
import io
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ)
PULAR = ("vendor/", "node_modules/", "dist/", "public/build/", "storage/", "bootstrap/cache/")


def arquivos(repo):
    saida = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=repo,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    return [f for f in saida if not f.startswith(PULAR) and (Path(repo) / f).is_file()]


def rodar(cmd, lote, repo, escrever):
    total, erros = 0, []
    for i in range(0, len(lote), 80):
        args = cmd + (["--write"] if escrever else []) + lote[i:i + 80]
        r = subprocess.run(args, cwd=repo, capture_output=True, text=True, env=ENV)
        for linha in r.stdout.splitlines():
            n, _, f = linha.partition("\t")
            total += int(n)
            print(f"{n:>5}  {f}")
        erros += [e for e in r.stderr.splitlines() if e.startswith("ERRO")]
        if r.returncode:
            erros.append(r.stderr.strip())
    return total, erros


PRAGMA = re.compile(r"(noqa|type:|pylint:|fmt:|isort:|pragma|coding[:=]|mypy:)")


def compactar(linhas, removidas):
    final = []
    houve_remocao = False
    for i, linha in enumerate(linhas):
        if i in removidas and removidas[i] is None:
            houve_remocao = True
            continue
        linha = removidas.get(i, linha)
        if linha.strip() == "" and houve_remocao and final and final[-1].strip() == "":
            continue
        if linha.strip() != "":
            houve_remocao = False
        final.append(linha)
    return final


def limpar_python(texto):
    linhas = texto.split(chr(10))
    removidas = {}
    for tok in tokenize.generate_tokens(io.StringIO(texto).readline):
        if tok.type != tokenize.COMMENT:
            continue
        n, col = tok.start
        if (n == 1 and tok.string.startswith("#!")) or PRAGMA.search(tok.string):
            continue
        antes = linhas[n - 1][:col]
        removidas[n - 1] = None if antes.strip() == "" else antes.rstrip()
    return removidas, linhas


def limpar_shell(texto):
    linhas = texto.split(chr(10))
    removidas = {i: None for i, l in enumerate(linhas) if re.match(r"\s*#(?!!)", l)}
    return removidas, linhas


def nativos(repo, arquivos, escrever):
    total = 0
    for f in arquivos:
        p = Path(repo) / f
        texto = p.read_text(encoding="utf-8")
        removidas, linhas = (limpar_python if f.endswith(".py") else limpar_shell)(texto)
        if not removidas:
            continue
        total += len(removidas)
        print(f"{len(removidas):>5}  {f}")
        if escrever:
            p.write_text(chr(10).join(compactar(linhas, removidas)), encoding="utf-8", newline="")
    return total


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    repo = Path(sys.argv[1]).resolve()
    escrever = "--write" in sys.argv
    if "--resolve-from" in sys.argv:
        ENV["STRIP_RESOLVE_FROM"] = str(Path(sys.argv[sys.argv.index("--resolve-from") + 1]).resolve())
    todos = arquivos(repo)
    php = [f for f in todos if f.endswith(".php")]
    js = [f for f in todos if f.endswith((".js", ".mjs", ".vue", ".css"))]
    t1, e1 = rodar(["php", str(AQUI / "strip_php.php")], php, repo, escrever) if php else (0, [])
    nat = [f for f in todos if f.endswith((".py", ".sh"))]
    t3 = nativos(repo, nat, escrever)
    t2, e2 = rodar(["node", str(AQUI / "strip_js.mjs")], js, repo, escrever) if js else (0, [])
    print(f"\n{'removidos' if escrever else 'a remover'}: PHP/Blade {t1} linhas, JS/Vue/CSS {t2} linhas, Python/Shell {t3} linhas")
    if e1 + e2:
        print("\nERROS (arquivos não tocados):")
        print("\n".join(e1 + e2))
        sys.exit(1)


if __name__ == "__main__":
    main()
