<?php
/**
 * Remove comentários de arquivos PHP e Blade, preservando docblocks e diretivas de ferramenta.
 * Uso: php strip_php.php [--write] arquivo...
 */
$write = in_array('--write', $argv, true);
$files = array_values(array_filter(array_slice($argv, 1), fn ($a) => $a !== '--write'));
const MARK = "\x01";
const KEEP = '/(@phpstan|@psalm|phpcs:|@codeCoverage|@noinspection|@suppress|php-cs-fixer)/i';

function limpar(string $texto): string
{
    $saida = [];
    $descartouAntes = false;
    foreach (explode("\n", $texto) as $linha) {
        if (!str_contains($linha, MARK)) {
            if ($descartouAntes && trim($linha) === '' && $saida && trim(end($saida)) === '') {
                continue;
            }
            $saida[] = $linha;
            $descartouAntes = false;
            continue;
        }
        $semMarca = str_replace(MARK, '', $linha);
        if (trim($semMarca) === '') {
            $descartouAntes = true;
            continue;
        }
        $saida[] = rtrim($semMarca);
        $descartouAntes = false;
    }
    return implode("\n", $saida);
}

function phpPuro(string $codigo, int &$n): string
{
    $out = '';
    foreach (token_get_all($codigo) as $t) {
        if (is_array($t) && $t[0] === T_COMMENT && !preg_match(KEEP, $t[1])) {
            $out .= MARK;
            $n += substr_count($t[1], "\n") + 1;
            continue;
        }
        $out .= is_array($t) ? $t[1] : $t;
    }
    return $out;
}

foreach ($files as $f) {
    $orig = file_get_contents($f);
    $n = 0;
    if (str_ends_with($f, '.blade.php')) {
        $novo = preg_replace_callback('/\{\{--.*?--\}\}|<!--(?!\[if|<!\[endif).*?-->/s', function ($m) use (&$n) {
            $n += substr_count($m[0], "\n") + 1;
            return MARK;
        }, $orig);
        $novo = preg_replace_callback('/@php\b(.*?)@endphp/s', function ($m) use (&$n) {
            return '@php' . phpPuro('<?php ' . $m[1], $n) . '@endphp';
        }, $novo);
        $novo = str_replace('@php<?php ', '@php ', $novo);
    } else {
        $novo = phpPuro($orig, $n);
    }
    if ($n === 0) {
        continue;
    }
    $novo = limpar($novo);
    if ($write) {
        file_put_contents($f, $novo);
    }
    echo "$n\t$f\n";
}
