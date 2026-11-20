"""Noms à champ FIXE de 7 caractères (personnages, ennemis, objets, métiers, techniques).

Mesuré le 19/11/2026 : tables 0x313D0..0x38000 (pas 0x2F personnages/ennemis, 0x0E objets,
0x11 métiers, 0x0C techniques) ; le nom fait TOUJOURS 7 octets, complété par des espaces (E1).
Un champ = 7 octets où la ROM JP avait un kana (>= 0x2A) au premier octet et l'anglais une lettre.

  python tools/interface.py --rom JP.ngc --en-ips EN.ips --out interface_en.txt   (référence)
Traductions : lang/<code>/if_*.txt, `#ADRESSE<TAB>NOM` (7 caractères max, appliqué par build.py).
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import rom
import table

ROOT = Path(__file__).resolve().parent.parent
DOSSIER = ROOT / 'lang' / 'fr'     # dossier de la langue, fixé par build.py
ZONE = (0x313D0, 0x38000)
LEN = 7
LETTRES = set(range(0x00, 0x1A)) | set(range(0x20, 0x2A))
TXT = LETTRES | {0xE1, 0xCC, 0xCF, 0xCD, 0xC9, 0xCA, 0xD8, 0xCE}


TABLES = [   # (début, fin, pas) mesurés le 19/11/2026 — nom de 7 à la position la plus fréquente
    (0x313D0, 0x342DD, 0x2F),   # personnages, ennemis
    (0x342DD, 0x35100, 0x0E),   # objets (premier : STGUMS en 0x342DD)
    (0x361B0, 0x36A40, 0x11),   # métiers / techniques d'ennemis
    (0x36AB0, 0x37C4A, 0x0C),   # techniques
]
# Tableau des missions : fiche de 0x23 octets = titre 12 car. + client 7 car.
MISSIONS = (0x37C55, 0x37D8E, 0x23, ((0, 12), (12, 7)))


def champs(jp, en):
    """{adresse: longueur} calés sur le pas de chaque table."""
    brut = _candidats(jp, en)
    out = {}
    import collections
    for a, b, st in TABLES:
        c = collections.Counter(x % st for x in brut if a <= x < b)
        if not c:
            continue
        m = c.most_common(1)[0][0]
        r = a + ((m - a) % st)
        while r + LEN <= b:
            f = en[r:r + LEN]
            if en[r] in LETTRES and all(x in TXT for x in f) and f != jp[r:r + LEN]:
                out[r] = LEN
            r += st
    a, b, st, flds = MISSIONS
    for r in range(a, b, st):
        for o, n in flds:
            if en[r + o] in LETTRES and en[r + o:r + o + n] != jp[r + o:r + o + n]:
                out[r + o] = n
    return dict(sorted(out.items()))


def _candidats(jp, en):
    out, s = [], ZONE[0]
    while s < ZONE[1]:
        f = en[s:s + LEN]
        if (en[s] in LETTRES and jp[s] >= 0x2A and jp[s] != 0xE1 and all(c in TXT for c in f)):
            out.append(s)
            s += LEN
        else:
            s += 1
    return out


def charger_fr():
    fr, errs = {}, []
    for f in sorted(DOSSIER.glob('if_*.txt')):
        for n, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('##'):
                continue
            if not line.startswith('#') or '\t' not in line:
                errs.append('%s:%d : format attendu #ADRESSE<TAB>NOM' % (f.name, n))
                continue
            a, t = line[1:].split('\t', 1)
            fr[int(a, 16)] = (t.rstrip('\r\n'), '%s:%d' % (f.name, n))
    return fr, errs


def appliquer(out, jp, en, errs):
    fr, e = charger_fr()
    errs += e
    ok = champs(jp, en)
    for a, (t, where) in fr.items():
        if a not in ok:
            errs.append('%s : #%06X n\'est pas un champ nom' % (where, a))
            continue
        try:
            b = b''.join(x for x, _, _ in table.tokens(t))
        except ValueError as ex:
            errs.append('%s : %s' % (where, ex))
            continue
        n = ok[a]
        if len(b) > n:
            errs.append('%s : %r fait %d > %d caractères' % (where, t, len(b), n))
            continue
        out[a:a + n] = b + b'\xe1' * (n - len(b))
    return len(fr)


def appliquer_chaines(out, en, errs):
    """ui_*.txt : `$ADRESSE<TAB>LONGUEUR<TAB>TEXTE` — chaînes écrites EN PLACE dans le code.

    Le segment anglais en[ADRESSE:ADRESSE+LONGUEUR] est découpé aux FF ; le français doit avoir le
    même nombre de morceaux, chacun pas plus long que l'anglais, complété par des espaces (E1).
    Les FF restent donc exactement à leur place (listes lues par numéro).
    """
    n = 0
    for f in sorted(DOSSIER.glob('ui_*.txt')):
        for k, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            where = '%s:%d' % (f.name, k)
            try:
                adr, ln, t = line[1:].split('\t', 2)
                a, ln = int(adr, 16), int(ln)
                b = b''.join(x for x, _, _ in table.tokens(t.rstrip('\r\n')))
            except ValueError as ex:
                errs.append('%s : %s' % (where, ex))
                continue
            src = en[a:a + ln].split(b'\xff')
            dst = b.split(b'\xff')
            if len(src) != len(dst):
                errs.append('%s : %d morceaux (FF) au lieu de %d' % (where, len(dst), len(src)))
                continue
            res = []
            for i, (s, d) in enumerate(zip(src, dst)):
                if len(d) > len(s):
                    errs.append('%s : morceau %d trop long (%d > %d) : %s' % (where, i + 1, len(d), len(s), t))
                res.append(d[:len(s)] + b'\xe1' * (len(s) - len(d)))
            out[a:a + ln] = b'\xff'.join(res)
            n += 1
    return n


def appliquer_octets(out, en, errs):
    """patch_*.txt : `%ADRESSE<TAB>OCTETS_ANGLAIS<TAB>OCTETS_FRANÇAIS` (hexadécimal).

    Sert à agrandir les CADRES (plans de tuiles compressés, ex. menu principal en 0x30984 :
    octet = type de tuile (quart fort) + répétitions (quart faible), FE = ligne, FF = fin).
    L'octet anglais est VÉRIFIÉ avant remplacement.
    """
    n = 0
    for f in sorted(DOSSIER.glob('patch_*.txt')):
        for k, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            where = '%s:%d' % (f.name, k)
            try:
                adr, a_hex, b_hex = line[1:].split('\t')[:3]
                a, old, new = int(adr, 16), bytes.fromhex(a_hex), bytes.fromhex(b_hex)
            except ValueError as ex:
                errs.append('%s : %s' % (where, ex))
                continue
            if en[a:a + len(old)] != old or len(old) != len(new):
                errs.append('%s : octets anglais attendus %s, trouvés %s' % (where, old.hex(), en[a:a + len(old)].hex()))
                continue
            out[a:a + len(new)] = new
            n += 1
    return n


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', required=True)
    ap.add_argument('--en-ips', required=True)
    ap.add_argument('--out', default='interface_en.txt')
    args = ap.parse_args()
    jp, en = rom.load(args.rom, args.en_ips)
    L = ['#%06X\t%s%s' % (a, table.decode(en[a:a + n]).rstrip(), '' if n == LEN else '\t(%d car.)' % n)
         for a, n in champs(jp, en).items()]
    p = Path(args.out)
    tmp = p.with_suffix('.tmp')
    tmp.write_text('\n'.join(L) + '\n', encoding='utf-8')
    tmp.replace(p)
    print(len(L), 'champs ->', p)
