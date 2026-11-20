"""Majuscules accentuées, dessinées à partir des lettres du jeu.

Lettres du jeu : 7 lignes (1..7) sur fond 1, tracé 2 ; ligne 0 vide.
Accentuée : accent sur les lignes 0-1, lettre ramenée à 6 lignes (2..7) en retirant une ligne
en double du milieu. Ç : C sur les lignes 0..5, cédille sur 6-7.
"""
import table

# Ligne à retirer pour passer de 7 à 6 lignes (index 1..7 dans le glyphe d'origine).
DROP = {'A': 3, 'E': 3, 'I': 3, 'O': 4, 'U': 3, 'C': 4}

ACCENTS = {   # 2 lignes, 8 colonnes ; '%' = tracé
    'aigu':   ['####%%##', '###%%###'],
    'grave':  ['##%%####', '###%%###'],
    'circ':   ['###%%###', '##%##%##'],
    'trema':  ['########', '#%%#%%##'],
}
SPEC = {
    'É': ('E', 'aigu'), 'È': ('E', 'grave'), 'Ê': ('E', 'circ'), 'Ë': ('E', 'trema'),
    'À': ('A', 'grave'), 'Â': ('A', 'circ'),
    'Ù': ('U', 'grave'), 'Û': ('U', 'circ'),
    'Î': ('I', 'circ'), 'Ï': ('I', 'trema'), 'Ô': ('O', 'circ'),
}


def rows_of(tile):
    return [[((tile[2 * y] | tile[2 * y + 1] << 8) >> (14 - 2 * x)) & 3 for x in range(8)] for y in range(8)]


def tile_of(rows):
    out = bytearray()
    for r in rows:
        w = 0
        for x, v in enumerate(r):
            w |= v << (14 - 2 * x)
        out += bytes([w & 0xFF, w >> 8])
    return bytes(out)


def glyph(rom, ch):
    c = table.CHARS[ch]
    return rows_of(rom[table.FONT + 16 * c:table.FONT + 16 * c + 16])


def pat(s):
    return [2 if k == '%' else 1 for k in s]


def build(rom):
    """{code: tuile 16 octets}"""
    out = {}
    for ch, (base, acc) in SPEC.items():
        g = glyph(rom, base)
        body = [g[y] for y in range(1, 8) if y != DROP[base]]
        out[table.CHARS[ch]] = tile_of([pat(ACCENTS[acc][0]), pat(ACCENTS[acc][1])] + body)
    g = glyph(rom, 'C')
    body = [g[y] for y in range(1, 8) if y != DROP['C']]
    out[table.CHARS['Ç']] = tile_of(body + [pat('###%####'), pat('##%%####')])
    # Point : le jeu a le « 。 » japonais (petit rond) ; on dessine un vrai point de 2x2 sur la ligne de base.
    out[table.CHARS['.']] = tile_of([pat('########')] * 6 + [pat('#%%#####')] * 2)
    return out
