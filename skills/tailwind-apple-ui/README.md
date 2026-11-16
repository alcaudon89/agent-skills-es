# tailwind-apple-ui

Skill para dar estilo Apple a proyectos web con Tailwind CSS v4: colores semánticos con modo oscuro, tipografía tipo Dynamic Type, Liquid Glass esmerilado y menús anclados a su control.

Su objetivo es que el agente no se pierda: todo estilo sale de unas **anclas** en `@theme`, se aplican siempre las mismas reglas y un script revisa los desvíos antes de entregar. La sintaxis de Tailwind no va copiada en la skill: se comprueba en vivo en la documentación oficial.

**Qué hace**

1. Mira el proyecto: versión de Tailwind, CSS de entrada y si ya tiene anclas propias. Si las tiene, las respeta y solo añade lo que falte. Si no, propone la plantilla `references/theme.css`. Si el proyecto va en v3, ofrece la migración oficial.
2. Aplica las reglas de anclas: nada de valores sueltos, tokens nuevos en `@theme` con nombre semántico y el modo oscuro resuelto en las variables.
3. Aplica los criterios de Apple en web: cristal solo en navegación y controles, nunca anidado, siempre con alternativa opaca, contraste AA y movimiento reducido respetado.
4. Ejecuta `scripts/revisa_estilos.py` y corrige o justifica cada aviso.

**Opcional:** si tienes las skills `apple-design` y `apple-liquid-glass`, usa su criterio. Si no, recurre al HIG de Apple.

**El script por su cuenta**

```bash
python3 -I scripts/revisa_estilos.py ruta/de/la/app
```

Usa solo la librería estándar de Python (3.10+) y no modifica nada. Admite `--json` y `--umbral-dark N`. Los avisos son orientativos: sus heurísticas pueden dar falsos positivos.

**Instalar solo esta skill**

```bash
npx skills add https://github.com/alcaudon89/agent-skills-es/tree/main/skills/tailwind-apple-ui
```

En claude.ai o la app de escritorio: descarga [tailwind-apple-ui.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/tailwind-apple-ui.zip) y súbelo en Personalizar → Skills → + → Crear skill → Subir una skill.

Más opciones en el [README principal](../../README.md).
