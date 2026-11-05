# Fase B — Verificación externa del remitente

Solo consultas pasivas sobre dominios y nombres **tecleados por ti**, nunca sobre enlaces del correo. Si no tienes herramientas (búsqueda web, lectura de páginas, DNS), marca cada punto como [NO VERIFICABLE] e indica qué consulta haría el usuario y en qué web.

Haz la Fase B que corresponda según el triaje del Paso 0.

## Comprobación de red (antes de empezar)

Prueba una consulta sencilla (una búsqueda web y, si puedes ejecutar código, una petición DNS sobre HTTPS a `dns.google`). Según el resultado:

- **Hay búsqueda y lectura de páginas**: sigue con normalidad.
- **Solo hay búsqueda web** (sin lectura de páginas, DNS ni RDAP): los datos saldrán de resúmenes del buscador. Márcalo en cada fila («resumen de búsqueda, página no leída») y baja la confianza.
- **No hay red**: no rellenes nada de memoria. Marca la Fase B como [NO VERIFICABLE].

Si falta red, avisa **al principio del informe**, en un bloque visible:

> 🌐 **Verificación externa parcial**: en esta sesión no tengo acceso a [lo que falte: búsqueda web / lectura de páginas / DNS y RDAP]. El registro mercantil, la antigüedad del dominio y las sanciones quedan sin comprobar o se basan en resúmenes del buscador.
>
> Si quieres un análisis completo, puedes darme acceso a la red **bajo tu responsabilidad** (la IA podrá hacer consultas a internet; yo solo consultaré dominios y registros tecleados por mí, nunca los enlaces del correo):
> - **claude.ai / app de escritorio**: Ajustes → Capacidades → activa la búsqueda web y, en «Ejecución de código», el acceso a la red (o añade los dominios necesarios a la lista permitida).
> - **Claude Code en la web**: menú del entorno en la barra de título → Editar → Acceso a la red: sube el nivel o añade los dominios a «Dominios permitidos». Guía: https://code.claude.com/docs/en/cloud-environments#network-access
> - **Claude Code en local**: revisa los permisos de WebFetch/WebSearch y la configuración del proxy o sandbox.
>
> Dominios útiles para esta verificación: `dns.google`, `rdap.org`, `rdap.verisign.com`, `handelsregister.de`, `boe.es`, `find-and-update.company-information.service.gov.uk`, `ec.europa.eu`, `sanctionsmap.eu`, `sanctionssearch.ofac.treas.gov`, `northdata.de`, el dominio del remitente y el de su matriz.
>
> También puedes hacer tú las comprobaciones pendientes (al final del informe tienes la lista con las webs).

Luego continúa con lo que sí puedas hacer; no pares el análisis.

## B1. Dominio e infraestructura

- Fecha de registro, registrador y DNS del dominio: RDAP (`https://rdap.org/domain/DOMINIO`, que redirige al registro correcto) o WHOIS. Para `.es`, el WHOIS de dominios.es oculta casi todo: dilo en vez de deducir.
- Registros A, MX, SPF (TXT), DMARC (`_dmarc.DOMINIO`, TXT) y, si quieres, DKIM: DNS sobre HTTPS, por ejemplo `https://dns.google/resolve?name=DOMINIO&type=TXT`.
- Si se menciona una empresa matriz o marca relacionada, compara la infraestructura de ambos dominios (IP, registrador, DNS, fechas). Una IP compartida indica un posible mismo operador, pero no lo prueba: puede ser alojamiento compartido.
- Dominio de menos de 90 días: señal de riesgo. Si el veredicto final la descarta, explica qué evidencia la compensa.
- Si hay sospecha de typosquatting, verifica también el dominio legítimo y compara.

## B2. Web del dominio (solo lectura)

