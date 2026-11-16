#!/usr/bin/env python3
"""Revisa los estilos Tailwind CSS v4 de un proyecto web y avisa de desvíos de las anclas.

Solo lee ficheros: no modifica nada ni ejecuta código del proyecto. Avisa, no bloquea:
sale con 0 haya o no avisos, y con 1 solo si la ruta no existe o no se puede leer.

Uso: python3 -I revisa_estilos.py RUTA [--json] [--umbral-dark N]
"""
import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

EXTENSIONES = {".html", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte", ".astro", ".css"}
EXCLUIDOS = {
    "node_modules", "dist", ".next", "build", ".git", ".svelte-kit", ".nuxt", ".output", ".astro",
    "out", "coverage", ".turbo", ".vercel",
}
TAMANO_MAX = 2 * 1024 * 1024

DESCRIPCIONES = {
    "ARB": "Valor arbitrario donde debería haber un token",
    "V3": "Sintaxis de Tailwind v3 obsoleta o eliminada en v4",
    "PALETA": "Color o sombra de la escala por defecto donde el proyecto tiene anclas propias",
    "CRISTAL-ANIDADO": "Cristal dentro de cristal: agrupa en un único contenedor",
    "CRISTAL-CONTENIDO": "Cristal en contenido (tarjetas, celdas, texto, imágenes): solo va en navegación y controles",
    "SIN-ALT-TRANSP": "Hay cristal y ninguna regla para prefers-reduced-transparency",
    "SIN-ALT-MOV": "Hay movimiento (transform, animaciones) y ninguna alternativa para reduced motion",
    "DARK-DISPERSO": "Demasiados dark: en componentes: resuelve el oscuro en las variables",
}

PALETA_V4 = (
    "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue"
    "|indigo|violet|purple|fuchsia|pink|rose"
)
PREFIJOS_COLOR = (
    "bg|text|border(?:-[trblxy])?|divide|ring|ring-offset|outline|fill|stroke|from|via|to|shadow"
    "|decoration|accent|caret|placeholder"
)


@dataclass(frozen=True)
class Aviso:
    codigo: str
    fichero: str
    linea: int
    texto: str


def _rutas(raiz: Path) -> Iterator[Path]:
    """Todos los ficheros bajo raiz, sin entrar en los directorios excluidos (se podan, no se recorren)."""
    for actual, dirs, ficheros in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUIDOS)
        for nombre in sorted(ficheros):
            yield Path(actual) / nombre


def recorrer(raiz: Path) -> Iterator[tuple[Path, str]]:
    """Ficheros con extensión admitida fuera de los directorios excluidos."""
    for f in _rutas(raiz):
        try:
            if f.suffix not in EXTENSIONES or not f.is_file() or f.stat().st_size > TAMANO_MAX:
                continue
            yield f, f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue


def _linea(texto: str, pos: int) -> int:
    return texto.count("\n", 0, pos) + 1


UTILIDADES_ARB = (
    r"bg|text|border(?:-[trblxy])?|ring|fill|stroke|outline|decoration|shadow|rounded(?:-[trbl]{1,2})?"
    r"|p[xytrbl]?|m[xytrbl]?|gap(?:-[xy])?|w|h|size|min-w|min-h|max-w|max-h|inset(?:-[xy])?|top|right|bottom|left"
)
ARB_RE = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*-?(?:" + UTILIDADES_ARB + r")-\["
    r"(?:#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|oklch\(|-?\d+(?:\.\d+)?(?:px|rem))"
)


def detectar_arb(rel: str, texto: str) -> list[Aviso]:
    return [Aviso("ARB", rel, _linea(texto, m.start()), m.group(0) + "…]") for m in ARB_RE.finditer(texto)]


@dataclass
class Tokens:
    colores_semanticos: set[str]
    paleta_anulada: bool
    colores: set[str] = field(default_factory=set)
    sombras: set[str] = field(default_factory=set)
    sombras_anuladas: bool = False


THEME_INICIO_RE = re.compile(r"@theme\b[^{;]*\{")
SOMBRA_TOKEN_RE = re.compile(r"--shadow-([\w-]+)\s*:")


def bloques_theme(texto: str) -> list[str]:
    """Contenido de cada bloque @theme, contando llaves (admite @keyframes dentro)."""
    bloques = []
    for m in THEME_INICIO_RE.finditer(texto):
        nivel, i = 1, m.end()
        while i < len(texto) and nivel:
            nivel += {"{": 1, "}": -1}.get(texto[i], 0)
            i += 1
        bloques.append(texto[m.end():i - 1])
    return bloques


