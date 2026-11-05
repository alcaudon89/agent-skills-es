#!/usr/bin/env python3
"""Extrae de un .eml o .msg los datos útiles para el análisis, ya desactivados (defang).

No abre enlaces, no guarda ni ejecuta adjuntos: solo lee el fichero y calcula hashes.
Uso: python3 -I extrae_eml.py RUTA.eml|RUTA.msg

Los .msg (Outlook) necesitan la librería olefile (pip install olefile). Sin ella, el
script pide el .eml. El cuerpo HTML de un .msg suele ir en RTF comprimido y solo se
recupera en parte: las señales que dependen del HTML son menos fiables en .msg.
"""
import base64
import email
import email.header
import hashlib
import html
import re
import sys
import unicodedata
from email import policy
from email.utils import getaddresses, parseaddr

CABECERAS = [
    "From", "Sender", "Reply-To", "Return-Path", "To", "Cc", "Subject", "Date",
    "Message-ID", "In-Reply-To", "References", "X-Mailer", "User-Agent",
    "X-Originating-IP", "List-Unsubscribe", "Feedback-ID", "X-sib-id",
    "X-Mailin-Campaign", "X-Mailin-Client", "X-MS-Exchange-Organization-SCL",
    "X-Spam-Status", "X-Microsoft-Antispam", "X-Forefront-Antispam-Report",
]
AUTENTICACION = ["Authentication-Results", "Received-SPF", "ARC-Authentication-Results", "DKIM-Signature"]
EXT_RIESGO = {
    "exe", "scr", "com", "bat", "cmd", "pif", "msi", "dll", "html", "htm", "shtml",
    "xhtml", "iso", "img", "vhd", "vhdx", "lnk", "js", "jse", "vbs", "vbe", "hta",
    "wsf", "ps1", "one", "docm", "xlsm", "pptm", "xlam", "zip", "rar", "7z", "gz",
    "tar", "cab", "svg", "jar", "ics", "url", "reg", "chm",
}
URL_RE = re.compile(r"""(?:https?|ftp)://[^\s"'<>()]+|www\.[^\s"'<>()]+""", re.I)
ATTR_RE = re.compile(r"""\b(href|src|action)\s*=\s*["']([^"']+)["']""", re.I)
ANCLA_RE = re.compile(r"""<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""", re.I | re.S)
OCULTO_RE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?:px|pt|em)?\b|"
    r"max-height\s*:\s*0|opacity\s*:\s*0(?:\.0+)?\b|width\s*:\s*0(?:px)?\b", re.I)
ANCHO_CERO = re.compile("[​‌‍⁠﻿‮‭⁦-⁩]")
INYECCION_RE = re.compile(
    r"ignore (all |the )?(previous|prior) instructions|ignora (las )?instrucciones|"
    r"you are an? (ai|assistant|llm)|eres una? (ia|asistente)|this (email|message) is safe|"
    r"este (correo|mensaje) es seguro|system prompt", re.I)


def defang(texto):
    if not texto:
        return texto
    t = re.sub(r"(?i)\bhttp", "hxxp", str(texto))
    t = re.sub(r"(?i)\bftp://", "fxp://", t)
    t = t.replace("@", "[@]")
    t = re.sub(r"(?<=[A-Za-z0-9])\.(?=[A-Za-z0-9])", "[.]", t)
    return t


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def defang_texto(texto):
    """Desactiva solo URLs y direcciones dentro de un texto libre."""
    texto = URL_RE.sub(lambda m: defang(m.group(0)), texto)
    return EMAIL_RE.sub(lambda m: defang(m.group(0)), texto)


def dominio(direccion):
    _, addr = parseaddr(direccion or "")
    return addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""


def decodifica_partes(msg):
    textos, adjuntos = {"text/plain": [], "text/html": []}, []
    for parte in msg.walk():
        if parte.is_multipart():
            continue
        ctype = parte.get_content_type()
        nombre = parte.get_filename()
        disp = (parte.get_content_disposition() or "").lower()
        datos = parte.get_payload(decode=True) or b""
        if nombre or disp == "attachment" or ctype not in textos:
            if not datos and not nombre:
                continue
            ext = nombre.rsplit(".", 1)[-1].lower() if nombre and "." in nombre else ""
            dobles = re.findall(r"\.([A-Za-z0-9]{2,5})(?=\.)", nombre or "")
            adjuntos.append({
                "nombre": nombre or "(sin nombre)",
                "mime": ctype,
                "disposicion": disp or "(ninguna)",
                "tamano": len(datos),
                "sha256": hashlib.sha256(datos).hexdigest(),
                "riesgo": ext in EXT_RIESGO,
                "doble_ext": bool(dobles) and ext in EXT_RIESGO,
                "rtlo": bool(nombre and "‮" in nombre),
            })
            if ctype == "text/html" or ext in {"html", "htm", "svg", "shtml", "xhtml"}:
                textos["text/html"].append(datos.decode(parte.get_content_charset() or "utf-8", "replace"))
            continue
        textos[ctype].append(datos.decode(parte.get_content_charset() or "utf-8", "replace"))
    return textos, adjuntos


