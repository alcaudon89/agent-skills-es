# verifica-correo

Audita un correo recibido para detectar phishing, suplantación, BEC, malware o fraude B2B, y comprueba si el remitente es una contraparte fiable (dominio, registro mercantil, VIES, sanciones).

> ⚠️ Es un análisis hecho por una IA: no es ciencia exacta y puede contener errores. Úsalo como ayuda para decidir, no como dictamen.

**Cómo funciona**

1. Si no tiene el contexto de tu empresa (en memoria o en la conversación), te lo pregunta una vez: qué vendéis, canales habituales y si esperabas el correo.
2. Si ya hiciste clic, abriste un adjunto o pagaste, te da primero las medidas urgentes.
3. Análisis estático del correo: cabeceras SPF/DKIM/DMARC, remitente, contenido, enlaces, adjuntos y técnicas de evasión. Sin abrir nada.
4. Verificación externa del remitente, proporcional al caso: dominio, web, registro mercantil, persona (solo datos profesionales), sanciones y reputación.
5. Contraste de hipótesis, informe con veredicto y puntuación 0–100, IOCs desactivados, acciones recomendadas y autorrevisión.

**Qué le puedes dar**

- `.eml` o el código fuente completo (lo mejor). Incluye `scripts/extrae_eml.py`, que extrae cabeceras, URLs y hashes de adjuntos sin abrir nada.
- `.msg` de Outlook: el script lo lee si tienes `olefile` (`pip install olefile`); si no, te pedirá el `.eml`.
- Un correo reenviado o una captura: funciona, pero con menos fiabilidad, y te lo dirá.

Si la sesión no tiene acceso a internet, te avisa al principio de que la verificación externa será parcial y te explica cómo abrir la red, bajo tu responsabilidad.

**Instalar solo esta skill**

```bash
npx skills add https://github.com/alcaudon89/agent-skills-es/tree/main/skills/verifica-correo
```

En claude.ai o la app de escritorio: descarga [verifica-correo.zip](https://github.com/alcaudon89/agent-skills-es/releases/latest/download/verifica-correo.zip) y súbelo en Personalizar → Skills → + → Crear skill → Subir una skill.

Más opciones en el [README principal](../../README.md).
