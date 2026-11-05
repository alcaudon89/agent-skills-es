# revisa-respuesta

Audita la última respuesta de Claude (resumen, análisis, explicación, código…) contra sus fuentes y entrega una versión corregida.

**Qué devuelve**

1. Veredicto en una frase.
2. Notas de 1 a 5 en veracidad, claridad y exhaustividad.
3. Problemas ordenados por gravedad: 🔴 crítico, 🟠 importante, 🟡 menor.
4. Afirmaciones no verificables.
5. Versión mejorada con la lista de cambios aplicados.

**Instalar solo esta skill**

```bash
npx skills add https://github.com/alcaudon89/agent-skills-es/tree/main/skills/revisa-respuesta
```

En claude.ai: descarga [revisa-respuesta.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/revisa-respuesta.zip) y súbelo en Ajustes → Capacidades → Skills.

Más opciones en el [README principal](../../README.md).
