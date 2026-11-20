"""Construit la ROM traduite (et le patch IPS) à partir de la ROM japonaise + patch anglais v0.9.

  python tools/build.py --rom JP.ngc --en-ips nigeronpa_en_0.9.ips [--lang fr] [--ips]
        -> out/<code>.ngc (+ out/<code>.ips, patch à appliquer sur la ROM JAPONAISE)
  python tools/build.py ... --identite -> sans traduction : doit redonner la ROM anglaise à l'octet près
  python tools/build.py ... --verif [--fichier X.txt] -> contrôle seulement

Traductions : lang/<code>/fr_*.txt, lignes `@ADRESSE<TAB>texte` (adresse = celle de en_script.txt,
produit par tools/extract.py).
Sans `/` dans le texte, les lignes sont coupées automatiquement à LARGEUR caractères.
`/` = retour à la ligne imposé, `{FD}` = attente. Lignes commençant par `#` = commentaires.
Le bloc de texte entier est reconstruit dans le MÊME ordre (les listes sont lues par numéro),
puis les 4 620 pointeurs sont recalculés.
"""
import sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import argparse
import zlib
from pathlib import Path
import rom
import table
import police_fr
import interface
import ips

ROOT = Path(__file__).resolve().parent.parent
DOSSIER = ROOT / 'lang' / 'fr'
LARGEUR = 18
GENERIQUE = (0x127B08, 0x127CFC)   # lignes du générique (préfixe de longueur), puis entrée vide = fin
# (début des fiches = 1er champ nom, fin, pas, décalage du mot 16 bits, tête de liste)
RELATIFS = [
    (0x313DD, 0x342DD, 0x2F, 45, 0x10004E),   # personnages -> biographies
    (0x342DD, 0x35100, 0x0E, 7, 0x100595),    # objets -> descriptions
    (0x36AB6, 0x37C4A, 0x0C, 7, 0x100595),    # techniques -> descriptions
]


def wrap(text, errs, where):
    if text.startswith('{UNELIGNE}'):            # une seule ligne imposée (marqueur « = »)
        text = text[len('{UNELIGNE}'):]
        toks = table.tokens(text.replace('{SANSCONTROLE}', ''))
        w = sum(x[1] for x in toks)
        if w > LARGEUR and not text.startswith('{SANSCONTROLE}'):
            errs.append('%s : ligne unique trop longue (%d > %d, noms comptés 7) : %s' % (where, w, LARGEUR, text))
        return b''.join(b for b, _, _ in toks)
    toks = table.tokens(text)
    manual = any(k == 'nl' for _, _, k in toks)
    if manual:
        col = 0
        for b, w, k in toks:
            col = 0 if k == 'nl' else col + w
            if col > LARGEUR:
                errs.append('%s : ligne trop longue (%d > %d) : %s' % (where, col, LARGEUR, text))
                break
        return b''.join(b for b, _, _ in toks)
    # découpage automatique par mots
    words, cur = [], []
    for t in toks:
        if t[2] == 'sp':
            if cur:
                words.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        words.append(cur)
    # Typographie française : « MAIS ENFIN ! » -> l'espace devant ! ? ; » … est INSÉCABLE.
    glue = {table.CHARS[c] for c in '!?»:…'}
    merged = []
    for wd in words:
        if merged and all(len(b) == 1 and b[0] in glue for b, _, _ in wd):
            merged[-1] = merged[-1] + [(bytes([0xE1]), 1, 'sp')] + wd
        else:
            merged.append(wd)
    words = merged
    # Espaces de tête / de fin = collage d'un nom par le jeu (« CONTRAT POUR » + nom) : on les garde.
    lead = len(text) - len(text.lstrip(' '))
    trail = len(text) - len(text.rstrip(' ')) if text.strip(' ') else 0
    out, col = bytearray(b'\xe1' * lead), lead
    for n, wd in enumerate(words):
        w = sum(x[1] for x in wd)
        if w > LARGEUR:
            errs.append('%s : mot trop long : %s' % (where, text))
        if n and col + 1 + w > LARGEUR:
            out.append(table.NEWLINE)
            col = 0
        elif n:
            out.append(0xE1)
            col += 1
        for b, ww, k in wd:
            out += b
        col += w
    out += b'\xe1' * trail
    return bytes(out)