def solo_texto(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


# --- Soporte .msg (Outlook, formato OLE) -------------------------------------
RTF_PRE = (b"{\\rtf1\\ansi\\mac\\deff0\\deftab720{\\fonttbl;}{\\f0\\fnil \\froman \\fswiss "
           b"\\fmodern \\fscript \\fdecor MS Sans SerifSymbolArialTimes New RomanCourier"
           b"{\\colortbl\\red0\\green0\\blue0\r\n\\par \\pard\\plain\\f0\\fs20\\b\\i\\u\\tab\\tx")


def lzfu(data):
    """Descomprime el RTF comprimido (MS-OXRTFCP) de un .msg."""
    import struct
    _, usize, magic, _ = struct.unpack("<IIII", data[:16])
    if magic == 0x414C454D:  # sin comprimir
        return data[16:16 + usize]
    buf = bytearray(RTF_PRE.ljust(4096, b"\0"))
    pos, out, i = len(RTF_PRE), bytearray(), 16
    while i < len(data) and len(out) < usize:
        flags = data[i]
        i += 1
        for b in range(8):
            if i >= len(data) or len(out) >= usize:
                break
            if flags & (1 << b):
                ref = (data[i] << 8) | data[i + 1]
                i += 2
                off, ln = ref >> 4, (ref & 0xF) + 2
                if off == pos % 4096:
                    return bytes(out)
                for k in range(ln):
                    c = buf[(off + k) % 4096]
                    out.append(c)
                    buf[pos % 4096] = c
                    pos += 1
            else:
                c = data[i]
                i += 1
                out.append(c)
                buf[pos % 4096] = c
                pos += 1
    return bytes(out)


def rtf_a_html(rtf):
    """Recupera las etiquetas HTML encapsuladas en el RTF (\\*\\htmltag). Parcial."""
    t = rtf.decode("latin-1")
    html_ = "".join(re.findall(r"\{\\\*\\htmltag\d*\s?((?:[^{}\\]|\\.)*)\}", t))
    html_ = re.sub(r"\\'([0-9a-f]{2})", lambda m: chr(int(m.group(1), 16)), html_)
    return html_.replace("\\{", "{").replace("\\}", "}").replace("\\\\", "\\")


def msg_a_eml(ruta):
    """Convierte un .msg en un objeto email.message con cabeceras, cuerpo y adjuntos."""
    try:
        import olefile
    except ImportError:
        sys.exit("Este fichero es un .msg de Outlook y falta la librería olefile.\n"
                 "Opciones: 1) pip install olefile y repetir; 2) guardar el correo como .eml "
                 "(o copiar su código fuente) y analizar ese fichero.")
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    ole = olefile.OleFileIO(ruta)

    def leer(nombre):
        return ole.openstream(nombre).read() if ole.exists(nombre) else None

    def texto(nombre):
        d = leer(nombre)
        return d.decode("utf-16-le", "replace").rstrip("\0") if d else ""

    cab = texto("__substg1.0_007D001F")
    if not cab:
        print("⚠️ El .msg no conserva las cabeceras de transporte: sin SPF/DKIM/DMARC ni ruta Received.")
    externo = email.message_from_string(cab + "\n\n", policy=policy.compat32) if cab else None
    msg = MIMEMultipart("mixed")
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(texto("__substg1.0_1000001F"), "plain", "utf-8"))
    html_ = leer("__substg1.0_10130102")
    if html_:
        html_ = html_.decode("utf-8", "replace")
    elif leer("__substg1.0_10090102"):
        html_ = rtf_a_html(lzfu(leer("__substg1.0_10090102")))
    if html_:
        alt.attach(MIMEText(html_, "html", "utf-8"))
    msg.attach(alt)
    for carpeta in sorted({e[0] for e in ole.listdir() if e[0].startswith("__attach")}):
        datos = leer(carpeta + "/__substg1.0_37010102") or b""
        nombre = (texto(carpeta + "/__substg1.0_3707001F") or texto(carpeta + "/__substg1.0_3704001F")
                  or "(sin nombre)")
        mime = texto(carpeta + "/__substg1.0_370E001F") or "application/octet-stream"
        parte = MIMEApplication(datos, _subtype=mime.split("/")[-1])
        parte.replace_header("Content-Type", mime)
        parte.add_header("Content-Disposition", "attachment", filename=nombre)
        msg.attach(parte)
    if externo is not None:
        for c, v in externo.items():
            if c.lower() not in ("content-type", "content-transfer-encoding", "mime-version"):
                msg[c] = v
    else:
        msg["Subject"] = texto("__substg1.0_0037001F")
        msg["From"] = texto("__substg1.0_0C1A001F") + " <" + texto("__substg1.0_0C1F001F") + ">"
    print("ℹ️ Entrada .msg convertida. El HTML se recupera en parte desde RTF: revisa a mano las "
          "señales que dependen de él.\n")
    return msg


