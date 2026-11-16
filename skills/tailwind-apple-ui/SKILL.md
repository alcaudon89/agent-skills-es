---
name: "tailwind-apple-ui"
description: "Estilo Apple y Liquid Glass en web con Tailwind CSS v4, a partir de anclas de diseño en @theme (colores semánticos, tipografía tipo Dynamic Type, radios, materiales de cristal). Mantiene un patrón fijo, verifica la sintaxis v4 contra la documentación oficial y revisa los desvíos con un script. Úsala al construir, planificar o revisar estilos web con aspecto Apple o en un proyecto web que ya lo use. No es para Expo ni React Native (para eso, expo-apple-ui)."
---

# Tailwind v4 + Apple UI (web)

Este skill fija **de dónde sale cada estilo** (las anclas en `@theme`), cómo se aplica el criterio de Apple en web y cómo se comprueba que nada se ha salido del patrón. No copia la documentación de Tailwind: la sintaxis se verifica en vivo.

Referencias (cárgalas solo cuando hagan falta):

- `references/theme.css`: plantilla de anclas (colores, tipografía, radios, sombras, movimiento y utilidades `glass-*`).
- `references/cristal-web.md`: dónde va el cristal, cómo agruparlo, alternativas, contraste y rendimiento.
- `references/anclaje.md`: menús y popovers anclados a su control (CSS anchor positioning).
- `references/v3-a-v4.md`: trampas de sintaxis v3 → v4.
- `scripts/revisa_estilos.py`: revisión automática de desvíos.

## Paso 0: contexto del proyecto (siempre)

Busca `package.json` en la raíz y, si no está o no depende de `tailwindcss`, en subcarpetas (monorepos: `apps/*`, `packages/*`, `web/`…), sin entrar en `node_modules`. Lee la versión de `tailwindcss` y cómo se integra (`@tailwindcss/vite`, `@tailwindcss/postcss` o la CLI). Localiza el CSS de entrada, el que tiene `@import "tailwindcss"`. Si hay varias apps, pregunta cuál.

Según lo que encuentres:

**A. v4 con anclas propias** (`@theme` o `:root` con colores semánticos, sean de Apple o no: Material, shadcn con `--background`, una marca). **Mandan sus anclas.** No renombres nada ni anules la paleta por defecto. Añade solo lo que falte (casi siempre los materiales de cristal de `theme.css`, adaptados a sus nombres) y pide permiso antes.

**B. v4 sin anclas.** Propón `theme.css` adaptado: el acento de marca en `--accent` y, si la marca lo pide, la familia tipográfica. Explica que anula la paleta y las sombras por defecto, de modo que solo existan las clases semánticas (más `white` y `black`). Tailwind descarta en silencio las clases que no existen: `bg-gray-500` no da error, simplemente no pinta. Por eso el script lo marca. Escríbelo junto al CSS de entrada (`@import "./theme.css";` después de `@import "tailwindcss";`) cuando el usuario confirme.

**C. v3.** Dilo y ofrece `npx @tailwindcss/upgrade`. No escribas estilos v3 ni mezcles sintaxis. Tras la migración, vuelve al caso A o B.

**D. Sin proyecto o sin Tailwind** (repo de diseño, specs, ADR). No instales nada. Si un ADR descarta Tailwind, dilo y para. Si no, entrega las anclas y las decisiones como documento, donde el repo guarde las decisiones y con su formato: tokens, qué superficies llevan cristal, alternativas y requisitos de accesibilidad. Marca la sintaxis como «verificar al crear el proyecto».

## Paso 1: fuentes, por capa

| Capa | Manda | Vía |
|---|---|---|
| Sintaxis y API de Tailwind | Documentación oficial actual | Ver abajo |
| Valores de diseño | Anclas del proyecto; si no hay, `theme.css` | `@theme` |
| Qué lleva cristal y qué no | Criterio Liquid Glass de Apple | Skill `apple-liquid-glass` si está instalada (solo principios, su código es SwiftUI); si no, HIG Materials |
| Movimiento, materiales, tipografía | Criterio de Apple | Skill `apple-design` si está; si no, HIG Motion y Typography |
| Cómo se hace el cristal en web | Este skill | `references/cristal-web.md` |

**Documentación de Tailwind.** Para cada utilidad o directiva de la que no estés seguro, lee el MDX oficial y quédate con la primera vía que funcione:

1. Lectura directa: `https://raw.githubusercontent.com/tailwindlabs/tailwindcss.com/main/src/docs/<página>.mdx` (p. ej. `theme`, `upgrade-guide`, `backdrop-filter-blur`, `adding-custom-styles`).
2. Clon superficial, si hay shell: `git clone --depth=1 https://github.com/tailwindlabs/tailwindcss.com /tmp/tw-docs` y busca en `src/docs/`.
3. La web: `https://tailwindcss.com/docs/<página>`.

Si la ruta da 404, Tailwind ha reorganizado su repo: busca el equivalente y **avisa al usuario de que este skill está desfasado**. Sin red, usa `references/v3-a-v4.md` y dilo.

Antes de seguir, indica en una línea la versión de Tailwind del proyecto (o la objetivo en el caso D) y de dónde has leído la documentación.

## Paso 2: reglas de anclas

