"""Extrait le script anglais -> en_script.txt (référence pour traduire).

Une ligne par message : `@ADRESSE<TAB>texte`. `*` après l'adresse = message pointé par un événement
(les autres sont des éléments de listes parcourues par numéro). `/` = retour à la ligne.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import rom
import table

ROOT = Path(__file__).resolve().parent.parent

import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--rom', required=True)
ap.add_argument('--en-ips', required=True)
ap.add_argument('--out', default='en_script.txt')
args = ap.parse_args()
jp, en = rom.load(args.rom, args.en_ips)
msgs = rom.messages(en)
ptrs = rom.pointers(jp, en)
pointed = {t for _, t in ptrs}
lines = []
for s, e in msgs:
    lines.append('@%06X%s\t%s' % (s, '*' if s in pointed else ' ', table.decode(en[s:e])))
out = Path(args.out)
tmp = out.with_suffix('.tmp')
tmp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
tmp.replace(out)
print('%d messages, %d pointeurs (%d cibles) -> %s' % (len(msgs), len(ptrs), len(pointed), out))
