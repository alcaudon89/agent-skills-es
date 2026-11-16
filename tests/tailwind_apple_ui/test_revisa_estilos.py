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
