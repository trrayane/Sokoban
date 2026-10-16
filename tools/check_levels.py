"""
Vérifie TOUS les niveaux du dossier levels/ :
  - format valide (1 joueur, autant de caisses que de cibles)
  - niveau résoluble (résolu avec A*) + coût optimal

Lancer :  python tools/check_levels.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.levels import LEVELS
from core.puzzle import SokobanPuzzle
from search import astar


def main():
    for lv in LEVELS:
        try:
            p = SokobanPuzzle(lv["grid"])
        except ValueError as e:
            print(f"{lv['file']:14} FORMAT INVALIDE : {e}")
            continue
        r = astar(p)
        nb = len(p.boxes)
        if r.status == "ok":
            print(f"{lv['file']:14} OK   caisses={nb}  solution optimale={r.cost} pas  ({r.expanded} nœuds)")
        elif r.status == "limit":
            print(f"{lv['file']:14} ??   trop difficile pour A* (limite atteinte)")
        else:
            print(f"{lv['file']:14} IMPOSSIBLE : aucune solution, modifiez le niveau")


if __name__ == "__main__":
    main()
