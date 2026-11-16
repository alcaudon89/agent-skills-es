# tailwind-apple-ui Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear la skill `tailwind-apple-ui`: estilos Tailwind CSS v4 en proyectos web a partir de anclas en `@theme`, con criterio Apple y Liquid Glass esmerilado, más un script que avisa de desvíos.

**Architecture:** Skill en `skills/tailwind-apple-ui/` con el formato del repo (`SKILL.md`, `README.md`, `references/`, `scripts/`). El script es un único módulo Python de librería estándar con un detector por código de aviso; los tests viven fuera de la skill (`tests/tailwind_apple_ui/`) para no inflar el ZIP. La plantilla `theme.css` se valida compilándola con la CLI oficial de Tailwind v4 y pasándole el propio script.

**Tech Stack:** Python 3 (stdlib, `unittest`), Tailwind CSS v4 (`@tailwindcss/cli`, solo para verificar), Markdown.

**Spec:** `docs/superpowers/specs/2026-11-16-tailwind-apple-ui-design.md`

## Global Constraints

- Todo en castellano, mismo tono y formato que `skills/expo-apple-ui/` (frontmatter `name` y `description` entre comillas dobles).
- Script: solo librería estándar, ejecutable como `python3 -I scripts/revisa_estilos.py <ruta> [--json] [--umbral-dark N]`.
- El script avisa, no bloquea: salida 0 con o sin avisos; 1 solo si la ruta no existe o no se puede leer.
- Extensiones revisadas: `.html .jsx .tsx .vue .svelte .astro .css`. Directorios excluidos: `node_modules`, `dist`, `.next`, `build`, `.git`.
- Códigos de aviso exactos: `ARB`, `V3`, `PALETA`, `CRISTAL-ANIDADO`, `CRISTAL-CONTENIDO`, `SIN-ALT-TRANSP`, `SIN-ALT-MOV`, `DARK-DISPERSO`.
- Cristal = esmerilado (`backdrop-filter` blur + saturate, borde, brillo). Nada de refracción SVG.
- Tipografía con pila `system-ui`; no embeber SF Pro ni activos de Apple.
- Plantilla para proyecto nuevo: `--color-*: initial;` y `--shadow-*: initial;`. Espaciado: `--spacing` por defecto (4 px), sin tocar.
- La skill se activa solo cuando se pide estilo Apple o el proyecto ya lo usa. Con anclas ajenas, se respetan; no se renombra ni se anula nada.

## Review Focus

1. **Proyecto shadcn** (`:root { --background: … }` + `@theme inline { --color-background: var(--background) }`): `PALETA` debe considerar `background` un semántico y avisar de `bg-gray-500`; no debe exigir los nombres de la plantilla.
2. **Clases v4 válidas que en v3 significaban otra cosa** (`shadow-sm`, `rounded-sm`, `outline-none`, `ring`): no deben dar `V3`. Solo se marcan formas que no existen en v4.
3. **Valores arbitrarios legítimos** (`content-['']`, `grid-cols-[1fr_auto]`, `w-[calc(100%-2rem)]`, `bg-(--mi-var)`): no deben dar `ARB`.
4. **Clases fuera de atributos** (template literals, `cn("…")`, `clsx`, `:class`): el script busca en todo el texto, no solo en `class=`.
5. **Ficheros raros** (no UTF-8, minificados enormes, enlaces rotos): se saltan sin romper la ejecución y sin salida distinta de 0.

---

### Task 1: Esqueleto del script y aviso `ARB`

**Files:**
- Create: `skills/tailwind-apple-ui/scripts/revisa_estilos.py`
- Create: `tests/tailwind_apple_ui/test_revisa_estilos.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Aviso: codigo: str; fichero: str; linea: int; texto: str` (`fichero` relativo a la raíz; `linea` 0 si el aviso es de proyecto).
  - `def recorrer(raiz: Path) -> Iterator[tuple[Path, str]]` — ficheros con extensión admitida fuera de los excluidos, texto leído con `errors="replace"`; salta ilegibles y ficheros > 2 MB.
  - `def analizar(raiz: Path, umbral_dark: int = 20) -> list[Aviso]` — orquesta todos los detectores; ordena por (codigo, fichero, linea).
  - `def main(argv: list[str] | None = None) -> int` — `argparse`; salida de texto agrupada por código con recuento, o `--json` (lista de dicts de `Aviso`).
  - Helper de tests: `def proyecto(tmp: Path, ficheros: dict[str, str]) -> Path` en el fichero de tests.

