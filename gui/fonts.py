"""Polices pixel-art (licence OFL) : Press Start 2P et Silkscreen, dans assets/fonts/.

Si les fichiers sont absents, on retombe sur une police système : le jeu reste jouable.
"""
from pathlib import Path

import pygame

DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _load(filename, size):
    try:
        return pygame.font.Font(str(DIR / filename), size)
    except (OSError, pygame.error):
        return pygame.font.SysFont("dejavusans,arial", max(10, int(size * 0.85)), bold=True)


def press(size):
    """Press Start 2P : titres et gros boutons (multiples de 8 = rendu net)."""
    return _load("PressStart2P-Regular.ttf", size)


def silk(size=16, bold=True):
    """Silkscreen : petits libellés (sous-titres, raccourcis clavier)."""
    return _load("Silkscreen-Bold.ttf" if bold else "Silkscreen-Regular.ttf", size)
