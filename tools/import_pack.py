"""
Importe les sprites du pack "2D Pixel Dungeon Asset Pack" dans assets/.

Utilisation :
    python tools/import_pack.py "chemin/vers/2D Pixel Dungeon Asset Pack"

Pour changer un sprite, modifiez la table MAPPING ci-dessous :
  - ("tileset", ligne, colonne)  -> une tuile de Dungeon_Tileset.png (grille 16x16)
  - ("char", ligne, colonne)     -> une tuile de Dungeon_Character.png
  - ("file", "dossier/fichier.png") -> un PNG du pack
Ajoutez ", flip" à la fin pour retourner l'image horizontalement.
"""
import sys
from pathlib import Path

import pygame

T = 16
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"

MAPPING = {
    "wall":          ("tileset", 0, 1),
    "floor":         ("tileset", 1, 1),
    "target":        ("file", "items and trap_animation/flag/flag_1.png"),
    "box":           ("file", "items and trap_animation/box_2/box_2_1.png"),
    "box_on_target": ("file", "items and trap_animation/chest/chest_open_4.png"),
    # joueur : (ligne, colonne) dans Dungeon_Character.png ; 2 frames d'animation
    "player_down_0":  ("char", 0, 0),
    "player_down_1":  ("char", 2, 0),
    "player_up_0":    ("char", 0, 0),
    "player_up_1":    ("char", 2, 0),
    "player_right_0": ("char", 0, 0),
    "player_right_1": ("char", 2, 0),
    "player_left_0":  ("char", 0, 0, "flip"),
    "player_left_1":  ("char", 2, 0, "flip"),
}


def cut(sheet, row, col):
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    s.blit(sheet, (0, 0), (col * T, row * T, T, T))
    return s


def main(pack_dir, out=ASSET_DIR):
    pack = Path(pack_dir)
    base = pack / "character and tileset"
    tileset = pygame.image.load(str(base / "Dungeon_Tileset.png"))
    chars = pygame.image.load(str(base / "Dungeon_Character.png"))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    for name, spec in MAPPING.items():
        kind = spec[0]
        if kind == "tileset":
            img = cut(tileset, spec[1], spec[2])
        elif kind == "char":
            img = cut(chars, spec[1], spec[2])
        else:
            img = pygame.image.load(str(pack / spec[1]))
        if spec[-1] == "flip":
            img = pygame.transform.flip(img, True, False)
        pygame.image.save(img, str(out / f"{name}.png"))
    print(f"{len(MAPPING)} sprites importés dans {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
