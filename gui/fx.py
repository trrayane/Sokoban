"""Effets visuels : dégradés, lueurs, particules, logo pixel-art 3D, décor animé, panneaux."""
import math
import random

import pygame

from gui import constants as C


# ------------------------------------------------------------------- maths
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_c(c1, c2, t):
    return tuple(int(lerp(x, y, t)) for x, y in zip(c1, c2))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_back(t):
    """Arrivée avec un petit rebond."""
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# --------------------------------------------------------------- surfaces
def vgradient(size, stops):
    """Dégradé vertical. stops = [(position 0..1, couleur), ...]."""
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        p = y / max(1, h - 1)
        col = stops[-1][1]
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= p <= p1:
                col = lerp_c(c0, c1, (p - p0) / max(1e-6, p1 - p0))
                break
        if len(col) == 3:
            col = tuple(col) + (255,)
        pygame.draw.line(s, col, (0, y), (w, y))
    return s


def tint(surf, color):
    t = surf.copy()
    t.fill(tuple(color)[:3] + (255,), special_flags=pygame.BLEND_RGBA_MULT)
    return t


def logo_surface(font, text, top, bottom, outline, extrude, depth=6, ol=4):
    """Texte 'logo de jeu' : dégradé + extrusion 3D + contour épais.
    Renvoie (surface, masque_du_texte, marge)."""
    mask = font.render(text, True, (255, 255, 255)).convert_alpha()
    w, h = mask.get_size()
    pad = ol + 1
    solid = pygame.Surface((w, h + depth), pygame.SRCALPHA)
    for i in range(depth + 1):
        solid.blit(mask, (0, i))
    out = pygame.Surface((w + 2 * pad, h + depth + 2 * pad), pygame.SRCALPHA)
    o = tint(solid, outline)
    for dx in range(-ol, ol + 1):
        for dy in range(-ol, ol + 1):
            if dx * dx + dy * dy <= ol * ol + ol:
                out.blit(o, (pad + dx, pad + dy))
    out.blit(tint(solid, extrude), (pad, pad))
    face = vgradient((w, h), [(0, top), (1, bottom)])
    face.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    out.blit(face, (pad, pad))
    return out, mask, pad


_title_cache = {}


def title_surface(font, text):
    """Titre d'écran (cache)."""
    key = (id(font), text)
    if key not in _title_cache:
        _title_cache[key] = logo_surface(font, text, (255, 240, 160), (244, 150, 30),
                                         (34, 16, 8), (150, 70, 12), depth=4, ol=3)[0]
    return _title_cache[key]


def spaced_text(font, text, color, spacing=2):
    imgs = [font.render(c, True, color) for c in text]
    w = sum(i.get_width() + spacing for i in imgs) - spacing
    s = pygame.Surface((w, max(i.get_height() for i in imgs)), pygame.SRCALPHA)
    x = 0
    for i in imgs:
        s.blit(i, (x, 0))
        x += i.get_width() + spacing
    return s


# ------------------------------------------------------------------ lueurs
_radial = {}


