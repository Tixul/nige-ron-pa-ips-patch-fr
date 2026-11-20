# Nige-Ron-Pa — notes techniques (ROM, texte, interface)

Tout ce qui suit a été mesuré sur la ROM japonaise et sur la traduction anglaise v0.9
(patch de Loïc / JinRawX, 2018), sur laquelle la version française est construite.

## Chaîne de construction
`tools/build.py` : ROM japonaise → (+ patch anglais v0.9, appliqué en mémoire) → ROM anglaise
2 Mio → texte français, noms, interface, police → ROM française → patch IPS **depuis la ROM
japonaise**. Contrôle d'identité : `--identite` sans traduction redonne la ROM anglaise à l'octet près.

## Le texte (bloc de dialogues)
- Le patch anglais a sorti tout le script du code : fichier 0x100000..0x127D10, 4 857 messages
  finis par `FF`. Place libre jusqu'à 0x1F8000 (0x1F8000.. = sauvegarde, jamais touchée).
- **Pointeurs** (4 620) : `A0 lo hi 3x 00` dans les événements (adresse CPU 0x30xxxx = fichier
  0x10xxxx), `44 lo hi 30 00` pour le combat, `f2 lo hi 32` pour le générique. `tools/rom.py`
  les retrouve : réécrits par le patch anglais, vers un début de message, à la place d'un pointeur
  japonais vers 0x20..0x2Fxxxx, et pas la lecture décalée d'un octet d'un vrai pointeur.
- Les messages non pointés sont des **listes lues par numéro** (objets, humeurs de Momo,
  biographies, générique) : `build.py` reconstruit le bloc **dans le même ordre, avec le même
  nombre de messages**, puis recalcule tous les pointeurs.
- **Positions relatives** dans les fiches (mot 16 bits) : objets (+7) et techniques (+7) vers leur
  description depuis @100595, personnages (+45) vers leur biographie depuis @10004E.
  `build.py` les recalcule (sinon la description perd ses premières lettres).

## Encodage (police du jeu, 2 bpp, glyphe(code) = fichier 0xC38D4 + 16 × code)
| codes | contenu |
|---|---|
| 00..19 | A..Z |
| 20..29 | 0..9 |
| 1A..1F, 2A..C8 | kana (police d'origine) |
| 42 43 44 46 47 48 49 4B 4C 4D 4F 50 | **É È Ê À Â Ç Ù Û Î Ï Ô Ë** dessinés par `tools/police_fr.py` sur des kana |
| E1 | espace ; C9 `!` ; CA `?` ; CC `.` (redessiné : le jeu avait un « 。 ») ; CD `'` ; CF `-` ; 1B `,` |
| D9 `…` ; D1 `~` ; D7 `♪` ; E5 `♥` ; 5E/5F `( )` ; 8E/8F `« »` ; EA colère ; EB goutte | |
| FE | retour à la ligne ; FD attente ; FF fin |
| FA xx | valeur qui change (FA 00 = nom de l'héroïne ou un nombre) — **obligatoire** |
| FB xx | **nom de l'objet n° xx** (fiche 0x342CF + 14 × xx) — fixe, peut s'écrire en toutes lettres |
| FC xx | petite pause |

Tous les kana encore utilisés par l'interface ont été traduits : sinon un kana 0x42..0x50
s'afficherait comme une lettre accentuée.

## Fenêtres
- **Dialogues** : 18 caractères par ligne, la fenêtre défile → aucune limite de longueur par
  message. Sans `/`, `build.py` coupe les lignes tout seul (espace insécable devant `! ? : » …`).
- **Combat** : fenêtre d'**une seule ligne**. Une deuxième ligne réutilise les tuiles de la
  première et écrase le cadre (mot répété, restes). Les messages de combat sont marqués
  `@ADRESSE=` (une ligne, 18 car. contrôlés) ou `@ADRESSE==` (largeur vérifiée à la main).
- **Générique** : chaque ligne commence par un octet = longueur + 2 ; lecture jusqu'à une entrée
  vide ; centrage du jeu (0x2020A7) → **17 caractères max**. `|` ajoute des lignes.
- **Cadres** : plans de tuiles compressés (octet = type × 16 + répétitions, `FE` ligne, `FF` fin).
  Élargir un cadre = augmenter les répétitions de chaque ligne (`patch_*.txt`, octets anglais vérifiés).
  Le menu principal (0x30984) passe de 6 à 8 cases utiles.

## Noms à taille fixe (`if_*.txt`)
Tables 0x313D0..0x37C4A, **7 caractères** par nom (pas 0x2F personnages/ennemis, 0x0E objets,
0x11 métiers, 0x0C techniques), titres de missions 12 + 7 (0x37C55). Pas d'**espace interne**
(GOMME-P) : le jeu semble couper un nom à la première espace.

## Chaînes en place dans le code (`ui_*.txt`)
`$ADRESSE<TAB>LONGUEUR<TAB>TEXTE` : le segment est découpé aux `FF` ; chaque morceau français
ne dépasse pas le japonais/l'anglais et est complété par des espaces (les `FF` ne bougent pas).
Fiche des stats : 4 caractères avant la valeur (うん = **CHA.**, にんたい = **ENDU**).

## Le patch IPS
La ROM passe de 1 Mio à 2 Mio. Les patcheurs agrandissent le fichier mais ne le remplissent pas
de la même façon (00 pour Flips/Lunar IPS, FF pour NgpCraft Emulator) : `tools/ips.py` écrit
donc **toute** la partie ajoutée (en RLE), pour obtenir la même ROM partout.

## Choix de traduction (résumé de `lang/fr/GLOSSAIRE.md`)
- Toutes les répliques relues **sur le japonais d'origine** (l'anglais v0.9 a servi de point de départ).
- L'héroïne (nom par défaut RIO) est une **fille** ; Momo est une fille-chat (« NYA »).
- Termes d'adresse japonais gardés : ONEE-CHAN, ANIKI, -SAN, -CHAN, -KUN, -SAMA, -SENPAI, -SENSEI.
- Lieux au thème vêtements du japonais : ROUGE, LIP, CUFFS, GARTER, TUNIC, MULE, SABOT, **SLIP**,
  **ÉTOLE**.
