"""
Écrans du jeu hors partie :
    MainMenu     : écran d'accueil (Commencer / Options / Crédits / Quitter)
    LevelSelect  : choix du niveau (miniatures, progression)
    OptionsScreen: vitesse, algorithme par défaut, plein écran, progression
    CreditsScreen: crédits (modifiez la liste CREDITS ci-dessous)
"""
import math
import random

import pygame

from core.levels import LEVELS
from core.puzzle import SokobanPuzzle
from gui import constants as C
from gui import fonts, fx
from gui.widgets import Button, draw_icon

# >>> MODIFIEZ ICI vos crédits <<<
CREDITS = [
    ("Projet", "Sokoban – Modélisation et résolution"),
    ("Réalisé par", "Rayane Terki"),
    ("Module", "Problem Solving – Master 1 Visual Computing"),
    ("Encadrante", "Dr. Meriem SEBAI"),
    ("Université", "USTHB – 2026/2027"),
    ("Graphismes", "Pixel art créé avec Aseprite"),
    ("Polices", "Press Start 2P et Silkscreen (licence OFL)"),
    ("Technologies", "Python 3 et Pygame"),
]


class Screen:
    def __init__(self, app):
        self.app = app
        self.buttons = []

    def on_enter(self):
        pass

    def handle_event(self, e):
        for b in self.buttons:
            if b.handle(e):
                return True
        return False

    def update(self, dt):
        pass

    def draw_buttons(self):
        for b in self.buttons:
            b.draw(self.app.screen, self.app.f_btn)

    def draw_title(self, text, y=60):
        a = self.app
        img = fx.title_surface(a.f_title, text.upper())
        rect = img.get_rect(center=(C.WIN_W // 2, y))
        a.screen.blit(img, rect)
        fx.diamond_rule(a.screen, rect.left - 80, y + 2, 56)
        fx.diamond_rule(a.screen, rect.right + 80, y + 2, 56)

    def back_button(self, target="menu"):
        return Button((24, 20, 130, 40), "Retour", lambda: self.app.go(target), icon="back",
                      tip="Retour  [Échap]")


# ====================================================================== ACCUEIL
class MainMenu(Screen):
    """Écran d'accueil : logo 3D animé, torches, scène décorative, menu à sélection."""
    ITEM_W, ITEM_H, STEP, Y0 = 360, 56, 68, 352
    TORCH = 7                      # échelle des torches (16 px -> 112 px)

    def __init__(self, app):
        super().__init__(app)
        W, H = C.WIN_W, C.WIN_H
        cx = W // 2
        spec = [("COMMENCER", "play", lambda: app.go("levels"), "gold"),
                ("OPTIONS", "gear", lambda: app.go("options"), "gold"),
                ("CRÉDITS", "info", lambda: app.go("credits"), "gold"),
                ("QUITTER", "power", app.quit, "red")]
        self.items = []
        for i, (label, icon, cb, kind) in enumerate(spec):
            self.items.append(dict(label=label, icon=icon, cb=cb, kind=kind, hl=0.0,
                                   rect=pygame.Rect(cx - self.ITEM_W // 2, self.Y0 + i * self.STEP,
                                                    self.ITEM_W, self.ITEM_H)))
        self.sel = 0
        self.t0 = pygame.time.get_ticks()
        self.f_item = fonts.silk(32)
        self.f_silk = fonts.silk(16)

        # logo : une surface 3D par lettre (animées séparément)
        self.letters = [fx.logo_surface(app.f_huge, ch, (255, 246, 176), (243, 142, 22),
                                        (36, 15, 8), (160, 72, 12), depth=8, ol=5) for ch in "SOKOBAN"]
        self.adv = 94
        self.strip = pygame.Surface((80, 130), pygame.SRCALPHA)          # reflet qui balaie le logo
        for x in range(80):
            a_ = int(215 * max(0.0, 1 - abs(x - 40) / 40) ** 1.4)
            pygame.draw.line(self.strip, (255, 255, 255, a_), (x, 0), (x, 130))
        self.sub = fx.spaced_text(self.f_silk, "POUSSEZ LES CAISSES SUR LES CIBLES", (214, 204, 255), 3)
        self.foot = fx.spaced_text(self.f_silk, "MASTER 1 VISUAL COMPUTING · USTHB", (118, 122, 160), 2)

        self.sparks = []
        self._burst = -1
        self._last = pygame.time.get_ticks()
        self.buttons = [
            Button((W - 104, H - 62, 40, 40), "", app.toggle_fullscreen, icon="fullscreen",
                   tip="Plein écran"),
            Button((W - 56, H - 62, 40, 40), "", app.toggle_sound,
                   icon=lambda: "sound_on" if app.sound.enabled else "sound_off", tip="Son  [N]")]

    # ------------------------------------------------------------ navigation
    def on_enter(self):
        self.t0 = pygame.time.get_ticks()
        self.sel = 0

    def select(self, i):
        if i != self.sel:
            self.sel = i
            self.app.sound.play("step")

    def activate(self, i):
        self.app.sound.play("click")
        self.items[i]["cb"]()

    def handle_event(self, e):
        n = len(self.items)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w, pygame.K_z):
                self.select((self.sel - 1) % n)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.select((self.sel + 1) % n)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.activate(self.sel)
            elif e.key == pygame.K_n:
                self.app.toggle_sound()
            elif e.key == pygame.K_ESCAPE:
                self.app.quit()
            return True
        if e.type == pygame.MOUSEMOTION:
            for i, it in enumerate(self.items):
                if it["rect"].collidepoint(e.pos):
                    self.select(i)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, it in enumerate(self.items):
                if it["rect"].collidepoint(e.pos):
                    self.sel = i
                    self.activate(i)
                    return True
        return super().handle_event(e)

    def update(self, dt):
        for i, it in enumerate(self.items):
            target = 1.0 if i == self.sel else 0.0
            it["hl"] += (target - it["hl"]) * min(1.0, dt / 80)

    # ---------------------------------------------------------------- dessin
    def torch_positions(self):
        T = self.TORCH * 16
        return [(64, 46), (C.WIN_W - 64 - T, 46)]

    def draw_wall_decor(self, surf, t):
        """Torches animées (vraies sprites du pack) + bannières."""
        sk = self.app.assets.skin
        pts = []
        for k, (x, y) in enumerate(self.torch_positions()):
            if sk.ok:
                frame = int(t * 8 + k * 2) % 4
                surf.blit(sk.anim(sk.torch, frame, self.TORCH * 16), (x + int(self.backdrop_dx), y + int(self.backdrop_dy)))
            pts.append((x + self.TORCH * 8, y + int(self.TORCH * 5)))
        return pts

    def stage(self, surf, dt):
        """Petite scène : le héros pousse une caisse sur sa cible (étincelles à l'arrivée)."""
        a, T, cx, y = self.app, 64, C.WIN_W // 2, 246
        sec = pygame.time.get_ticks() / 1000
        speed, dist, hold = 80, 5 * T, 1.6
        cyc = dist / speed + hold
        n, tt = int(sec // cyc), sec % cyc
        moving = tt < dist / speed
        offset = min(tt * speed, dist)
        box_x = cx - 192 + offset
        tx = cx + 128
        for i in range(8):
            surf.blit(a.assets.get("floor", T), (cx - 256 + i * T, y))
        surf.blit(a.assets.get("wall", T), (cx - 320, y))
        surf.blit(a.assets.get("wall", T), (cx + 256, y))
        # ombre portée
        sh = pygame.Surface((T, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 95), sh.get_rect())
        surf.blit(sh, (box_x - T + 2, y + T - 12))
        surf.blit(sh, (box_x + 2, y + T - 12))
        surf.blit(a.assets.get("target", T), (tx, y))
        done = offset >= dist
        if done:
            pulse = 0.55 + 0.25 * math.sin(sec * 6)
            fx.add_glow(surf, (tx + T // 2, y + T // 2), 90, (255, 200, 70), pulse)
            if self._burst != n:
                self._burst = n
                for _ in range(22):
                    ang = random.uniform(0, 6.283)
                    sp = random.uniform(60, 190)
                    self.sparks.append([tx + T / 2, y + T / 2, math.cos(ang) * sp,
                                        math.sin(ang) * sp - 60, random.uniform(0.5, 1.0), 0.0])
        surf.blit(a.assets.get("box_on_target" if done else "box", T), (box_x, y))
        frame = (pygame.time.get_ticks() // 180) % 2 if moving else 0
        surf.blit(a.assets.player("RIGHT", frame, T), (box_x - T, y))
        for sp in self.sparks[:]:
            sp[5] += dt
            sp[0] += sp[2] * dt
            sp[1] += sp[3] * dt
            sp[3] += 420 * dt
            if sp[5] >= sp[4]:
                self.sparks.remove(sp)
                continue
            k = 1 - sp[5] / sp[4]
            s = pygame.Surface((4, 4))
            s.fill((int(255 * k), int(210 * k), int(90 * k)))
            surf.blit(s, (sp[0], sp[1]), special_flags=pygame.BLEND_RGB_ADD)

    def draw_logo(self, surf, tm, t):
        W = C.WIN_W
        total = self.adv * 7 - 6
        x0 = (W - total) // 2
        top = 78
        # halo derrière le titre
        fx.add_glow_rect(surf, pygame.Rect(W // 2 - 300, top + 10, 600, 90), (150, 74, 14), 0.8)
        # balayage lumineux toutes les 4 s
        cyc = 4.2
        p = ((tm - 1.2) % cyc) / 1.0 if tm > 1.2 else 9
        band = fx.lerp(-80, total + 80, p) if p <= 1 else None
        for i, (img, mask, pad) in enumerate(self.letters):
            ap = fx.ease_back((tm - 0.05 - i * 0.08) / 0.55)
            if ap <= 0.001:
                continue
            y = top + math.sin(t * 2.0 + i * 0.55) * 4 + (1 - ap) * -150
            lx = x0 + i * self.adv
            img.set_alpha(int(255 * fx.clamp(ap * 3)))
            surf.blit(img, (lx - pad, y - pad))
            if band is not None and ap > 0.9:
                rel = band - 40 - lx
                if -80 < rel < mask.get_width():
                    tmp = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
                    tmp.blit(self.strip, (rel, 0))
                    tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    surf.blit(tmp, (lx, y))

    def draw_item(self, surf, i, it, tm, t):
        ap = fx.ease_out((tm - 0.55 - i * 0.1) / 0.45)
        if ap <= 0.001:
            return
        hl = it["hl"]
        red = it["kind"] == "red"
        base = it["rect"]
        r = pygame.Rect(base.x + int((1 - ap) * -90), base.y, base.w, base.h).inflate(int(30 * hl), int(6 * hl))
        pressed = hl > 0.5 and pygame.mouse.get_pressed()[0] and base.collidepoint(pygame.mouse.get_pos())
        if hl > 0.02:       # halo
            fl = 0.8 + 0.2 * math.sin(t * 9)
            fx.add_glow_rect(surf, r, (230, 70, 80) if red else (255, 160, 40), 0.55 * hl * fl * ap)
        # couleurs interpolées entre repos et sélection
        if red:
            top_c, bot_c, brd_c, txt_c, lip_c = (244, 120, 120), (190, 52, 66), (255, 190, 190), (255, 244, 244), (110, 24, 38)
        else:
            top_c, bot_c, brd_c, txt_c, lip_c = (255, 222, 118), (236, 150, 30), (255, 246, 190), (48, 28, 6), (150, 88, 10)
        c_top = fx.lerp_c((34, 36, 62), top_c, hl)
        c_bot = fx.lerp_c((22, 24, 44), bot_c, hl)
        c_brd = fx.lerp_c((96, 102, 144), brd_c, hl)
        c_txt = fx.lerp_c((208, 212, 236), txt_c, hl)
        c_lip = fx.lerp_c((12, 13, 24), lip_c, hl)
        lip = 5
        face = pygame.Rect(0, 0, r.w, r.h - lip)
        lay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(lay, c_lip + (255,), (0, lip, r.w, r.h - lip), border_radius=12)
        fy = lip if pressed else 0
        grad = fx.vgradient(face.size, [(0, c_top), (1, c_bot)])
        mask = pygame.Surface(face.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        if hl < 0.98:                    # léger verre translucide au repos
            grad.fill((255, 255, 255, int(235 - 25 * (1 - hl))), special_flags=pygame.BLEND_RGBA_MULT)
        lay.blit(grad, (0, fy))
        pygame.draw.rect(lay, c_brd, (0, fy, face.w, face.h), 2, border_radius=12)
        hi = fx.lerp_c((70, 76, 112), (255, 255, 255), hl * 0.75)
        pygame.draw.line(lay, hi, (14, fy + 4), (face.w - 15, fy + 4))
        # icône + libellé
        label = self.f_item.render(it["label"], True, c_txt)
        shade = self.f_item.render(it["label"], True, fx.lerp_c((0, 0, 0), (255, 240, 170) if not red else (120, 20, 30), hl))
        cy = fy + face.h // 2
        lay.blit(shade, shade.get_rect(center=(face.w // 2 + 16, cy + 1)))
        lay.blit(label, label.get_rect(center=(face.w // 2 + 16, cy - 2)))
        draw_icon(lay, it["icon"], 38, cy, c_txt, 1.35)
        lay.set_alpha(int(255 * ap))
        surf.blit(lay, r)
        # flèches de sélection qui rebondissent
        if hl > 0.05:
            b = int(math.sin(t * 7) * 4)
            col = (255, 214, 90) if not red else (255, 140, 140)
            my = r.y + (r.h - lip) // 2
            pygame.draw.polygon(surf, col, [(r.x - 30 + b, my - 10), (r.x - 30 + b, my + 10), (r.x - 16 + b, my)])
            pygame.draw.polygon(surf, col, [(r.right + 30 - b, my - 10), (r.right + 30 - b, my + 10), (r.right + 16 - b, my)])

    def draw(self, surf):
        a = self.app
        now = pygame.time.get_ticks()
        dt = min(50, now - self._last) / 1000
        self._last = now
        tm = (now - self.t0) / 1000
        t = now / 1000
        W, H = C.WIN_W, C.WIN_H
        cx = W // 2

        self.backdrop_dx, self.backdrop_dy = a.backdrop.sx, a.backdrop.sy
        torch_pts = [(x + int(a.backdrop.sx), y + int(a.backdrop.sy))
                     for x, y in [(p[0], p[1]) for p in self.torch_points()]]
        a.draw_background(torch_pts)
        fx.add_glow(surf, (cx, 470), 380, (74, 34, 90), 0.55)     # halo d'ambiance sous le menu
        self.draw_wall_decor(surf, t)
        self.draw_logo(surf, tm, t)

        # sous-titre entouré de filets
        sa = fx.ease_out((tm - 0.7) / 0.5)
        if sa > 0:
            self.sub.set_alpha(int(255 * sa))
            sy = 198
            surf.blit(self.sub, self.sub.get_rect(center=(cx, sy)))
            hw = self.sub.get_width() // 2
            fx.diamond_rule(surf, cx - hw - 90, sy, 62)
            fx.diamond_rule(surf, cx + hw + 90, sy, 62)

        self.stage(surf, dt)
        for i, it in enumerate(self.items):
            self.draw_item(surf, i, it, tm, t)

        # raccourcis clavier + pied de page
        fa = fx.ease_out((tm - 1.1) / 0.5)
        if fa > 0:
            lay = pygame.Surface((420, 44), pygame.SRCALPHA)
            fx.keycap(lay, pygame.Rect(0, 0, 34, 34), arrow="up")
            fx.keycap(lay, pygame.Rect(40, 0, 34, 34), arrow="down")
            lab = self.f_silk.render("CHOISIR", True, (150, 156, 196))
            lay.blit(lab, (84, 9))
            fx.keycap(lay, pygame.Rect(176, 0, 96, 34), self.f_silk, "ENTRÉE")
            lab = self.f_silk.render("VALIDER", True, (150, 156, 196))
            lay.blit(lab, (282, 9))
            lay.set_alpha(int(255 * fa))
            surf.blit(lay, (28, H - 68))
            self.foot.set_alpha(int(255 * fa))
            surf.blit(self.foot, self.foot.get_rect(center=(cx, H - 20)))
        self.draw_buttons()

    def torch_points(self):
        """Position (x, y) du bout de flamme de chaque torche."""
        T = self.TORCH * 16
        return [(x + T // 2, y + int(T * 0.30)) for x, y in self.torch_positions()]


# ================================================================= CHOIX NIVEAU
class LevelSelect(Screen):
    COLS, CW, CH, GAP, TOP = 5, 190, 172, 24, 120

    def __init__(self, app):
        super().__init__(app)
        self.buttons = [self.back_button("menu")]
        self.sel = 0
        self.scroll = 0
        self.thumbs = {}

    def on_enter(self):
        self.sel = min(self.app.level_idx, len(LEVELS) - 1)
        self.ensure_visible()

    # --- géométrie
    def card_rect(self, i):
        r, c = divmod(i, self.COLS)
        total = self.COLS * self.CW + (self.COLS - 1) * self.GAP
        x0 = (C.WIN_W - total) // 2
        return pygame.Rect(x0 + c * (self.CW + self.GAP),
                           self.TOP + r * (self.CH + self.GAP) - self.scroll,
                           self.CW, self.CH)

    def max_scroll(self):
        rows = -(-len(LEVELS) // self.COLS)
        content = rows * (self.CH + self.GAP)
        return max(0, content - (C.WIN_H - self.TOP - 10))

    def ensure_visible(self):
        r = self.card_rect(self.sel)
        if r.top < self.TOP - 10:
            self.scroll = max(0, self.scroll - (self.TOP - 10 - r.top))
        elif r.bottom > C.WIN_H - 10:
            self.scroll = min(self.max_scroll(), self.scroll + r.bottom - (C.WIN_H - 10))

    # --- miniature
    def thumb(self, i):
        if i not in self.thumbs:
            w, h = self.CW - 16, 96
            p = SokobanPuzzle(LEVELS[i]["grid"])
            L, a = p.layout, self.app.assets
            t = max(4, min(w // L.width, h // L.height, 32))
            s = pygame.Surface((w, h))
            s.fill(C.BOARD_BG)
            ox, oy = (w - L.width * t) // 2, (h - L.height * t) // 2
            if a.skin.ok:
                s.blit(a.skin.build_static(L, t), (ox, oy))
                for (r, c) in L.targets:
                    s.blit(a.get("target", t), (ox + c * t, oy + r * t))
            else:
                for (r, c) in L.inside:
                    s.blit(a.get("floor", t), (ox + c * t, oy + r * t))
                    if (r, c) in L.targets:
                        s.blit(a.get("target", t), (ox + c * t, oy + r * t))
                for (r, c) in L.visible_walls:
                    s.blit(a.get("wall", t), (ox + c * t, oy + r * t))
            for (r, c) in p.boxes:
                s.blit(a.get("box_on_target" if (r, c) in L.targets else "box", t),
                       (ox + c * t, oy + r * t))
            pr, pc = p.player
            s.blit(a.player("DOWN", 0, t), (ox + pc * t, oy + pr * t))
            self.thumbs[i] = (s, len(p.boxes))
        return self.thumbs[i]

    # --- événements
    def launch(self, i):
        if 0 <= i < len(LEVELS):
            self.app.start_level(i)

    def handle_event(self, e):
        n = len(LEVELS)
        if e.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.max_scroll(), self.scroll - e.y * 40))
            return True
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.go("menu")
            elif e.key == pygame.K_RETURN:
                self.launch(self.sel)
            else:
                d = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1,
                     pygame.K_UP: -self.COLS, pygame.K_DOWN: self.COLS}.get(e.key)
                if d is not None and 0 <= self.sel + d < n:
                    self.sel += d
                    self.ensure_visible()
            return True
        if e.type == pygame.MOUSEMOTION and e.pos[1] > self.TOP - 10:
            for i in range(n):
                if self.card_rect(i).collidepoint(e.pos):
                    self.sel = i
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                and e.pos[1] > self.TOP - 10):
            for i in range(n):
                if self.card_rect(i).collidepoint(e.pos):
                    self.launch(i)
                    return True
        return super().handle_event(e)

    # --- dessin
    def draw(self, surf):
        a = self.app
        a.draw_background()
        self.draw_title("Choisir un niveau", 44)
        done = set(a.settings["completed"])
        sub = a.f_small.render(f"{len(done)} / {len(LEVELS)} niveaux terminés",
                               True, C.TEXT_DIM)
        surf.blit(sub, sub.get_rect(center=(C.WIN_W // 2, 86)))

        surf.set_clip(pygame.Rect(0, self.TOP - 10, C.WIN_W, C.WIN_H - self.TOP + 10))
        for i in range(len(LEVELS)):
            r = self.card_rect(i)
            if r.bottom < self.TOP - 10 or r.top > C.WIN_H:
                continue
            selected = (i == self.sel)
            if selected:
                fx.add_glow_rect(surf, r, (255, 160, 40), 0.30)
            pygame.draw.rect(surf, C.PANEL_BG, r, border_radius=10)
            pygame.draw.rect(surf, C.ACCENT if selected else C.PANEL_BORDER, r,
                             3 if selected else 1, border_radius=10)
            thumb, nb = self.thumb(i)
            surf.blit(thumb, (r.x + 8, r.y + 8))
            surf.blit(a.f_bold.render(f"Niveau {i + 1}", True, C.TEXT), (r.x + 12, r.y + 112))
            info = f"{nb} caisse{'s' if nb > 1 else ''}"
            surf.blit(a.f_small.render(info, True, C.TEXT_DIM), (r.x + 12, r.y + 142))
            if i in done:
                ok = a.f_small.render("Terminé", True, C.GOOD)
                surf.blit(ok, (r.right - ok.get_width() - 12, r.y + 142))
        surf.set_clip(None)
        self.draw_buttons()


# ===================================================================== OPTIONS
class OptionsScreen(Screen):
    X, Y0, STEP = 640, 190, 84

    def __init__(self, app):
        super().__init__(app)
        self.msg = ""
        X, Y0, S = self.X, self.Y0, self.STEP
        b = self.buttons
        b.append(self.back_button("menu"))
        b.append(Button((X, Y0, 50, 44), "", lambda: app.set_speed(app.speed_idx - 1), icon="minus"))
        b.append(Button((X + 250, Y0, 50, 44), "", lambda: app.set_speed(app.speed_idx + 1), icon="plus"))
        for i, name in enumerate(app.algos):
            b.append(Button((X + i * 100, Y0 + S, 90, 44), name,
                            lambda n=name: app.set_default_algo(n),
                            active=lambda n=name: app.algo == n))
        b.append(Button((X, Y0 + 2 * S, 200, 44),
                        lambda: "Activé" if app.settings["fullscreen"] else "Désactivé",
                        app.toggle_fullscreen,
                        active=lambda: app.settings["fullscreen"]))
        b.append(Button((X, Y0 + 3 * S, 300, 44), "Réinitialiser la progression", self.reset_progress,
                        icon="restart", kind="danger"))

    def on_enter(self):
        self.msg = ""

    def reset_progress(self):
        self.app.reset_progress()
        self.msg = "Progression effacée."

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.go("menu")
            return True
        return super().handle_event(e)

    def draw(self, surf):
        a = self.app
        a.draw_background()
        self.draw_title("Options", 60)
        panel = pygame.Rect(150, 150, C.WIN_W - 300, 4 * self.STEP + 30)
        fx.panel(surf, panel)

        rows = ["Vitesse de simulation", "Algorithme par défaut",
                "Plein écran", "Progression"]
        for i, label in enumerate(rows):
            y = self.Y0 + i * self.STEP
            surf.blit(a.f_bold.render(label, True, C.TEXT), (190, y + 10))
        # barre de vitesse
        for k in range(len(C.SPEEDS)):
            col = C.ACCENT if k <= a.speed_idx else C.BTN
            pygame.draw.rect(surf, col, (self.X + 62 + k * 30, self.Y0 + 10, 24, 24),
                             border_radius=4)
        n_done = len(a.settings["completed"])
        surf.blit(a.f_small.render(f"{n_done} / {len(LEVELS)} niveaux terminés",
                                   True, C.TEXT_DIM), (190, self.Y0 + 3 * self.STEP + 36))
        if self.msg:
            surf.blit(a.f_small.render(self.msg, True, C.GOOD),
                      (self.X + 320, self.Y0 + 3 * self.STEP + 14))
        self.draw_buttons()


# ===================================================================== CREDITS
class CreditsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [self.back_button("menu")]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.app.go("menu")
            return True
        return super().handle_event(e)

    def draw(self, surf):
        a = self.app
        a.draw_background()
        self.draw_title("Crédits", 60)
        panel = pygame.Rect(180, 130, C.WIN_W - 360, 62 * len(CREDITS) + 20)
        fx.panel(surf, panel)
        y = panel.y + 18
        for head, text in CREDITS:
            h = a.f_small.render(head.upper(), True, C.TEXT_DIM)
            t = a.f_bold.render(text, True, C.TEXT)
            surf.blit(h, h.get_rect(center=(C.WIN_W // 2, y + 8)))
            surf.blit(t, t.get_rect(center=(C.WIN_W // 2, y + 32)))
            y += 62
        end = a.f_norm.render("Merci d'avoir joué !", True, C.ACCENT)
        surf.blit(end, end.get_rect(center=(C.WIN_W // 2, panel.bottom + 34)))
        self.draw_buttons()
