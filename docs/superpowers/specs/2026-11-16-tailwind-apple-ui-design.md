# Diseño: skill `tailwind-apple-ui`

Fecha: 2026-11-16 · Estado: borrador para aprobación

## Intención

Que Claude Code, al escribir estilos con Tailwind CSS v4 en proyectos web, siga siempre el mismo patrón y no se pierda: todo estilo sale de unas **anclas de diseño** claras (tokens en `@theme`), y se aplica lo que Apple recomienda para su lenguaje visual y para Liquid Glass, traducido a la web.

Es el equivalente web de `expo-apple-ui`: puente entre la fuente técnica (Tailwind v4, leída en vivo) y el criterio Apple, con reglas propias para resolver choques.

## Por qué

- Los modelos escriben Tailwind v3 por inercia (`tailwind.config.js`, `@tailwind base`, nombres antiguos) y rellenan con valores arbitrarios (`bg-[#1c1c1e]`, `p-[13px]`), así que el sistema visual se degrada pantalla a pantalla.
- `apple-design` ya trae criterio web (movimiento, materiales, tipografía) pero no Tailwind. `apple-liquid-glass` es solo SwiftUI. Nadie traduce Liquid Glass a CSS/Tailwind con reglas fijas.
- No existe skill oficial de Tailwind ni `llms.txt`; las skills de la comunidad cubren sintaxis v4, no un sistema de anclas con criterio Apple.

## Objetivos

1. Un **sistema de anclas** cerrado en `@theme` del que sale toda clase: colores semánticos (con oscuro), tipografía, espaciado, radios, sombras, materiales de cristal, movimiento.
2. **Reglas Apple** aplicadas a la web: cristal solo en navegación y controles, sin cristal anidado, acento solo en lo interactivo, accesibilidad de la transparencia y del movimiento.
3. **Sintaxis v4 correcta**, verificada contra la documentación oficial actual.
4. **Comprobación automática** con un script que avisa de desvíos antes de entregar.
5. Apartado de **CSS anchor positioning** para menús, popovers y tooltips anclados a su control.

## No objetivos

- Expo/React Native/NativeWind (lo cubre `expo-apple-ui`).
- Tailwind v3: si el proyecto está en v3, se avisa y se ofrece la migración oficial; no se escriben estilos v3.
- Copiar la marca, logos, SF Pro o iconos de Apple. Se imita el criterio, no los activos. SF Pro solo vía `system-ui`/`-apple-system` (la fuente del sistema del usuario), nunca embebida.
- Componentes JS (React, Vue…). La skill gobierna estilos; el marco de componentes es el del proyecto.

## Antiobjetivos (fracaso aunque «funcione»)

- Cristal en tarjetas, celdas o bloques de texto.
- Valores arbitrarios donde existe token, o tokens nuevos inventados por pantalla sin pasar por `@theme`.
- Texto sobre cristal que no cumple contraste AA en claro y oscuro.
- Duplicar la plantilla de anclas en un proyecto que ya tiene las suyas.

## Restricciones

- Estándar Agent Skills, en castellano, mismo formato que el resto del repo (`SKILL.md` con frontmatter `name`/`description`, `README.md`, `references/`, `scripts/`).
- Script en Python, solo librería estándar, ejecutable con `python3 -I`.
- Debe funcionar sin red (plantilla y reglas en local); la lectura en vivo de docs de Tailwind es una mejora, no un requisito.
- Soporte de navegador desigual: `backdrop-filter` (general), `prefers-reduced-transparency` (no en todos los navegadores), anchor positioning (no en todos). Siempre con alternativa.

## Enfoques considerados

| Enfoque | Qué es | A favor | En contra |
|---|---|---|---|
| A. Puente puro | Solo reglas; sintaxis en vivo de Tailwind y criterio de `apple-design`/`apple-liquid-glass`. Cada proyecto define sus anclas | Mínimo mantenimiento | Claude define las anclas de cero cada vez: justo donde se pierde |
| B. Reglas + plantilla | A más un `theme.css` de partida con anclas Apple | Patrón idéntico entre proyectos | Mantener la plantilla |
| **C. B + script** (elegido) | B más `revisa_estilos.py` que detecta desvíos | La consistencia se comprueba, no se confía | Más código; regex da falsos positivos → solo avisa |