COLOR_TOKEN_RE = re.compile(r"--color-([\w-]+)\s*:")
COLOR_DE_PALETA_RE = re.compile(r"^(?:(?:" + PALETA_V4 + r")-\d{2,3}|black|white|transparent|current|inherit)$")


def leer_tokens(textos_css: Iterable[str]) -> Tokens:
    t = Tokens(set(), False)
    for texto in textos_css:
        for bloque in bloques_theme(texto):
            if re.search(r"--color-\*\s*:\s*initial", bloque):
                t.paleta_anulada = True
            if re.search(r"--shadow-\*\s*:\s*initial", bloque):
                t.sombras_anuladas = True
            for nombre in COLOR_TOKEN_RE.findall(bloque):
                t.colores.add(nombre)
                if not COLOR_DE_PALETA_RE.match(nombre):
                    t.colores_semanticos.add(nombre)
            t.sombras.update(SOMBRA_TOKEN_RE.findall(bloque))
    return t


V3_CLASES_RE = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*(?:"
    r"(?:bg|text|border|divide|ring|placeholder)-opacity-\d+"
    r"|flex-(?:shrink|grow)(?:-\d+)?(?![\w-])"
    r"|overflow-ellipsis|decoration-(?:slice|clone)"
    r"|[\w-]+-\[--[\w-]+\]"
    r")"
)
# `!` delante (v3) solo dentro de una cadena y tras inicio o espacio: evita la negación de JS.
V3_IMPORTANTE_RE = re.compile(r"(?<=[\s\"'`])![a-z][\w:-]*")
# Valores de directivas (Vue v-if/:prop/@evento, Svelte on:, Alpine x-…) y manejadores on*: son JS, no clases.
ATRIBUTO_JS_RE = re.compile(r"(?:\bv-[\w:.\[\]-]+|(?<![\w-])[:@#][\w.:\[\]-]+|\bon[\w:]+|\bx-[\w:.-]+)\s*=\s*$")
CADENA_RE = re.compile(r"\"[^\"\n]*\"|'[^'\n]*'|`[^`]*`")
V3_CSS_RE = re.compile(r"@tailwind\s+(?:base|components|utilities|variants)")
CONFIG_NOMBRES = ("tailwind.config.js", "tailwind.config.cjs", "tailwind.config.mjs", "tailwind.config.ts")


def detectar_v3(rel: str, texto: str, es_css: bool) -> list[Aviso]:
    avisos = []
    if es_css:
        avisos += [Aviso("V3", rel, _linea(texto, m.start()), m.group(0)) for m in V3_CSS_RE.finditer(texto)]
    else:
        avisos += [Aviso("V3", rel, _linea(texto, m.start()), m.group(0)) for m in V3_CLASES_RE.finditer(texto)]
        for c in CADENA_RE.finditer(texto):
            if ATRIBUTO_JS_RE.search(texto, max(0, c.start() - 80), c.start()):
                continue
            for m in V3_IMPORTANTE_RE.finditer(texto, c.start(), c.end()):
                avisos.append(Aviso("V3", rel, _linea(texto, m.start()), m.group(0)))
    return avisos


def detectar_config_v3(raiz: Path, textos_css: list[str]) -> list[Aviso]:
    if any("@config" in t for t in textos_css):
        return []
    avisos = []
    for f in _rutas(raiz):
        if f.name in CONFIG_NOMBRES:
            rel = f.relative_to(raiz).as_posix()
            avisos.append(Aviso("V3", rel, 0, "config en JS sin @config: en v4 va en @theme"))
    return avisos


PALETA_RE = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*(?:" + PREFIJOS_COLOR + r")-(?:" + PALETA_V4 + r")-\d{2,3}(?:/\d+)?(?![\w-])"
)


PALETA_BN_RE = re.compile(r"(?<![\w-])(?:[\w-]+:)*(?:" + PREFIJOS_COLOR + r")-(?:black|white)(?:/\d+)?(?![\w-])")
SOMBRA_DEFECTO_RE = re.compile(r"(?<![\w-])(?:[\w-]+:)*shadow-(2xs|xs|sm|md|lg|xl|2xl|inner)(?![\w-])")
NO_GENERA = "no genera CSS: la escala por defecto está anulada; usa un token"


def _nombre_color(clase: str) -> str:
    """bg-blue-500/50 → blue-500; hover:text-white → white."""
    base = clase.split(":")[-1].split("/")[0]
    m = re.search(r"-((?:" + PALETA_V4 + r")-\d{2,3}|black|white)$", base)
    return m.group(1) if m else ""


