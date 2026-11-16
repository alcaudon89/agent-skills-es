"""Tests de skills/tailwind-apple-ui/scripts/revisa_estilos.py.

Ejecutar desde la raíz del repo:
    python3 -m unittest discover -s tests/tailwind_apple_ui -v
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_REPO / "skills" / "tailwind-apple-ui" / "scripts"))

from revisa_estilos import analizar, main  # noqa: E402


def proyecto(tmp: Path, ficheros: dict) -> Path:
    for ruta, texto in ficheros.items():
        f = tmp / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(texto, encoding="utf-8")
    return tmp


def codigos(avisos):
    return [a.codigo for a in avisos]


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()


class TestArb(Base):
    def test_arb_color_y_medida(self):
        r = proyecto(self.tmp, {"a.html": '<div class="bg-[#1c1c1e] p-[13px] text-[rgb(0,0,0)]"></div>'})
        self.assertEqual(codigos(analizar(r)), ["ARB", "ARB", "ARB"])

    def test_arb_no_marca_legitimos(self):
        r = proyecto(self.tmp, {"a.tsx": "cn(\"content-[''] grid-cols-[1fr_auto] w-[calc(100%-2rem)] bg-(--x)\")"})
        self.assertEqual(analizar(r), [])

    def test_excluye_node_modules_y_extensiones(self):
        r = proyecto(self.tmp, {"node_modules/x.html": 'class="bg-[#fff]"', "a.md": "bg-[#fff]"})
        self.assertEqual(analizar(r), [])

    def test_fichero_no_utf8_no_rompe(self):
        r = proyecto(self.tmp, {})
        (r / "b.html").write_bytes(b'\xff\xfe class="bg-[#000]"')
        self.assertEqual(codigos(analizar(r)), ["ARB"])

    def test_arb_linea(self):
        r = proyecto(self.tmp, {"a.html": '<p>\n<div class="bg-[#000]"></div>'})
        (aviso,) = analizar(r)
        self.assertEqual((aviso.fichero, aviso.linea), ("a.html", 2))


class TestV3(Base):
    def test_v3_formas_inexistentes_en_v4(self):
        r = proyecto(self.tmp, {
            "app.css": "@tailwind base;",
            "tailwind.config.js": "",
            "a.html": 'class="bg-opacity-50 flex-shrink-0 !flex bg-[--brand] overflow-ellipsis"',
        })
        self.assertEqual(codigos(analizar(r)).count("V3"), 7)

    def test_v3_no_marca_clases_v4_validas(self):
        r = proyecto(self.tmp, {"a.html": 'class="shadow-sm rounded-sm outline-none ring flex! shrink-0 grow"'})
        self.assertEqual(analizar(r), [])

    def test_v3_negacion_js_no_es_importante(self):
        jsx = 'if (a && !open) {}\nreturn <>{!isOpen && <div className="flex" />}</>'
        r = proyecto(self.tmp, {"a.tsx": jsx})
        self.assertEqual(analizar(r), [])

    def test_v3_importante_delante_en_cadena(self):
        r = proyecto(self.tmp, {"a.tsx": 'const c = `p-4 !mt-0`'})
        self.assertEqual(codigos(analizar(r)), ["V3"])

    def test_v3_config_cargado_con_arroba_config_no_avisa(self):
        r = proyecto(self.tmp, {"app.css": '@import "tailwindcss";\n@config "../tailwind.config.js";',
                                "tailwind.config.js": ""})
        self.assertEqual(analizar(r), [])


class TestPaleta(Base):
    def test_paleta_con_tokens_shadcn(self):
        css = ":root{--background:#fff}\n@theme inline{--color-background:var(--background);}"
        r = proyecto(self.tmp, {"app.css": css, "a.tsx": 'cn("bg-gray-500 text-blue-600")'})
        self.assertEqual(codigos(analizar(r)), ["PALETA", "PALETA"])

    def test_paleta_sin_semanticos_no_avisa(self):
        r = proyecto(self.tmp, {"a.html": 'class="bg-gray-500"'})
        self.assertEqual(analizar(r), [])

    def test_paleta_anulada_no_avisa(self):
        css = "@theme{--color-*:initial;--color-label:#000;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="bg-gray-500"'})
        self.assertEqual(analizar(r), [])

    def test_paleta_tokens_solo_de_paleta_no_cuentan_como_semanticos(self):
        css = "@theme{--color-blue-500:#00f;--color-white:#fff;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="bg-gray-500"'})
        self.assertEqual(analizar(r), [])


class TestMain(Base):
    def test_main_codigos_de_salida(self):
        r = proyecto(self.tmp, {"a.html": 'class="bg-[#000]"'})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(r)]), 0)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(r / "no-existe")]), 1)

    def test_main_json(self):
        r = proyecto(self.tmp, {"a.html": 'class="bg-[#000]"'})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main([str(r), "--json"])
        datos = json.loads(out.getvalue())
        self.assertEqual(datos[0]["codigo"], "ARB")
        self.assertEqual(datos[0]["fichero"], "a.html")
        self.assertEqual(datos[0]["linea"], 1)


if __name__ == "__main__":
    unittest.main()
