"""
Générateur de niveaux Sokoban — reverse generation reproductible (seed fixe).

Principe :
  1. on construit une pièce (template procédural : piliers, cloisons, îlots, croix…)
  2. on place des cibles au hasard
  3. on joue le niveau À L'ENVERS : depuis l'état résolu (caisses = cibles),
     on tire les caisses (inverses exactes des poussées) pendant N coups.
     Chaque étape est validée (cases libres, joueur joignable, pas de case morte)
     → le niveau est SOLVABLE PAR CONSTRUCTION.
  4. on note la difficulté avec A* et on ne garde le niveau que s'il rentre
     dans la tranche (palier), BFS + DFS + A* doivent tous réussir.

Usage :
    python tools/make_levels.py            # régénère les 30 niveaux dans levels/
    python tools/make_levels.py --check    # audit BFS/DFS/A* des niveaux existants
"""
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.puzzle import ACTIONS, SokobanPuzzle, parse_level   # noqa: E402
from search import ALGORITHMS                                 # noqa: E402
from search.astar import astar                               # noqa: E402
from search.bfs import bfs                                   # noqa: E402
from search.dfs import dfs                                   # noqa: E402

LEVEL_DIR = ROOT / "levels"
SEED = 20261016

# Paliers :  Apprenti (1-10)  Explorateur (11-20)  Expert (21-30)
TIERS = {
    1: dict(boxes=(1, 2), W=(8, 11), H=(6, 9), moves=(14, 45), astar=(25, 2_000),
            cost=(8, 60), bfs=(0, 60_000), dfs_ok=True),
    2: dict(boxes=(3, 4), W=(10, 13), H=(7, 10), moves=(45, 120), astar=(1_500, 60_000),
            cost=(14, 90), bfs=(0, 250_000), dfs_ok=True),
    3: dict(boxes=(4, 5), W=(10, 13), H=(7, 10), moves=(35, 100), astar=(15_000, 900_000),
            cost=(14, 160), bfs=(0, 1_250_000), dfs_ok=True),
}

KINDS = ["pillars", "partitions", "islands", "cross", "bays"]


# --------------------------------------------------------------------- pièces
def flood(walls, H, W, start):
    seen = {start}
    stack = [start]
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (y + dy, x + dx)
            if 0 <= n[0] < H and 0 <= n[1] < W and n not in walls and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


def fix_pockets(walls, H, W):
    """Toute case libre non atteignable devient un mur (arrivée à un point fixe)."""
    while True:
        free = {(y, x) for y in range(1, H - 1) for x in range(1, W - 1)
                if (y, x) not in walls}
        if not free:
            return walls
        reach = flood(walls, H, W, min(free))
        missing = free - reach
        if not missing:
            return walls
        walls |= missing