def load_fr():
    fr = {}
    errs = []
    for f in sorted(DOSSIER.glob('fr_*.txt')):
        for n, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            if not line.startswith('@') or '\t' not in line:
                errs.append('%s:%d : format attendu @ADRESSE<TAB>texte' % (f.name, n))
                continue
            adr, txt = line[1:].split('\t', 1)
            # « @ADR=<TAB>texte » : une SEULE ligne, jamais coupée (fenêtre de combat : 1 ligne de 18 ;
            # une 2e ligne réutilise les tuiles de la 1re et écrase le cadre).
            uneligne = adr.rstrip('* ').endswith('=')
            a = int(adr.rstrip('* ').rstrip('='), 16)
            if a in fr:
                errs.append('%s:%d : @%06X déjà traduit' % (f.name, n, a))
            # NE PAS strip() : les espaces de tête placent le texte dans les menus.
            t = txt.rstrip('\r\n')
            if adr.rstrip('* ').endswith('=='):   # largeur vérifiée à la main (nombres courts)
                t = '{SANSCONTROLE}' + t
            fr[a] = (('{UNELIGNE}' + t) if uneligne else t, '%s:%d' % (f.name, n))
    return fr, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', required=True, help='ROM japonaise d origine (voir README)')
    ap.add_argument('--en-ips', required=True, help='patch anglais v0.9 d origine (nigeronpa_en_0.9.ips)')
    ap.add_argument('--lang', default='fr', help='dossier lang/<code>')
    ap.add_argument('--ips', action='store_true', help='écrire aussi out/<code>.ips (depuis la ROM japonaise)')
    ap.add_argument('--identite', action='store_true')
    ap.add_argument('--verif', action='store_true', help='contrôle seulement, aucune ROM écrite')
    ap.add_argument('--fichier', help='ne lister que les erreurs de ce fichier (ex. fr_12_dialogues.txt)')
    ap.add_argument('--out', help='ROM produite (défaut out/<code>.ngc)')
    args = ap.parse_args()
    global DOSSIER
    DOSSIER = ROOT / 'lang' / args.lang
    if not DOSSIER.is_dir():
        raise SystemExit('dossier introuvable : %s' % DOSSIER)
    interface.DOSSIER = DOSSIER
    if not args.out:
        args.out = str(ROOT / 'out' / (args.lang + '.ngc'))

    jp, en = rom.load(args.rom, args.en_ips)
    msgs = rom.messages(en)
    ptrs = rom.pointers(jp, en)
    fr, errs = ({}, []) if args.identite else load_fr()
    known = {s for s, _ in msgs}
    ends = dict(msgs)
    import re
    # {FA}{xx} = valeur qui CHANGE (nom du joueur, nombre) : obligatoire. {FB}{xx} = nom d'objet FIXE :
    # on peut l'écrire en toutes lettres en français (meilleure grammaire), donc non exigé.
    var = re.compile(r'\{FA\}\{[0-9A-Fa-f]{2}\}')
    for a, (txt, where) in fr.items():
        if a not in known:
            errs.append('%s : @%06X n\'est pas un début de message' % (where, a))
            continue
        en_txt = table.decode(en[a:ends[a]])
        if sorted(v.upper() for v in var.findall(txt)) != sorted(v.upper() for v in var.findall(en_txt)):
            errs.append('%s : variables {FA} différentes de l\'anglais (%s)' % (where, ' '.join(var.findall(en_txt)) or 'aucune'))
        if en_txt.startswith(' ') != txt.startswith(' '):
            errs.append('%s : l\'anglais %s par un espace, garder pareil' % (where, 'commence' if en_txt.startswith(' ') else 'ne commence pas'))

    block, newpos, done = bytearray(), {}, 0
    for s, e in msgs:
        newpos[s] = rom.TEXT_START + len(block)
        if s in fr and GENERIQUE[0] <= s < GENERIQUE[1]:
            # Générique : chaque ligne = [longueur+2] texte FF, lue à la suite jusqu'à une entrée vide.
            # « | » sépare plusieurs lignes (on peut en AJOUTER : rien ne les compte par numéro ensuite).
            txt, where = fr[s]
            parts = []
            for piece in txt.split('|'):
                try:
                    b = b''.join(x for x, _, _ in table.tokens(piece))
                except ValueError as ex:
                    errs.append('%s : %s' % (where, ex))
                    b = b''
                # Centrage du jeu (0x2020A7) : colonne = (0x12 - (longueur+2) + 1) & 0xFE -> 17 car. max.
                if len(b) > 17:
                    errs.append('%s : ligne de générique trop longue (%d > 17) : %s' % (where, len(b), piece))
                parts.append(bytes([len(b) + 2]) + b)
            block += b'\xff'.join(parts)
            done += 1
        elif s in fr:
            txt, where = fr[s]
            try:
                block += wrap(txt, errs, where)
            except ValueError as ex:
                errs.append('%s : %s' % (where, ex))
            done += 1
        else:
            block += en[s:e]
        block.append(table.END)
    end = rom.TEXT_START + len(block)
    if end > rom.FREE_END:
        errs.append('texte trop long : fin 0x%X > 0x%X' % (end, rom.FREE_END))
    noms = 0 if args.identite else interface.appliquer(bytearray(en), jp, en, errs)
    chaines = 0 if args.identite else interface.appliquer_chaines(bytearray(en), en, errs)
    rustines = 0 if args.identite else interface.appliquer_octets(bytearray(en), en, errs)
    if args.fichier:
        errs = [e for e in errs if e.startswith(args.fichier + ':')]
    if args.verif:
        print('\n'.join(errs) if errs else 'aucune erreur')
        print('%d message(s) traduits au total' % done)
        sys.exit(1 if errs else 0)
    if errs:
        print('\n'.join(errs))
        print('%d erreur(s), ROM NON écrite' % len(errs))
        sys.exit(1)

    out = bytearray(en)
    # effacer l'ancien bloc (FF = vide), écrire le nouveau
    out[rom.TEXT_START:rom.TEXT_END] = b'\xff' * (rom.TEXT_END - rom.TEXT_START)
    out[rom.TEXT_START:end] = block
    for i, t in ptrs:
        a = rom.CPU_BASE + newpos[t]
        out[i:i + 3] = bytes([a & 0xFF, a >> 8 & 0xFF, a >> 16])
    # POSITIONS RELATIVES dans les fiches (mesuré 19/11) : la description d'un objet / d'une technique
    # = tête 0x100595 + mot 16 bits de la fiche ; la biographie d'un personnage = 0x10004E + mot.
    # Si le texte change de longueur, ces positions doivent suivre (sinon : 1re lettre mangée, etc.).
    for base, fin_t, st, f, head in RELATIFS:
        for r in range(base, fin_t - st + 1, st):
            v = en[r + f] | en[r + f + 1] << 8
            t = head + v
            if en[r + f:r + f + 2] != jp[r + f:r + f + 2] and t in newpos:
                nv = newpos[t] - newpos[head]
                out[r + f:r + f + 2] = bytes([nv & 0xFF, nv >> 8])
    if not args.identite:
        for code, tile in police_fr.build(en).items():
            out[table.FONT + 16 * code:table.FONT + 16 * code + 16] = tile
        interface.appliquer(out, jp, en, [])
        interface.appliquer_chaines(out, en, [])
        interface.appliquer_octets(out, en, [])

    if args.identite:
        same = bytes(out) == en
        print('identité :', 'OK, ROM anglaise reproduite à l\'octet près' if same else 'ÉCHEC')
        sys.exit(0 if same else 1)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_bytes(out)
    tmp.replace(p)
    if args.ips:
        patch = ips.make(jp, bytes(out))
        assert ips.apply(jp, patch) == bytes(out), 'IPS : relecture différente'
        q = p.with_suffix('.ips')
        tmp = q.with_suffix('.tmp')
        tmp.write_bytes(patch)
        tmp.replace(q)
        print('patch IPS (sur la ROM japonaise) : %d octets -> %s' % (len(patch), q))
    print('%d noms, %d chaînes d\'interface, %d rustines de cadre' % (noms, chaines, rustines))
    print('%d messages traduits / %d ; texte 0x%X..0x%X (%d octets, %d libres) ; CRC32 %08X -> %s' % (
        done, len(msgs), rom.TEXT_START, end, len(block), rom.FREE_END - end, zlib.crc32(out), p))


main()
