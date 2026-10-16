"""Widgets Pygame : bouton unifié (icône + texte, 4 styles, effet d'appui, infobulle).

Usage :
    Button(rect, "Texte", callback)                          # bouton classique
    Button(rect, "", callback, icon="undo", tip="Annuler [U]")  # bouton icône seul
    Button(rect, "Jouer", callback, icon="play", kind="primary")

Styles (kind) : "secondary" (défaut), "primary", "danger", "ghost".
Les icônes sont dessinées en vectoriel : voir ICONS plus bas.
"""
import math

import pygame

from gui import constants as C

BTN_RADIUS = 9
LIP = 3                          # épaisseur du "relief" sous le bouton

# (face, face survolée, relief, texte, bordure)
KINDS = {
    "secondary": ((58, 64, 94), (80, 88, 130), (34, 38, 60), C.TEXT, (84, 92, 128)),
    "primary":   ((245, 184, 56), (255, 207, 96), (168, 114, 22), (34, 26, 10), (255, 220, 130)),
    "danger":    ((150, 62, 74), (182, 80, 94), (92, 34, 44), C.TEXT, (200, 110, 120)),
    "ghost":     ((36, 40, 58), (58, 64, 94), (36, 40, 58), C.TEXT, (70, 76, 104)),
}
ACTIVE = ((236, 164, 44), (250, 186, 74), (160, 104, 18), (34, 26, 10), (255, 214, 120))
DISABLED = ((44, 48, 68), (44, 48, 68), (32, 35, 52), C.TEXT_DIM, (54, 58, 80))


