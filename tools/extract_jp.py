"""Script JAPONAIS aligné sur les adresses anglaises -> jp_script.txt (`@ADRESSE<TAB>japonais`).

Chaque pointeur réécrit par le patch anglais remplace, AU MÊME ENDROIT de la ROM japonaise, un
pointeur vers le message japonais d'origine : on lit donc le message JP au bout de ce pointeur.
Les messages de listes (non pointés) sont alignés par numéro derrière le dernier message pointé.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import rom
import jp as J
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--rom', required=True)
ap.add_argument('--en-ips', required=True)
ap.add_argument('--out', default='jp_script.txt')
args = ap.parse_args()
jp, en = rom.load(args.rom, args.en_ips)
msgs = rom.messages(en)
idx = {s: k for k, (s, _) in enumerate(msgs)}
jp_of = {}
for i, t in rom.pointers(jp, en):
    j = (jp[i + 2] - 0x20) << 16 | jp[i + 1] << 8 | jp[i]
    jp_of.setdefault(t, j)
lines, cur = [], None
for s, e in msgs:
    if s in jp_of:
        cur = jp_of[s]
    if cur is None or cur >= len(jp):
        lines.append('@%06X\t' % s)
        continue
    z = jp.find(b'\xff', cur)
    lines.append('@%06X\t%s' % (s, J.decode(jp[cur:z])))
    cur = z + 1
out = Path(args.out)
tmp = out.with_suffix('.tmp')
tmp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
tmp.replace(out)
print(len(lines), '->', out)