Elegido C por el usuario: el objetivo es consistencia y solo se garantiza si se comprueba.

## Decisiones tomadas

- **Usuario:** proyectos web; anclas = tokens de diseño como núcleo; anchor positioning como apartado; enfoque C.
- **Mías (revisables):**
  - Nombre `tailwind-apple-ui`.
  - Paleta por defecto = colores de sistema de Apple (valores públicos del HIG, en claro y oscuro); la marca sustituye `--color-accent` y lo que el proyecto ya tenga.
  - El script avisa, no bloquea (código de salida 0 con avisos; 1 solo si no puede leer ficheros).

## Diseño

### Estructura

```
skills/tailwind-apple-ui/
├── SKILL.md
├── README.md
├── references/
│   ├── theme.css              # plantilla de anclas (@theme + modo oscuro + materiales)
│   ├── cristal-web.md         # Liquid Glass traducido a CSS/Tailwind: dónde sí, dónde no, recetas
│   ├── anclaje.md             # CSS anchor positioning con Tailwind v4, con alternativa
│   └── v3-a-v4.md             # trampas de sintaxis y renombrados v3 → v4
└── scripts/
    └── revisa_estilos.py
```

### `SKILL.md` (flujo)

**Paso 0. Contexto.** Localizar `package.json` (raíz y subcarpetas de monorepo, sin `node_modules`). Leer versión de `tailwindcss` e integración (`@tailwindcss/vite`, `@tailwindcss/postcss`, CLI). Encontrar el CSS de entrada (`@import "tailwindcss"`). Casos:
- v4 con `@theme` propio → **mandan sus anclas**; solo se añaden las que falten (p. ej. materiales de cristal), con permiso.
- v4 sin anclas → proponer la plantilla adaptada (acento de marca) y escribirla tras confirmación.
- v3 → avisar, ofrecer `npx @tailwindcss/upgrade`, no mezclar.
- Sin Tailwind / sin proyecto → modo diseño: producir las anclas y decisiones como documento, sin instalar nada.

**Paso 1. Fuentes, por capa.**

| Capa | Manda | Vía |
|---|---|---|
| Sintaxis y API de Tailwind | Docs oficiales actuales | Clon superficial de `tailwindlabs/tailwindcss.com` o raw del MDX de la utilidad; si no hay red, `references/v3-a-v4.md` y avisar |
| Valores de diseño | Anclas del proyecto, si no plantilla | `@theme` |
| Qué lleva cristal | Criterio Liquid Glass de Apple | `apple-liquid-glass` si está; si no, HIG Materials |
| Movimiento, materiales, tipografía | `apple-design` | Si no está, HIG Motion/Typography |
| Cómo se hace el cristal en web | Esta skill | `references/cristal-web.md` |

Indicar en una línea qué versión de Tailwind tiene el proyecto y de dónde se leyó la documentación.

**Paso 2. Reglas de anclas.**
1. Toda clase sale de un token. Valor arbitrario solo si no hay token y es único (medida de un asset); si se repite, se convierte en token.
2. Token nuevo → en `@theme`, con nombre semántico (`--color-label-secondary`, no `--color-gris-3`).
3. Colores siempre semánticos; el oscuro se resuelve en las variables, no con `dark:` disperso por los componentes.
4. Variante oscura declarada una vez con `@custom-variant` si el proyecto usa clase; si no, `prefers-color-scheme`.
5. Patrones repetidos → `@utility` (p. ej. `glass-bar`), no cadenas de clases copiadas.

