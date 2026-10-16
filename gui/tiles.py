"""
Habillage visuel du jeu à partir du pack "2D Pixel Dungeon Asset Pack" :
  - murs auto-orientés (haut / bas / gauche / droite / coins) comme dans la tileset,
  - sol avec variantes tirées au hasard (pas un seul bloc répété),
  - torches animées, portes, lueur des torches, sprites du joueur.

Légende des caractères de niveau liés au décor :
    T = torche accrochée au mur      P = porte (PP côte à côte = porte double)
"""
import random
from pathlib import Path

import pygame

T = 16  # taille native d'une tuile

# (ligne, colonne) dans Dungeon_Tileset.png
FLOORS_PLAIN = [(6, 0), (6, 1), (6, 2), (6, 3), (7, 0), (7, 1), (7, 2), (7, 3),
                (0, 6), (0, 7), (1, 6), (2, 6)]
FLOORS_CRACKED = [(0, 8), (0, 9), (1, 7), (1, 8), (1, 9), (2, 7), (2, 8), (2, 9)]
WALL_TOP = [(0, 1), (0, 2), (0, 3), (0, 4)]       # face visible du mur du haut
WALL_BOTTOM = [(4, 1), (4, 2), (4, 3), (4, 4)]    # mur du bas
WALL_LEFT = [(1, 0), (2, 0), (3, 0)]              # mur de gauche
WALL_RIGHT = [(1, 5), (2, 5), (3, 5)]             # mur de droite
CORNER = {"SE": (0, 0), "SW": (0, 5), "NE": (5, 0), "NW": (5, 5)}
DOOR_SINGLE = (3, 8)
DOOR_LEFT, DOOR_RIGHT = (3, 6), (3, 7)

# sprites du joueur dans Dungeon_Character.png : (ligne, colonne) ; ligne+2 = 2e frame
PLAYER_CELLS = {"DOWN": (0, 0), "UP": (0, 6), "RIGHT": (0, 5), "LEFT": (0, 5)}