- [ ] **Step 1: Tests que fallan**

```python
def test_arb_color_y_medida(self):
    r = proyecto(self.tmp, {"a.html": '<div class="bg-[#1c1c1e] p-[13px] text-[rgb(0,0,0)]"></div>'})
    self.assertEqual([a.codigo for a in analizar(r)], ["ARB", "ARB", "ARB"])

def test_arb_no_marca_legitimos(self):  # Review Focus 3
    r = proyecto(self.tmp, {"a.tsx": 'cn("content-[\'\'] grid-cols-[1fr_auto] w-[calc(100%-2rem)] bg-(--x)")'})
    self.assertEqual(analizar(r), [])

def test_excluye_node_modules_y_extensiones(self):
    r = proyecto(self.tmp, {"node_modules/x.html": 'class="bg-[#fff]"', "a.md": 'bg-[#fff]'})
    self.assertEqual(analizar(r), [])

def test_fichero_no_utf8_no_rompe(self):  # Review Focus 5
    r = proyecto(self.tmp, {})
    (r / "b.html").write_bytes(b'\xff\xfe class="bg-[#000]"')
    self.assertEqual([a.codigo for a in analizar(r)], ["ARB"])

def test_main_codigos_de_salida(self):
    r = proyecto(self.tmp, {"a.html": 'class="bg-[#000]"'})
    self.assertEqual(main([str(r)]), 0)
    self.assertEqual(main([str(r / "no-existe")]), 1)

def test_main_json(self):
    # captura stdout; json.loads devuelve lista con {"codigo": "ARB", "fichero": "a.html", "linea": 1, ...}
```

- [ ] **Step 2: Ejecutar y ver que fallan**

Run: `python3 -m unittest discover -s tests/tailwind_apple_ui -v`
Expected: ERROR por `ModuleNotFoundError` (el test añade `skills/tailwind-apple-ui/scripts` a `sys.path`).

- [ ] **Step 3: Implementar `Aviso`, `recorrer`, `analizar`, `main` y el detector `ARB`**

`ARB`: regex sobre utilidades de color, espaciado y tamaño (`bg|text|border|ring|fill|stroke|outline|p[xytrbl]?|m[xytrbl]?|gap|w|h|size|inset|top|right|bottom|left|rounded|shadow`) seguidas de `-[` con `#hex`, `rgb(a)`, `hsl(a)`, `oklch(` o número con `px|rem`. `calc(`, `var(` y `content-[` no cuentan. Línea = número de línea del match.

- [ ] **Step 4: Ejecutar y ver que pasan**

Run: `python3 -m unittest discover -s tests/tailwind_apple_ui -v`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add skills/tailwind-apple-ui/scripts tests/tailwind_apple_ui
git commit -m "tailwind-apple-ui: script de revisión con aviso ARB"
```

### Task 2: Avisos `V3` y `PALETA`

**Files:**
- Modify: `skills/tailwind-apple-ui/scripts/revisa_estilos.py`
- Modify: `tests/tailwind_apple_ui/test_revisa_estilos.py`

**Interfaces:**
- Consumes: `Aviso`, `recorrer`, `analizar` (Task 1).
- Produces: `@dataclass class Tokens: colores_semanticos: set[str]; paleta_anulada: bool` y `def leer_tokens(textos_css: Iterable[str]) -> Tokens`. Task 3 añadirá campos a `Tokens`.

- [ ] **Step 1: Tests que fallan**

```python
def test_v3_formas_inexistentes_en_v4(self):
    r = proyecto(self.tmp, {"app.css": "@tailwind base;", "tailwind.config.js": "", "a.html":
        'class="bg-opacity-50 flex-shrink-0 !flex bg-[--brand] overflow-ellipsis"'})
    codigos = [a.codigo for a in analizar(r)]
    self.assertEqual(codigos.count("V3"), 7)  # @tailwind, config, y 5 clases

