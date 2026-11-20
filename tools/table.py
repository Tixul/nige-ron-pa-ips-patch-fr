"""Table de caractères de Nige-Ron-Pa (police du jeu, glyphe(code) = fichier 0xC38D4 + 16*code).

A..Z = 0x00..0x19 et 0..9 = 0x20..0x29 existent DÉJÀ dans la police japonaise.
Les majuscules accentuées sont dessinées par tools/police_fr.py sur des cases de hiragana
jamais affichées par le script (0x42..0x50, sauf 0x45/0x4A/0x4E qui servent de paramètres).

Contrôles : FE = retour à la ligne, FD = attente/page, FF = fin de message.
FA/FB/FC + 1 octet = variable (nom, objet…) : écrit {FA}{xx} dans les fichiers texte.
Tout autre octet s'écrit {XX}.
"""
import re

FONT = 0xC38D4

CHARS = {}
for i in range(26):
    CHARS[chr(65 + i)] = 0x00 + i
for i in range(10):
    CHARS[str(i)] = 0x20 + i
CHARS.update({
    ' ': 0xE1, '!': 0xC9, '?': 0xCA, '.': 0xCC, "'": 0xCD, '-': 0xCF, ',': 0x1B,
    '…': 0xD9, '~': 0xD1, '♪': 0xD7, '♥': 0xE5, '(': 0x5E, ')': 0x5F,
    '«': 0x8E, '»': 0x8F, '+': 0xCE, '%': 0xD8, '★': 0xCB, ':': 0xEE, '=': 0xE6, '○': 0xD5,
    # Majuscules accentuées (dessinées par police_fr.py)
    'É': 0x42, 'È': 0x43, 'Ê': 0x44, 'À': 0x46, 'Â': 0x47, 'Ç': 0x48,
    'Ù': 0x49, 'Û': 0x4B, 'Î': 0x4C, 'Ï': 0x4D, 'Ô': 0x4F, 'Ë': 0x50,
})
NEWLINE, PAGE, END = 0xFE, 0xFD, 0xFF
VARS = (0xFA, 0xFB, 0xFC)          # suivies d'un octet paramètre
# Les accents n'existent pas dans la ROM anglaise : au décodage de l'anglais on ne les sort pas.
DEC = {v: k for k, v in CHARS.items() if k not in 'ÉÈÊÀÂÇÙÛÎÏÔË'}

# Largeur estimée (en cases) d'une variable, pour le découpage automatique des lignes.
VAR_WIDTH = {0xFA: 7, 0xFB: 10, 0xFC: 0}


def decode(data: bytes) -> str:
    """Octets d'UN message (sans le FF final) -> texte. FE = '/', FD = '{FD}'."""
    out, i = [], 0
    while i < len(data):
        c = data[i]
        if c in VARS and i + 1 < len(data):
            out.append('{%02X}{%02X}' % (c, data[i + 1]))
            i += 2
            continue
        if c == NEWLINE:
            out.append('/')
        elif c in DEC:
            out.append(DEC[c])
        else:
            out.append('{%02X}' % c)
        i += 1
    return ''.join(out)


TOKEN = re.compile(r'\{([0-9A-Fa-f]{2})\}|(.)', re.S)


def tokens(text: str):
    """Texte -> liste d'unités (octets, largeur, genre). genre : 'c' car., 'nl', 'pg', 'sp', 'var', 'raw'."""
    out = []
    toks = TOKEN.findall(text)
    i = 0
    while i < len(toks):
        hx, ch = toks[i]
        if hx:
            v = int(hx, 16)
            if v in VARS and i + 1 < len(toks) and toks[i + 1][0]:
                p = int(toks[i + 1][0], 16)
                out.append((bytes([v, p]), VAR_WIDTH[v], 'var'))
                i += 2
                continue
            if v == NEWLINE:
                out.append((bytes([v]), 0, 'nl'))
            elif v == PAGE:
                out.append((bytes([v]), 0, 'pg'))
            else:
                out.append((bytes([v]), 1, 'raw'))
        elif ch == '/':
            out.append((bytes([NEWLINE]), 0, 'nl'))
        elif ch == ' ':
            out.append((bytes([0xE1]), 1, 'sp'))
        elif ch in CHARS:
            out.append((bytes([CHARS[ch]]), 1, 'c'))
        else:
            raise ValueError('caractère inconnu %r dans %r' % (ch, text))
        i += 1
    return out
