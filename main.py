"""
Point d'entrée du projet Sokoban.

    python main.py                  -> écran d'accueil
    python main.py --level 3        -> lance directement le niveau 3
    python main.py --cli --level 4 --algo A*   -> résolution en console (sans fenêtre)
"""
import argparse
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)          # exécutable PyInstaller
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
if not FROZEN:
    sys.path.insert(0, str(ROOT))


def ensure_assets():
    from gui.assets import NAMES
    if all((ROOT / "assets" / f"{n}.png").exists() for n in NAMES):
        return
    if FROZEN:
        print("Sprites manquants dans l'exécutable.")
        return
    print("Sprites manquants : génération des assets par défaut...")
    from tools import generate_assets
    generate_assets.main()


def run_cli(level, algo):
    from core.levels import LEVELS
    from core.puzzle import SokobanPuzzle
    from search import ALGORITHMS

    problem = SokobanPuzzle(LEVELS[level - 1]["grid"])
    print(f"=== {LEVELS[level - 1]['name']} ===")
    print(problem, "\n")
    r = ALGORITHMS[algo](problem)
    print(f"Algo : {r.algo}   statut : {r.status}")
    if r.status == "ok":
        print(f"Coût : {r.cost}")
        print(f"Nœuds développés : {r.expanded}   générés : {r.generated}")
        print(f"Temps : {r.time * 1000:.1f} ms")
        print("Solution :", " ".join(a[0] for a in r.solution))   # U D L R
    else:
        print(f"Nœuds développés : {r.expanded}")


def main():
    ap = argparse.ArgumentParser(description="Sokoban – modélisation et résolution")
    ap.add_argument("--level", type=int, default=None, help="lance directement ce niveau (1-20)")
    ap.add_argument("--cli", action="store_true", help="mode console, sans interface")
    ap.add_argument("--algo", default="BFS", help="BFS, DFS ou A*")
    args = ap.parse_args()

    if args.cli:
        run_cli(args.level or 1, args.algo)
        return
    ensure_assets()
    from gui.app import App
    app = App()
    if args.level:
        app.start_level(args.level - 1)
    app.run()


if __name__ == "__main__":
    main()