**Paso 3. Reglas Apple en web.** (detalle en `cristal-web.md`)
1. Primero lo nativo de la web (`<dialog>`, `popover`, `<details>`), luego el cristal.
2. Cristal solo en navegación y controles flotantes: barras, toolbars, sheets, menús, popovers. Nunca contenido.
3. Sin cristal sobre cristal: agrupar en un contenedor de cristal único.
4. Siempre alternativa: sin `backdrop-filter` → superficie opaca; `prefers-reduced-transparency: reduce` → opaca; contraste AA en claro y oscuro.
5. Acento solo en elementos interactivos.
6. Movimiento: criterio de `apple-design` (springs para lo que toca el dedo, ease-out para el resto, `@starting-style`/`starting:` para entradas), con `motion-reduce:` que reduce, no elimina.
7. Tipografía: pila `system-ui`, escala de la plantilla, tracking según tamaño.

**Paso 4. Anclaje (anchor positioning).** Menús y popovers anclados al control que los abre (`anchor-name`, `position-anchor`, `position-try`), con detección `@supports (anchor-name: --x)` y alternativa de posicionamiento clásico. Detalle en `anclaje.md`; sintaxis verificada en vivo (MDN) por ser reciente.

**Paso 5. Revisión.** Ejecutar `python3 -I scripts/revisa_estilos.py <ruta-del-proyecto>`, revisar cada aviso (corregir o justificar falso positivo), y repasar la lista: anclas usadas, cristal solo en la capa correcta, alternativas, contraste, movimiento reducido, build ejecutado (o decir que no se pudo).

### `references/theme.css`

`@theme` con: `--color-*` semánticos (label ×4, background ×3, grouped background, separator, fill, accent y los de sistema: red, green, blue…), con oscuro; `--font-sans` en pila del sistema y escala tipográfica inspirada en Dynamic Type (large-title … caption2) con `--text-*--line-height` y `--text-*--letter-spacing`; `--radius-*`; `--shadow-*`; materiales `--glass-*` (fondo translúcido, blur, borde, brillo) y sus alternativas opacas; `--ease-*` y `--duration-*`. Más `@utility glass-*` y el bloque de alternativas para `prefers-reduced-transparency` y `@supports not (backdrop-filter: …)`. Valores de color tomados del HIG; marcados en comentario como «verificar contra HIG» si cambian.

### `scripts/revisa_estilos.py`

Recorre `.html .jsx .tsx .vue .svelte .astro .css` (excluye `node_modules`, `dist`, `.next`, `build`). Avisos, con fichero:línea:

| Código | Detecta |
|---|---|
| `ARB` | Valor arbitrario de color/medida (`-[#…]`, `-[13px]`, `-[rgb(…)]`) |
| `V3` | Sintaxis v3: `@tailwind`, `tailwind.config.*`, `bg-[--var]`, `!` delante, renombrados (`shadow-sm` antiguo, `outline-none`, `flex-shrink-*`, `bg-opacity-*`…) |
| `PALETA` | Colores de paleta cruda (`bg-gray-500`, `text-blue-600`) donde la plantilla define semánticos — solo si el proyecto tiene `@theme` con semánticos |
| `CRISTAL-ANIDADO` | Elemento con `backdrop-blur`/`glass-*` dentro de otro en el mismo fichero (heurística) |
| `CRISTAL-CONTENIDO` | `backdrop-blur`/`glass-*` en `article`, `li`, `td`, `p`, `img` o clases tipo `card` |
| `SIN-ALT-TRANSP` | Hay cristal y no hay regla `prefers-reduced-transparency` en el CSS |
| `SIN-ALT-MOV` | Hay animaciones/transiciones y ningún `motion-reduce:` ni `prefers-reduced-motion` |
| `DARK-DISPERSO` | Más de N usos de `dark:` en componentes (umbral configurable) |

Salida agrupada por código con recuento y la ruta del CSS de entrada detectado. Opción `--json`. Sin dependencias.

### Integración en el repo

- `marketplace.json`: entrada `tailwind-apple-ui`, versión 1.4.0.
- README principal: fila en la tabla, enlace al ZIP, línea en Uso.
- Workflow de release: sin cambios (empaqueta cualquier carpeta de `skills/`).

## Queda al constructor

- Valores exactos de la escala tipográfica y de los materiales (con fuente citada).
- Lista concreta de renombrados v3→v4 (de la guía oficial).
- Heurísticas finas del script y su umbral por defecto.
- Pruebas del script: fixtures mínimos con casos que deben avisar y que no.
