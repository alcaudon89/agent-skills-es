#!/usr/bin/env python3
"""Revisa los estilos Tailwind CSS v4 de un proyecto web y avisa de desvíos de las anclas.

Solo lee ficheros: no modifica nada ni ejecuta código del proyecto. Avisa, no bloquea:
sale con 0 haya o no avisos, y con 1 solo si la ruta no existe o no se puede leer.

Uso: python3 -I revisa_estilos.py RUTA [--json] [--umbral-dark N]
"""
import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

EXTENSIONES = {".html", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".css"}
EXCLUIDOS = {"node_modules", "dist", ".next", "build", ".git"}
TAMANO_MAX = 2 * 1024 * 1024

DESCRIPCIONES = {
    "ARB": "Valor arbitrario donde debería haber un token",
    "V3": "Sintaxis de Tailwind v3 que no existe en v4",
    "PALETA": "Color de la paleta por defecto donde el proyecto tiene colores semánticos",
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


def recorrer(raiz: Path) -> Iterator[tuple[Path, str]]:
    """Ficheros con extensión admitida fuera de los directorios excluidos."""
    for f in sorted(raiz.rglob("*")):
        rel = f.relative_to(raiz)
        if any(parte in EXCLUIDOS for parte in rel.parts):
            continue
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


THEME_RE = re.compile(r"@theme\b[^{]*\{(.*?)\}", re.S)
COLOR_TOKEN_RE = re.compile(r"--color-([\w-]+)\s*:")
COLOR_DE_PALETA_RE = re.compile(r"^(?:(?:" + PALETA_V4 + r")-\d{2,3}|black|white|transparent|current|inherit)$")


def leer_tokens(textos_css: Iterable[str]) -> Tokens:
    semanticos: set[str] = set()
    anulada = False
    for texto in textos_css:
        for bloque in THEME_RE.findall(texto):
            if re.search(r"--color-\*\s*:\s*initial", bloque):
                anulada = True
            for nombre in COLOR_TOKEN_RE.findall(bloque):
                if not COLOR_DE_PALETA_RE.match(nombre):
                    semanticos.add(nombre)
    return Tokens(semanticos, anulada)


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
            for m in V3_IMPORTANTE_RE.finditer(texto, c.start(), c.end()):
                avisos.append(Aviso("V3", rel, _linea(texto, m.start()), m.group(0)))
    return avisos


def detectar_config_v3(raiz: Path, textos_css: list[str]) -> list[Aviso]:
    if any("@config" in t for t in textos_css):
        return []
    avisos = []
    for nombre in CONFIG_NOMBRES:
        for f in raiz.rglob(nombre):
            rel = f.relative_to(raiz)
            if not any(parte in EXCLUIDOS for parte in rel.parts):
                avisos.append(Aviso("V3", rel.as_posix(), 0, "config en JS sin @config: en v4 va en @theme"))
    return avisos


PALETA_RE = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*(?:" + PREFIJOS_COLOR + r")-(?:" + PALETA_V4 + r")-\d{2,3}(?:/\d+)?(?![\w-])"
)


def detectar_paleta(rel: str, texto: str, tokens: Tokens) -> list[Aviso]:
    if not tokens.colores_semanticos or tokens.paleta_anulada:
        return []
    return [Aviso("PALETA", rel, _linea(texto, m.start()), m.group(0)) for m in PALETA_RE.finditer(texto)]


def analizar(raiz: Path, umbral_dark: int = 20) -> list[Aviso]:
    ficheros = [(f.relative_to(raiz).as_posix(), f.suffix == ".css", t) for f, t in recorrer(raiz)]
    textos_css = [t for _, es_css, t in ficheros if es_css]
    tokens = leer_tokens(textos_css)
    avisos: list[Aviso] = detectar_config_v3(raiz, textos_css)
    for rel, es_css, texto in ficheros:
        avisos += detectar_arb(rel, texto)
        avisos += detectar_v3(rel, texto, es_css)
        if not es_css:
            avisos += detectar_paleta(rel, texto, tokens)
    return sorted(avisos, key=lambda a: (a.codigo, a.fichero, a.linea))


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
