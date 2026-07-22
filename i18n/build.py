# -*- coding: utf-8 -*-
"""Erzeugt die uebersetzten Fassungen von index.html.

    python i18n/build.py            # alle Sprachen aus i18n/*.json
    python i18n/build.py en         # nur Englisch

Verfahren: index.html (deutsch) ist die einzige Quelle. Jede Sprachdatei
i18n/<code>.json enthaelt geordnete Ersetzungspaare auf dem rohen HTML.
Jedes Paar nennt, wie oft es vorkommen muss — stimmt die Zahl nicht, bricht
der Build ab. Dadurch bleibt kein deutscher Rest stehen, wenn sich die
Quelle aendert; der Fehler zeigt genau, welcher Baustein nachgezogen werden
muss.

Neue Sprache: i18n/<code>.json nach dem Muster von en.json anlegen und das
Kuerzel in der LANGS-Liste in index.html ergaenzen.
"""
import io, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'index.html')
I18N = os.path.join(BASE, 'i18n')
SITE = 'https://www.kiron.tech'


def build(code):
    spec = json.load(io.open(os.path.join(I18N, code + '.json'), encoding='utf-8'))
    html = io.open(SRC, encoding='utf-8').read()

    fehler = []
    for i, pair in enumerate(spec['pairs']):
        de, en = pair[0], pair[1]
        soll = pair[2] if len(pair) > 2 else 1
        ist = html.count(de)
        if ist != soll:
            fehler.append('  [%d] erwartet %dx, gefunden %dx: %r' % (i, soll, ist, de[:70]))
            continue
        html = html.replace(de, en)

    if fehler:
        print('BUILD ABGEBROCHEN (%s) — %d Bausteine passen nicht:' % (code, len(fehler)))
        print('\n'.join(fehler))
        print('\nTipp: python i18n/extract.py zeigt die aktuellen Textstellen.')
        return False

    # Sprachattribut
    html = html.replace('<html lang="de">', '<html lang="%s">' % code, 1)

    # hreflang: canonical zeigt auf die uebersetzte Fassung
    html = html.replace('<link rel="canonical" href="%s/">' % SITE,
                        '<link rel="canonical" href="%s/%s/">' % (SITE, code), 1)

    # Umschalter: aktive Sprache markieren
    html = html.replace('<a href="/"    hreflang="de" aria-current="true"',
                        '<a href="/"    hreflang="de" aria-current="false"', 1)
    html = html.replace('<a href="/%s/" hreflang="%s" aria-current="false"' % (code, code),
                        '<a href="/%s/" hreflang="%s" aria-current="true"' % (code, code), 1)

    # Rechtsseiten bleiben deutsch und liegen im Wurzelverzeichnis —
    # die absoluten Pfade stimmen daher unveraendert.

    out_dir = os.path.join(BASE, code)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    io.open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8', newline='\n').write(html)

    rest = re.findall(r'[A-Za-zÄÖÜäöü]*(?:ä|ö|ü|ß|Ä|Ö|Ü)[A-Za-zÄÖÜäöüß]*', html)
    rest = sorted({w for w in rest if len(w) > 3})
    print('%s/index.html geschrieben (%d Bausteine).' % (code, len(spec['pairs'])))
    if rest:
        print('  Hinweis: %d Woerter mit Umlauten uebrig — pruefen, ob uebersetzt gehoert:' % len(rest))
        print('  ' + ', '.join(rest[:25]) + (' …' if len(rest) > 25 else ''))
    return True


def main():
    codes = sys.argv[1:] or [f[:-5] for f in sorted(os.listdir(I18N)) if f.endswith('.json')]
    ok = all(build(c) for c in codes)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