def test_v3_no_marca_clases_v4_validas(self):  # Review Focus 2
    r = proyecto(self.tmp, {"a.html": 'class="shadow-sm rounded-sm outline-none ring flex!"'})
    self.assertEqual(analizar(r), [])

def test_paleta_con_tokens_shadcn(self):  # Review Focus 1
    css = ":root{--background:#fff}\n@theme inline{--color-background:var(--background);}"
    r = proyecto(self.tmp, {"app.css": css, "a.tsx": 'cn("bg-gray-500 text-blue-600")'})
    self.assertEqual([a.codigo for a in analizar(r)], ["PALETA", "PALETA"])

def test_paleta_sin_semanticos_no_avisa(self):
    r = proyecto(self.tmp, {"a.html": 'class="bg-gray-500"'})
    self.assertEqual(analizar(r), [])

def test_paleta_anulada_no_avisa(self):
    css = "@theme{--color-*:initial;--color-label:#000;}"
    r = proyecto(self.tmp, {"app.css": css, "a.html": 'class="bg-gray-500"'})
    self.assertEqual(analizar(r), [])
```

- [ ] **Step 2: Ejecutar y ver que fallan** — mismo comando; Expected: FAIL en los cinco.

- [ ] **Step 3: Implementar `leer_tokens` y los detectores**

`leer_tokens`: declaraciones `--color-<nombre>` dentro de bloques `@theme` (con o sin `inline`). Un nombre es semántico si no coincide con `<color-de-paleta>-<50..950>`, `black`, `white` o `transparent`. Los colores de paleta son la lista de v4: slate, gray, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose. `paleta_anulada` = aparece `--color-*: initial`.
`V3`: `@tailwind` en CSS; existencia de `tailwind.config.{js,cjs,mjs,ts}` (aviso de proyecto, línea 0, solo si no hay `@config` que lo cargue); clases `(bg|text|border|divide|ring|placeholder)-opacity-\d+`, `flex-(shrink|grow)(-\d+)?\b`, `overflow-ellipsis`, `decoration-(slice|clone)`, `!` al inicio de una clase, `-\[--` (variable sin paréntesis).
`PALETA`: solo si `colores_semanticos` no está vacío y `paleta_anulada` es falso; prefijos de color + `<paleta>-<tono>`.

- [ ] **Step 4: Ejecutar y ver que pasan** — Expected: OK

- [ ] **Step 5: Commit** — `git commit -m "tailwind-apple-ui: avisos V3 y PALETA"`

### Task 3: Avisos de cristal, alternativas y oscuro

**Files:**
- Modify: `skills/tailwind-apple-ui/scripts/revisa_estilos.py`
- Modify: `tests/tailwind_apple_ui/test_revisa_estilos.py`

**Interfaces:**
- Consumes: `Aviso`, `recorrer`, `analizar`, `Tokens` (Tasks 1–2).
- Produces: `ES_CRISTAL = re.compile(r"\b(backdrop-blur(-[\w\[\]().%-]+)?|backdrop-filter|glass-[\w-]+)\b")`, que reutiliza la Task 4 para comprobar la plantilla.

- [ ] **Step 1: Tests que fallan**

```python
def test_cristal_anidado(self):
    html = '<nav class="glass-bar"><div class="backdrop-blur-md">x</div></nav>'
    self.assertIn("CRISTAL-ANIDADO", codigos(analizar(proyecto(self.tmp, {"a.html": html}))))

def test_cristal_en_contenido(self):
    html = '<li class="backdrop-blur">a</li><div class="card glass-panel">b</div>'
    self.assertEqual(codigos(analizar(proyecto(self.tmp, {"a.html": html}))).count("CRISTAL-CONTENIDO"), 2)

def test_cristal_jsx_classname(self):
    jsx = 'return <article className={cn("glass-panel")}>x</article>'
    self.assertIn("CRISTAL-CONTENIDO", codigos(analizar(proyecto(self.tmp, {"a.tsx": jsx}))))

def test_sin_alternativa_transparencia(self):
    r = proyecto(self.tmp, {"a.html": '<nav class="glass-bar"></nav>'})
    self.assertIn("SIN-ALT-TRANSP", codigos(analizar(r)))
    (r / "app.css").write_text("@media (prefers-reduced-transparency: reduce){.glass-bar{background:#fff}}")
    self.assertNotIn("SIN-ALT-TRANSP", codigos(analizar(r)))

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
```

- [ ] **Step 2: Ejecutar y ver que fallan** — Expected: FAIL en los seis.

- [ ] **Step 3: Implementar los detectores**

`CRISTAL-ANIDADO` y `CRISTAL-CONTENIDO`: `html.parser.HTMLParser` sobre cada fichero de marcado. Se lee `class` y `className` (incluido el texto dentro de `{…}`). Se mantiene una pila de etiquetas abiertas con un indicador de cristal; las etiquetas vacías y las autocerradas no se apilan, y los cierres que no cuadran se ignoran. Es contenido si la etiqueta es `article|li|td|p|img` o alguna clase contiene `card`.
`SIN-ALT-TRANSP`: hay cristal en algún fichero y la cadena `prefers-reduced-transparency` no aparece en ninguno (aviso de proyecto, línea 0).
`SIN-ALT-MOV`: hay `transition`, `animate-` o `@keyframes`, y no aparece `motion-reduce:`, `motion-safe:` ni `prefers-reduced-motion`.
`DARK-DISPERSO`: más de `umbral_dark` apariciones de `dark:` en ficheros que no son CSS (un aviso de proyecto con el recuento en `texto`).

- [ ] **Step 4: Ejecutar y ver que pasan** — Expected: OK (todos los tests de las Tasks 1–3).

- [ ] **Step 5: Probar a mano sobre un repo real si hay uno a mano; si no, sobre el propio repo**

Run: `python3 -I skills/tailwind-apple-ui/scripts/revisa_estilos.py . ; echo "salida=$?"`
Expected: sin trazas de error y `salida=0`.

- [ ] **Step 6: Commit** — `git commit -m "tailwind-apple-ui: avisos de cristal, alternativas y modo oscuro"`

### Task 4: Plantilla de anclas `theme.css`

**Files:**
- Create: `skills/tailwind-apple-ui/references/theme.css`
- Create: `tests/tailwind_apple_ui/compila_plantilla.sh`

**Interfaces:**
- Consumes: `revisa_estilos.py` (Tasks 1–3).
- Produces: estos nombres de token, que usan las referencias y el `SKILL.md`:
  - Colores: `label`, `label-secondary`, `label-tertiary`, `label-quaternary`, `background`, `background-secondary`, `background-tertiary`, `grouped-background`, `separator`, `fill`, `accent`, `red`, `orange`, `yellow`, `green`, `teal`, `blue`, `indigo`, `purple`, `pink`, `gray`.
  - Texto: `large-title`, `title-1`, `title-2`, `title-3`, `headline`, `body`, `callout`, `subheadline`, `footnote`, `caption-1`, `caption-2`, cada uno con `--line-height` y `--letter-spacing`.
  - Radios: `--radius-sm|md|lg|xl|2xl|full`. Sombras: `--shadow-sm|md|lg`.
  - Movimiento: `--ease-out-soft`, `--ease-spring`, `--duration-fast|base|slow`.
  - Utilidades: `glass-bar`, `glass-panel`, `glass-control`.

- [ ] **Step 1: Script de verificación que falla**

`compila_plantilla.sh` crea un directorio temporal y un `in.css` con `@import "tailwindcss"; @import "<ruta>/theme.css";`, más un `index.html` con `bg-background text-label glass-bar bg-gray-500 shadow-2xl`. Después ejecuta `npx -y @tailwindcss/cli@4 -i in.css -o out.css --content index.html` y comprueba:
- `out.css` contiene `.bg-background`, `.text-label` y `.glass-bar`;
- no contiene `.bg-gray-500` ni `.shadow-2xl` (paleta y sombras anuladas);
- contiene `prefers-reduced-transparency` y `@supports not`;
- `python3 -I skills/tailwind-apple-ui/scripts/revisa_estilos.py <tmp>` no saca `SIN-ALT-TRANSP`.

Run: `bash tests/tailwind_apple_ui/compila_plantilla.sh`
Expected: FAIL (no existe `theme.css`).

- [ ] **Step 2: Escribir `theme.css`**

Bloque `@theme` con `--color-*: initial;` y `--shadow-*: initial;` al principio, y luego los tokens de la lista. Los colores son los valores de sistema del HIG para claro (iOS: label `#000000`, secondaryLabel `rgb(60 60 67 / 0.6)`, systemBackground `#ffffff`, systemBlue `#007aff`…), y el oscuro se resuelve en las mismas variables con `@media (prefers-color-scheme: dark)` sobre `:root`. Por eso los tokens de `@theme` apuntan a variables de `:root` (patrón `@theme inline`). Cada valor del HIG lleva un comentario `/* HIG: <nombre> — verificar */`. `--accent` es `var(--blue)` por defecto, con un comentario «sustituir por el acento de marca». La escala tipográfica sale de los tamaños de Dynamic Type por defecto (large-title 34/41, body 17/22, caption-2 11/13, en px convertidos a rem), con tracking del HIG. `--font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
Los `@utility glass-*` usan `background: color-mix(in oklab, var(--background) 70%, transparent)`, `backdrop-filter: blur(..) saturate(180%)`, borde de 1 px semitransparente y brillo interior con `box-shadow: inset`. Llevan dos alternativas: `@supports not (backdrop-filter: blur(1px))` y `@media (prefers-reduced-transparency: reduce)`, ambas con fondo opaco `var(--background-secondary)`.
Cabecera con un comentario: qué es, que se usa en proyectos nuevos y que en proyectos con anclas propias se copian solo los bloques de materiales.

- [ ] **Step 3: Ejecutar la verificación** — Expected: todas las comprobaciones OK. Si no hay red para `npx`, indicarlo en el commit y no dar por buena la compilación.

- [ ] **Step 4: Commit** — `git commit -m "tailwind-apple-ui: plantilla de anclas theme.css"`

### Task 5: Referencias `cristal-web.md`, `anclaje.md` y `v3-a-v4.md`

**Files:**
- Create: `skills/tailwind-apple-ui/references/cristal-web.md`
- Create: `skills/tailwind-apple-ui/references/anclaje.md`
- Create: `skills/tailwind-apple-ui/references/v3-a-v4.md`

**Interfaces:**
- Consumes: los nombres de token y de utilidad de la Task 4; los códigos de aviso de las Tasks 1–3.

- [ ] **Step 1: `cristal-web.md`.** Incluye:
  - dónde sí y dónde no (las reglas del paso 3 del spec);
  - tabla de superficies: barra de navegación, toolbar, sheet o `<dialog>`, menú o `popover`, botón flotante, cada una con su utilidad `glass-*`;
  - receta para agrupar sin anidar;
  - contraste AA sobre cristal en claro y oscuro (comprobarlo con el fondo más claro y el más oscuro que pueda pasar por debajo);
  - rendimiento (`backdrop-filter` en pocas superficies, nunca en elementos que se repiten).

  Las fuentes son el HIG Materials y `apple-liquid-glass`, de la que solo se toman los principios. Cada regla enlaza al aviso del script que la vigila.
- [ ] **Step 2: `anclaje.md`.** Menú anclado a su botón con `popover` + `anchor-name`/`position-anchor`/`position-try-fallbacks`, escrito con clases y valores arbitrarios de Tailwind v4 o con `@utility`. Alternativa dentro de `@supports not (anchor-name: --a)`. Aviso de que es una API reciente y de que su sintaxis se comprueba en MDN antes de usarla.
- [ ] **Step 3: `v3-a-v4.md`.** Tabla de la guía oficial (`https://tailwindcss.com/docs/upgrade-guide`), comprobada en vivo al escribirla: directivas, config en CSS, renombrados (`shadow-sm`→`shadow-xs`, `shadow`→`shadow-sm`, `rounded-sm`→`rounded-xs`, `rounded`→`rounded-sm`, `outline-none`→`outline-hidden`, `ring`→`ring-3`, etc.), clases eliminadas (`*-opacity-*`, `flex-shrink-*`…), variables `(--x)`, `!` al final, color de borde por defecto y `@source`. Al final, una línea con la fecha de comprobación.
- [ ] **Step 4: Verificar enlaces y coherencia.** Run: `grep -ohE 'glass-[a-z]+|--color-[a-z-]+' skills/tailwind-apple-ui/references/*.md | sort -u`. Expected: todos los nombres existen en `theme.css`.
- [ ] **Step 5: Commit** — `git commit -m "tailwind-apple-ui: referencias de cristal, anclaje y migración"`

### Task 6: `SKILL.md` y `README.md` de la skill

**Files:**
- Create: `skills/tailwind-apple-ui/SKILL.md`
- Create: `skills/tailwind-apple-ui/README.md`

**Interfaces:**
- Consumes: rutas de las Tasks 1–5; uso exacto del script de la Task 1.

- [ ] **Step 1: `SKILL.md`.** Frontmatter:
  - `name: "tailwind-apple-ui"`;
  - `description`: estilo Apple y Liquid Glass en web con Tailwind CSS v4, con anclas en `@theme`. Úsala al construir, planificar o revisar estilos web con aspecto Apple o en un proyecto que ya lo use. No es para Expo ni React Native (para eso, `expo-apple-ui`).

  Cuerpo con los pasos 0 a 5 del spec (sección «`SKILL.md` (flujo)»), la tabla «quién manda en cada capa», las reglas de anclas y las reglas Apple. En el paso 0 van los cuatro casos: anclas propias, sin anclas, v3 o sin proyecto (modo diseño, sin instalar nada). Referencias cargadas solo cuando hagan falta. La lista de revisión final incluye ejecutar el script y explicar o corregir cada aviso. Sección de mantenimiento al estilo de `expo-apple-ui`. Menos de 200 líneas.
- [ ] **Step 2: `README.md`.** Mismo esquema que `skills/expo-apple-ui/README.md`: qué es, qué hace (4 puntos), opcionales (`apple-design`, `apple-liquid-glass`), instalación de esta skill sola y uso del script.
- [ ] **Step 3: Verificar.** Run: `head -4 skills/tailwind-apple-ui/SKILL.md && wc -l skills/tailwind-apple-ui/SKILL.md && grep -oE 'references/[a-z0-9-]+\.(md|css)|scripts/[a-z_]+\.py' skills/tailwind-apple-ui/SKILL.md | sort -u | xargs -I{} test -f skills/tailwind-apple-ui/{} && echo rutas-ok`. Expected: frontmatter correcto, menos de 200 líneas y `rutas-ok`.
- [ ] **Step 4: Commit** — `git commit -m "tailwind-apple-ui: SKILL.md y README"`

### Task 7: Alta en el repo

**Files:**
- Modify: `.claude-plugin/marketplace.json` (nueva entrada en `plugins`, `metadata.version` → `1.4.0`)
- Modify: `README.md` (fila en la tabla de skills, enlace al ZIP, mención en «Cambia `revisa-respuesta` por…», párrafo en «Uso»)

- [ ] **Step 1: Editar.** Entrada con el mismo patrón que `expo-apple-ui`: `"name": "tailwind-apple-ui"`, `"source": "./"`, `"strict": false` y `"skills": ["./skills/tailwind-apple-ui"]`. El párrafo de Uso: «en un proyecto web con Tailwind v4, pide algo como “haz esta barra con Liquid Glass” o escribe `/tailwind-apple-ui`…».
- [ ] **Step 2: Verificar.** Run: `python3 -c "import json;d=json.load(open('.claude-plugin/marketplace.json'));print(d['metadata']['version'],[p['name'] for p in d['plugins']])" && python3 -m unittest discover -s tests/tailwind_apple_ui`. Expected: `1.4.0 [..., 'tailwind-apple-ui']` y tests OK.
- [ ] **Step 3: Commit y push** — `git commit -m "tailwind-apple-ui: alta en marketplace y README" && git push`
