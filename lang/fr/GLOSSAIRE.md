# Glossaire et règles de style — Nige-Ron-Pa en français

## Contexte
RPG comique (Dennou Eizo, 1999). Le héros ({FA}{00}, un GARÇON paresseux, nom choisi par le joueur)
passe l'examen d'aptitude pour devenir « travailleur » (sorte d'aventurier à licences/métiers) avec
REMA (sa « grande soeur » d'adoption, autoritaire, elle s'emporte vite) et MOMO (fille-chat, « NYA »).
Ton : comédie légère, répliques vives, registre familier entre amis, poli avec les adultes/clients.

## Noms propres (garder tels quels)
Personnages : REMA, MOMO, KEITH (KEITH-SENPAI), SORU (SORU-SENPAI), UMARU, SHARON, MEL, EMIRU, GARTER,
MAR, ODA, TONY, BILLY, GEIJI, PONPOKO, REIKA, GORO, KIRARA, APPO, GERO, MEKAHACHI, POCHIRIN, KEI.
Lieux : ROUGE, LIP, CUFFS, SLIP (forêt de SLIP, スリップ), ÉTOLE (ストール ; « D'ÉTOLE »), RAGURAN (ruines de RAGURAN), SABOT/SABO.
Suffixes japonais gardés : -SENPAI, -CHAN, -SAN.

## Japonismes (décision de Tixul, 19/11) : garder les TERMES D'ADRESSE japonais, traduire tout le reste
Le public francophone connaît ces mots ; « GRANDE SOEUR » sonne mal. Écriture courante :
- おねえちゃん / おねえさん -> ONEE-CHAN / ONEE-SAN ; ねえさま / おねえさま -> ONEE-SAMA (quand on S'ADRESSE à
  elle ou qu'on la NOMME : « ONEE-CHAN ! », « ONEE-CHAN EST PARTIE »). « MA GRANDE SOEUR » reste possible quand
  on décrit le lien de parenté à un tiers.
- おにいちゃん -> ONII-CHAN ; あにき -> ANIKI.
- Suffixes : -SAN, -CHAN, -KUN, -SAMA, -SENPAI, -SENSEI (センセ) gardés derrière les noms.
- Tout le reste se TRADUIT (pas de « ARIGATOU », « KAWAII », etc. ; mais onomatopées/cris libres).

## Termes
| anglais | français |
|---|---|
| WORKER | TRAVAILLEUR (fém. TRAVAILLEUSE) |
| WORK TEST / WORKER TEST | EXAMEN D'APTITUDE |
| LICENSE / LICENCE | LICENCE |
| JOB (métier) | JOB / MÉTIER selon la phrase |
| WORK (une mission) | MISSION / BOULOT |
| REQUESTER / CLIENT | CLIENT |
| DEVIL KING | ROI DÉMON |
| MAZOKU | MAZOKU (peuple démon, invariable) |
| MATERIA | MATERIA |
| WORKSHOP | ATELIER |
| LOUNGE | SALON |
| BADGE | INSIGNE |
| DEN / DENN (monnaie) | DEN |
| BIG SIS | GRANDE SOEUR |
| BIG BROTHER | GRAND FRÈRE |
| CHAMPIONS OF JUSTICE | CHAMPIONS DE LA JUSTICE |
| GRAVE-ROBBERS | PILLEURS DE TOMBES |
| PRINCESS | PRINCESSE |
| ROMPA TRIO | TRIO ROMPA |
| PARTY (groupe) | ÉQUIPE |
| HP / MP | PV / PM |
| EXP | EXP |

## Règles techniques (VÉRIFIÉES par `python tools/build.py --rom JP.ngc --en-ips EN.ips --verif`)
- Une ligne par message : `@ADRESSE<TAB>TEXTE` (copier l'adresse de en_script.txt, SANS l'astérisque).
- MAJUSCULES uniquement. Accents disponibles : É È Ê Ë À Â Ç Ù Û Î Ï Ô. PAS de Œ (écrire OE), pas de minuscules.
- Caractères autorisés : A-Z 0-9 espace ! ? . , ' - … ~ ♪ ♥ ( ) « » + % ★ : = et les accents ci-dessus.
  Pas de « ; », pas de guillemets droits ", pas de « / » dans les dialogues.
- Ne PAS mettre de « / » : les lignes (18 caractères) sont coupées automatiquement.
- Codes entre accolades : les recopier À L'IDENTIQUE.
  - {FA}{xx} et {FB}{xx} (noms, objets) : OBLIGATOIRES, même nombre et mêmes valeurs que l'anglais.
  - {FC}{xx} = petite pause ; {FD} = attente du bouton : à garder, placés au même endroit du sens.
  - {EA} (colère), {EB} (goutte de gêne), {D0}, {7F}, {8E}… = symboles : à garder.
- Si l'anglais commence par un espace, le français aussi (fragment collé à un nom par le jeu).
- Typographie : espace avant ! ? : (« QUOI ?! », « MAIS ENFIN ! »), « ... » s'écrit … ; guillemets «TEXTE» sans espaces internes.
- Un mot de plus de 18 caractères est refusé.
- Lignes « TEXTE 1234 », « TO TRANSLATE » ou vides : NE PAS les traduire (les omettre).
- Localiser = ADAPTER : chaque réplique doit être naturelle en français et avoir du sens seule ;
  le japonais d'origine fait foi ; l'anglais sert de repère, sans inventer d'information.
  Accords : ⚠ CORRIGÉ 19/11 d'après le japonais : le personnage joué ({FA}{00}, nom par défaut RIO) est une
  FILLE (« あたし », « …わよ », « なによぉ », Momo l'appelle « {FA}{00}-CHAN ») — tout accord la concernant
  au FÉMININ (fatiguée, prête, contente…). REMA, MOMO, SHARON, MEL, REIKA sont aussi des filles.
  ⚠ Corrigé le 19/11 d'après les biographies japonaises : EMIRU (mangaka « okama ») et KIRARA (son grand
  frère) sont des HOMMES qui se présentent en femmes (« あたい ») : le féminin dans leurs répliques est voulu,
  les fans les croient « soeurs ».

## Mots insérés par le jeu : {FB}{xx} = nom de l'OBJET n°xx (table 0x342CF + 14*xx, 7 caractères)
Vérifié sur la ROM japonaise : 61 WORKSHOP (l'entreprise), 62 LICENCE, 63 LA BASE (ワークベース), 64 EXAMEN,
65 ACADÉMIE, 66 TOUR DE HEEL, 67 GRANDE SOEUR (おねえちゃん), 68 TRIO ROMPA, 69 KEITH-SAMA, 6A KEITH-SENPAI,
6C « ARIGATOU », E0 CONVOCATION, E2 INSIGNE DE TRAVAILLEUR, E5 REMÈDE DE MANITO, E6 CPU DRAGON, E7 CHÈQUE,
E8 INSIGNE DE HÉROS, E9 MIROIR DES TÉNÈBRES, EC PASSEPORT. Le mot affiché est celui de trad/if_01_noms.txt.
