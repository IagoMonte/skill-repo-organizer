#!/usr/bin/env python3
"""Audita um repositório contra os critérios da skill. Só leitura.

Uso: python audit.py <repo> [--history]
Verifica: arquivos rastreados que deveriam ficar locais, segredos/infra no conteúdo,
comentários avulsos no código, .env sem exemplo. Com --history repete a busca de segredos
em todos os commits. Sai com código 1 se houver qualquer achado.
"""
import re
import subprocess
import sys
from pathlib import Path

LOCAL_ONLY = re.compile(
    r"(^|/)(\.env(?:\.(?!example$)[^/]+)?$|AGENTS\.md|CLAUDE\.md|\.claude/|\.agents/|skills-lock\.json|"
    r"[^/]+\.(ps1|cmd|log|pem|key|sqlite|sql|tgz|zip)|men-ai/|shots/|validacao[^/]*/)"
)
MD_PERMITIDO = re.compile(r"(^|/)(README|LEIAME|LICENSE)(\.md)?$|(^|/)docs/|(^|/)SKILL\.md$|(^|/)references/")
SEGREDOS = re.compile(
    r"(\b(?:\d{1,3}\.){3}\d{1,3}\b|BEGIN [A-Z ]*PRIVATE|ssh-(?:rsa|ed25519)|gh[pos]_[A-Za-z0-9]{20}|"
    r"sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{12}|(?i:pass(?:word)?|secret|token|api[_-]?key)(?:\s*=\s*|:\s*)[\"'][^\"'$ ]{6,}[\"'])"
)
FIXTURES = re.compile(r"(^|/)(tests?|e2e|database/seeders|database/factories)/")
IGNORA_IP = re.compile(r"127\.0\.0\.1|0\.0\.0\.0|\b10\.0\.0\.\d+|\b255\.255\.|\d+\.\d+\.\d+\.\d+/\d+")
BINARIO = re.compile(r"\.(png|jpe?g|gif|ico|woff2?|pdf|lock|svg)$|package-lock\.json$")


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout or ""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    repo = Path(sys.argv[1]).resolve()
    achados = []
    arquivos = git(repo, "ls-files", "-co", "--exclude-standard").splitlines()

    for f in arquivos:
        if LOCAL_ONLY.search(f):
            achados.append(f"LOCAL-ONLY no repo: {f}")
        if f.endswith(".md") and not MD_PERMITIDO.search(f):
            achados.append(f"documento fora do padrão (só README e docs/ de usuário): {f}")

    for f in arquivos:
        p = repo / f
        if BINARIO.search(f) or not p.is_file():
            continue
        try:
            linhas = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for n, linha in enumerate(linhas, 1):
            m = SEGREDOS.search(linha)
            if m and not IGNORA_IP.search(m.group(0)) and not (FIXTURES.search(f) and re.match(r"[\d.]+$", m.group(0))):
                achados.append(f"segredo/infra? {f}:{n}: {linha.strip()[:90]}")

    aqui = Path(__file__).resolve().parent
    r = subprocess.run([sys.executable, str(aqui / "strip_comments.py"), str(repo)], capture_output=True, text=True)
    m = re.search(r"PHP/Blade (\d+) linhas, JS/Vue/CSS (\d+) linhas, Python/Shell (\d+)", r.stdout)
    if m and any(int(m.group(i)) for i in (1, 2, 3)):
        achados.append(f"comentários avulsos: {m.group(1)} (PHP/Blade) + {m.group(2)} (JS/Vue/CSS) + {m.group(3)} (Python/Shell) linhas; rode strip_comments.py --write")

    if "--history" in sys.argv:
        for h in git(repo, "rev-list", "--all").split():
            for linha in git(repo, "show", "--format=", "-U0", h).splitlines():
                if linha.startswith("+") and (m := SEGREDOS.search(linha)) and not IGNORA_IP.search(m.group(0)):
                    achados.append(f"segredo/infra no histórico {h[:8]}: {linha[1:90].strip()}")

    for a in dict.fromkeys(achados):
        print(a)
    print(f"\n{len(set(achados))} achado(s)" if achados else "limpo")
    sys.exit(1 if achados else 0)


if __name__ == "__main__":
    main()
