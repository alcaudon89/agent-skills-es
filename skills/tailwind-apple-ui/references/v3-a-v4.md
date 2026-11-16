# Trampas de Tailwind v3 a v4

Resumen de la guía oficial (`https://tailwindcss.com/docs/upgrade-guide`) para no escribir v3 por inercia. Para migrar un proyecto entero, usa `npx @tailwindcss/upgrade`. No migres a mano.

Requisitos de v4: Safari 16.4+, Chrome 111+ y Firefox 128+ (usa `@property` y `color-mix()`).

## Configuración

| v3 | v4 |
|---|---|
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` |
| `tailwind.config.js` (`theme.extend`) | Variables en `@theme { … }` dentro del CSS |
| Config JS detectada sola | Solo se carga con `@config "./tailwind.config.js";` (último recurso) |
| `content: [...]` | Detección automática; `@source "…"` para rutas que no detecta |
| `@layer utilities { .x {…} }` | `@utility x { … }` |
| `theme('colors.red.500')` | `var(--color-red-500)`; en media queries, `theme(--breakpoint-xl)` |
| `prefix: 'tw-'` | `@import "tailwindcss" prefix(tw);` → `tw:flex` |
| `container: { center, padding }` | `@utility container { margin-inline: auto; padding-inline: 2rem; }` |
| `@apply` en Vue o Svelte sin más | `@reference "../app.css";` antes de `@apply` |

## Renombrados

Las clases de la izquierda **siguen existiendo** en v4, pero con otro tamaño. Por eso el script no las marca. Si migras código v3, cámbialas con cuidado.

| v3 | v4 |
|---|---|
| `shadow-sm` | `shadow-xs` |
| `shadow` | `shadow-sm` |
| `drop-shadow-sm` | `drop-shadow-xs` |
| `drop-shadow` | `drop-shadow-sm` |
| `blur-sm` | `blur-xs` |
| `blur` | `blur-sm` |
| `backdrop-blur-sm` | `backdrop-blur-xs` |
| `backdrop-blur` | `backdrop-blur-sm` |
| `rounded-sm` | `rounded-xs` |
| `rounded` | `rounded-sm` |
| `outline-none` | `outline-hidden` (el nuevo `outline-none` pone `outline-style: none`) |
| `ring` (3 px) | `ring-3` (`ring` ahora es 1 px) |

Con la plantilla de esta skill, las sombras y los radios ya los define `theme.css`. Usa sus nombres (`shadow-sm|md|lg` y `rounded-sm…2xl`), no los de Tailwind.

## Eliminadas (el script avisa con `V3`)

| v3 | v4 |
|---|---|
| `bg-opacity-*`, `text-opacity-*`, `border-opacity-*`, `divide-opacity-*`, `ring-opacity-*`, `placeholder-opacity-*` | Modificador de opacidad: `bg-label/50` |
| `flex-shrink-*` / `flex-grow-*` | `shrink-*` / `grow-*` |
| `overflow-ellipsis` | `text-ellipsis` |
| `decoration-slice` / `decoration-clone` | `box-decoration-slice` / `box-decoration-clone` |

## Sintaxis

| v3 | v4 |
|---|---|
| `bg-[--brand]` | `bg-(--brand)` |
| `!flex` (importante delante) | `flex!` (detrás; el de delante está obsoleto) |
| `first:*:pt-0` (variantes de derecha a izquierda) | `*:first:pt-0` (de izquierda a derecha) |

## Cambios de comportamiento por defecto

- **Color de borde:** antes `gray-200`, ahora `currentColor`. Pon siempre el color: `border border-separator`.
- **Ring:** antes 3 px y azul, ahora 1 px y `currentColor`.
- **Placeholder:** antes `gray-400`, ahora el color del texto al 50%.
- **Cursor en botones:** ahora `default`. Si quieres `pointer`, ponlo en `@layer base`.
- **`space-*` y `divide-*`:** ahora usan `:not(:last-child)` y margen inferior. Mejor usa `flex`/`grid` con `gap`.
- **`hover:`** solo se aplica en dispositivos con hover (`@media (hover: hover)`).
- **`transition`** también anima `outline-color`: pon el color de outline fijo, no solo en `hover:`.
- **Degradados con variantes:** ya no reinician todo el degradado; usa `via-none` para quitar el punto medio.

Comprobado contra la guía oficial el 2026-11-16 (Tailwind 4.3.5).
