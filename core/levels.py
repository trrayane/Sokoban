"""
Chargement des niveaux depuis le dossier levels/  (level01.txt, level02.txt, ...).

Un niveau = un fichier texte. Symboles :
    O mur   ' ' vide   S cible   B caisse   R joueur   . joueur sur cible   * caisse sur cible
Pour ajouter un niveau : créez levels/level11.txt, c'est tout.
"""
from pathlib import Path

LEVEL_DIR = Path(__file__).resolve().parent.parent / "levels"


def load_levels():
    levels = []
    for i, path in enumerate(sorted(LEVEL_DIR.glob("level*.txt")), 1):
        grid = path.read_text(encoding="utf-8").split("\n")
        while grid and not grid[-1].strip():     # retire les lignes vides finales
            grid.pop()
        levels.append({"name": f"Niveau {i}", "grid": grid, "file": path.name})
    return levels


LEVELS = load_levels()
