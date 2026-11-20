"""Décodage du texte JAPONAIS d'origine (table lue sur la police du jeu, 19/11/2026).

  python tools/jp.py JP.ngc ADRESSE_FICHIER [nombre_de_messages]
"""
import sys
sys.dont_write_bytecode = True

T = {}
for i in range(26):
    T[i] = chr(65 + i)
for i in range(10):
    T[0x20 + i] = str(i)
for base, s in ((0x1A, 'ぁぃぅぇぉっ'), (0x2A, 'ァィゥェォッ'),
                (0x30, 'あいうえおかきくけこさしすせそた'), (0x40, 'ちつてとなにぬねのはひふへほまみ'),
                (0x50, 'むめもやゆよらりるれろわをん()'), (0x60, 'アイウエオカキクケコサシスセソタ'),
                (0x70, 'チツテトナニヌネノハヒフヘホマミ'), (0x80, 'ムメモヤユヨラリルレロワヲン『』'),
                (0x90, 'がぎぐげござじずぜぞだぢづでどば'), (0xA0, 'びぶべぼぱぴぷぺぽゃゅょャュョ・'),
                (0xB0, 'ガギグゲゴザジズゼゾダヂヅデドバ'), (0xC0, 'ビブベボパピプペポ!?★。、+ー'),
                (0xD0, '※~/♀♂○×♪%…月日人')):
    for k, ch in enumerate(s):
        T[base + k] = ch
T.update({0xE1: '　', 0xE4: 'ー', 0xE5: '♥', 0xE6: '=', 0xE0: '円', 0xFE: '/', 0xFD: '{FD}'})


def decode(b):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if c in (0xFA, 0xFB, 0xFC) and i + 1 < len(b):
            out.append('{%02X}{%02X}' % (c, b[i + 1]))
            i += 2
            continue
        out.append(T.get(c, '{%02X}' % c))
        i += 1
    return ''.join(out)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    jp = open(sys.argv[1], 'rb').read()
    a = int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    for _ in range(n):
        e = jp.index(b'\xff', a)
        print('%06X\t%s' % (a, decode(jp[a:e])))
        a = e + 1
