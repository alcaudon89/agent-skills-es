# agent-skills-es

Skills en castellano para agentes de IA. Siguen el estándar abierto [Agent Skills](https://agentskills.io), así que funcionan en Claude (web, escritorio y Claude Code) y en otros agentes compatibles como Codex, Cursor, Gemini CLI o GitHub Copilot.

## Skills

| Skill | Qué hace |
|---|---|
| [revisa-respuesta](skills/revisa-respuesta) | Audita la respuesta anterior contra sus fuentes (veracidad, claridad y exhaustividad), gradúa los fallos y entrega una versión corregida. |
| [verifica-correo](skills/verifica-correo) | Analiza un correo recibido (phishing, suplantación, BEC, malware, fraude B2B) y verifica si el remitente es una contraparte fiable. Análisis orientativo hecho por IA. |
| [expo-apple-ui](skills/expo-apple-ui) | UI estilo Apple en apps Expo/React Native (Liquid Glass, movimiento fluido, controles nativos). Lee en vivo los skills oficiales de Expo y resuelve los choques con los criterios de Apple. |

## Instalación

Cada skill se instala por separado: elige solo las que quieras.

### Claude (claude.ai, app de escritorio)

Para usar las skills en el chat de Claude, sin Claude Code:

1. Descarga el ZIP de la skill desde la [última release](https://github.com/alcaudon89/agent-skills-es/releases/latest):
   - [revisa-respuesta.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/revisa-respuesta.zip)
   - [verifica-correo.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/verifica-correo.zip)
   - [expo-apple-ui.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/expo-apple-ui.zip)
2. Comprueba que tienes activada la ejecución de código: **Ajustes → Capacidades → Ejecución de código y creación de archivos** (en la versión nueva de Ajustes se llama **Crear y editar archivos**).
3. Ve a **Personalizar → Skills**, pulsa **+**, luego **Crear skill → Subir una skill**, y elige el ZIP **sin descomprimirlo**.
4. La skill aparece en tu lista; comprueba que está activada.

Disponible en los planes Free, Pro, Max, Ultra, Team y Enterprise. En Team y Enterprise, un administrador debe tener activadas las skills en **Ajustes de la organización → Plugins y skills**. Las skills que subes son privadas: nadie más las ve salvo que las compartas.

Para usarla no hace falta nada especial: pide lo que hace la skill (por ejemplo, «revisa tu respuesta») y Claude la carga sola.

### Claude Code (marketplace de plugins)

```
/plugin marketplace add alcaudon89/agent-skills-es
/plugin install revisa-respuesta@agent-skills-es
```

Cambia `revisa-respuesta` por `verifica-correo` o `expo-apple-ui` para instalar las otras.

### Otros agentes (Codex, Cursor, Gemini CLI, Copilot…) o Claude Code

Pega la URL de la carpeta de la skill:

```bash
npx skills add https://github.com/alcaudon89/agent-skills-es/tree/main/skills/revisa-respuesta
```

### A mano

Copia la carpeta de la skill (por ejemplo, `skills/revisa-respuesta`) en la carpeta de skills de tu agente; en Claude Code es `~/.claude/skills/`.

## Uso

**revisa-respuesta**: tras cualquier respuesta, pide «revisa tu respuesta» o escribe `/revisa-respuesta`. Claude comprueba cada afirmación contra su origen, puntúa veracidad, claridad y exhaustividad, lista los problemas por gravedad (🔴 🟠 🟡) y reescribe la respuesta corregida.

**verifica-correo**: adjunta el `.eml` (o pega el código fuente) y pregunta «¿es fiable este correo?» o escribe `/verifica-correo`. Si no conoce tu empresa, te hará unas preguntas de contexto antes de analizar. Es un análisis de IA orientativo: puede contener errores.

**expo-apple-ui**: en un proyecto Expo, pide algo como «haz esta pantalla con Liquid Glass» o escribe `/expo-apple-ui`. Lee el SDK del proyecto, carga la versión actual de los skills oficiales de Expo y aplica las reglas de Apple: cristal solo en navegación y controles, alternativas para iOS < 26 y Android, y accesibilidad de la transparencia.

## Licencia

MIT