def main(ruta):
    with open(ruta, "rb") as f:
        cabecera = f.read(8)
        f.seek(0)
        es_msg = cabecera == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # firma OLE: .msg
        if es_msg:
            msg = msg_a_eml(ruta)
        else:
            msg = email.message_from_binary_file(f, policy=policy.compat32)

    print("# Extracción de", ruta, "(indicadores desactivados)\n")
    print("## Cabeceras clave")
    for c in CABECERAS:
        for v in msg.get_all(c, []):
            print(f"- {c}: {defang(str(email.header.make_header(email.header.decode_header(v))))}")

    print("\n## Coherencia de dominios")
    doms = {c: dominio(msg.get(c)) for c in ["From", "Reply-To", "Return-Path", "Sender"]}
    mid = msg.get("Message-ID", "")
    doms["Message-ID"] = mid.rsplit("@", 1)[-1].strip("> ").lower() if "@" in mid else ""
    for c, d in doms.items():
        print(f"- {c}: {defang(d) or '(vacío)'}")
    if doms["Reply-To"] and doms["Reply-To"] != doms["From"]:
        print("- ⚠️ Reply-To con dominio distinto del From")
    nombre, _ = parseaddr(msg.get("From", ""))
    if "@" in nombre:
        print("- ⚠️ El nombre visible del From contiene una dirección de correo")
    if "xn--" in (doms["From"] + doms["Reply-To"]):
        print("- ⚠️ Dominio en punycode (posible homoglifo)")

    print("\n## Autenticación")
    for c in AUTENTICACION:
        for v in msg.get_all(c, []):
            v = re.sub(r"\s+", " ", str(v))
            if c == "DKIM-Signature":
                d = re.search(r"\bd=([^;\s]+)", v)
                s = re.search(r"\bs=([^;\s]+)", v)
                v = f"d={d.group(1) if d else '?'} s={s.group(1) if s else '?'}"
            print(f"- {c}: {defang(v)}")

    print("\n## Ruta Received (de arriba = destino a abajo = origen)")
    for i, v in enumerate(msg.get_all("Received", []), 1):
        print(f"{i}. {defang(re.sub(r'[ \t\r\n]+', ' ', str(v)))}")

    print("\n## Cabeceras en base64 decodificadas")
    for c, v in msg.items():
        for trozo in re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", str(v)):
            try:
                dec = base64.b64decode(trozo + "=" * (-len(trozo) % 4), validate=True).decode("utf-8")
            except Exception:
                continue
            if dec.isprintable() and len(dec) >= 6 and "=?" not in str(v) and c not in ("DKIM-Signature", "ARC-Message-Signature", "ARC-Seal"):
                print(f"- {c}: {defang(trozo)} → {defang(dec)}")

    textos, adjuntos = decodifica_partes(msg)
    html_total = "\n".join(textos["text/html"])
    plano = "\n".join(textos["text/plain"])

    print("\n## Enlaces del HTML (texto visible → destino real)")
    for href, visible in ANCLA_RE.findall(html_total):
        vis = solo_texto(visible)[:120]
        dom_vis = re.search(r"([a-z0-9-]+\.)+[a-z]{2,}", vis.lower())
        dom_href = re.search(r"//([^/:?#]+)", href.lower())
        alerta = ""
        if dom_vis and dom_href and dom_vis.group(0) not in dom_href.group(1):
            alerta = "  ⚠️ el texto muestra otro dominio"
        print(f"- «{defang_texto(vis) or '(imagen o vacío)'}» → {defang(html.unescape(href))}{alerta}")

    print("\n## Todas las URLs (href, src, action, texto, cabeceras)")
    urls = set(html.unescape(u) for _, u in ATTR_RE.findall(html_total))
    urls |= set(URL_RE.findall(plano)) | set(URL_RE.findall(solo_texto(html_total)))
    urls |= set(URL_RE.findall(str(msg.get("List-Unsubscribe", ""))))
    for u in sorted(urls):
        if u.lower().startswith(("http", "www", "ftp", "//")):
            marcas = []
            if re.search(r"//\d{1,3}(\.\d{1,3}){3}", u):
                marcas.append("IP")
            if "xn--" in u.lower():
                marcas.append("punycode")
            if re.search(r"//[^/]*@", u):
                marcas.append("@ en la URL")
            if re.search(r"[?&#][^=]*=?[^&]*(%40|@)", u):
                marcas.append("email en parámetros")
            print(f"- {defang(u)}" + (f"  [{', '.join(marcas)}]" if marcas else ""))

    print("\n## Adjuntos")
    if not adjuntos:
        print("- Ninguno")
    for a in adjuntos:
        avisos = [t for t, ok in (("extensión de riesgo", a["riesgo"]), ("doble extensión", a["doble_ext"]),
                                  ("carácter RTLO en el nombre", a["rtlo"])) if ok]
        print(f"- {a['nombre']} | MIME {a['mime']} | {a['disposicion']} | {a['tamano']} bytes | "
              f"SHA-256 {a['sha256']}" + (f"  ⚠️ {', '.join(avisos)}" if avisos else ""))

    print("\n## Evasión y contenido sospechoso")
    hallazgos = []
    sin_imgs = re.sub(r"(?is)<img\b[^>]*>", " ", html_total)
    if OCULTO_RE.search(sin_imgs):
        hallazgos.append("CSS que oculta texto o bloques (display:none, tamaño 0, opacidad 0…): revisa qué oculta")
    if re.search(r"<img\b[^>]*style\s*=\s*[\"'][^\"']*(display\s*:\s*none|visibility\s*:\s*hidden)", html_total, re.I):
        hallazgos.append("imagen remota oculta (display:none): píxel de seguimiento oculto, avisa al remitente de que se abrió")
    if ANCHO_CERO.search(html_total + plano):
        hallazgos.append("caracteres de ancho cero o de control de dirección")
    if re.search(r"<script\b|javascript:|\bon(load|click|error|mouseover)\s*=", html_total, re.I):
        hallazgos.append("JavaScript embebido")
    if re.search(r"<form\b", html_total, re.I):
        hallazgos.append("formulario HTML")
    if re.search(r"<img[^>]+(width|height)\s*=\s*[\"']?[01][\"'\s>]", html_total, re.I):
        hallazgos.append("posible píxel de seguimiento (imagen de 0–1 px)")
    if INYECCION_RE.search(unicodedata.normalize("NFKC", html_total + plano)):
        hallazgos.append("texto que parece dirigido a una IA o a un filtro (posible inyección de instrucciones)")
    if html_total and not plano:
        hallazgos.append("solo parte HTML, sin text/plain")
    if not es_msg and html_total and len(solo_texto(html_total)) < 40 and re.search(r"<img\b", html_total, re.I):
        hallazgos.append("correo formado casi solo por imágenes")
    if not es_msg and plano and html_total:
        a, b = set(solo_texto(html_total).lower().split()), set(plano.lower().split())
        if a and b and len(a & b) / max(len(a | b), 1) < 0.3:
            hallazgos.append("las partes text/plain y text/html dicen cosas muy distintas")
    hallazgos.append("(alertas automáticas: compruébalas a mano antes de usarlas en el informe)")
    for h in hallazgos or ["Sin señales automáticas (revísalo igualmente a mano)"]:
        print(f"- {h}")

    print("\n## Cuerpo en texto plano (primeros 3000 caracteres, desactivado)")
    cuerpo = plano.strip() or solo_texto(html_total)
    print(defang_texto(cuerpo[:3000]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 -I extrae_eml.py RUTA.eml")
    main(sys.argv[1])
