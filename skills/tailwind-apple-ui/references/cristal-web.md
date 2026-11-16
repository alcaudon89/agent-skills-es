# Liquid Glass en web con Tailwind v4

Traducción a CSS del criterio de Apple para materiales y Liquid Glass. En web se hace con **cristal esmerilado**: `backdrop-filter` con blur y saturación, un borde fino y un brillo interior. La refracción real (filtros SVG en `backdrop-filter`) queda fuera: solo funciona en Chromium y es frágil.

Fuentes del criterio: HIG «Materials» (`https://developer.apple.com/design/human-interface-guidelines/materials`) y, si está instalada, la skill `apple-liquid-glass`. De esa skill se toman los principios, no el código SwiftUI.

## Dónde sí y dónde no

El cristal es una capa funcional que flota **sobre** el contenido. No es decoración.

| Superficie | ¿Cristal? | Utilidad |
|---|---|---|
| Barra de navegación o cabecera fija | Sí | `glass-bar` |
| Toolbar o barra inferior | Sí | `glass-bar` |
| Sheet o `<dialog>` que sube desde abajo | Sí | `glass-panel` |
| Menú o `popover` | Sí | `glass-panel` |
| Botón flotante, control segmentado flotante | Sí | `glass-control` |
| Tarjeta de contenido | **No** → `bg-background-secondary` | aviso `CRISTAL-CONTENIDO` |
| Celda de lista, fila de tabla | **No** → `bg-background` | aviso `CRISTAL-CONTENIDO` |
| Bloque de texto, imagen, vídeo | **No** | aviso `CRISTAL-CONTENIDO` |

Antes de construir una superficie de cristal, usa lo que la web ya trae: `<dialog>` para sheets y modales, `popover` para menús y `<details>` para desplegables. El cristal se pone encima, como estilo.

## Nada de cristal sobre cristal

Dos capas de `backdrop-filter` apiladas se ven turbias y cuestan el doble. Si varios controles de cristal conviven, agrúpalos en **un único** contenedor de cristal y deja los de dentro sin material:

```html
<!-- Mal: cristal anidado (aviso CRISTAL-ANIDADO) -->
<div class="glass-panel flex gap-2 p-2">
  <button class="glass-control px-4 py-2">Editar</button>
  <button class="glass-control px-4 py-2">Compartir</button>
</div>

<!-- Bien: un contenedor, botones sin material -->
<div class="glass-panel flex gap-2 p-2">
  <button class="rounded-full px-4 py-2 text-accent hover:bg-fill">Editar</button>
  <button class="rounded-full px-4 py-2 text-accent hover:bg-fill">Compartir</button>
</div>
```

## Siempre con alternativa

Las utilidades `glass-*` de `theme.css` ya incluyen las dos:

- **Sin soporte de `backdrop-filter`** (`@supports not`): fondo opaco `--glass-opaque`.
- **Reducir transparencia** (`prefers-reduced-transparency: reduce`): fondo opaco y sin blur. No todos los navegadores exponen esta preferencia. Donde no existe, se queda el cristal, así que el contraste tiene que cumplir de todas formas.

Si escribes cristal a mano, fuera de las utilidades, copia ese patrón. El aviso `SIN-ALT-TRANSP` salta si en el proyecto hay cristal y ninguna regla para `prefers-reduced-transparency`.

## Contraste

El texto sobre cristal tiene que cumplir **WCAG AA** (4,5:1 en texto normal y 3:1 en texto grande y en iconos) en claro y en oscuro. Compruébalo con lo peor que pueda pasar por debajo: el fondo más claro y el más oscuro del contenido que se desplaza bajo la barra. Si no llega:

1. Sube la opacidad del tinte (`--glass-tint`, del 72% hacia el 85%).
2. Usa `text-label` y no `text-label-secondary` sobre el cristal.
3. Como último recurso, usa el fondo opaco.

## Tinte y acento

El color de acento (`text-accent`, `bg-accent`) va **solo** en elementos interactivos: botones, enlaces, el estado seleccionado. No tiñas el cristal decorativo con la marca: el tinte del material sale del fondo (`--glass-tint`).

## Movimiento de las superficies de cristal

- Las entradas de sheets y popovers con `starting:` (o `@starting-style`) y `transition` usan `ease-(--ease-out-soft)` y `duration-(--duration-base)`.
- Si la superficie se arrastra (un sheet con el dedo), se usa un spring con la velocidad heredada. El criterio está en `apple-design`; en CSS no se puede, hace falta JS.
- `motion-reduce:` reduce el movimiento: cambia el desplazamiento por un fundido corto, no lo elimina del todo. El aviso `SIN-ALT-MOV` salta si hay animaciones y ninguna alternativa.

## Rendimiento

- `backdrop-filter` en **pocas** superficies: las fijas y las flotantes. Nunca en elementos que se repiten (listas, rejillas).
- No animes `backdrop-filter` ni el blur. Anima `opacity` y `transform` de la superficie.
- Evita el cristal en elementos muy grandes que cubren toda la pantalla mientras se desplaza contenido pesado (vídeo, canvas).