class Skin:
    def __init__(self, folder):
        pack = Path(folder) / "pack"
        self.ok = (pack / "Dungeon_Tileset.png").exists()
        self._cache = {}
        if not self.ok:
            return
        self.tileset = pygame.image.load(str(pack / "Dungeon_Tileset.png")).convert_alpha()
        self.chars = pygame.image.load(str(pack / "Dungeon_Character.png")).convert_alpha()
        load = lambda n: pygame.image.load(str(pack / n)).convert_alpha()
        self.torch = [load(f"torch_{i}.png") for i in range(1, 5)]
        self.side_torch = [load(f"side_torch_{i}.png") for i in range(1, 5)]
        self.flag = [load(f"flag_{i}.png") for i in range(1, 5)]

    # ------------------------------------------------------------ utilitaires
    def _scaled(self, key, surf, size):
        k = (key, size)
        if k not in self._cache:
            self._cache[k] = pygame.transform.scale(surf, (size, size))
        return self._cache[k]

    def cut(self, sheet, row, col):
        s = pygame.Surface((T, T), pygame.SRCALPHA)
        s.blit(sheet, (0, 0), (col * T, row * T, T, T))
        return s

    def tile(self, cell, size, flip=False):
        key = ("tile", cell, flip)
        if key not in self._cache:
            s = self.cut(self.tileset, *cell)
            self._cache[key] = pygame.transform.flip(s, True, False) if flip else s
        return self._scaled(("tile", cell, flip), self._cache[key], size)

    def player(self, facing, frame, size):
        facing = facing.upper()
        r, c = PLAYER_CELLS[facing]
        r += 2 * (frame % 2)
        key = ("player", facing, frame % 2)
        if key not in self._cache:
            s = self.cut(self.chars, r, c)
            for y in range(T):                    # efface les repères bleus/rouges des coins
                for x in range(T):
                    if (x < 3 or x > 12) and (y < 3 or y > 12):
                        pr, pg, pb, pa = s.get_at((x, y))
                        if pa and ((pb > 180 and pr < 150) or (pr > 180 and pg < 120 and pb < 120)):
                            s.set_at((x, y), (0, 0, 0, 0))
            self._cache[key] = pygame.transform.flip(s, True, False) if facing == "LEFT" else s
        return self._scaled(key, self._cache[key], size)

    def anim(self, frames, index, size, flip=False):
        key = ("anim", id(frames), index % len(frames), flip)
        if key not in self._cache:
            s = frames[index % len(frames)]
            self._cache[key] = pygame.transform.flip(s, True, False) if flip else s
        return self._scaled(key, self._cache[key], size)

    def glow(self, size):
        """Halo orangé radial (pré-calculé)."""
        key = ("glow", size)
        if key not in self._cache:
            R = int(size * 2.6)
            g = pygame.Surface((2 * R, 2 * R), pygame.SRCALPHA)
            steps = 28
            for i in range(steps):
                rad = int(R * (1 - i / steps))
                a = int(70 * (i / steps) ** 1.6)
                pygame.draw.circle(g, (255, 150, 60, a), (R, R), rad)
            self._cache[key] = g
        return self._cache[key]

    # ------------------------------------------------------------ murs / sol
    @staticmethod
    def _rng(r, c, salt=0):
        return random.Random(r * 7919 + c * 104729 + salt)

    @staticmethod
    def wall_orient(L, r, c):
        """Où se trouve le sol par rapport à ce mur ? -> 'top','bottom','left','right', coin."""
        ins = L.inside
        N, S = (r - 1, c) in ins, (r + 1, c) in ins
        E, W = (r, c + 1) in ins, (r, c - 1) in ins
        if S:
            return "top"
        if N:
            return "bottom"
        if E:
            return "left"
        if W:
            return "right"
        if (r + 1, c + 1) in ins:
            return "SE"
        if (r + 1, c - 1) in ins:
            return "SW"
        if (r - 1, c + 1) in ins:
            return "NE"
        return "NW"

    def wall_cell(self, L, r, c):
        o = self.wall_orient(L, r, c)
        rng = self._rng(r, c, 1)
        if o == "top":
            return rng.choice(WALL_TOP)
        if o == "bottom":
            return rng.choice(WALL_BOTTOM)
        if o == "left":
            return rng.choice(WALL_LEFT)
        if o == "right":
            return rng.choice(WALL_RIGHT)
        return CORNER[o]

    def floor_cell(self, r, c):
        rng = self._rng(r, c, 2)
        pool = FLOORS_CRACKED if rng.random() < 0.28 else FLOORS_PLAIN
        return rng.choice(pool)

    def build_static(self, L, size):
        """Surface transparente : sol + murs + portes (dessinée une seule fois par niveau)."""
        surf = pygame.Surface((L.width * size, L.height * size), pygame.SRCALPHA)
        shade = pygame.Surface((size, max(2, size // 5)), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 70))
        for (r, c) in L.inside:
            surf.blit(self.tile(self.floor_cell(r, c), size), (c * size, r * size))
            if (r - 1, c) in L.walls:                        # ombre sous le mur du haut
                surf.blit(shade, (c * size, r * size))
        for (r, c) in L.visible_walls:
            surf.blit(self.tile(self.wall_cell(L, r, c), size), (c * size, r * size))
        # portes : "PP" = porte double, "P" seul = porte simple
        doors = sorted(p for p, ch in L.decor.items() if ch == "P" and p in L.visible_walls)
        used = set()
        for (r, c) in doors:
            if (r, c) in used:
                continue
            if L.decor.get((r, c + 1)) == "P" and (r, c + 1) not in used:
                cells = [((r, c), DOOR_LEFT), ((r, c + 1), DOOR_RIGHT)]
            else:
                cells = [((r, c), DOOR_SINGLE)]
            for (pr, pc), cell in cells:
                used.add((pr, pc))
                surf.blit(self.tile(cell, size), (pc * size, pr * size))
        return surf
