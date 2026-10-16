"""Constantes de l'interface."""
WIN_W, WIN_H = 1120, 720
FPS = 60

BOARD_W, BOARD_H = 760, 600        # zone d'affichage de la grille
PANEL_X = 780                      # début du panneau d'information
PANEL_W = WIN_W - PANEL_X - 20

MAX_TILE = 64
BOARD_TOP = 56                     # place réservée en haut pour le bouton "Machine"
MOVE_MS = 120                      # durée d'un pas du joueur (animation)

# Palette
BG = (24, 26, 38)
PANEL_BG = (36, 40, 58)
PANEL_BORDER = (70, 76, 104)
TEXT = (230, 232, 245)
TEXT_DIM = (150, 156, 185)
ACCENT = (255, 196, 64)
GOOD = (110, 220, 130)
BAD = (240, 100, 100)
BTN = (58, 64, 94)
BTN_HOVER = (78, 86, 126)
BTN_ACTIVE = (232, 160, 40)
BOARD_BG = (16, 17, 26)

# Vitesses de simulation (ms entre deux pas)
SPEEDS = [400, 250, 150, 80, 40, 20]
DEFAULT_SPEED = 2
