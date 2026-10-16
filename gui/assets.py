"""Chargement et mise à l'échelle des sprites (pixel art net, sans lissage)."""
from pathlib import Path

import pygame

from gui.tiles import Skin

NAMES = ["floor", "wall", "target", "box", "box_on_target"] + [
    f"player_{d}_{f}" for d in ("up", "down", "left", "right") for f in (0, 1)
]


class Assets:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.base = {}
        for name in NAMES:
            path = self.folder / f"{name}.png"
            if not path.exists():
                raise FileNotFoundError(
                    f"Sprite manquant : {path}\n"
                    "Lancez  python tools/generate_assets.py  ou ajoutez votre PNG Aseprite."
                )
            self.base[name] = pygame.image.load(str(path)).convert_alpha()
        self._cache = {}
        self.skin = Skin(self.folder)
        if self.skin.ok:                       # sprites du pack pour menus / miniatures
            self.base["wall"] = self.skin.cut(self.skin.tileset, 0, 1)
            self.base["floor"] = self.skin.cut(self.skin.tileset, 6, 0)

    def get(self, name, tile):
        key = (name, tile)
        if key not in self._cache:
            # `scale` (et non smoothscale) => pixels nets, style rétro
            self._cache[key] = pygame.transform.scale(self.base[name], (tile, tile))
        return self._cache[key]

    def player(self, facing, frame, tile):
        if self.skin.ok:
            return self.skin.player(facing, frame, tile)
        return self.get(f"player_{facing.lower()}_{frame % 2}", tile)
