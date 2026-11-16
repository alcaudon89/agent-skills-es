# Menús y popovers anclados (CSS anchor positioning)

En Apple, un menú sale del control que lo abre y se recoloca solo si no cabe. En web eso se consigue con **CSS anchor positioning**, sin JS para calcular posiciones.

Es una API reciente: MDN la marca como *Baseline 2026* (funciona en las últimas versiones de los navegadores principales desde enero de 2026), pero algunas partes tienen soporte desigual. **Antes de usarla, comprueba la sintaxis y el soporte en MDN** (`https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning/Using`) y deja siempre la alternativa de abajo.

## Piezas

| Propiedad | Va en | Para qué |
|---|---|---|
| `anchor-name: --nombre` | el control | Lo declara ancla |
| `position-anchor: --nombre` | el menú | A qué ancla se pega |
| `position-area: bottom span-right` | el menú | Dónde se coloca respecto al ancla |
| `position-try-fallbacks: flip-block` | el menú | Alternativas si no cabe (se prueban en orden) |
| `@position-try --x { … }` | CSS | Alternativa a medida |

Con `popover` + `popovertarget`, el navegador crea un ancla implícita entre el botón y el popover. Para usarla hay que dar `position-anchor: auto` al popover y quitar los estilos que trae por defecto (`inset`, `margin`). Si no, el popover sale centrado.

## Receta con Tailwind v4

Las propiedades de anclaje no tienen utilidades propias en Tailwind. Ponlas en un `@utility` para no repetir valores arbitrarios por los componentes:

```css
/* En el CSS de entrada, junto a las anclas */
@utility anchor-menu-trigger {
  anchor-name: --menu;
}

@utility anchor-menu {
  position: fixed;
  inset: auto;
  margin: 0;
  position-anchor: --menu;
  position-area: bottom span-right;
  position-try-fallbacks: flip-block;
  margin-block-start: --spacing(2);
  /* Alternativa sin anchor positioning: debajo del botón, en flujo normal */
  @supports not (anchor-name: --a) {
    position: absolute;
    top: 100%;
    left: 0;
  }
}
```

```html
<div class="relative">
  <button popovertarget="menu" class="anchor-menu-trigger glass-control px-4 py-2 text-accent">
    Opciones
  </button>
  <div id="menu" popover class="anchor-menu glass-panel min-w-48 p-1">
    <button class="w-full rounded-md px-3 py-2 text-left text-body text-label hover:bg-fill">Renombrar</button>
    <button class="w-full rounded-md px-3 py-2 text-left text-body text-red hover:bg-fill">Eliminar</button>
  </div>
</div>
```

Notas:

- Si hay varios menús en la misma página, cada pareja necesita su propio nombre de ancla (`--menu-perfil`, `--menu-orden`). También puedes usar `anchor-scope` para limitar el nombre a un componente.
- El menú lleva `glass-panel` y sus filas **no** llevan cristal (regla de no anidar).
- Entrada con `starting:opacity-0 starting:scale-95 transition duration-(--duration-fast) ease-(--ease-out-soft)` y `motion-reduce:starting:scale-100`: con movimiento reducido el menú solo hace el fundido, sin escalar.
- La alternativa sin soporte necesita que el contenedor sea `relative`. En navegadores sin anchor positioning, un `popover` sale en la capa superior y no respeta `relative`. Si eso importa, la alternativa razonable es un `<details>` o un menú sin `popover`.
