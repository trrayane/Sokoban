"""
Modélisation du problème Sokoban (partie A.1 du sujet).

Codage des cases (identique au sujet) :
    'R' joueur      'O' mur        ' ' case vide
    'S' cible       'B' caisse     '.' joueur sur cible    '*' caisse sur cible

Un état = (position du joueur, ensemble des caisses).
Les éléments statiques (murs, cibles) sont stockés dans un objet `Layout`
partagé entre tous les états : on ne les recopie jamais.
"""

# Actions : (delta_ligne, delta_colonne)
ACTIONS = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

WALL, EMPTY, TARGET, BOX, PLAYER = "O", " ", "S", "B", "R"
TORCH, DOOR = "T", "P"                      # décor posé dans un mur
DECOR_CHARS = (TORCH, DOOR)
PLAYER_ON_TARGET, BOX_ON_TARGET = ".", "*"


class Layout:
    """Partie statique du niveau (identique pour tous les états)."""

    def __init__(self, walls, targets, height, width, inside, decor=None):
        self.walls = frozenset(walls)
        self.decor = dict(decor or {})           # {(ligne, col): 'T' torche | 'P' porte}
        self.targets = frozenset(targets)
        self.height = height
        self.width = width
        self.inside = frozenset(inside)          # cases jouables (intérieur)
        self.dead_squares = self._compute_dead_squares()
        self.visible_walls = self._compute_visible_walls()

    def _compute_dead_squares(self):
        """Cases d'où une caisse ne pourra jamais atteindre une cible
        (calcul par 'tirage' inverse depuis les cibles)."""
        alive = set(self.targets)
        stack = list(self.targets)
        while stack:
            p = stack.pop()
            for dr, dc in ACTIONS.values():
                q = (p[0] - dr, p[1] - dc)          # position précédente de la caisse
                r = (p[0] - 2 * dr, p[1] - 2 * dc)  # position du joueur qui pousse
                if q in self.walls or r in self.walls:
                    continue
                if q in self.inside and q not in alive:
                    alive.add(q)
                    stack.append(q)
        return frozenset(self.inside - alive)

    def _compute_visible_walls(self):
        """Murs touchant l'intérieur (on n'affiche pas les murs 'décoratifs')."""
        vis = set()
        for (r, c) in self.walls:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (r + dr, c + dc) in self.inside:
                        vis.add((r, c))
        return frozenset(vis)


def parse_level(lines):
    """Transforme une liste de chaînes en (Layout, position joueur, caisses)."""
    height = len(lines)
    width = max(len(l) for l in lines)
    walls, targets, boxes, player = set(), set(), set(), None
    decor = {}
    for r, line in enumerate(lines):
        for c, ch in enumerate(line.ljust(width)):
            pos = (r, c)
            if ch == WALL:
                walls.add(pos)
            elif ch in DECOR_CHARS:                  # torche / porte : se comporte comme un mur
                walls.add(pos)
                decor[pos] = ch
            if ch in (TARGET, PLAYER_ON_TARGET, BOX_ON_TARGET):
                targets.add(pos)
            if ch in (BOX, BOX_ON_TARGET):
                boxes.add(pos)
            if ch in (PLAYER, PLAYER_ON_TARGET):
                if player is not None:
                    raise ValueError("Un seul joueur autorisé")
                player = pos
    if player is None:
        raise ValueError("Aucun joueur dans le niveau")
    if len(boxes) != len(targets):
        raise ValueError("Il faut autant de caisses que de cibles")

    # Intérieur = cases atteignables depuis le joueur sans traverser de mur
    inside, stack = {player}, [player]
    while stack:
        r, c = stack.pop()
        for dr, dc in ACTIONS.values():
            n = (r + dr, c + dc)
            if n not in walls and n not in inside and 0 <= n[0] < height and 0 <= n[1] < width:
                inside.add(n)
                stack.append(n)
    return Layout(walls, targets, height, width, inside, decor), player, boxes


class SokobanPuzzle:
    """Un état du jeu Sokoban."""

    def __init__(self, level=None, *, layout=None, player=None, boxes=None):
        """
        level : liste de chaînes (niveau initial), OU
        layout/player/boxes : construction interne d'un état successeur.
        """
        if level is not None:
            layout, player, boxes = parse_level(level)
        self.layout = layout
        self.player = player
        self.boxes = frozenset(boxes)
        self._hash = hash((self.player, self.boxes))

    # --- égalité / hachage : indispensables pour l'ensemble `explored` ---
    def __eq__(self, other):
        return self.player == other.player and self.boxes == other.boxes

    def __hash__(self):
        return self._hash

    # --- fonctions demandées par le sujet ---
    def isGoal(self):
        """But : toutes les caisses sont sur des cibles (ordre quelconque)."""
        return self.boxes == self.layout.targets

    def successorFunction(self):
        """Liste de couples (action, état successeur) pour tous les coups valides."""
        walls, boxes = self.layout.walls, self.boxes
        pr, pc = self.player
        result = []
        for name, (dr, dc) in ACTIONS.items():
            nr, nc = pr + dr, pc + dc
            if (nr, nc) in walls:
                continue                                  # mur
            new_boxes = boxes
            if (nr, nc) in boxes:                         # on pousse une caisse
                br, bc = nr + dr, nc + dc
                if (br, bc) in walls or (br, bc) in boxes:
                    continue                              # case derrière bloquée
                new_boxes = (boxes - {(nr, nc)}) | {(br, bc)}
            result.append((name, SokobanPuzzle(layout=self.layout,
                                               player=(nr, nc), boxes=new_boxes)))
        return result

    # --- outils ---
    def is_deadlock(self):
        """Vrai si une caisse est sur une case morte (jamais récupérable)."""
        return not self.boxes.isdisjoint(self.layout.dead_squares)

    def to_grid(self):
        """Représentation texte avec les symboles du sujet."""
        L = self.layout
        rows = []
        for r in range(L.height):
            row = []
            for c in range(L.width):
                p = (r, c)
                on_t = p in L.targets
                if p in L.walls:
                    ch = WALL
                elif p in self.boxes:
                    ch = BOX_ON_TARGET if on_t else BOX
                elif p == self.player:
                    ch = PLAYER_ON_TARGET if on_t else PLAYER
                else:
                    ch = TARGET if on_t else EMPTY
                row.append(ch)
            rows.append("".join(row))
        return rows

    def __str__(self):
        return "\n".join(self.to_grid())
