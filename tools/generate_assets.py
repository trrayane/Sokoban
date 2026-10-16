"""
Génère les sprites pixel art 16x16 dans assets/.

Ces PNG sont des assets de DÉPART. Pour utiliser vos propres sprites Aseprite,
exportez simplement des PNG (16x16 ou 32x32) avec EXACTEMENT les mêmes noms de
fichiers : le jeu les redimensionne automatiquement (sans lissage).

Lancer :  python tools/generate_assets.py
"""
import os
from pathlib import Path

import pygame

S = 16
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


def surf():
    return pygame.Surface((S, S), pygame.SRCALPHA)


def make_floor():
    s = surf()
    s.fill((238, 210, 165))
    for i in range(S):                      # bords légèrement plus foncés
        s.set_at((15, i), (222, 192, 146))
        s.set_at((i, 15), (222, 192, 146))
    for p in [(3, 4), (10, 9), (6, 12), (12, 2)]:   # petits grains
        s.set_at(p, (228, 198, 152))
    return s


def make_wall():
    s = surf()
    s.fill((142, 142, 152))
    mortar, light = (78, 78, 92), (188, 188, 198)
    for row in range(4):
        y0 = row * 4
        pygame.draw.line(s, mortar, (0, y0 + 3), (15, y0 + 3))
        xs = (7, 15) if row % 2 == 0 else (3, 11)
        for x in xs:
            pygame.draw.line(s, mortar, (x, y0), (x, y0 + 2))
        for x in range(S):
            if (x not in xs) and s.get_at((x, y0)) != mortar:
                s.set_at((x, y0), light)
    return s


def make_target():
    s = surf()
    red = (205, 60, 60)
    for i in range(3, 13):                  # carré en pointillés
        if i % 2 == 1:
            for p in [(i, 3), (i, 12), (3, i), (12, i)]:
                s.set_at(p, red)
    for p in [(3, 3), (12, 3), (3, 12), (12, 12)]:
        s.set_at(p, red)
    for i in range(6):                      # petite croix
        s.set_at((5 + i, 5 + i), red)
        s.set_at((10 - i, 5 + i), red)
    return s


def make_box(base, border, inner, light):
    s = surf()
    pygame.draw.rect(s, base, (1, 1, 14, 14))
    pygame.draw.rect(s, border, (1, 1, 14, 14), 1)
    pygame.draw.rect(s, inner, (3, 3, 10, 10), 1)
    for i in range(3, 13):                  # planche en diagonale
        s.set_at((i, i), inner)
    for x in range(2, 14):
        s.set_at((x, 2), light)
    return s


def make_player(direction, frame):
    s = surf()
    skin, hair = (245, 205, 160), (92, 52, 26)
    shirt, pants, shoe, eye = (50, 110, 205), (40, 50, 115), (30, 30, 35), (20, 20, 20)
    # tête
    pygame.draw.rect(s, skin, (5, 2, 6, 5))
    if direction == "down":
        pygame.draw.rect(s, hair, (5, 2, 6, 2))
        s.set_at((6, 5), eye); s.set_at((9, 5), eye)
    elif direction == "up":
        pygame.draw.rect(s, hair, (5, 2, 6, 5))
    elif direction == "left":
        pygame.draw.rect(s, hair, (5, 2, 6, 2))
        pygame.draw.rect(s, hair, (9, 4, 2, 3))
        s.set_at((6, 5), eye)
    else:  # right
        pygame.draw.rect(s, hair, (5, 2, 6, 2))
        pygame.draw.rect(s, hair, (5, 4, 2, 3))
        s.set_at((9, 5), eye)
    # corps + bras
    pygame.draw.rect(s, shirt, (5, 7, 6, 5))
    pygame.draw.rect(s, shirt, (4, 7, 1, 3))
    pygame.draw.rect(s, shirt, (11, 7, 1, 3))
    s.set_at((4, 10), skin); s.set_at((11, 10), skin)
    # jambes (2 frames pour l'animation de marche)
    if frame == 0:
        pygame.draw.rect(s, pants, (5, 12, 2, 2)); pygame.draw.rect(s, pants, (9, 12, 2, 2))
        pygame.draw.rect(s, shoe, (5, 14, 2, 1)); pygame.draw.rect(s, shoe, (9, 14, 2, 1))
    else:
        pygame.draw.rect(s, pants, (5, 12, 2, 1)); pygame.draw.rect(s, pants, (9, 12, 2, 3))
        pygame.draw.rect(s, shoe, (5, 13, 2, 1)); pygame.draw.rect(s, shoe, (9, 15, 2, 1))
    return s


def main(folder=ASSET_DIR):
    folder = Path(folder)
    os.makedirs(folder, exist_ok=True)
    sprites = {
        "floor": make_floor(),
        "wall": make_wall(),
        "target": make_target(),
        "box": make_box((160, 100, 45), (70, 40, 15), (115, 70, 30), (205, 145, 75)),
        "box_on_target": make_box((240, 205, 60), (110, 90, 20), (190, 155, 30), (255, 235, 130)),
    }
    for d in ("up", "down", "left", "right"):
        for f in (0, 1):
            sprites[f"player_{d}_{f}"] = make_player(d, f)
    for name, img in sprites.items():
        pygame.image.save(img, str(folder / f"{name}.png"))
    print(f"{len(sprites)} sprites générés dans {folder}")


if __name__ == "__main__":
    main()
