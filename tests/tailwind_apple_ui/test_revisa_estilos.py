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

    def test_paleta_anulada_avisa_que_no_genera_css(self):
        css = "@theme{--color-*:initial;--color-label:#000;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="bg-gray-500"'})
        (aviso,) = analizar(r)
        self.assertEqual(aviso.codigo, "PALETA")
        self.assertIn("no genera CSS", aviso.texto)

    def test_paleta_tokens_solo_de_paleta_no_cuentan_como_semanticos(self):
        css = "@theme{--color-blue-500:#00f;--color-white:#fff;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="bg-gray-500"'})
        self.assertEqual(analizar(r), [])


ALT = "@media (prefers-reduced-transparency: reduce){.x{}}"


class TestCristal(Base):
    def test_cristal_anidado(self):
        html = '<nav class="glass-bar"><div class="backdrop-blur-md">x</div></nav>'
        r = proyecto(self.tmp, {"a.html": html, "app.css": ALT})
        self.assertEqual(codigos(analizar(r)), ["CRISTAL-ANIDADO"])

    def test_cristal_hermanos_no_es_anidado(self):
        html = '<nav class="glass-bar">a</nav><img src="x"><div class="glass-control">b</div>'
        r = proyecto(self.tmp, {"a.html": html, "app.css": ALT})
        self.assertEqual(analizar(r), [])

    def test_cristal_en_contenido(self):
        html = '<li class="backdrop-blur">a</li><div class="card glass-panel">b</div>'
        r = proyecto(self.tmp, {"a.html": html, "app.css": ALT})
        self.assertEqual(codigos(analizar(r)).count("CRISTAL-CONTENIDO"), 2)

    def test_cristal_jsx_classname(self):
        jsx = 'return <article className={cn("glass-panel")}>x</article>'
        r = proyecto(self.tmp, {"a.tsx": jsx, "app.css": ALT})
        self.assertEqual(codigos(analizar(r)), ["CRISTAL-CONTENIDO"])

    def test_sin_alternativa_transparencia(self):
        r = proyecto(self.tmp, {"a.html": '<nav class="glass-bar"></nav>'})
        self.assertIn("SIN-ALT-TRANSP", codigos(analizar(r)))
        (r / "app.css").write_text(ALT)
        self.assertNotIn("SIN-ALT-TRANSP", codigos(analizar(r)))


class TestMovimientoYOscuro(Base):
    def test_sin_alternativa_movimiento(self):
        r = proyecto(self.tmp, {"a.html": '<div class="transition-transform"></div>'})
        self.assertIn("SIN-ALT-MOV", codigos(analizar(r)))
        (r / "a.html").write_text('<div class="transition-transform motion-reduce:transition-none"></div>')
        self.assertNotIn("SIN-ALT-MOV", codigos(analizar(r)))

    def test_dark_disperso_umbral(self):
        html = "\n".join('<p class="dark:text-white">x</p>' for _ in range(3))
        r = proyecto(self.tmp, {"a.html": html})
        self.assertNotIn("DARK-DISPERSO", codigos(analizar(r)))
        self.assertIn("DARK-DISPERSO", codigos(analizar(r, umbral_dark=2)))

    def test_dark_en_css_no_cuenta(self):
        css = "\n".join("@variant dark { .a{} }" for _ in range(5)) + "\n.b:where(.dark *){}"
        r = proyecto(self.tmp, {"app.css": css.replace("@variant dark", "dark:")})
        self.assertNotIn("DARK-DISPERSO", codigos(analizar(r, umbral_dark=1)))


