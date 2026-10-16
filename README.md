<div align="center">

# 🎮 SOKOBAN

### Modélisation & résolution automatique par recherche de solutions

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-FFD43B?style=flat-square&logo=pygame&logoColor=black)
![Levels](https://img.shields.io/badge/niveaux-30-EA4335?style=flat-square)
![Algorithms](https://img.shields.io/badge/BFS%20%C2%B7%20DFS%20%C2%B7%20A*%20-4285F4?style=flat-square)
![Status](https://img.shields.io/badge/statut-complet-brightgreen?style=flat-square)

**Jeu pixel-art jouable à la main + moteur de recherche qui résout les niveaux tout seul
(BFS, DFS, A\*) et les compare côte à côte.**

<img src="docs/compare.png" alt="Panneau Machine : comparaison BFS / DFS / A*" width="92%">

</div>

---

## ✨ Fonctionnalités

- 🕹️ **Jeu complet** — déplacement fluide (animations, 2 frames de marche par direction),
  annulation, redémarrage, déplacement continu en maintenant une touche.
- 🤖 **Mode Machine** — lancez BFS, DFS ou A\* sur le niveau courant et **regardez la solution
  se rejouer** pas à pas (lecture / pause / pas à pas / vitesse variable).
- 📊 **Tableau comparatif intégré** — coût, nœuds développés, nœuds générés et temps
  de mesure des 3 algorithmes, sur le même niveau.
- 🗺️ **30 niveaux** générés puis validés automatiquement — du tutoriel (1-2 caisses)
  aux **niveaux Experts** (4-6 caisses) où A\* déploie plus de **400 000 nœuds**.
  **Les 3 algorithmes (BFS, DFS, A\*) résolvent les 30 niveaux** — vérifié par
  `python tools/make_levels.py --check`.
- 🧩 **Éditeur de niveaux en texte** — un niveau = un fichier `.txt` dessiné avec des caractères,
  validé et testé en un `python tools/check_levels.py`.
- 🎨 **Pixel art dungeon** — tileset *2D Pixel Dungeon Asset Pack*, torches animées, portes,
  murs et sol à variantes aléatoires, particules et parallaxe.
- 🔊 **Sons & musique** — 8 effets (pas, poussée, mur, cible, annulation, clic, victoire) + musique,
  tous remplaçables par vos fichiers.
- 💾 **Options sauvegardées** — vitesse, algorithme par défaut, plein écran, son, progression
  (`settings.json`).
- 🎉 **Victoire figée** — une fois le niveau réussi, le joueur **ne bouge plus** :
  plus aucune touche de déplacement ni d'annulation, mais les boutons
  **Niveau suivant**, **Accueil** et le mode **Machine** restent utilisables
  (Entrée = niveau suivant).
- 🧠 **Architecture « vraie IA »** — modélisation du problème découplée des algorithmes :
  on ajoute un algorithme en **une ligne**.

---

## 🎮 Jouer sur Windows — sans rien installer

> **[⬇ Télécharger `Sokoban.exe`](https://github.com/trrayane/Sokoban/releases/latest)** —
> un seul fichier, **Python non requis**.
>
> 1. Téléchargez `Sokoban.exe` depuis la dernière release.
> 2. Double-cliquez dessus — c'est tout. (Si Windows SmartScreen s'affiche :
>    *Plus d'infos* → *Exécuter quand même*.)
>
> L'exécutable embarque le jeu complet (30 niveaux, sprites, sons, polices) —
> vos options et votre progression sont sauvegardées dans `settings.json`
> à côté du `.exe`.

## 🚀 Démarrage rapide (source)

```bash
git clone https://github.com/trrayane/Sokoban.git
cd Sokoban

pip install -r requirements.txt   # pygame>=2.5
python main.py                    # écran d'accueil
```

Modes avancés :

```bash
python main.py --level 5                          # lance directement le niveau 5
python main.py --cli --level 10 --algo "A*"       # résolution en console, sans fenêtre
python tools/check_levels.py                      # valide & teste tous vos niveaux
python tools/generate_assets.py                   # régénère les sprites par défaut
python tools/generate_sounds.py                   # régénère les sons par défaut
```

> **Première exécution :** si des sprites manquent, le jeu les génère automatiquement avant
> d'afficher le menu — vous n'avez rien à configurer.

---

## 🕹️ Commandes

| Touche | Action |
|---|---|
| ↑ ↓ ← → / **ZQSD** / **WASD** | déplacement (maintenir = mouvement continu) |
| **U** / Retour arrière | annuler le dernier coup |
| **R** | recommencer le niveau |
| **M** ou bouton **Machine** | choisir l'algorithme (BFS / DFS / A\*) ou comparer les 3 |
| **N** ou bouton **Son** | son on / off (sauvegardé) |
| **F11** ou Options → Plein écran | plein écran / fenêtre (repli automatique si le GPU refuse) |
| **Espace** | lecture / pause de la simulation |
| **[** **]** ou **PgUp / PgDn** | niveau précédent / suivant |
| **+** / **−** | vitesse de simulation |
| **Échap** | écran précédent (jeu → niveaux → accueil) |

---

## 🖥️ L'interface

| Accueil | Sélection des niveaux |
|---|---|
| <img src="docs/menu.png" alt="Menu principal" width="100%"> | <img src="docs/levels.png" alt="Sélection des niveaux" width="100%"> |

| Jeu | Options |
|---|---|
| <img src="docs/gameplay.png" alt="Partie en cours" width="100%"> | <img src="docs/options.png" alt="Options" width="100%"> |

---

## 🧠 Partie A — Modélisation du problème

Le problème est indépendant de l'affichage (`core/`) :

```python
class SokobanPuzzle:
    def isGoal(self):            # toutes les caisses sur des cibles ?
    def successorFunction(self): # [(action, état_successeur), ...] pour les coups valides
```

- **État** = `(position du joueur, ensemble des caisses)` — hachable et comparable,
  indispensable pour l'ensemble `explored`.
- **Partie statique** (`Layout` : murs, cibles, intérieur) est **partagée entre tous les états** :
  elle n'est jamais recopiée → gain mémoire et temps considérable sur les grands espaces.
- **Codes du sujet** : `R` joueur · `O` mur · ` ` sol · `S` cible · `B` caisse
  · `.` joueur sur cible · `*` caisse sur cible.
- **Bonus** : détection des *dead squares* (cases d'où une caisse ne peut plus jamais rejoindre
  une cible) calculée par tirage inverse depuis les cibles → élagage et aide au niveau design.

```python
from core.levels import LEVELS
from core.puzzle import SokobanPuzzle

problem = SokobanPuzzle(LEVELS[0]["grid"])
print(problem.isGoal())          # False
for action, nxt in problem.successorFunction():
    print(action, "->", nxt.player)
```

---

## 🔍 Partie B — Algorithmes de recherche

| Algorithme | Implémentation | Garantie |
|---|---|---|
| **BFS** | file FIFO, `explored` sur états hachés | solution **optimale** (nombre de pas) |
| **DFS** | pile, couper-circuits sur états | solution **non optimale**, très peu de mémoire |
| **A\*** | file à priorité, `g + h` | solution **optimale** si h admissible |

**Heuristique A\*** : somme des distances de Manhattan caisse → cible la plus proche
(admissible et consistante → A\* est optimal et n'agrandit jamais un nœud deux fois).

Tous les algorithmes renvoient la même structure `SearchResult` :

```python
@dataclass
class SearchResult:
    algo: str
    status: str          # 'ok' | 'limit' | 'no_solution'
    solution: list       # ex. ['UP', 'LEFT', 'RIGHT', ...]
    path: list           # états intermédiaires (pour la simulation animée)
    cost: int            # nombre de pas
    expanded: int        # nœuds développés
    generated: int       # nœuds générés
    max_frontier: int    # taille maximale de la frontière
    time: float          # secondes
```

### 📊 Benchmark réel (Python 3.13 — les 30 niveaux passent, 0 échec)

| Niveau | Caisses | Algorithme | Coût | Nœuds développés | Temps |
|:--:|:--:|:--:|--:|--:|--:|
| **1** (Apprenti) | 2 | BFS | 13 | 282 | 1 ms |
| | | DFS | 23 | 124 | <1 ms |
| | | **A\*** | **13** | **235** | 1 ms |
| **9** (Apprenti) | 2 | BFS | 18 | 577 | 2 ms |
| | | DFS | 154 | 4 495 | 19 ms |
| | | **A\*** | **18** | **443** | 2 ms |
| **23** (Expert) | 4 | BFS | 25 | 245 298 | 1.8 s |
| | | DFS | 53 615 | 341 783 | 2.0 s |
| | | **A\*** | **25** | **68 062** | **1.0 s** |
| **29** (Expert) | 5 | BFS | 36 | 599 094 | 5.8 s |
| | | DFS | 137 378 | 493 574 | 4.4 s |
| | | **A\*** | **36** | **407 115** | 11.1 s |

> **À retenir** — sur le niveau 29 (Expert, 5 caisses), BFS doit développer **600 000 nœuds**
> là où A\* en développe 407 000 **et reste optimal**, tandis que DFS trouve une solution
> 3 800× plus longue. Reproduisez : `python main.py --cli --level 29 --algo "A*"`.
>
> **Toutes les recherches élaguent les cases mortes** (une caisse sur case morte ne peut
> plus jamais atteindre une cible) : élagage admissible qui ne perd aucune solution
> optimale et fait passer BFS/DFS de « limite atteinte » à **30/30 niveaux résolus**.

**Ajouter un algorithme en une ligne** (`search/__init__.py`) :

```python
ALGORITHMS = {"BFS": bfs, "DFS": dfs, "A*": astar, "Greedy": greedy}  # → apparaît dans l'UI
```

---

## 🗂️ Architecture du projet

```
sokoban/
├── main.py                    # point d'entrée (GUI ou --cli)
├── requirements.txt           # pygame>=2.5
├── core/                      # 🧠 PARTIE A — modélisation
│   ├── puzzle.py              #   SokobanPuzzle, Layout, parse_level()
│   ├── node.py                #   Node : état, parent, action, g, getPath(), getSolution()
│   └── levels.py              #   chargement auto de levels/*.txt
├── search/                    # 🔍 PARTIE B — algorithmes
│   ├── common.py              #   SearchResult + helpers
│   ├── bfs.py                 #   BFS
│   ├── dfs.py                 #   DFS
│   └── astar.py               #   A* (heuristique Manhattan)
├── gui/                       # 🖥️ PARTIE C — interface Pygame
│   ├── app.py                 #   fenêtre, scènes, jeu manuel, simulation, comparatif
│   ├── menus.py               #   accueil, niveaux, options, crédits (CREDITS[])
│   ├── tiles.py               #   mapping tileset → sol / murs / portes / torches
│   ├── fx.py                  #   parallaxe, particules, torches animées, fondus
│   ├── assets.py / sound.py   #   chargement sprites & sons
│   ├── widgets.py / fonts.py  #   boutons, icônes, polices pixel
│   ├── settings.py            #   sauvegarde options + progression
│   └── constants.py           #   tailles, couleurs, vitesses
├── levels/                    # 🗺️ 30 niveaux (1-10 Apprenti, 11-20 Explorateur, 21-30 Expert)
├── assets/                    # 🎨 sprites, tileset, sons, polices
├── tools/                     # ⚙️ générateur de niveaux, assets, sons, validation
└── docs/                      # captures d'écran du README
```

---

## 🗺️ Niveaux & éditeur

**Format** — un niveau = un fichier `levels/levelXX.txt`, dessiné en texte :

```text
OOTOPPOTOO
O        O
O  B  B  O
T  OOOO  O
O S    S O
O  B  B  O
O  S RS  O
OOOOOOOOOO
```

| Caractère | Signification |
|---|---|
| `O` | mur |
| ` ` (espace) | sol |
| `S` | cible |
| `B` | caisse |
| `R` | joueur (`. ` = joueur sur cible, `*` = caisse sur cible) |
| `T` | torche posée dans le mur (s'oriente toute seule) |
| `P` | porte (`PP` = porte double) |

**Les 30 niveaux de la base** — tous générés puis **vérifiés par BFS + DFS + A\*** :

| Palier | Niveaux | Caisses | Difficulté humaine |Complexité IA (nœuds A\*) |
|---|---|---|---|---|
| 🟢 **Apprenti** | 1-10 | 1-2 | prise en main, poussées simples | < 2 000 |
| 🟡 **Explorateur** | 11-20 | 3-4 | coordination de caisses, pièces séparées | 2 000 → 30 000 |
| 🔴 **Expert** | 21-30 | 4-6 | séquences longues, casse-tête de haut niveau | 15 000 → **400 000+** |

**Comment ils sont fabriqués** (`tools/make_levels.py`) : **reverse generation** —
on part de l'état résolu (caisses déjà sur cibles) et on **tire les caisses à l'envers**
(inverses exactes des poussées) pendant 15 à 100 coups, en rejetant tout coup qui place
une caisse sur une **case morte**. Le niveau est donc **solvable par construction**,
puis chaque niveau est filtré sur son nombre de nœuds A\*/BFS/DFS pour rentrer dans
la tranche de son palier.

```bash
python tools/make_levels.py            # régénère les 30 niveaux (reproductible, seed fixe)
python tools/make_levels.py --check    # audit BFS/DFS/A* de tous les niveaux
python tools/make_levels.py --only 27  # régénère un seul niveau
```

**Créer un niveau à la main en 4 étapes :**

1. Copiez un fichier existant : `copy levels\level10.txt levels\level31.txt`
2. Dessinez-le (règles : zone entièrement close par des murs, **un seul `R`**,
   autant de `B` que de `S`).
3. `python tools/check_levels.py` → validité **et** résolubles vérifiées par A\*.
4. Relancez le jeu : le niveau apparaît automatiquement (ordre alphabétique).

> Astuce pour vos propres niveaux difficiles : gardez les caisses au milieu de la pièce
> (pas collées aux murs) et obligez le joueur à faire des allers-retours — c'est ça,
> un niveau dur pour un humain.

---

## 🎨 Direction artistique

### Sprites (16×16, agrandis ×N sans lissage — pixels nets)

<img src="docs/sprites.png" alt="Aperçu des sprites 16x16" width="88%">

Noms attendus dans `assets/` pour remplacer un sprite par le vôtre (Aseprite, PNG, fond
transparent) : `floor`, `wall`, `target`, `box`, `box_on_target`,
`player_{up,down,left,right}_{0,1}`.

### Tileset & décor

<img src="docs/tileset.png" alt="Tileset Dungeon" width="60%">

Les murs, les coins, les portes et le sol (variantes aléatoires) sont découpés automatiquement
dans `Dungeon_Tileset.png` via `gui/tiles.py` — **aucun réglage manuel** nécessaire si vous
changez de tileset, tant que la grille reste cohérente.

### Polices

`assets/fonts/` : **Press Start 2P** (logo) et **Silkscreen** (titres, chiffres) —
licence SIL OFL, usage libre. Si les fichiers sont absents, le jeu bascule sur une police système.

### Sons (`assets/sounds/`)

| Fichier | Déclencheur |
|---|---|
| `step.wav` | déplacement du joueur |
| `push.wav` | poussée d'une caisse |
| `bump.wav` | collision avec un mur |
| `target.wav` | caisse posée sur une cible |
| `undo.wav` | annulation (U) |
| `click.wav` | clic sur un bouton |
| `win.wav` | niveau résolu |
| `music.wav` | musique de fond (boucle) |

Remplacez un fichier par le vôtre (même nom, `.wav` ou `.ogg`), ou régénérez les défauts :
`python tools/generate_sounds.py`.

---

## 🛠️ Compiler son propre `.exe`

```bash
pip install pyinstaller pillow
python build.py                   # -> dist/Sokoban.exe (fichier unique ~34 Mo)
```

`build.py` génère automatiquement l'icône (à partir du sprite du joueur), emballe
`assets/` + `levels/` dans l'exécutable et sort un `Sokoban.exe` **windowed, autonome** :
copiable sur n'importe quel PC Windows 10/11, aucune dépendance à installer.
Les réglages (`settings.json`) s'écrivent à côté du `.exe`.

---

## ⚙️ Outils CLI

| Commande | Rôle |
|---|---|
| `python tools/check_levels.py` | vérifie tous les fichiers de `levels/` (syntaxe, caisses = cibles, solvabilité A\*) |
| `python tools/make_levels.py` | (ré)génère les 30 niveaux par reverse generation + audit BFS/DFS/A\* |
| `python tools/generate_assets.py` | régénère les 13 sprites 16×16 par défaut |
| `python tools/generate_sounds.py` | régénère les 8 sons `.wav` synthétiques |
| `python tools/import_pack.py "<chemin>"` | importe/recoupe un asset pack via la table `MAPPING` |
| `python main.py --cli --level N --algo X` | résolution headless : coût, nœuds, temps, solution |

---

## 🙏 Crédits

- **Graphismes** — [2D Pixel Art]
- **Polices** — *Press Start 2P* & *Silkscreen*, licences SIL Open Font License.
- **Projet** — Sokoban, module *Problem Solving* — Master 1 Visual Computing, **USTHB**
- **Code** — Python 3 & Pygame, sans autre dépendance.

> Pensez à créditer l'auteur du pack si vous publiez une version : la licence du pack
> et ses termes sont à vérifier sur la page itch.io du pack.

---

<div align="center">

**[⬆ Haut de page](#-sokoban)** · *Fait avec Python, Pygame et beaucoup de pixels*

</div>
