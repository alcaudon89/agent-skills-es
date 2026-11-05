# Fase A — Análisis estático del correo

Se hace siempre. Solo con lo que contiene el correo: sin visitar nada.

## A1. Cabeceras y autenticación

- **Confianza de las cabeceras**: solo son fiables las cabeceras `Received` y `Authentication-Results` añadidas por los servidores del destinatario (las de más arriba). Todo lo que hay por debajo del primer salto externo lo escribe el remitente y puede ser falso. Identifica dónde está esa frontera.
- **SPF, DKIM y DMARC** (`Authentication-Results`, `Received-SPF`, `ARC-*`):
  - SPF valida el dominio del Envelope-From / Return-Path, no el From visible. Un SPF `pass` de otro dominio no autentica el From.
  - Indica si DKIM firma un dominio distinto del From (`d=`) y si está alineado.
  - DMARC `pass` exige alineación de SPF o DKIM con el From. Indica la política publicada (`p=none` / `quarantine` / `reject`): con `p=none`, la suplantación exacta del dominio llega a la bandeja.
  - Si hay `ARC-*`, el correo pasó por un reenvío o lista: valora si el sellador es de confianza.
- **Coherencia** entre From, Return-Path / Envelope-From, Reply-To y Sender. Un Reply-To distinto del From es señal típica de BEC.
- **Cadena Received**: reconstruye la ruta de abajo arriba, señala saltos anómalos, IP de origen, webmails genéricos e incoherencias horarias o de zona horaria.
- **Message-ID**: si su dominio no coincide con el remitente, explica si es normal para la plataforma de envío.
- **X-Mailer, User-Agent, X-Originating-IP** y cabeceras de proveedor (`X-MS-Exchange-*`, `X-Google-*`, `X-Mailin-*`, `X-sib-id`, `Feedback-ID`…). Decodifica las que vengan en base64 y los identificadores de cuenta de la plataforma de envío (sirven para denunciar el abuso).
- **Veredictos del propio filtro** (`X-MS-Exchange-Organization-SCL`, `X-Spam-Status`, `X-Forefront-Antispam-Report`, `X-Microsoft-Antispam`): anótalos como un dato más, no como la conclusión.
- **Plataformas de email marketing** (Brevo/Sendinblue, Mailchimp, SendGrid, Amazon SES…): indica si se usan para un mensaje que se presenta como personal y uno a uno.

## A2. Remitente e identidad aparente

- Suplantación del nombre visible (display name spoofing), incluido el truco de meter una dirección falsa dentro del nombre: `"pagos@proveedor.com" <x@otro.xyz>`.
- Dominios parecidos al legítimo (typosquatting): letras cambiadas o duplicadas, `rn` por `m`, guiones, TLD distinto, subdominios, homoglifos, punycode (`xn--`).
- Correo gratuito (Gmail, Outlook, Proton…) que se hace pasar por empresa, banco, organismo o directivo.
- **Hilo secuestrado**: «RE:» o «RV:» sin hilo previo real, o una conversación auténtica citada desde una dirección nueva. Si el usuario tiene correos anteriores con ese contacto (o un conector de correo, con su permiso), compara dirección, firma, estilo y datos de pago.

## A3. Contenido e ingeniería social

- Urgencia, amenaza, miedo, recompensa o autoridad.
- Peticiones sensibles: credenciales, códigos 2FA, datos bancarios, cambio de IBAN, transferencias, tarjetas regalo, criptomonedas.
- Suplantaciones habituales en España: AEAT, Seguridad Social, DGT, Correos, bancos, eléctricas, mensajería, Microsoft 365. Ningún organismo pide pagos ni credenciales por un enlace del correo.
- **BEC**: cambio de datos de pago de un proveedor, facturas inesperadas, petición de confidencialidad, saltarse procedimientos, «estoy en una reunión, no me llames».
- **Fraude B2B y presupuestos falsos**:
  - Plantilla masiva: listas con un solo elemento, referencias generadas automáticamente con datos sacados de la web del destinatario, frases genéricas («cotice solo lo que fabrica»).
  - Incoherencia entre lo que se pide y lo que fabrica el destinatario (usa el contexto de la empresa).
  - Captación de información industrial: procesos internos, subcontratas, maquinaria, escalones de precio detallados.
  - Petición de datos corporativos o de identidad: razón social, CIF, DNI del administrador, escrituras, certificado bancario, firmas.
  - Anuncio de una segunda fase (NDA, planos CAD, portal de proveedores, registro previo): es el vector habitual de enlaces de phishing, adjuntos maliciosos o cobros por adelantado.
  - Fraude del comprador: pedido grande de un cliente nuevo, entrega a un tercero o a otro país, pago aplazado, prisa, dirección de entrega en un almacén de tránsito.
- Saludo genérico, errores de idioma, traducción automática, tono impropio, firma incoherente.
- **Coherencia contextual**: ¿tiene sentido que esta entidad envíe este mensaje, por este canal, a esta persona?

## A4. Enlaces

- Extrae **todas** las URLs: `href`, `src`, `action` de formularios, texto plano, imágenes enlazadas, cabecera `List-Unsubscribe`.
- Compara el texto visible con el destino real del `href`.
- Señala: acortadores, redirecciones abiertas (`?url=`, `?redirect=`), IP en lugar de dominio, subdominios engañosos (`banco.com.dominio-malo.xyz`), servicios legítimos abusados (formularios, nube, IPFS, páginas gratuitas, Google Sites, SharePoint de terceros), el email de la víctima codificado en parámetros o en el fragmento `#`, y URLs ofuscadas (base64, codificación `%`, `@` en la URL).
- Enlaces de seguridad reescritos (Safe Links, Proofpoint URL Defense, Mimecast): decodifica el destino real sin visitarlo.
- Códigos QR en imágenes o adjuntos (quishing): indícalo aunque no puedas decodificarlos.

## A5. Adjuntos

- Nombre, extensión, tipo MIME declarado, tamaño y hash (SHA-256). Señala discrepancias entre extensión y MIME.
- Extensiones de riesgo: doble extensión (`factura.pdf.exe`), `.html/.htm/.shtml`, `.iso/.img/.vhd`, `.lnk`, `.js/.vbs/.hta/.wsf`, `.one`, documentos con macros (`.docm/.xlsm`), `.zip/.rar/.7z` con contraseña (sobre todo si la contraseña va en el cuerpo), `.svg` con scripts, `.ics` con enlaces.
- Adjuntos HTML o SVG con formularios de login o JavaScript.
- PDF con un único botón o enlace («Ver documento»): el riesgo está en el enlace, trátalo como en A4.
- El hash puede consultarse en VirusTotal. **No subas el fichero.** Un hash sin resultados no significa que sea seguro.

## A6. Técnicas de evasión en el HTML/MIME

- Texto oculto (`display:none`, tamaño 0, color igual al fondo) y caracteres de ancho cero o de control de dirección (RTLO).
- Contenido codificado u ofuscado (base64, quoted-printable anómalo, entidades HTML) y JavaScript embebido.
- Texto oculto dirigido a una IA o a filtros antispam (instrucciones, párrafos de relleno legítimo).
- Píxeles de seguimiento y recursos remotos.
- Discrepancias entre la parte `text/plain` y la parte `text/html`.
- Correo formado solo por una imagen, para eludir los filtros de texto.