def detectar_paleta(rel: str, texto: str, tokens: Tokens) -> list[Aviso]:
    avisos = []
    if tokens.paleta_anulada:
        for rx in (PALETA_RE, PALETA_BN_RE):
            for m in rx.finditer(texto):
                if _nombre_color(m.group(0)) not in tokens.colores:
                    avisos.append(Aviso("PALETA", rel, _linea(texto, m.start()), f"{m.group(0)} ({NO_GENERA})"))
    elif tokens.colores_semanticos:
        avisos += [Aviso("PALETA", rel, _linea(texto, m.start()), m.group(0)) for m in PALETA_RE.finditer(texto)]
    if tokens.sombras_anuladas:
        for m in SOMBRA_DEFECTO_RE.finditer(texto):
            if m.group(1) not in tokens.sombras:
                avisos.append(Aviso("PALETA", rel, _linea(texto, m.start()), f"{m.group(0)} ({NO_GENERA})"))
    return avisos


ES_CRISTAL = re.compile(r"(?<![\w-])(backdrop-blur(-[\w\[\]().%-]+)?|backdrop-filter|glass-[\w-]+)(?![\w-])")
# Cada alternativa empieza por un carácter distinto: sin retroceso exponencial en ficheros raros.
_LLAVES = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
_VALOR = r"(?:\"[^\"]*\"|'[^']*'|" + _LLAVES + r"|[^\s>\"'{]+)"
ETIQUETA_RE = re.compile(
    r"<(/?)([A-Za-z][\w.:-]*)((?:[^<>{}\"'/]|/(?!>)|\"[^\"\n]*\"|'[^'\n]*'|" + _LLAVES + r")*)(/?)>"
)
CLASE_ATTR_RE = re.compile(r"(?:^|\s)(?::class|class:list|class|className)\s*=\s*(" + _VALOR + r")")
DIRECTIVA_CLASE_RE = re.compile(r"(?:^|\s)class:(?!list\b)([\w-]+)")  # Svelte: class:glass-bar={x}
VACIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CONTENIDO = {"article", "li", "td", "p", "img"}


def detectar_cristal(rel: str, texto: str) -> list[Aviso]:
    """CRISTAL-ANIDADO y CRISTAL-CONTENIDO con una pila de etiquetas (heurística, tolera JSX)."""
    avisos: list[Aviso] = []
    pila: list[tuple[str, bool]] = []
    for m in ETIQUETA_RE.finditer(texto):
        cierre, etiqueta, attrs, autocierre = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if cierre:
            nombres = [e for e, _ in pila]
            if etiqueta in nombres:
                del pila[len(nombres) - 1 - nombres[::-1].index(etiqueta):]
            continue
        clases = " ".join(CLASE_ATTR_RE.findall(attrs) + DIRECTIVA_CLASE_RE.findall(attrs))
        cristal = bool(ES_CRISTAL.search(clases))
        if cristal:
            linea = _linea(texto, m.start())
            if any(g for _, g in pila):
                avisos.append(Aviso("CRISTAL-ANIDADO", rel, linea, f"<{etiqueta}> con cristal dentro de otro cristal"))
            if etiqueta in CONTENIDO or re.search(r"(?<![\w-])card(?![\w])", clases):
                avisos.append(Aviso("CRISTAL-CONTENIDO", rel, linea, f"<{etiqueta}> {clases.strip()}"))
        if not autocierre and etiqueta not in VACIAS:
            pila.append((etiqueta, cristal))
    return avisos


# Solo movimiento espacial: transform, animaciones y keyframes. Un fundido de color no necesita alternativa.
MOVIMIENTO_RE = re.compile(
    r"(?<![\w-])(?:transition-(?:transform|all)|animate-(?!none\b)[\w-]+"
    r"|(?:[\w-]+:)+-?(?:translate|scale|rotate|skew)-[\w./\[\]-]+)(?![\w-])|@keyframes"
)
ALT_MOV_RE = re.compile(r"motion-reduce:|motion-safe:|prefers-reduced-motion")