1. **Toda clase sale de un token.** Valor arbitrario (`bg-[#1c1c1e]`, `p-[13px]`) solo si no hay token y el valor es único, como la medida de un asset. Si se repite, conviértelo en token.
2. **Token nuevo, en `@theme`**, con nombre semántico: `--color-label-secondary`, no `--color-gris-3`. Nunca un token suelto en un componente.
3. **Colores siempre semánticos.** El modo oscuro se resuelve en las variables, no con `dark:` disperso por los componentes. `dark:` solo para excepciones puntuales.
4. **Modo oscuro por clase**, si el proyecto lo usa: declara una vez `@custom-variant dark (&:where(.dark, .dark *));` y cambia el `@media` de `theme.css` por `.dark { … }`.
5. **Patrones repetidos, en `@utility`** (como `glass-bar`), no cadenas de clases copiadas entre componentes.
6. **Espaciado con la escala de Tailwind** (`--spacing`, 4 px), coherente con la retícula de 4 y 8 pt de Apple. No inventes medidas intermedias.

## Paso 3: reglas de Apple en web

Detalle y ejemplos en `references/cristal-web.md`.

1. **Primero lo nativo de la web, después el cristal.** `<dialog>` para sheets y modales, `popover` para menús y `<details>` para desplegables. El cristal es un estilo encima.
2. **El cristal va en la capa de navegación y controles, no en el contenido.** Sí: barras, toolbars, sheets, menús y botones flotantes. No: tarjetas, celdas, texto e imágenes.
3. **Nada de cristal sobre cristal.** Varios controles juntos van en un único contenedor de cristal, y los de dentro sin material.
4. **Siempre con alternativa.** Superficie opaca sin `backdrop-filter` y con `prefers-reduced-transparency: reduce`. Las utilidades `glass-*` ya las traen.
5. **Contraste AA** del texto sobre cristal en claro y en oscuro, comprobado con el fondo más claro y el más oscuro que pueda pasar por debajo.
6. **El acento solo en lo interactivo.** No tiñas el cristal decorativo con la marca.
7. **Movimiento.** Si hay un dedo implicado, spring con la velocidad heredada (en JS, criterio de `apple-design`). Si no, `ease-(--ease-out-soft)` o `ease-(--ease-spring)` con `duration-(--duration-*)`. Entradas con `starting:`. `motion-reduce:` reduce el movimiento (fundido corto en lugar de desplazamiento), no lo elimina.
8. **Tipografía.** Pila `system-ui` (en Apple sale SF Pro sin embeberla) y escala `text-large-title` … `text-caption-2`. Nunca tamaños sueltos.

## Paso 4: menús y popovers anclados

Para menús, popovers y tooltips que salen de su control, usa CSS anchor positioning con la receta de `references/anclaje.md`: `@utility` con `anchor-name`, `position-anchor`, `position-area` y `position-try-fallbacks`, más una alternativa en `@supports not (anchor-name: --a)`. Es una API reciente: comprueba la sintaxis en MDN antes de usarla.

## Paso 5: revisión antes de entregar

Ejecuta el script sobre la app (no hace falta red; solo lee). Revisa `.html .js .jsx .ts .tsx .mjs .vue .svelte .astro .css` (incluidos los bloques `<style>`) y omite `node_modules` y las carpetas de build:

```bash
python3 -I <ruta-del-skill>/scripts/revisa_estilos.py <ruta-de-la-app>
```

Revisa cada aviso: corrígelo o explica por qué es un falso positivo. El script avisa pero no bloquea, y sus heurísticas pueden equivocarse.

| Aviso | Qué significa |
|---|---|
| `ARB` | Valor arbitrario de color o medida donde debería haber un token |
| `V3` | Sintaxis de v3 que no existe en v4 (`@tailwind`, `bg-opacity-*`, `bg-[--x]`, `!` delante, config JS sin `@config`) |
| `PALETA` | Color o sombra de la escala por defecto (`bg-gray-500`, `shadow-xl`) en un proyecto con anclas propias. Si la escala está anulada, avisa de que esa clase no genera CSS |
| `CRISTAL-ANIDADO` | Cristal dentro de cristal |
| `CRISTAL-CONTENIDO` | Cristal en `article`, `li`, `td`, `p`, `img` o en una tarjeta |
| `SIN-ALT-TRANSP` | Hay cristal y ninguna regla de `prefers-reduced-transparency` |
| `SIN-ALT-MOV` | Hay animaciones y ninguna alternativa de movimiento reducido |
| `DARK-DISPERSO` | Demasiados `dark:` en componentes (umbral con `--umbral-dark N`, 20 por defecto) |

Lista final:

- [ ] Versión de Tailwind y fuente de la documentación indicadas; sintaxis verificada o marcada para verificar
- [ ] Todas las clases salen de las anclas; los tokens nuevos están en `@theme` con nombre semántico
- [ ] Cristal solo en navegación y controles, sin anidar, con alternativas
- [ ] Contraste AA en claro y oscuro; Reducir transparencia y Reducir movimiento respetados
- [ ] Script ejecutado y cada aviso corregido o justificado
- [ ] Build del proyecto ejecutado y vista comprobada en navegador. Si no has podido, dilo y deja los pasos; no lo des por hecho

En el caso D, la entrega es el documento de decisiones: los puntos de código se escriben como requisitos, no se marcan como hechos.

## Mantenimiento de este skill

La sintaxis de Tailwind se lee en vivo, así que se actualiza sola. Este archivo y `theme.css` solo hay que tocarlos si Tailwind reorganiza su documentación (el Paso 1 lo detecta y avisa), si Apple cambia sus colores o su escala tipográfica (los valores llevan «verificar» en `theme.css`) o si cambian las reglas de choque. `references/v3-a-v4.md` lleva la fecha de su última comprobación.