def room(rng, kind, W, H):
    walls = set()
    for x in range(W):
        walls.add((0, x))
        walls.add((H - 1, x))
    for y in range(H):
        walls.add((y, 0))
        walls.add((y, W - 1))

    if kind == "pillars":
        sy, sx = rng.choice([(3, 3), (3, 4), (4, 4), (4, 3)])
        oy, ox = rng.randint(1, sy - 1), rng.randint(1, sx - 1)
        for y in range(oy, H - 1, sy):
            for x in range(ox, W - 1, sx):
                if 1 <= y <= H - 2 and 1 <= x <= W - 2:
                    walls.add((y, x))

    elif kind == "partitions":
        for _ in range(rng.randint(1, 3)):
            if rng.random() < 0.5:                      # cloison horizontale
                y = rng.randint(2, H - 3)
                x0, x1 = sorted((rng.randint(1, W - 3), rng.randint(3, W - 2)))
                gap = rng.randint(x0, x1)
                g2 = rng.randint(x0, x1) if rng.random() < 0.35 else gap
                for x in range(x0, x1 + 1):
                    if x not in (gap, g2):
                        walls.add((y, x))
            else:                                        # cloison verticale
                x = rng.randint(2, W - 3)
                y0, y1 = sorted((rng.randint(1, H - 3), rng.randint(3, H - 2)))
                gap = rng.randint(y0, y1)
                g2 = rng.randint(y0, y1) if rng.random() < 0.35 else gap
                for y in range(y0, y1 + 1):
                    if y not in (gap, g2):
                        walls.add((y, x))

    elif kind == "islands":
        for _ in range(rng.randint(2, 5)):
            y, x = rng.randint(2, H - 3), rng.randint(2, W - 3)
            ly, lx = rng.randint(1, 2), rng.randint(1, 3)
            for yy in range(y, min(y + ly, H - 2)):
                for xx in range(x, min(x + lx, W - 2)):
                    walls.add((yy, xx))

    elif kind == "cross":
        y = rng.randint(3, max(3, H - 4))
        x = rng.randint(3, max(3, W - 4))
        gap1 = rng.randint(1, W - 2)
        gap2 = rng.randint(1, H - 2)
        for xx in range(1, W - 1):
            if xx not in (gap1, gap1 + 1):
                walls.add((y, xx))
        for yy in range(1, H - 1):
            if yy not in (gap2, gap2 + 1):
                walls.add((yy, x))

    elif kind == "bays":
        n = rng.randint(2, 4)
        step = (W - 2) // (n + 1)
        for i in range(1, n + 1):
            x = min(W - 2, i * step + rng.randint(-1, 1))
            if rng.random() < 0.5:                        # alcôve du haut
                walls.add((1, x))
                if rng.random() < 0.6:
                    walls.add((1, x - 1 if x > 2 else x + 1))
            else:                                         # alcôve du bas
                walls.add((H - 2, x))
                if rng.random() < 0.6:
                    walls.add((H - 2, x - 1 if x > 2 else x + 1))

    return fix_pockets(walls, H, W)


# -------------------------------------------------------------- cibles / mort
def pick_targets(rng, free, n, H, W):
    free = sorted(free)
    for _ in range(400):
        cand = rng.sample(free, min(n, len(free)))
        if all(abs(a[0] - b[0]) + abs(a[1] - b[1]) >= 2 for i, a in enumerate(cand)
               for b in cand[i + 1:]):
            return set(cand)
    return None


def layout_of(walls, targets, H, W):
    free = [(y, x) for y in range(1, H - 1) for x in range(1, W - 1)
            if (y, x) not in walls and (y, x) not in targets]
    player = min(free)
    grid = []
    for y in range(H):
        row = []
        for x in range(W):
            p = (y, x)
            if p in walls:
                row.append("O")
            elif p == player:
                row.append("R")
            elif p in targets:
                row.append("*")          # caisse posée : parse_level exige caisses = cibles
            else:
                row.append(" ")
        grid.append("".join(row))
    layout, _, _ = parse_level(grid)
    return layout


