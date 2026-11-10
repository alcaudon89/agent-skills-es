---
name: "expo-apple-ui"
description: "UI estilo Apple en apps Expo/React Native: Liquid Glass, movimiento fluido, sheets, tabs y controles nativos. Orquesta los skills oficiales de Expo (leídos en vivo) con los criterios de diseño de Apple. Úsala al construir, planificar o revisar pantallas iOS en Expo (también antes de crear el proyecto), aplicar Liquid Glass, animar gestos o sheets, o migrar una app Expo al diseño de iOS 26."
---

# Expo + Apple UI (skill puente)

Este skill no contiene APIs de Expo. Decide qué fuente manda en cada capa, obtiene la versión **actual** de los skills oficiales de Expo y resuelve los choques entre Expo y los criterios de Apple.

## Paso 0: contexto del proyecto (siempre)

Localiza la app Expo. Busca `package.json` en la raíz y, si no está o no depende de `expo`, en subcarpetas (monorepos: `apps/*`, `packages/*`, `mobile/`…), sin entrar en `node_modules`. Según lo que encuentres, sigue uno de estos dos modos:

**A. Hay app Expo** (un `package.json` con `expo` en dependencias):

1. Lee de ese `package.json` la versión de `expo` (SDK), `react-native-reanimated`, `react-native-gesture-handler`, y si existen `@expo/ui`, `expo-glass-effect` y `expo-blur`. Si hay varias apps Expo, pregunta cuál.
2. Anota el SDK. Los skills de Expo siguen el **último SDK**. Si el proyecto va por detrás, contrasta cada API con la documentación versionada (`https://docs.expo.dev/versions/v<SDK>.0.0/`) antes de usarla.
3. Instala dependencias siempre con `npx expo install <paquete>`, nunca con `npm install` a secas.

**B. Aún no hay app Expo** (repo de diseño o planificación: ADR, specs, mapas de recon, tokens). No te detengas ni crees el proyecto por tu cuenta:

1. Busca si la documentación del repo ya fija la plataforma o el SDK (ADR, notas de arquitectura). Si un ADR descarta Expo o React Native, dilo y para: este skill no aplica.
2. Toma como SDK objetivo el que fije esa documentación o, si no hay, el último estable según `https://expo.dev/changelog`. Indícalo como **objetivo**, no como instalado.
3. Aplica los Pasos 1 a 3 para producir criterio, no código: qué superficies llevan cristal, qué componentes nativos se usan (NativeTabs, form sheets, `@expo/ui`), paquetes previstos, alternativas por plataforma y requisitos de accesibilidad. Escríbelo donde el repo guarde las decisiones (un ADR nuevo, la spec de diseño o la de la pantalla), con el formato que ya use.
4. Marca cada API citada como «verificar al crear el proyecto» y no ejecutes `npx expo install`.
5. Si el usuario quiere empezar ya a programar, propón `npx create-expo-app@latest` y espera su confirmación; después vuelve al modo A.

**Si hay `package.json` pero sin Expo** (web, backend u otra app React Native sin Expo), dilo y pregunta antes de seguir: las reglas de diseño valen, pero las APIs del Paso 1 no.

## Paso 1: cargar Expo en su versión actual

Skills de Expo que usa este puente:

| Skill | Para qué |
|---|---|
| `expo-native-ui` | Estilo HIG, colores semánticos, SF Symbols, efectos visuales (blur, glass) |
| `expo-ui` | `@expo/ui`: SwiftUI real en iOS, Compose en Android; BottomSheet, Picker, Menu, Switch… |
| `expo-router` | NativeTabs (glass automático en iOS 26), stacks, form sheets, toolbars |
| `expo-animation` | Todo el código de movimiento: springs, gestos, haptics, reduced motion |
| `expo-design-system` | Tokens y componentes compartidos, auditoría de «native slop» |

Obtenlos en este orden y quédate con la primera vía que funcione:

1. **Instalados en la sesión** (aparecen en la lista de skills, p. ej. `expo:expo-ui`): cárgalos con la herramienta Skill.
2. **Clon en vivo**, si hay shell con acceso a GitHub: `git clone --depth=1 https://github.com/expo/skills /tmp/expo-skills`. Lee `plugins/expo/skills/<skill>/SKILL.md` y sus `references/` según haga falta.
3. **Lectura directa**: WebFetch de `https://raw.githubusercontent.com/expo/skills/main/plugins/expo/skills/<skill>/SKILL.md`.

Carga solo los skills que la tarea necesita, y de cada uno solo las referencias pertinentes.

**Si una ruta da 404**, Expo ha reorganizado el repo. Ya pasó: `building-native-ui` se dividió en `expo-native-ui`, `expo-router` y `expo-animation`. Descubre los nombres actuales listando `https://api.github.com/repos/expo/skills/contents/plugins/expo/skills` o el clon y elige los equivalentes. Después **avisa al usuario de que la tabla de arriba está desfasada**, para que actualice este skill.

Antes de seguir, indica en una línea qué versión de los skills de Expo has leído (commit o fecha si la conoces; si no, la vía: «skill instalado», «clon de hoy», «raw de `main`») y el SDK del proyecto, o el SDK objetivo en el modo B.

## Paso 2: quién manda en cada capa

