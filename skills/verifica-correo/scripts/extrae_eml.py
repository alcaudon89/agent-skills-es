#!/usr/bin/env python3
"""Extrae de un .eml los datos útiles para el análisis, ya desactivados (defang).

No abre enlaces, no guarda ni ejecuta adjuntos: solo lee el fichero y calcula hashes.
Uso: python3 -I extrae_eml.py RUTA.eml
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


def main(ruta):
    with open(ruta, "rb") as f:
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
    if OCULTO_RE.search(html_total):
        hallazgos.append("CSS que oculta texto (display:none, tamaño 0, opacidad 0…)")
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
    if html_total and len(solo_texto(html_total)) < 40 and re.search(r"<img\b", html_total, re.I):
        hallazgos.append("correo formado casi solo por imágenes")
    if plano and html_total:
        a, b = set(solo_texto(html_total).lower().split()), set(plano.lower().split())
        if a and b and len(a & b) / max(len(a | b), 1) < 0.3:
            hallazgos.append("las partes text/plain y text/html dicen cosas muy distintas")
    for h in hallazgos or ["Sin señales automáticas (revísalo igualmente a mano)"]:
        print(f"- {h}")

    print("\n## Cuerpo en texto plano (primeros 3000 caracteres, desactivado)")
    cuerpo = plano.strip() or solo_texto(html_total)
    print(defang_texto(cuerpo[:3000]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 -I extrae_eml.py RUTA.eml")
    main(sys.argv[1])