def detectar_proyecto(textos: list[tuple[str, bool, str]], umbral_dark: int) -> list[Aviso]:
    todo = "\n".join(t for _, _, t in textos)
    avisos = []
    if ES_CRISTAL.search(todo) and "prefers-reduced-transparency" not in todo:
        avisos.append(Aviso("SIN-ALT-TRANSP", ".", 0, "añade una superficie opaca bajo prefers-reduced-transparency: reduce"))
    if MOVIMIENTO_RE.search(todo) and not ALT_MOV_RE.search(todo):
        avisos.append(Aviso("SIN-ALT-MOV", ".", 0, "añade motion-reduce: o @media (prefers-reduced-motion)"))
    usos_dark = sum(t.count("dark:") for _, es_css, t in textos if not es_css)
    if usos_dark > umbral_dark:
        avisos.append(Aviso("DARK-DISPERSO", ".", 0, f"{usos_dark} usos de dark: (umbral {umbral_dark})"))
    return avisos


APPLY_RE = re.compile(r"@apply\s+[^;}]*")


def solo_apply(css: str) -> str:
    """El CSS con todo en blanco salvo las líneas @apply (mismos offsets)."""
    partes, pos = [], 0
    for m in APPLY_RE.finditer(css):
        partes += [_blanco(css[pos:m.start()]), m.group(0)]
        pos = m.end()
    partes.append(_blanco(css[pos:]))
    return "".join(partes)


STYLE_RE = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)", re.S | re.I)


def _blanco(t: str) -> str:
    return re.sub(r"[^\n]", " ", t)


def separar_estilos(texto: str) -> tuple[str, str]:
    """(marcado, estilos): mismos offsets y líneas; cada parte deja la otra en blanco."""
    marcado, estilos, pos = [], [], 0
    for m in STYLE_RE.finditer(texto):
        antes = texto[pos:m.start(2)]
        marcado += [antes, _blanco(m.group(2))]
        estilos += [_blanco(antes), m.group(2)]
        pos = m.end(2)
    marcado.append(texto[pos:])
    estilos.append(_blanco(texto[pos:]))
    return "".join(marcado), "".join(estilos)


def analizar(raiz: Path, umbral_dark: int = 20) -> list[Aviso]:
    ficheros = []
    for f, texto in recorrer(raiz):
        rel = f.relative_to(raiz).as_posix()
        if f.suffix == ".css":
            ficheros.append((rel, True, texto, "", texto))
        else:
            marcado, estilos = separar_estilos(texto)
            ficheros.append((rel, False, texto, marcado, estilos))
    textos_css = [estilos for *_, estilos in ficheros if estilos.strip()]
    tokens = leer_tokens(textos_css)
    avisos: list[Aviso] = detectar_config_v3(raiz, textos_css)
    for rel, es_css, texto, marcado, estilos in ficheros:
        avisos += detectar_arb(rel, texto)
        if estilos.strip():
            avisos += detectar_v3(rel, estilos, True)
            avisos += detectar_paleta(rel, solo_apply(estilos), tokens)
        if not es_css:
            avisos += detectar_v3(rel, marcado, False)
            avisos += detectar_paleta(rel, marcado, tokens)
            avisos += detectar_cristal(rel, marcado)
    avisos += detectar_proyecto([(rel, es_css, texto) for rel, es_css, texto, *_ in ficheros], umbral_dark)
    return sorted(avisos, key=lambda a: (a.codigo, a.fichero, a.linea, a.texto))


def _imprimir(avisos: list[Aviso]) -> None:
    if not avisos:
        print("Sin avisos.")
        return
    por_codigo: dict[str, list[Aviso]] = {}
    for a in avisos:
        por_codigo.setdefault(a.codigo, []).append(a)
    for codigo, lista in por_codigo.items():
        print(f"\n{codigo} ({len(lista)}): {DESCRIPCIONES.get(codigo, '')}")
        for a in lista:
            donde = a.fichero if a.linea == 0 else f"{a.fichero}:{a.linea}"
            print(f"  {donde}  {a.texto}")
    print(f"\nTotal: {len(avisos)} avisos. Son avisos, no errores: corrige o justifica cada uno.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Revisa estilos Tailwind v4 contra las anclas del proyecto.")
    p.add_argument("ruta", type=Path)
    p.add_argument("--json", action="store_true", help="salida en JSON")
    p.add_argument("--umbral-dark", type=int, default=20, help="usos de dark: tolerados en componentes")
    args = p.parse_args(argv)
    if not args.ruta.is_dir():
        print(f"No se puede leer la ruta: {args.ruta}", file=sys.stderr)
        return 1
    avisos = analizar(args.ruta, args.umbral_dark)
    if args.json:
        print(json.dumps([asdict(a) for a in avisos], ensure_ascii=False, indent=2))
    else:
        _imprimir(avisos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
