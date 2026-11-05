# claude-skills-es

Skills para Claude escritas en castellano. Funcionan en Claude Code, claude.ai y la app de escritorio.

## Skills

| Skill | Qué hace |
|---|---|
| [revisa-respuesta](skills/revisa-respuesta) | Audita la respuesta anterior contra sus fuentes (veracidad, claridad y exhaustividad), gradúa los fallos y entrega una versión corregida. |

## Instalar una sola skill

### Con la URL de su carpeta (Claude Code, Cursor y otros agentes)

```bash
npx skills add https://github.com/alcaudon89/claude-skills-es/tree/main/skills/revisa-respuesta
```

### Claude Code (marketplace de plugins)

```
/plugin marketplace add alcaudon89/claude-skills-es
/plugin install revisa-respuesta@claude-skills-es
```

Cada skill es un plugin independiente: se instala solo la que eliges.

### claude.ai y app de escritorio

1. Descarga el ZIP: [revisa-respuesta.zip](https://github.com/alcaudon89/claude-skills-es/releases/latest/download/revisa-respuesta.zip)
2. En Claude, ve a **Ajustes → Capacidades → Skills** y súbelo.

### A mano

Copia la carpeta `skills/revisa-respuesta` en `~/.claude/skills/`.

## Uso

Tras cualquier respuesta, pide «revisa tu respuesta» o escribe `/revisa-respuesta`. Claude comprueba cada afirmación contra su origen, puntúa veracidad, claridad y exhaustividad, lista los problemas por gravedad (🔴 🟠 🟡) y reescribe la respuesta corregida.

## Licencia

MIT
