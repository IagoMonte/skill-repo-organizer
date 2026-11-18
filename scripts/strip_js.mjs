/**
 * Remove comentários de .js/.mjs/.vue/.css, preservando JSDoc e diretivas de ferramenta.
 * Uso: node strip_js.mjs [--write] arquivo...
 * acorn e vue/compiler-sfc vêm do node_modules do cwd ou de STRIP_RESOLVE_FROM.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { resolve } from 'node:path'

const require = createRequire(resolve(process.env.STRIP_RESOLVE_FROM || process.cwd(), 'package.json'))
const acorn = require('acorn')
const write = process.argv.includes('--write')
const files = process.argv.slice(2).filter((a) => a !== '--write')
const MARK = '\u0001'
const KEEP = /^\s*(eslint|@ts-|istanbul|c8 |@vite-ignore|@__PURE__|#__PURE__|webpackChunk|vitest-|prettier|jshint|global |@vitest)/

function limpar(texto) {
  const saida = []
  let descartou = false
  for (const linha of texto.split('\n')) {
    if (!linha.includes(MARK)) {
      if (descartou && linha.trim() === '' && saida.length && saida[saida.length - 1].trim() === '') continue
      saida.push(linha)
      descartou = false
      continue
    }
    const sem = linha.replaceAll(MARK, '')
    if (sem.trim() === '') { descartou = true; continue }
    saida.push(sem.replace(/\s+$/, ''))
    descartou = false
  }
  return saida.join('\n')
}

function marcar(codigo, ranges) {
  let out = codigo
  for (const [a, b] of ranges.sort((x, y) => y[0] - x[0])) out = out.slice(0, a) + MARK + out.slice(b)
  return out
}

function js(codigo) {
  const ranges = []
  acorn.parse(codigo, {
    ecmaVersion: 'latest', sourceType: 'module', allowHashBang: true,
    onComment: (block, text, start, end) => {
      if (block && text.startsWith('*')) return
      if (KEEP.test(text)) return
      ranges.push([start, end])
    },
  })
  return ranges
}

function css(codigo) {
  const ranges = []
  for (let i = 0; i < codigo.length; i++) {
    const c = codigo[i]
    if (c === '"' || c === "'") {
      for (i++; i < codigo.length && codigo[i] !== c; i++) if (codigo[i] === String.fromCharCode(92)) i++
    } else if (c === '/' && codigo[i + 1] === '*') {
      const fim = codigo.indexOf('*/', i + 2)
      const end = fim < 0 ? codigo.length : fim + 2
      if (codigo[i + 2] !== '!' && !KEEP.test(codigo.slice(i + 2, end - 2))) ranges.push([i, end])
      i = end - 1
    }
  }
  return ranges
}

function vue(codigo, arquivo) {
  const { parse } = require('vue/compiler-sfc')
  const { descriptor, errors } = parse(codigo, { filename: arquivo })
  if (errors.length) throw new Error(errors[0].message)
  const ranges = []
  const base = (b) => b.loc.start.offset
  for (const b of [descriptor.script, descriptor.scriptSetup].filter(Boolean))
    for (const [a, z] of js(b.content)) ranges.push([base(b) + a, base(b) + z])
  for (const s of descriptor.styles)
    for (const [a, z] of css(s.content)) ranges.push([base(s) + a, base(s) + z])
  if (descriptor.template) {
    const t = descriptor.template
    for (const m of t.content.matchAll(/<!--(?!\[if)[\s\S]*?-->/g)) ranges.push([base(t) + m.index, base(t) + m.index + m[0].length])
  }
  return ranges
}

for (const f of files) {
  const orig = readFileSync(f, 'utf8')
  let ranges
  try {
    ranges = f.endsWith('.vue') ? vue(orig, f) : f.endsWith('.css') ? css(orig) : js(orig)
  } catch (e) {
    console.error(`ERRO\t${f}\t${e.message}`)
    continue
  }
  if (!ranges.length) continue
  if (write) writeFileSync(f, limpar(marcar(orig, ranges)))
  console.log(`${ranges.length}\t${f}`)
}