class TestRevisionFinal(Base):
    def test_v3_negacion_en_atributos_vue(self):
        vue = '<template><div v-if="!isOpen" :disabled="!valid && !loading" @click="!x">a</div></template>'
        r = proyecto(self.tmp, {"a.vue": vue})
        self.assertEqual(analizar(r), [])

    def test_style_de_sfc_se_trata_como_css(self):
        vue = '<template><p>a</p></template>\n<style>\n.a { flex-shrink: 0; flex-grow: 1 }\n</style>'
        r = proyecto(self.tmp, {"a.vue": vue})
        self.assertEqual(analizar(r), [])

    def test_style_de_sfc_detecta_tailwind_v3(self):
        svelte = '<p>a</p>\n<style>\n@tailwind base;\n</style>'
        r = proyecto(self.tmp, {"a.svelte": svelte})
        avisos = analizar(r)
        self.assertEqual([(a.codigo, a.linea) for a in avisos], [("V3", 3)])

    def test_paleta_anulada_avisa_clases_que_no_generan_css(self):
        css = "@theme{--color-*:initial;--color-label:#000;--shadow-*:initial;--shadow-md:0 0 1px #000;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="text-blue-500 shadow-xl shadow-md text-label"'})
        self.assertEqual([(a.codigo, a.texto.split()[0]) for a in analizar(r)],
                         [("PALETA", "shadow-xl"), ("PALETA", "text-blue-500")])

    def test_paleta_anulada_respeta_tokens_definidos(self):
        css = "@theme{--color-*:initial;--color-label:#000;--color-white:#fff;}"
        r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="text-white"'})
        self.assertEqual(analizar(r), [])

    def test_theme_con_keyframes_anidados(self):
        css = ("@theme inline {\n --animate-x: x 1s;\n @keyframes x { from { opacity: 0 } to { opacity: 1 } }\n"
               " --color-background: var(--background);\n}")
        r = proyecto(self.tmp, {"app.css": css, "a.tsx": 'cn("bg-gray-500")'})
        self.assertEqual([c for c in codigos(analizar(r)) if c == "PALETA"], ["PALETA"])

    def test_revisa_js_y_ts(self):
        r = proyecto(self.tmp, {"b.js": 'const c = "bg-[#123456]"', "v.ts": 'cva("p-[13px]")'})
        self.assertEqual(codigos(analizar(r)), ["ARB", "ARB"])

    def test_excluye_directorios_de_build_habituales(self):
        r = proyecto(self.tmp, {f"{d}/x.html": 'class="bg-[#fff]"'
                                for d in (".svelte-kit", ".nuxt", ".output", ".astro", "out", "coverage")})
        self.assertEqual(analizar(r), [])


class TestMenores(Base):
    def test_paleta_en_apply_de_css(self):
        css = "@theme inline{--color-background:var(--background);}\n.a { @apply bg-gray-500 p-4; }"
        r = proyecto(self.tmp, {"app.css": css})
        avisos = analizar(r)
        self.assertEqual([(a.codigo, a.linea) for a in avisos], [("PALETA", 2)])

    def test_tokens_de_paleta_en_css_no_son_avisos(self):
        css = "@theme inline{--color-background:var(--background);--color-blue-500:#00f;}"
        self.assertEqual(analizar(proyecto(self.tmp, {"app.css": css})), [])

    def test_sin_alt_mov_no_salta_con_solo_color(self):
        html = '<a class="transition-colors hover:text-accent">a</a><Transition name="fade"></Transition>'
        self.assertEqual(analizar(proyecto(self.tmp, {"a.vue": html})), [])

    def test_sin_alt_mov_salta_con_transform_en_hover(self):
        r = proyecto(self.tmp, {"a.html": '<a class="transition hover:scale-105">a</a>'})
        self.assertEqual(codigos(analizar(r)), ["SIN-ALT-MOV"])

    def test_cristal_en_directivas_svelte_y_astro(self):
        r = proyecto(self.tmp, {
            "a.svelte": '<nav class:glass-bar={fijo}><div class:glass-control={x}>a</div></nav>',
            "b.astro": '<nav class:list={["glass-bar"]}><li class:list={["glass-panel"]}>b</li></nav>',
            "app.css": ALT,
        })
        self.assertEqual(sorted(codigos(analizar(r))),
                         ["CRISTAL-ANIDADO", "CRISTAL-ANIDADO", "CRISTAL-CONTENIDO"])


class TestRendimiento(Base):
    def test_entrada_patologica_es_rapida(self):
        import time
        texto = ("<div className={a " + "{" * 30 + " x=1 ") * 200 + "\n" + '<a b="' * 5000
        r = proyecto(self.tmp, {"x.tsx": texto})
        t0 = time.monotonic()
        analizar(r)
        self.assertLess(time.monotonic() - t0, 1.0)


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