# =============================================================== icônes vectorielles
def _line(s, col, pts, w=3):
    pygame.draw.lines(s, col, False, pts, w)
    for p in pts:
        pygame.draw.circle(s, col, p, w // 2)


def _head(s, col, end, d, size=5):
    """Pointe de flèche en `end`, dans la direction unitaire d."""
    tip = (end[0] + d[0] * size, end[1] + d[1] * size)
    base = (end[0] - d[0] * 2, end[1] - d[1] * 2)
    p = (-d[1], d[0])
    pygame.draw.polygon(s, col, [tip, (base[0] + p[0] * size, base[1] + p[1] * size),
                                 (base[0] - p[0] * size, base[1] - p[1] * size)])


def _speaker(s, col, x, y):
    pygame.draw.polygon(s, col, [(x - 9, y - 3), (x - 5, y - 3), (x - 1, y - 8),
                                 (x - 1, y + 8), (x - 5, y + 3), (x - 9, y + 3)])


def _arc(s, col, x, y, r, a0, a1, w=2, step=10):
    """Arc (degrés, sens trigonométrique) dessiné en polyligne : plus propre que draw.arc."""
    pts = []
    for a in range(a0, a1 + 1, step):
        t = math.radians(a)
        pts.append((round(x + r * math.cos(t)), round(y - r * math.sin(t))))
    _line(s, col, pts, w)
    return pts


def _icon_restart(s, col, x, y):
    pts = _arc(s, col, x, y, 7, 70, 330, 2)
    t = math.radians(330)
    _head(s, col, pts[-1], (-math.sin(t), -math.cos(t)), 4)


def _icon_sound_on(s, col, x, y):
    _speaker(s, col, x, y)
    _arc(s, col, x - 1, y, 5, -45, 45, 2)
    _arc(s, col, x - 1, y, 9, -45, 45, 2)


def _icon_home(s, col, x, y):
    _line(s, col, [(x - 9, y + 8), (x - 9, y - 1), (x, y - 9), (x + 9, y - 1), (x + 9, y + 8), (x - 9, y + 8)], 2)
    pygame.draw.rect(s, col, (x - 2, y + 2, 4, 6))


def _icon_power(s, col, x, y):
    _arc(s, col, x, y + 1, 7, 125, 415, 2)
    _line(s, col, [(x, y - 9), (x, y)], 2)


def _icon_undo(s, col, x, y):
    _line(s, col, [(x - 4, y - 4), (x + 3, y - 4), (x + 8, y), (x + 8, y + 3), (x + 3, y + 7), (x - 5, y + 7)], 3)
    pygame.draw.polygon(s, col, [(x - 10, y - 4), (x - 3, y - 10), (x - 3, y + 2)])


def _icon_gear(s, col, x, y):
    for k in range(8):
        a = k * math.pi / 4
        pygame.draw.line(s, col, (x + 6 * math.cos(a), y + 6 * math.sin(a)),
                         (x + 9 * math.cos(a), y + 9 * math.sin(a)), 3)
    pygame.draw.circle(s, col, (x, y), 6, 3)


ICONS = {
    "prev":   lambda s, c, x, y: _line(s, c, [(x + 3, y - 7), (x - 4, y), (x + 3, y + 7)]),
    "next":   lambda s, c, x, y: _line(s, c, [(x - 3, y - 7), (x + 4, y), (x - 3, y + 7)]),
    "back":   lambda s, c, x, y: _line(s, c, [(x + 3, y - 7), (x - 4, y), (x + 3, y + 7)]),
    "first":  lambda s, c, x, y: (pygame.draw.rect(s, c, (x - 8, y - 7, 3, 14)),
                                  pygame.draw.polygon(s, c, [(x + 8, y - 7), (x - 3, y), (x + 8, y + 7)])),
    "last":   lambda s, c, x, y: (pygame.draw.rect(s, c, (x + 5, y - 7, 3, 14)),
                                  pygame.draw.polygon(s, c, [(x - 8, y - 7), (x + 3, y), (x - 8, y + 7)])),
    "play":   lambda s, c, x, y: pygame.draw.polygon(s, c, [(x - 5, y - 8), (x + 7, y), (x - 5, y + 8)]),
    "pause":  lambda s, c, x, y: (pygame.draw.rect(s, c, (x - 6, y - 7, 4, 14)),
                                  pygame.draw.rect(s, c, (x + 2, y - 7, 4, 14))),
    "minus":  lambda s, c, x, y: pygame.draw.rect(s, c, (x - 7, y - 1, 14, 3)),
    "plus":   lambda s, c, x, y: (pygame.draw.rect(s, c, (x - 7, y - 1, 14, 3)),
                                  pygame.draw.rect(s, c, (x - 1, y - 7, 3, 14))),
    "restart": _icon_restart,
    "undo":   _icon_undo,
    "gear":   _icon_gear,
    "sound_on": _icon_sound_on,
    "sound_off": lambda s, c, x, y: (_speaker(s, c, x, y),
                                     pygame.draw.line(s, c, (x + 3, y - 4), (x + 9, y + 4), 2),
                                     pygame.draw.line(s, c, (x + 9, y - 4), (x + 3, y + 4), 2)),
    "levels": lambda s, c, x, y: [pygame.draw.rect(s, c, (x + dx, y + dy, 7, 7), border_radius=2)
                                  for dx in (-8, 1) for dy in (-8, 1)],
    "chip":   lambda s, c, x, y: (pygame.draw.rect(s, c, (x - 5, y - 5, 10, 10), 2, border_radius=2),
                                  [pygame.draw.line(s, c, (x + i, y - 9), (x + i, y - 5), 2) for i in (-2, 2)],
                                  [pygame.draw.line(s, c, (x + i, y + 5), (x + i, y + 9), 2) for i in (-2, 2)],
                                  [pygame.draw.line(s, c, (x - 9, y + i), (x - 5, y + i), 2) for i in (-2, 2)],
                                  [pygame.draw.line(s, c, (x + 5, y + i), (x + 9, y + i), 2) for i in (-2, 2)]),
    "caret":  lambda s, c, x, y: pygame.draw.polygon(s, c, [(x - 5, y - 2), (x + 5, y - 2), (x, y + 4)]),
    "home":   _icon_home,
    "info":   lambda s, c, x, y: (pygame.draw.circle(s, c, (x, y), 9, 2),
                                  pygame.draw.line(s, c, (x, y - 1), (x, y + 5), 2),
                                  pygame.draw.circle(s, c, (x, y - 4), 1)),
    "power":  _icon_power,
    "fullscreen": lambda s, c, x, y: [_line(s, c, [(x + sx * 4, y + sy * 8), (x + sx * 8, y + sy * 8), (x + sx * 8, y + sy * 4)], 2)
                                      for sx in (-1, 1) for sy in (-1, 1)],
    "chart":  lambda s, c, x, y: (pygame.draw.rect(s, c, (x - 8, y + 1, 4, 7)),
                                  pygame.draw.rect(s, c, (x - 2, y - 4, 4, 12)),
                                  pygame.draw.rect(s, c, (x + 4, y - 8, 4, 16))),
}


def draw_icon(surface, name, cx, cy, color, scale=1.0):
    fn = ICONS.get(name)
    if not fn:
        return
    if scale == 1.0:
        fn(surface, color, int(cx), int(cy))
        return
    tmp = pygame.Surface((32, 32), pygame.SRCALPHA)         # agrandissement pour gros boutons
    fn(tmp, color, 16, 16)
    size = round(32 * scale)
    tmp = pygame.transform.smoothscale(tmp, (size, size))
    surface.blit(tmp, tmp.get_rect(center=(int(cx), int(cy))))


# ===================================================================== bouton
class Button:
    on_click = None                 # fonction appelée à chaque clic (son)
    _tip = None                     # (texte, rect) de l'infobulle à afficher
    _hover_any = False              # un bouton est survolé (curseur main)
    ICON_W, GAP = 18, 8

    def __init__(self, rect, label="", callback=None, active=None, enabled=None, visible=None,
                 icon=None, kind="secondary", tip=None, trailing=None, font=None):
        self.rect = pygame.Rect(rect)
        self.label = label          # str ou fonction -> str
        self.callback = callback
        self.active = active        # fonction -> bool (bouton "sélectionné")
        self.enabled = enabled      # fonction -> bool
        self.visible = visible      # fonction -> bool (None = toujours visible)
        self.icon = icon            # nom d'icône (str ou fonction -> str)
        self.kind = kind
        self.tip = tip              # infobulle (ex. "Annuler  [U]")
        self.trailing = trailing    # petite icône à droite (ex. "caret")
        self.font = font            # police imposée (sinon celle de l'écran)
        self._hover_since = None

    def is_visible(self):
        return self.visible() if self.visible else True

    def is_enabled(self):
        return self.enabled() if self.enabled else True

    def text(self):
        return self.label() if callable(self.label) else self.label

    def icon_name(self):
        return self.icon() if callable(self.icon) else self.icon

    # ------------------------------------------------------------------ dessin
    def draw(self, surface, font):
        if not self.is_visible():
            self._hover_since = None
            return
        font = self.font or font
        enabled = self.is_enabled()
        hover = enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        down = hover and pygame.mouse.get_pressed()[0]
        active = bool(self.active and self.active())

        now = pygame.time.get_ticks()
        if hover:
            Button._hover_any = True
            if self._hover_since is None:
                self._hover_since = now
            if self.tip and now - self._hover_since > 450:
                Button._tip = (self.tip, self.rect)
        else:
            self._hover_since = None

        face_c, hover_c, lip_c, text_c, border_c = (
            DISABLED if not enabled else ACTIVE if active else KINDS.get(self.kind, KINDS["secondary"]))
        r = self.rect
        ghost = self.kind == "ghost" and not active and enabled
        face = pygame.Rect(r.x, r.y + (LIP if down else 0), r.w, r.h - LIP)
        if ghost:
            if hover:
                pygame.draw.rect(surface, hover_c, r, border_radius=BTN_RADIUS)
                pygame.draw.rect(surface, border_c, r, 1, border_radius=BTN_RADIUS)
            face = pygame.Rect(r.x, r.y, r.w, r.h - LIP + 2)
        else:
            pygame.draw.rect(surface, lip_c, (r.x, r.y + LIP, r.w, r.h - LIP), border_radius=BTN_RADIUS)
            pygame.draw.rect(surface, hover_c if hover else face_c, face, border_radius=BTN_RADIUS)
            pygame.draw.rect(surface, border_c, face, 1, border_radius=BTN_RADIUS)
            if enabled and not down:      # fin reflet en haut
                hi = tuple(min(255, v + 34) for v in (hover_c if hover else face_c))
                pygame.draw.line(surface, hi, (face.x + 9, face.y + 2), (face.right - 10, face.y + 2))

        # contenu : [icône] [texte] [icône finale], centré dans la face
        label = self.text()
        img = font.render(label, True, text_c) if label else None
        scale = 1.0 if font.get_height() <= 24 else 1.5     # icônes plus grandes avec la grosse police
        iw = round(self.ICON_W * scale)
        items = []                                   # (nom d'icône | None, largeur)
        if self.icon_name():
            items.append((self.icon_name(), iw))
        if img:
            items.append((None, img.get_width()))
        if self.trailing:
            items.append((self.trailing, 12))
        total = sum(w for _, w in items) + self.GAP * (len(items) - 1)
        x, cy = face.centerx - total // 2, face.centery
        for name, w in items:
            if name:
                draw_icon(surface, name, x + w / 2, cy, text_c, scale if name != self.trailing else 1.0)
            else:
                surface.blit(img, (x, cy - img.get_height() // 2))
            x += w + self.GAP

    @classmethod
    def draw_tip(cls, surface, font):
        """À appeler une fois par image, après tous les boutons (infobulle + curseur)."""
        tip, rect = cls._tip or (None, None)
        if tip:
            img = font.render(tip, True, C.TEXT)
            box = pygame.Rect(0, 0, img.get_width() + 20, img.get_height() + 12)
            box.midtop = (rect.centerx, rect.bottom + 8)
            if box.bottom > surface.get_height() - 4:
                box.midbottom = (rect.centerx, rect.top - 8)
            box.clamp_ip(surface.get_rect().inflate(-8, -8))
            pygame.draw.rect(surface, (14, 15, 24), box.move(0, 2), border_radius=7)
            pygame.draw.rect(surface, (22, 24, 38), box, border_radius=7)
            pygame.draw.rect(surface, C.PANEL_BORDER, box, 1, border_radius=7)
            surface.blit(img, img.get_rect(center=box.center))
        try:
            hand = cls._hover_any
            if getattr(cls, "_cursor_hand", None) != hand:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW)
                cls._cursor_hand = hand
        except pygame.error:
            pass
        cls._tip = None
        cls._hover_any = False

    # --------------------------------------------------------------- événements
    def handle(self, event):
        if (self.is_visible() and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos) and self.is_enabled()):
            if Button.on_click:
                Button.on_click()
            self.callback()
            return True
        return False


# ============================================================ barre d'outils (fond)
def draw_toolbar_bg(surface, rect, radius=0, border="bottom"):
    """Fond de barre d'outils pour regrouper visuellement des boutons."""
    pygame.draw.rect(surface, C.PANEL_BG, rect, border_radius=radius)
    if border == "bottom":
        pygame.draw.line(surface, C.PANEL_BORDER, rect.bottomleft, rect.bottomright)
    elif border == "all":
        pygame.draw.rect(surface, C.PANEL_BORDER, rect, 1, border_radius=radius)


def draw_separator(surface, x, y0, y1):
    pygame.draw.line(surface, C.PANEL_BORDER, (x, y0), (x, y1))