| Capa | Manda | Apoyo |
|---|---|---|
| APIs, paquetes, sintaxis | Expo (actual) | Ninguno: en el *cómo*, Expo gana siempre |
| Qué lleva cristal y qué no | Criterio Liquid Glass de Apple | Expo para implementarlo |
| Código de movimiento y gestos | `expo-animation` | — |
| Criterio de movimiento (por qué y hacia dónde) | Criterio de movimiento fluido de Apple | `expo-animation` |
| Materiales, jerarquía, tipografía, principios | HIG de Apple | `expo-native-ui` |
| SwiftUI dentro de `@expo/ui/swift-ui` o módulos Swift propios | Semántica SwiftUI de `glassEffect`, `GlassEffectContainer` y morphing | `expo-ui` (cómo se expone en React) |

**Fuentes del criterio Apple**, en este orden:

1. Si están instalados, los skills `apple-liquid-glass` (cristal y SwiftUI) y `apple-design` (movimiento fluido, materiales, tipografía). De `apple-design` usa los principios, no los ejemplos de código, porque son CSS y Pointer Events.
2. Si no, la documentación oficial:
   - Materiales: `https://developer.apple.com/design/human-interface-guidelines/materials`
   - Liquid Glass en vistas propias: `https://developer.apple.com/documentation/SwiftUI/Applying-Liquid-Glass-to-custom-views`
   - Movimiento: `https://developer.apple.com/design/human-interface-guidelines/motion`

La física del movimiento fluido (proyección de momento, efecto goma, paso de velocidad al spring) ya está implementada en React Native en las recetas de `expo-animation`. No la reimplementes.

## Paso 3: reglas para resolver choques

1. **Primero lo nativo, después el cristal a medida.** Antes de construir una superficie de cristal propia, mira lo que ya existe: NativeTabs para tabs, BottomSheet de `@expo/ui` o form sheet de expo-router para sheets, toolbars y headers nativos. Todo eso ya trae Liquid Glass en iOS 26 sin código extra.
2. **El cristal va en la capa de navegación y controles, no en el contenido.** Esta regla prevalece sobre los ejemplos de Expo con «Glass Card». Sí: botones flotantes, toolbars, tab bars, sheets, menús y overlays que flotan sobre el contenido. No: celdas de lista, tarjetas de contenido, bloques de texto, media.
3. **Nada de cristal sobre cristal.** Si varios elementos de cristal conviven o se transforman entre sí, agrúpalos: `GlassEffectContainer` vía `@expo/ui/swift-ui` si se usa SwiftUI, o una única `GlassView` contenedora con `expo-glass-effect`.
4. **Siempre las dos guardas y una alternativa.** La comprobación es `isLiquidGlassAvailable() && isGlassEffectAPIAvailable()`; confirma en Expo el nombre actual de las guardas. Alternativas por defecto:
   - iOS < 26: `BlurView` de `expo-blur` con tint `systemMaterial` / `systemChromeMaterial`.
   - Android: superficie sólida o tonal del tema (Material). No simules cristal con blur en Android salvo que se pida expresamente: es caro y no es nativo.
   - Web, si el proyecto la tiene: fondo translúcido con `backdrop-filter`, solo en la capa de navegación.
5. **Accesibilidad de la transparencia.** Respeta *Reducir transparencia* (`AccessibilityInfo.isReduceTransparencyEnabled()`): si está activada, sustituye cristal o blur por una superficie opaca. El contraste del texto sobre cristal debe cumplir WCAG AA en claro y en oscuro. *Reducir movimiento* lo gestiona `expo-animation`: menos movimiento y más suave, no cero.
6. **Tinte con moderación.** El color de acento solo va en elementos interactivos. No tiñas cristal decorativo.
7. **Movimiento.** Si hay un dedo implicado, spring con la velocidad heredada. Si no, timing con ease-out. En las transiciones de pantalla, las de la plataforma. Los parámetros los da `expo-animation`, no este skill.

## Paso 4: revisión antes de entregar

- [ ] Versión de los skills de Expo leída y SDK (del proyecto u objetivo) indicados; APIs verificadas contra ese SDK o marcadas para verificar
- [ ] Componentes nativos donde existen (tabs, sheets, menús, pickers)
- [ ] Cristal solo en la capa de navegación y controles, sin cristal anidado
- [ ] Guardas y alternativas para iOS < 26, Android y, si aplica, web
- [ ] Reducir transparencia y Reducir movimiento respetados; contraste AA en claro y oscuro
- [ ] Gestos con spring y velocidad heredada; ningún `setState` en handlers de gesto
- [ ] Prueba en dispositivo real o, como mínimo, en el simulador de iOS 26 y en Android. Si no has podido ejecutarla, dilo y deja al usuario los pasos para hacerla; no la des por hecha

En el modo B, la entrega es el documento de decisiones: los puntos de código (guardas, gestos, pruebas) se escriben como requisitos, no se marcan como hechos.

## Mantenimiento de este skill

Lo que viene de Expo se mantiene al día solo, porque se lee en vivo en cada uso. Este archivo solo hay que tocarlo si Expo renombra skills (el Paso 1 lo detecta y avisa) o si cambian las reglas de choque. En Claude Code con el plugin oficial de Expo instalado, este se actualiza con `/plugin marketplace update expo-plugins`.