- Lee solo la página raíz del dominio del remitente (no la de los enlaces del correo): ¿hay web pública, aviso legal / Impressum, datos de contacto coherentes? En España, el aviso legal debe incluir razón social, NIF y datos registrales (LSSI, art. 10).
- Si aparece un listado de directorios o páginas de acceso: anota títulos y fechas, y valora si imitan a una marca conocida (phishing) o parecen herramientas privadas. **No** inicies sesión, **no** descargues ficheros, **no** explores carpetas ocultas ni de nombre aleatorio: eso ya no es verificación, es intrusión.
- Revisa la web de la empresa matriz si la hay (aviso legal, productos, coherencia con la firma).
- Si la web no responde o no hay herramienta, dilo; no lo interpretes como prueba de nada.

## B3. Existencia y datos de la empresa

- Registro mercantil oficial del país:
  - España: BORME (boe.es, gratuito) y Registro Mercantil (registradores.org, nota simple de pago).
  - Alemania: handelsregister.de (gratuito desde agosto de 2022).
  - Reino Unido: Companies House (find-and-update.company-information.service.gov.uk).
  - Otros: el registro oficial del país, o el buscador europeo e-Justice (BRIS).
  - Si solo encuentras agregadores, dilo.
- Extrae: número de registro, fechas de constitución e inscripción, domicilio, objeto social, administradores, socios y capital, y la forma de representación (solidaria o mancomunada) si consta.
- **NIF español**: comprueba que el formato y la letra o dígito de control son válidos. Un formato válido no prueba que exista.
- **Coherencia**: ¿el domicilio y el nombre del registro coinciden con la firma del correo? ¿El objeto social cubre la actividad? ¿La antigüedad de la empresa encaja con el volumen o tipo de negocio que propone? ¿Hay actos recientes que alerten (cambio de administrador y de domicilio a la vez, venta de la sociedad, disolución, concurso)?
- NIF-IVA intracomunitario en VIES (ec.europa.eu/taxation_customs/vies) si lo facilitan o aparece publicado. Que no esté en VIES no significa que no exista, solo que no opera intracomunitariamente con ese número.
- Presencia comercial verificable: ferias, directorios sectoriales, marcas registradas (EUIPO, OEPM, DPMA), apps publicadas, licitaciones públicas.

## B4. Persona remitente (solo datos profesionales)

- Comprueba únicamente datos profesionales públicos: cargo en el registro mercantil, perfil profesional (LinkedIn), publicaciones o productos a su nombre, coherencia con la empresa.
- No recopiles datos personales (ver regla 10 de SKILL.md).
- **Homónimos**: un perfil con el mismo nombre no prueba que sea la misma persona si no menciona la empresa, el dominio o el producto. Indica qué lo vincula y qué no.
- Para usar un perfil como prueba de historial, necesitas un vínculo verificable con la empresa y una fecha visible. No deduzcas antigüedades.

## B5. Sanciones y cumplimiento

- Comprueba la empresa, sus administradores y socios en listas de sanciones: EU Sanctions Map (sanctionsmap.eu) y lista consolidada de la UE; si aplica, OFAC (sanctionssearch.ofac.treas.gov), la lista del Reino Unido (OFSI) y la de la ONU.
- Si algún perfil (aunque sea de un posible homónimo) menciona una entidad sancionada, repórtalo con matices: haber trabajado en una entidad sancionada no implica estar sancionado; lo determinante es si la empresa o las personas figuran en la lista. Recomienda la comprobación formal.
- Si el destino de la mercancía es un país con restricciones de exportación o el producto puede ser de doble uso, señálalo y recomienda consultar con el responsable de comercio exterior.

## B6. Reputación técnica

- Reputación de la IP y del dominio: AbuseIPDB, VirusTotal (búsqueda por dominio o hash, sin subir ficheros), URLScan (resultados existentes, sin lanzar escaneos de enlaces del correo), MXToolbox (listas negras).
- No marques como maliciosa la IP compartida de una plataforma de envío legítima (Google, Microsoft, Brevo, SendGrid…).
- Sin herramientas, recomiéndalas con la URL exacta para que el usuario la teclee.
