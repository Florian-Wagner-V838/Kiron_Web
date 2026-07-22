# -*- coding: utf-8 -*-
"""Listet alle uebersetzbaren Textstellen aus index.html auf.

Hilfsskript fuer die Pflege der Sprachdateien: zeigt, welche Strings in
i18n/<lang>.json vorkommen muessen. Aendert nichts.

    python i18n/extract.py            # alle Segmente
    python i18n/extract.py --missing  # nur die, die in en.json fehlen
"""
import io, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'index.html')

# Attribute, deren Inhalt sichtbarer Text ist
ATTRS = ('alt', 'placeholder', 'aria-label', 'title', 'content')


def segments(html):
    """Liefert alle uebersetzbaren Strings in Reihenfolge des Auftretens."""
    out = []

    # <title> und meta description
    for m in re.finditer(r'<title>(.*?)</title>', html, re.S):
        out.append(m.group(1).strip())
    for m in re.finditer(r'<meta name="description" content="(.*?)"', html, re.S):
        out.append(m.group(1).strip())

    body = html.split('<body>', 1)[1] if '<body>' in html else html
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)

    # Chat-Antworten und Datenstrings im Script separat behandeln
    script = ''
    m = re.search(r'<script>(.*?)</script>', body, re.S)
    if m:
        script = m.group(1)
        body = body.replace(m.group(0), '')

    # Attribute
    for m in re.finditer(r'\b(' + '|'.join(ATTRS) + r')="([^"]{2,})"', body):
        val = m.group(2).strip()
        if val and not val.startswith(('http', '/', '#')) and re.search(r'[A-Za-zÄÖÜäöüß]', val):
            out.append(val)

    # Textknoten
    for chunk in re.split(r'<[^>]+>', body):
        t = re.sub(r'\s+', ' ', chunk).strip()
        if len(t) >= 2 and re.search(r'[A-Za-zÄÖÜäöüß]{2,}', t):
            out.append(t)

    # Strings im Script (einfache und doppelte Anfuehrungszeichen)
    for m in re.finditer(r"'((?:[^'\\]|\\.){8,}?)'", script):
        t = m.group(1)
        if re.search(r'[A-Za-zÄÖÜäöüß]{3,}', t) and not re.match(r'^[a-z_]+$', t) \
           and 'http' not in t and not t.startswith('.') and not t.startswith('#'):
            out.append(t)

    # Duplikate raus, Reihenfolge halten
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def main():
    html = io.open(SRC, encoding='utf-8').read()
    segs = segments(html)

    if '--missing' in sys.argv:
        path = os.path.join(BASE, 'i18n', 'en.json')
        have = json.load(io.open(path, encoding='utf-8')) if os.path.exists(path) else {}
        segs = [s for s in segs if s not in have]
        print('# %d Segmente ohne Uebersetzung' % len(segs))

    print(json.dumps({s: '' for s in segs}, ensure_ascii=False, indent=1))
    sys.stderr.write('%d Segmente\n' % len(segs))


if __name__ == '__main__':
    main()
