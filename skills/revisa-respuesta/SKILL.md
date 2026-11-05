---
name: "revisa-respuesta"
description: "Revisa la respuesta anterior (resumen, análisis, explicación, código o cualquier otra) contra sus fuentes: veracidad, claridad y exhaustividad, con notas, fallos graduados y versión corregida. Úsala cuando el usuario pida revisar, comprobar o verificar lo dicho antes («revisa tu respuesta», «¿es correcto?», «comprueba lo anterior»)."
---

# Revisa respuesta

Audita la respuesta más reciente de la conversación, sea del tipo que sea: un resumen, un análisis, una explicación técnica, una recomendación, código o datos. El objetivo principal es comprobar si lo que dice es verdad según su origen. Después, entrega una versión mejorada que aplique lo detectado en la revisión.

## 1. Identificar respuesta y origen

- Localiza la última respuesta sustantiva. Si el usuario señala otra, revisa esa.
- Determina de dónde salió cada afirmación:
  - documentos adjuntos o texto pegado;
  - resultados de búsquedas web o páginas consultadas;
  - resultados de herramientas (consultas, código ejecutado, conectores);
  - lo dicho antes en la conversación;
  - conocimiento propio sin fuente.
- Si el origen es web o un dato que puede haber cambiado (precios, normas, versiones, cargos, plazos), vuelve a verificarlo con búsqueda en lugar de fiarte del resultado anterior.
- Si una afirmación no tiene fuente y no puede verificarse, márcala como «no verificable»; no la des por buena ni por falsa.

## 2. Evaluar tres criterios

Contrasta cada afirmación con su origen. No des nada por bueno sin comprobarlo.

**Veracidad**
- Cifras, fechas, nombres, cargos, unidades y cálculos (rehaz los cálculos).
- Atribuciones: quién dijo o decidió qué; propuestas presentadas como decisiones.
- Matices perdidos: condicionales convertidos en certezas, hipótesis como hechos.
- Afirmaciones que van más allá de lo que dice la fuente o que contradicen la fuente.
- Contenido inventado: citas, referencias, enlaces, funciones o APIs que no existen.
- En código o pasos técnicos: si funcionaría tal cual y si se corresponde con la documentación.

**Claridad**
- Estructura y orden lógico.
- Frases ambiguas, referencias sin antecedente, jerga sin explicar.
- Longitud proporcionada; relleno o repeticiones.

**Exhaustividad**
- Si responde a todo lo que se preguntó.
- Puntos relevantes de la fuente que faltan (decisiones, riesgos, excepciones, plazos).
- Desequilibrio: lo secundario con mucho peso y lo importante apenas tratado.

## 3. Formato de la revisión

1. **Veredicto** en una frase: fiable tal cual, fiable con correcciones o no fiable.
2. **Notas** (1–5), cada una con una línea de justificación:
   - Veracidad: x/5
   - Claridad: x/5
   - Exhaustividad: x/5
3. **Problemas detectados**, numerados y ordenados por gravedad:
   - 🔴 Crítico: dato falso, inventado u omisión que cambia la conclusión.
   - 🟠 Importante: imprecisión, matiz perdido o falta relevante.
   - 🟡 Menor: redacción, orden, estilo.
   Para cada uno: cita breve del fragmento, qué falla, qué dice el origen (con enlace o ubicación) y la corrección.
4. **No verificable**: lista de afirmaciones sin fuente comprobable, si las hay.
5. **Lo que está bien**: solo si aporta; una o dos líneas, sin halagos.

## 4. Versión mejorada

Tras la revisión, reescribe la respuesta original aplicando todos los problemas detectados.

- Corrige cada 🔴 y 🟠 sin excepción; aplica los 🟡 salvo que cambien el estilo del autor sin mejorar nada.
- Mantén el tipo, el propósito, el tono y el formato de la original (un resumen sigue siendo un resumen, un bloque de código sigue siendo código). Ajusta la longitud solo si la revisión lo pedía.
- No introduzcas afirmaciones nuevas que no estén respaldadas por el origen o por lo verificado en la revisión.
- Lo «no verificable»: elimínalo si no es esencial; si lo es, consérvalo señalado como no confirmado.
- Entrega la versión completa y lista para usar, no un parche.
- Debajo, una lista breve de **Cambios aplicados** que remita a los números de los problemas (p. ej. «#1 cifra corregida», «#4 añadido el plazo de entrega»).
- Si el veredicto es «fiable tal cual» y no hay problemas, dilo y no generes versión nueva.

## Reglas

- Sé directo y concreto; nada de «podría ser más claro» sin señalar dónde y cómo.
- Si un criterio no tiene problemas, dilo; no inventes defectos para rellenar.
- Si la respuesta es tuya, revísala con el mismo rigor que si fuera ajena y reconoce los errores sin rodeos.
- Al final, lista las fuentes consultadas en la revisión.
- Responde en castellano.