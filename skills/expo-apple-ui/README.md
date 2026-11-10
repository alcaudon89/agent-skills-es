# expo-apple-ui

Skill puente para construir UI estilo Apple en apps Expo/React Native: Liquid Glass, movimiento fluido, sheets, tabs y controles nativos.

No copia nada de Expo. En cada uso lee los [skills oficiales de Expo](https://github.com/expo/skills) en su versión actual y les añade lo que no cubren: qué lleva cristal y qué no, qué se muestra donde no hay Liquid Glass (iOS < 26, Android, web) y la accesibilidad de la transparencia.

**Qué hace**

1. Mira el SDK de Expo del proyecto y carga solo los skills de Expo que la tarea necesita (`expo-native-ui`, `expo-ui`, `expo-router`, `expo-animation`, `expo-design-system`).
2. Decide qué fuente manda en cada capa: Expo para las APIs y los criterios de Apple para el diseño.
3. Aplica las reglas de choque, por ejemplo: el cristal solo en navegación y controles, nunca en el contenido.
4. Repasa una lista de comprobación antes de entregar.

Si Expo reorganiza su repo, el skill encuentra los nombres nuevos y avisa de que hay que actualizar la tabla.

**Opcional:** si tienes skills de criterio Apple (`apple-liquid-glass`, `apple-design`), los usa. Si no, recurre a la documentación oficial de Apple.

**Instalar solo esta skill**

```bash
npx skills add https://github.com/alcaudon89/agent-skills-es/tree/main/skills/expo-apple-ui
```

En claude.ai o la app de escritorio: descarga [expo-apple-ui.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/expo-apple-ui.zip) y súbelo en Personalizar → Skills → + → Crear skill → Subir una skill.

Más opciones en el [README principal](../../README.md).