# --------------------------------------------------- tirage inverse des caisses
def reverse_walk(rng, layout, targets, nmoves):
    walls = layout.walls
    dead = layout.dead_squares
    H, W = layout.height, layout.width
    free = sorted(layout.inside - targets)
    if not free:
        return None
    boxes = set(targets)
    player = rng.choice(free)
    if player in boxes:
        player = min(layout.inside - boxes)

    last = None
    visited = {frozenset(boxes)}
    dirs = list(ACTIONS.values())

    for _ in range(nmoves):
        # atteignable depuis le joueur (sans traverser les caisses)
        reach = {player}
        stack = [player]
        while stack:
            y, x = stack.pop()
            for dy, dx in dirs:
                n = (y + dy, x + dx)
                if n not in walls and n not in boxes and n not in reach:
                    reach.add(n)
                    stack.append(n)

        cand = []
        blocked = []
        for b in boxes:
            for dy, dx in dirs:
                nb = (b[0] + dy, b[1] + dx)          # nouvelle case de la caisse
                stand = (b[0] + 2 * dy, b[1] + 2 * dx)  # case du joueur derrière
                if nb in walls or nb in boxes or stand in walls or stand in boxes:
                    continue
                if nb in dead:                        # case morte : jamais récupérable
                    continue
                if nb not in reach:                   # le joueur doit atteindre nb
                    continue
                key = (b, nb)
                new_boxes = frozenset((boxes - {b}) | {nb})
                entry = (new_boxes not in visited, key, new_boxes, stand)
                if last is None or key != last:
                    cand.append(entry)
                else:
                    blocked.append(entry)             # annulation du dernier coup : dernier recours
        if not cand:
            cand = blocked                            # seul coup dispo : on l'autorise
        if not cand:
            return None
        cand.sort(key=lambda c: not c[0])             # préfère les états inédits
        pool = cand[:max(1, len(cand) // 2)] if cand[0][0] else cand
        _, key, new_boxes, stand = rng.choice(pool)
        boxes, player, last = new_boxes, stand, key
        visited.add(new_boxes)

    if boxes == frozenset(targets) or not (boxes - targets):
        return None
    return boxes, player


# --------------------------------------------------------------- écriture / vérif
def render(rng, layout, targets, boxes, player):
    H, W = layout.height, layout.width
    grid = []
    for y in range(H):
        row = []
        for x in range(W):
            p = (y, x)
            if p in layout.walls:
                ch = "O"
            elif p == player:
                ch = "." if p in targets else "R"
            elif p in boxes:
                ch = "*" if p in targets else "B"
            elif p in targets:
                ch = "S"
            else:
                ch = " "
            row.append(ch)
        grid.append(row)

    # décor : torches sur les murs (géométrie inchangée, 'T'/'P' = mur)
    for y in range(H):
        for x in range(W):
            if grid[y][x] != "O":
                continue
            near_floor = any((y + dy, x + dx) not in layout.walls
                             for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
                             if 0 <= y + dy < H and 0 <= x + dx < W)
            if not near_floor:
                continue
            on_border = y in (0, H - 1) or x in (0, W - 1)
            if rng.random() < (0.30 if on_border else 0.14):
                grid[y][x] = "T"
            elif rng.random() < 0.07:
                grid[y][x] = "P"
    return ["".join(r) for r in grid]


def evaluate(grid, band=None):
    """Vérifie les 3 algorithmes (en cascade : A* -> BFS -> DFS pour aller vite).

    band : dict optionnel avec les plafonds par algo pour stopper tôt.
    Renvoie (ok, info).
    """
    try:
        p = SokobanPuzzle(grid)
    except ValueError as e:
        return False, {"err": str(e)}
    info = {"boxes": len(p.boxes)}
    a_min, a_max = (band or {}).get("astar", (0, 10 ** 12))
    b_max = (band or {}).get("bfs", (0, 10 ** 12))[1]
    c_min, c_max = (band or {}).get("cost", (0, 10 ** 12))
    # pendant la génération, on plafonne les nœuds pour rejeter vite les candidats trop durs
    cap = bool(band)

    r = astar(p, max_nodes=min(1_500_000, int(a_max * 1.6) + 1000) if cap else 1_500_000)
    info["A*"] = {"status": r.status, "cost": r.cost, "exp": r.expanded,
                  "gen": r.generated, "t": r.time}
    if (r.status != "ok" or not (a_min <= r.expanded <= a_max)
            or not (c_min <= (r.cost or -1) <= c_max)):
        info.setdefault("why", "A* hors tranche")
        return False, info

    r = bfs(p, max_nodes=min(1_500_000, int(b_max * 1.4) + 1000) if cap else 1_500_000)
    info["BFS"] = {"status": r.status, "cost": r.cost, "exp": r.expanded,
                   "gen": r.generated, "t": r.time}
    if r.status != "ok" or r.expanded > b_max:
        info.setdefault("why", "BFS trop gros")
        return False, info

    r = dfs(p, max_nodes=1_000_000 if cap else 1_500_000)
    info["DFS"] = {"status": r.status, "cost": r.cost, "exp": r.expanded,
                   "gen": r.generated, "t": r.time}
    if r.status != "ok":
        info.setdefault("why", "DFS limite")
        return False, info
    return True, info


def audit(grid):
    """Évaluation complète (tableau README) : les 3 algos sans plafond de bande."""
    return evaluate(grid, band=None)


def tier_of(index):
    return 1 if index <= 10 else (2 if index <= 20 else 3)


def _candidate(rng, T):
    """Essaie de fabriquer un niveau qui rentre dans la tranche T. Renvoie ou None."""
    W = rng.randint(*T["W"])
    H = rng.randint(*T["H"])
    kind = rng.choice(KINDS)
    walls = room(rng, kind, W, H)
    free = [(y, x) for y in range(1, H - 1) for x in range(1, W - 1)
            if (y, x) not in walls]
    nbox = rng.randint(*T["boxes"])
    if len(free) < nbox * 6:
        return None
    targets = pick_targets(rng, free, nbox, H, W)
    if not targets:
        return None
    layout = layout_of(walls, targets, H, W)
    if len(layout.inside) < nbox * 6:
        return None
    walk = reverse_walk(rng, layout, targets, rng.randint(*T["moves"]))
    if walk is None:
        return None
    boxes, player = walk
    grid = render(rng, layout, targets, boxes, player)
    ok, info = evaluate(grid, T)
    if not ok:
        return None
    return grid, info, kind


def generate(verbose=True, only=None):
    results = []
    for index in range(1, 31):
        if only and index not in only:
            continue
        rng = random.Random(SEED * 100 + index)   # seed par niveau : reproductible
        tier = tier_of(index)
        T = TIERS[tier]
        # phase 1 : tranche stricte — phase 2 : un peu assouplie (niveau quand même correct)
        loose = {**T,
                 "astar": (max(1, T["astar"][0] // 2), int(T["astar"][1] * 1.5)),
                 "cost": (max(10, T["cost"][0] - 6), T["cost"][1] + 40),
                 "bfs": (0, 950_000)}
        got = None
        t0 = time.perf_counter()
        for phase, (band, attempts) in enumerate(((T, 60), (loose, 50)), 1):
            for _ in range(attempts):
                if time.perf_counter() - t0 > 240:     # budget temps par niveau
                    break
                got = _candidate(rng, band)
                if got:
                    break
            if got:
                break
        if got is None:
            print(f"level{index:02d}  ECHEC de génération", flush=True)
            continue
        grid, info, kind = got
        results.append((index, kind, info))
        path = LEVEL_DIR / f"level{index:02d}.txt"
        path.write_text("\n".join(grid) + "\n", encoding="utf-8")
        if verbose:
            print(f"level{index:02d} [{tier}] {kind:11} boxes={info['boxes']}  "
                  f"coût={info['A*']['cost']:3}  A*={info['A*']['exp']:7} nœuds  "
                  f"BFS={info['BFS']['exp']:7}  DFS={info['DFS']['exp']:7}  "
                  f"({time.perf_counter() - t0:.0f} s)", flush=True)
    return results


def check(verbose=True):
    """Audit de tous les niveaux de levels/ avec BFS + DFS + A*."""
    from core.levels import LEVELS
    bad = []
    if verbose:
        print(f"{'niveau':10} {'cb':3} {'coût':5} {'A* nœuds':9} {'BFS nœuds':10} "
              f"{'DFS nœuds':10} statut")
    for lv in LEVELS:
        ok, info = evaluate(lv["grid"])
        if verbose:
            if ok:
                print(f"{lv['file']:10} {info['boxes']:3} {info['A*']['cost']:5} "
                      f"{info['A*']['exp']:9} {info['BFS']['exp']:10} "
                      f"{info['DFS']['exp']:10} OK")
            else:
                st = {n: info.get(n, {}).get("status", "—") for n in ("BFS", "DFS", "A*")}
                print(f"{lv['file']:10} {info.get('boxes', '?'):>3} {'':5} {'':9} "
                      f"{'':10} {'':10} ECHEC {st} {info.get('why', '')}")
        if not ok:
            bad.append(lv["file"])
    if verbose:
        print("\nProblemes :", bad if bad else "aucun — tous les niveaux passent BFS+DFS+A*")
    return bad


if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = {int(a) for a in sys.argv[sys.argv.index("--only") + 1].split(",")}
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    LEVEL_DIR.mkdir(exist_ok=True)
    if only is None:
        for old in LEVEL_DIR.glob("level*.txt"):
            old.unlink()
    generate(only=only)
    if "--no-check" not in sys.argv:
        print()
        bad = check()
        sys.exit(1 if bad else 0)