def radial(radius, color, strength=1.0):
    """Halo radial pour un blit additif (le noir n'ajoute rien)."""
    key = (radius, tuple(color), round(strength, 2))
    s = _radial.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2))
        steps = max(14, radius // 3)
        for i in range(steps):
            k = (i / steps) ** 2 * strength
            col = tuple(min(255, int(c * k)) for c in color)
            pygame.draw.circle(s, col, (radius, radius), int(radius * (1 - i / steps)))
        _radial[key] = s
    return s


def add_glow(surf, center, radius, color, strength=1.0):
    g = radial(radius, color, strength)
    surf.blit(g, g.get_rect(center=(int(center[0]), int(center[1]))), special_flags=pygame.BLEND_RGB_ADD)


_ellipse = {}


def add_glow_rect(surf, rect, color, strength=1.0):
    """Halo elliptique autour d'un rectangle (additif)."""
    key = (rect.w, rect.h, tuple(color), round(strength, 2))
    g = _ellipse.get(key)
    if g is None:
        g = pygame.transform.smoothscale(radial(96, color, strength), (rect.w + 110, rect.h + 90))
        _ellipse[key] = g
    surf.blit(g, g.get_rect(center=rect.center), special_flags=pygame.BLEND_RGB_ADD)


def make_vignette(w, h, strength=215):
    sw, sh = w // 10, h // 10
    s = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for y in range(sh):
        for x in range(sw):
            dx = (x / (sw - 1) - 0.5) * 2
            dy = (y / (sh - 1) - 0.5) * 2
            d = math.sqrt(dx * dx * 0.85 + dy * dy * 1.15)
            s.set_at((x, y), (6, 5, 16, int(strength * clamp((d - 0.42) / 0.95) ** 1.5)))
    return pygame.transform.smoothscale(s, (w, h))


# ----------------------------------------------------------------- panneau
def panel(surf, rect, alpha=215):
    """Panneau 'verre sombre' à bordure double et coins dorés."""
    sh = pygame.Surface((rect.w + 30, rect.h + 30), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 90), sh.get_rect().inflate(-10, -10), border_radius=18)
    surf.blit(sh, (rect.x - 15, rect.y - 8))
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(body, (16, 18, 34, alpha), body.get_rect(), border_radius=12)
    surf.blit(body, rect)
    pygame.draw.rect(surf, (92, 88, 138), rect, 2, border_radius=12)
    pygame.draw.rect(surf, (40, 44, 72), rect.inflate(-10, -10), 1, border_radius=9)
    gold, L = (255, 196, 64), 22
    for x, y, sx, sy in ((rect.left, rect.top, 1, 1), (rect.right - 1, rect.top, -1, 1),
                         (rect.left, rect.bottom - 1, 1, -1), (rect.right - 1, rect.bottom - 1, -1, -1)):
        pygame.draw.line(surf, gold, (x + sx * 12, y), (x + sx * (12 + L), y), 3)
        pygame.draw.line(surf, gold, (x, y + sy * 12), (x, y + sy * (12 + L)), 3)


def diamond_rule(surf, cx, y, half_len, color=(255, 196, 64)):
    """Filet décoratif avec losange central : ——◆——"""
    pygame.draw.line(surf, color, (cx - half_len, y), (cx - 10, y), 2)
    pygame.draw.line(surf, color, (cx + 10, y), (cx + half_len, y), 2)
    pygame.draw.polygon(surf, color, [(cx - 6, y), (cx, y - 6), (cx + 6, y), (cx, y + 6)])


def keycap(surf, rect, font=None, label=None, arrow=None):
    """Petite touche de clavier (flèche dessinée ou texte)."""
    pygame.draw.rect(surf, (20, 22, 38), rect.move(0, 3), border_radius=7)
    pygame.draw.rect(surf, (52, 57, 88), rect, border_radius=7)
    pygame.draw.rect(surf, (116, 124, 168), rect, 1, border_radius=7)
    col = (226, 230, 248)
    c = rect.center
    if arrow:
        d = {"up": [(c[0] - 6, c[1] + 3), (c[0] + 6, c[1] + 3), (c[0], c[1] - 5)],
             "down": [(c[0] - 6, c[1] - 3), (c[0] + 6, c[1] - 3), (c[0], c[1] + 5)]}[arrow]
        pygame.draw.polygon(surf, col, d)
    elif label:
        img = font.render(label, True, col)
        surf.blit(img, img.get_rect(center=(c[0], c[1] - 1)))


