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
from typing import Iterator

EXTENSIONES = {".html", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".css"}
EXCLUIDOS = {"node_modules", "dist", ".next", "build", ".git"}
TAMANO_MAX = 2 * 1024 * 1024

DESCRIPCIONES = {
    "ARB": "Valor arbitrario donde debería haber un token",
}


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


def analizar(raiz: Path, umbral_dark: int = 20) -> list[Aviso]:
    avisos: list[Aviso] = []
    for f, texto in recorrer(raiz):
        rel = f.relative_to(raiz).as_posix()
        avisos += detectar_arb(rel, texto)
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