# ------------------------------------------------------------------- décor
class Backdrop:
    """Salle de donjon animée : parallaxe à la souris, lueur des torches,
    braises qui montent, poussières flottantes, vignette."""
    PAD = 26

    def __init__(self, assets):
        T, P = 64, self.PAD
        W, H = C.WIN_W + 2 * P, C.WIN_H + 2 * P
        wall, floor = assets.get("wall", T), assets.get("floor", T)
        wall_rows = 4
        base = pygame.Surface((W, H))
        for y in range(0, H, T):
            for x in range(0, W, T):
                base.blit(wall if y // T < wall_rows else floor, (x, y))
        wall_bottom = wall_rows * T
        # éclairage : mur sombre en haut, sol éclairé au centre
        light = vgradient((W, H), [
            (0, (58, 52, 92)), (wall_bottom / H - 0.02, (112, 100, 150)),
            (wall_bottom / H + 0.01, (80, 70, 104)), (0.58, (126, 106, 136)), (1, (38, 34, 58))])
        base.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        # ombre portée du mur sur le sol
        base.blit(vgradient((W, 46), [(0, (0, 0, 0, 170)), (1, (0, 0, 0, 0))]), (0, wall_bottom))
        pygame.draw.line(base, (20, 16, 30), (0, wall_bottom - 1), (W, wall_bottom - 1), 3)
        self.base = base
        self.vig = make_vignette(C.WIN_W, C.WIN_H)
        self.sx = self.sy = 0.0
        self._last = pygame.time.get_ticks()
        rnd = random.Random(7)
        self.motes = [[rnd.uniform(0, C.WIN_W), rnd.uniform(0, C.WIN_H), rnd.uniform(4, 14),
                       rnd.uniform(0, 6.28), rnd.choice((2, 2, 3))] for _ in range(46)]
        self.embers = []
        self._dots = {}
        self._acc = 0.0

    def _dot(self, size, level):
        key = (size, level)
        if key not in self._dots:
            s = pygame.Surface((size, size))
            k = level / 15
            s.fill((int(255 * k), int(170 * k), int(70 * k)))
            self._dots[key] = s
        return self._dots[key]

    def draw(self, surf, torches=(), parallax=True):
        now = pygame.time.get_ticks()
        dt = min(50, now - self._last) / 1000
        self._last = now
        t = now / 1000
        mx, my = pygame.mouse.get_pos()
        tx = -(mx / C.WIN_W - 0.5) * 18 if parallax else 0
        ty = -(my / C.WIN_H - 0.5) * 12 if parallax else 0
        self.sx += (tx - self.sx) * 0.08
        self.sy += (ty - self.sy) * 0.08
        ox, oy = int(self.sx), int(self.sy)
        surf.blit(self.base, (-self.PAD + ox, -self.PAD + oy))

        # lueur vacillante des torches
        for i, (x, y) in enumerate(torches):
            f = 0.78 + 0.14 * math.sin(t * 11 + i * 2) + 0.08 * math.sin(t * 5.3 + i)
            add_glow(surf, (x + ox, y + oy), 270, (255, 138, 44), clamp(f, 0.5, 1.0) * 0.62)
            self._acc += dt
        # braises
        if torches:
            while self._acc > 0.05:
                self._acc -= 0.05
                x, y = random.choice(torches)
                self.embers.append([x + random.uniform(-8, 8), y, random.uniform(-14, 14),
                                    -random.uniform(34, 80), random.uniform(1.0, 2.1), 0.0])
        for e in self.embers[:]:
            e[5] += dt
            e[0] += (e[2] + math.sin(t * 3 + e[1] * 0.05) * 10) * dt
            e[1] += e[3] * dt
            if e[5] >= e[4]:
                self.embers.remove(e)
                continue
            lvl = int(15 * (1 - e[5] / e[4]))
            if lvl > 0:
                surf.blit(self._dot(3 if lvl > 6 else 2, lvl), (e[0] + ox, e[1] + oy),
                          special_flags=pygame.BLEND_RGB_ADD)
        # poussières
        for m in self.motes:
            m[1] -= m[2] * dt
            m[0] += math.sin(t * 0.7 + m[3]) * 8 * dt
            if m[1] < -6:
                m[1] = C.WIN_H + 6
                m[0] = random.uniform(0, C.WIN_W)
            lvl = int(4 + 5 * (0.5 + 0.5 * math.sin(t * 1.3 + m[3])))
            surf.blit(self._dot(m[4], lvl), (m[0] + ox * 1.6, m[1] + oy * 1.6),
                      special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.vig, (0, 0))
