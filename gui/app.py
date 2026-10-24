"""
Interface Pygame (partie C du sujet) :
  - affiche la grille avec des sprites pixel art,
  - simule la solution trouvée (lecture / pause / pas à pas / vitesse),
  - affiche coût, nombre d'étapes (nœuds développés) et temps de chaque algorithme,
  - permet aussi de jouer à la main (flèches) avec annulation.
"""
import math
import threading
from pathlib import Path

import pygame

from core.levels import LEVELS
from core.puzzle import SokobanPuzzle
from gui import constants as C
from gui import fonts, fx
from gui import settings as S
from gui.assets import Assets
from gui.sound import Sound
from gui.menus import CreditsScreen, LevelSelect, MainMenu, OptionsScreen
from gui.widgets import Button, draw_separator, draw_toolbar_bg
from search import ALGORITHMS

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


class App:
    def __init__(self):
        pygame.init()
        self.settings = S.load()
        self.screen = None
        self.apply_display()
        pygame.display.set_caption("Sokoban – Résolution par recherche")
        self.clock = pygame.time.Clock()
        self.assets = Assets(ASSET_DIR)
        self.sound = Sound(self.settings.get("sound", True))
        Button.on_click = lambda: self.sound.play("click")

        self.f_small = pygame.font.SysFont("dejavusans,arial", 14)
        self.f_norm = pygame.font.SysFont("dejavusans,arial", 16)
        self.f_bold = pygame.font.SysFont("dejavusans,arial", 18, bold=True)
        self.f_title = fonts.silk(32)       # titres d'écran (pixel-art, accents corrects)
        self.f_big = fonts.silk(40)         # "Niveau résolu !"
        self.f_huge = fonts.press(88)       # logo du menu
        self.f_menu = pygame.font.SysFont("dejavusans,arial", 24, bold=True)
        self.f_btn = pygame.font.SysFont("dejavusans,arial", 15, bold=True)   # boutons

        self.backdrop = fx.Backdrop(self.assets)      # décor animé des menus
        self.fade = 1.0                               # fondu d'entrée (1 -> 0)
        self._fade_surf = pygame.Surface((C.WIN_W, C.WIN_H))

        self.algos = list(ALGORITHMS.keys())
        saved = "A* h3" if self.settings["algo"] == "A*" else self.settings["algo"]
        self.algo = saved if saved in self.algos else self.algos[0]
        self.compare_algos = [n for n in self.algos if n != "A* best"]
        self.results = {}            # (index_niveau, algo) -> SearchResult
        self.busy = False
        self.busy_label = ""
        self.pending = []            # résultats fournis par le thread
        self.lock = threading.Lock()
        self.speed_idx = max(0, min(len(C.SPEEDS) - 1, self.settings['speed']))
        self.running = True
        self.machine_open = False     # menu déroulant "Machine"
        self.held = []                # flèches maintenues (déplacement continu)
        self.queued = None            # prochain coup pré-saisi pendant une animation
        self.anim = None

        self.load_level(0)
        self.build_buttons()

        self.scene = "menu"
        self.bg = self.make_background()
        self.screens = {
            "menu": MainMenu(self),
            "levels": LevelSelect(self),
            "options": OptionsScreen(self),
            "credits": CreditsScreen(self),
        }

    # ------------------------------------------------- navigation / options
    def apply_display(self):
        """(Ré)ouvre la fenêtre. SCALED garde une surface logique 1120x720
        étirée à l'écran (la souris est traduite automatiquement).
        Le plein écran passe par toggle_fullscreen : bien plus fiable que
        FULLSCREEN|SCALED sur Windows (sinon écran noir / plantage).
        Chaque étape a un repli : le jeu s'ouvre toujours, même sans GPU."""
        size = (C.WIN_W, C.WIN_H)
        try:
            self.screen = pygame.display.set_mode(size, pygame.SCALED)
            scaled = True
        except pygame.error:
            self.screen = pygame.display.set_mode(size)
            scaled = False
        if self.settings["fullscreen"]:
            ok = False
            if scaled:
                try:
                    ok = pygame.display.toggle_fullscreen() == 0
                except pygame.error:
                    ok = False
            if not ok:
                for flags in (pygame.SCALED | pygame.FULLSCREEN, pygame.FULLSCREEN):
                    try:
                        self.screen = pygame.display.set_mode(size, flags)
                        break
                    except pygame.error:
                        continue

    def make_background(self):
        """Fond décoratif : sol + murs du jeu, assombris."""
        T = 64
        bg = pygame.Surface((C.WIN_W, C.WIN_H))
        for y in range(0, C.WIN_H, T):
            for x in range(0, C.WIN_W, T):
                edge = y in (0, ((C.WIN_H - 1) // T) * T) or x in (0, ((C.WIN_W - 1) // T) * T)
                bg.blit(self.assets.get("wall" if edge else "floor", T), (x, y))
        veil = pygame.Surface((C.WIN_W, C.WIN_H), pygame.SRCALPHA)
        veil.fill((14, 16, 30, 195))
        bg.blit(veil, (0, 0))
        return bg

    def draw_background(self, torches=(), parallax=True):
        self.backdrop.draw(self.screen, torches, parallax)

    def draw_fade(self):
        """Fondu depuis le noir à chaque changement d'écran."""
        if self.fade > 0:
            self._fade_surf.set_alpha(int(255 * fx.ease_out(self.fade)))
            self.screen.blit(self._fade_surf, (0, 0))

    def go(self, scene):
        self.playing = False
        self.fade = 1.0
        self.scene = scene
        if scene in self.screens:
            self.screens[scene].on_enter()

    def start_level(self, idx):
        self.load_level(idx)
        self.fade = 1.0
        self.scene = "game"

    def quit(self):
        self.running = False

    def save(self):
        S.save(self.settings)

    def set_speed(self, i):
        self.speed_idx = max(0, min(len(C.SPEEDS) - 1, i))
        self.settings["speed"] = self.speed_idx
        self.save()

    def set_default_algo(self, name):
        self.algo = name
        self.settings["algo"] = name
        self.save()

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        self.apply_display()
        self.save()

    def mark_completed(self):
        if self.level_idx not in self.settings["completed"]:
            self.settings["completed"].append(self.level_idx)
            self.save()

    def reset_progress(self):
        self.settings["completed"] = []
        self.save()

    # ------------------------------------------------------------------ niveau
    def load_level(self, idx):
        self.level_idx = idx % len(LEVELS)
        self.initial = SokobanPuzzle(LEVELS[self.level_idx]["grid"])
        L = self.initial.layout
        pad = 20
        avail_h = C.BOARD_H + 20 - C.BOARD_TOP - 10
        t = min((C.BOARD_W - pad) // L.width, avail_h // L.height, C.MAX_TILE)
        if t >= 32:
            t = t // 16 * 16                    # multiple de 16 => pixels réguliers
        self.tile = max(16, t)
        self.static = self.assets.skin.build_static(L, self.tile) if self.assets.skin.ok else None
        self.torches = [(p, self.assets.skin.wall_orient(L, *p))
                        for p, ch in L.decor.items() if ch == "T" and p in L.visible_walls]
        self.machine_open = False
        self.reset()

    def reset(self):
        self.current = self.initial
        self.history = []
        self.moves = 0
        self.pushes = 0
        self.path = None             # liste d'états de la simulation
        self.actions = None
        self.sim_index = 0
        self.playing = False
        self.sim_timer = 0
        self.facing = "DOWN"
        self.frame = 0
        self.shown = None            # résultat dont la simulation est affichée
        self.message = ""
        self.anim = None
        self.queued = None

    # ----------------------------------------------------------------- boutons
    def build_buttons(self):
        """Tous les boutons suivent la même grille : hauteur 40, écart 8, icône + libellé court.

        Barre du haut  : [Machine v] [Niveaux] [Son]   [< Niveau n >]   [Recommencer] [Annuler]
        Panneau droit  : (mode machine) niveau, Recommencer / Annuler, Jouer moi-même
        Barre du bas   : (mode machine) |<  <  Lecture  >  >|  |  -  vitesse  +
        """
        H, G = 40, 8
        x, w = C.PANEL_X, C.PANEL_W
        W = C.WIN_W
        self.buttons = []
        add = self.buttons.append
        machine_mode = self.machine_mode
        manual = lambda: not self.machine_mode()
        prev_lvl = lambda: self.load_level(self.level_idx - 1)
        next_lvl = lambda: self.load_level(self.level_idx + 1)
        can_undo = lambda: bool(self.history)

        # ---- Barre du haut, à gauche : toujours visible
        add(Button((12 + 140 + G, 6, 124, H), "Niveaux", lambda: self.go("levels"),
                   icon="levels", tip="Choisir un niveau  [Échap]"))
        add(Button((12 + 140 + G + 124 + G, 6, H, H), "", self.toggle_sound,
                   icon=lambda: "sound_on" if self.sound.enabled else "sound_off",
                   tip="Son  [N]"))

        # ---- Barre du haut, centre + droite (mode manuel)
        cx = W // 2
        add(Button((cx - 170, 6, H, H), "", prev_lvl, icon="prev", kind="ghost",
                   tip="Niveau précédent  [PgUp]", visible=manual))
        add(Button((cx + 130, 6, H, H), "", next_lvl, icon="next", kind="ghost",
                   tip="Niveau suivant  [PgDn]", visible=manual))
        add(Button((W - 12 - 120, 6, 120, H), "Annuler", self.undo, icon="undo",
                   enabled=can_undo, tip="Annuler le dernier coup  [U]", visible=manual))
        add(Button((W - 12 - 120 - G - 150, 6, 150, H), "Recommencer", self.reset, icon="restart",
                   tip="Recommencer le niveau  [R]", visible=manual))

        # ---- Panneau de droite (mode machine)
        add(Button((x, 56, H, H), "", prev_lvl, icon="prev", kind="ghost",
                   tip="Niveau précédent  [PgUp]", visible=machine_mode))
        add(Button((x + w - H, 56, H, H), "", next_lvl, icon="next", kind="ghost",
                   tip="Niveau suivant  [PgDn]", visible=machine_mode))
        half = (w - G) // 2
        add(Button((x, 108, half, H), "Recommencer", self.reset, icon="restart",
                   tip="Recommencer le niveau  [R]", visible=machine_mode))
        add(Button((x + half + G, 108, w - half - G, H), "Annuler", self.undo, icon="undo",
                   enabled=can_undo, tip="Annuler le dernier coup  [U]", visible=machine_mode))
        add(Button((x, 156, w, H), "Jouer moi-même", self.reset, icon="play", kind="primary",
                   tip="Quitter la simulation et reprendre la main", visible=machine_mode))

        # ---- Victoire
        by = C.BOARD_H + 20 - 58
        last = lambda: self.level_idx >= len(LEVELS) - 1
        add(Button((cx - 210, by, 200, 44), "Niveau suivant", next_lvl, icon="next", kind="primary",
                   visible=lambda: self.is_won() and not last()))
        add(Button((cx + 10, by, 200, 44), "Accueil", lambda: self.go("menu"), icon="home",
                   visible=lambda: self.is_won() and not last()))
        add(Button((cx - 100, by, 200, 44), "Accueil", lambda: self.go("menu"), icon="home",
                   kind="primary", visible=lambda: self.is_won() and last()))

        # ---- Barre de lecture, sous la grille (mode machine) : groupes centrés
        sim = lambda: self.path is not None
        play_w = 128
        group_a = 4 * H + play_w + 4 * G
        group_b = H + 8 + self.speed_bar_w() + 8 + H
        total = group_a + 36 + group_b
        bw = C.BOARD_W + 20
        x0 = (bw - total) // 2
        y = C.WIN_H - 56
        self.transport_rect = pygame.Rect(x0 - 16, y - 8, total + 32, H + 22)
        add(Button((x0, y, H, H), "", lambda: self.goto(0), icon="first",
                   tip="Début", visible=sim))
        add(Button((x0 + (H + G), y, H, H), "", lambda: self.step(-1), icon="prev",
                   tip="Pas en arrière", visible=sim))
        add(Button((x0 + 2 * (H + G), y, play_w, H),
                   lambda: "Pause" if self.playing else "Lecture", self.toggle_play,
                   icon=lambda: "pause" if self.playing else "play", kind="primary",
                   tip="Lecture / pause  [Espace]", visible=sim))
        add(Button((x0 + 2 * (H + G) + play_w + G, y, H, H), "", lambda: self.step(1), icon="next",
                   tip="Pas en avant", visible=sim))
        add(Button((x0 + 3 * (H + G) + play_w + G, y, H, H), "", lambda: self.goto(len(self.path) - 1),
                   icon="last", tip="Fin", visible=sim))
        bx = x0 + group_a + 36
        self.sep_x = x0 + group_a + 18
        add(Button((bx, y, H, H), "", lambda: self.change_speed(-1), icon="minus",
                   tip="Plus lent  [-]", visible=sim))
        self.speed_rect = pygame.Rect(bx + H + 8, y, self.speed_bar_w(), H)
        add(Button((bx + H + 8 + self.speed_bar_w() + 8, y, H, H), "", lambda: self.change_speed(1),
                   icon="plus", tip="Plus rapide  [+]", visible=sim))

        # ---- Bouton "Machine" + menu déroulant des algorithmes
        self.machine_btn = Button((12, 6, 140, H), "Machine", self.toggle_machine_menu,
                                  icon="chip", trailing="caret", kind="primary",
                                  active=lambda: self.machine_open,
                                  enabled=lambda: not self.busy,
                                  tip="Résoudre avec un algorithme  [M]")
        self.menu_buttons = []
        mx, my, mw = 16, 62 + 28, 226
        for i, name in enumerate(self.algos):
            self.menu_buttons.append(Button((mx, my + i * (36 + 4), mw - 12, 36), f"Résoudre avec {name}",
                                            lambda n=name: self.run_machine(n), icon="play",
                                            visible=lambda: self.machine_open))
        self.menu_buttons.append(Button((mx, my + len(self.algos) * 40 + 8, mw - 12, 36),
                                        "Comparer les algos", self.run_compare, icon="chart",
                                        kind="primary", visible=lambda: self.machine_open))

    @staticmethod
    def speed_bar_w():
        return len(C.SPEEDS) * 14 + (len(C.SPEEDS) - 1) * 4 + 16

    def machine_mode(self):
        return self.shown is not None or self.path is not None

    def board_w(self):
        """Largeur de la zone de jeu : tout l'écran, sauf en mode machine (panneau à droite)."""
        return C.BOARD_W + 20 if self.machine_mode() else C.WIN_W

    def toggle_sound(self):
        self.settings["sound"] = self.sound.toggle()
        self.save()

    def is_won(self):
        return (self.scene == "game" and self.path is None and self.shown is None
                and self.current.isGoal() and self.anim is None)

    def toggle_machine_menu(self):
        self.machine_open = not self.machine_open

    def run_machine(self, name):
        self.machine_open = False
        self.algo = name
        self.solve()

    def run_compare(self):
        self.machine_open = False
        self.compare_all()

    def change_speed(self, d):
        self.speed_idx = max(0, min(len(C.SPEEDS) - 1, self.speed_idx + d))

    # ------------------------------------------------------------- recherche
    def solve(self):
        self._start_worker([self.algo], compare=False)

    def compare_all(self):
        self._start_worker(self.compare_algos, compare=True)

    def _start_worker(self, algos, compare):
        if self.busy:
            return
        self.busy = True
        self.busy_label = "Comparaison en cours" if compare else "Recherche en cours : " + algos[0]
        idx, problem = self.level_idx, self.initial
        if not compare:                    # on repart du début du niveau pour la simulation
            self.reset()

        def work():
            for name in algos:
                res = ALGORITHMS[name](problem)
                with self.lock:
                    self.pending.append((idx, name, res, compare))
            with self.lock:
                self.pending.append(None)           # marqueur de fin

        threading.Thread(target=work, daemon=True).start()

    def process_pending(self):
        with self.lock:
            items, self.pending = self.pending, []
        for item in items:
            if item is None:
                self.busy = False
                continue
            idx, name, res, compare = item
            self.results[(idx, name)] = res
            if not compare and idx == self.level_idx and self.scene == "game":
                self.start_simulation(res)

    # ------------------------------------------------------------ simulation
    def start_simulation(self, res):
        self.reset()
        self.shown = res
        if res.status != "ok":
            self.message = ("Limite de nœuds atteinte" if res.status == "limit"
                            else "Aucune solution")
            return
        self.path, self.actions = res.path, res.solution
        self.sim_index = 0
        self.playing = len(self.path) > 1

    def toggle_play(self):
        if self.path is None:
            return
        if self.sim_index >= len(self.path) - 1:
            self.goto(0)
        self.playing = not self.playing

    def goto(self, i):
        if self.path is None:
            return
        self.playing = False
        self.anim = None
        self.sim_index = max(0, min(len(self.path) - 1, i))
        self.current = self.path[self.sim_index]
        self.frame += 1

    def step(self, d):
        if self.path is None:
            return
        self.playing = False
        self._advance(d)

    def _advance(self, d):
        new = max(0, min(len(self.path) - 1, self.sim_index + d))
        if new == self.sim_index:
            return False
        prev = self.current
        if d > 0:
            self.facing = self.actions[new - 1]
        self.sim_index = new
        self.current = self.path[new]
        self.frame += 1
        dur = int(min(C.MOVE_MS, C.SPEEDS[self.speed_idx] * 0.85))
        if d > 0:
            self.play_move_sound(prev, self.current)
        if d > 0 and dur >= 30:
            self.start_anim(prev, self.current, dur)
        else:
            self.anim = None
        return True

    # ------------------------------------------------------------- animation
    def start_anim(self, prev, new, dur):
        moved = new.boxes - prev.boxes
        box = (new.player, next(iter(moved))) if moved else None   # la caisse part de la case du joueur
        self.anim = {"t": 0, "dur": dur, "p0": prev.player, "p1": new.player, "box": box}

    # ------------------------------------------------------------ jeu manuel
    def try_move(self, action):
        if self.is_won():                             # niveau réussi : plus de déplacement
            return
        if self.path is not None:                   # on quitte la simulation
            self.path, self.actions, self.playing = None, None, False
            self.shown = None
        for a, s in self.current.successorFunction():
            if a == action:
                self.history.append((self.current, self.facing, self.moves, self.pushes))
                if s.boxes != self.current.boxes:
                    self.pushes += 1
                self.moves += 1
                prev = self.current
                self.current, self.facing = s, action
                self.frame += 1
                self.start_anim(prev, s, C.MOVE_MS)
                self.play_move_sound(prev, s)
                if s.isGoal():
                    self.mark_completed()
                return
        self.facing = action                        # on se tourne quand même
        if getattr(self, "bump", 0) <= 0:
            self.sound.play("bump")
        self.bump = 140                             # petit "rebond" contre le mur

    def play_move_sound(self, prev, new):
        moved = new.boxes - prev.boxes
        if moved:
            self.sound.play("push")
            if next(iter(moved)) in new.layout.targets:
                self.sound.play("target")
        else:
            self.sound.play("step")

    def undo(self):
        if self.history:
            self.current, self.facing, self.moves, self.pushes = self.history.pop()
            self.anim = None
            self.sound.play("undo")

    # ------------------------------------------------------------ événements
    MOVE_KEYS = {pygame.K_UP: "UP", pygame.K_DOWN: "DOWN", pygame.K_LEFT: "LEFT",
                 pygame.K_RIGHT: "RIGHT", pygame.K_w: "UP", pygame.K_z: "UP",
                 pygame.K_s: "DOWN", pygame.K_a: "LEFT", pygame.K_q: "LEFT",
                 pygame.K_d: "RIGHT"}

    def handle_game_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
            return
        # menu "Machine" : on le ferme si on clique ailleurs
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.machine_open:
                for b in self.menu_buttons:
                    if b.handle(e):
                        return
                self.machine_open = False
                if self.machine_btn.rect.collidepoint(e.pos):
                    return
            elif self.machine_btn.handle(e):
                return
        if e.type == pygame.KEYUP and e.key in self.MOVE_KEYS:
            d = self.MOVE_KEYS[e.key]
            if d in self.held:
                self.held.remove(d)
        elif e.type == pygame.KEYDOWN:
            k = e.key
            won = self.is_won()                       # après victoire : plus de déplacement
            if k == pygame.K_ESCAPE:
                if self.machine_open:
                    self.machine_open = False
                else:
                    self.go("levels")
            elif k in self.MOVE_KEYS and not won:
                d = self.MOVE_KEYS[k]
                self.held = [x for x in self.held if x != d] + [d]
                if self.anim is None:
                    self.try_move(d)
                else:
                    self.queued = d
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.is_won():
                if self.level_idx < len(LEVELS) - 1:
                    self.load_level(self.level_idx + 1)
                else:
                    self.go("menu")
            elif k == pygame.K_r:
                self.reset()
            elif k in (pygame.K_u, pygame.K_BACKSPACE) and not won:
                self.undo()
            elif k == pygame.K_n:
                self.toggle_sound()
            elif k == pygame.K_m and not self.busy:
                self.toggle_machine_menu()
            elif k == pygame.K_SPACE and not won:
                self.toggle_play()
            elif k in (pygame.K_PAGEUP, pygame.K_LEFTBRACKET):
                self.load_level(self.level_idx - 1)
            elif k in (pygame.K_PAGEDOWN, pygame.K_RIGHTBRACKET):
                self.load_level(self.level_idx + 1)
            elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.change_speed(1)
            elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.change_speed(-1)
        for b in self.buttons:
            if b.handle(e):
                break

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif self.scene == "game":
            self.handle_game_event(e)
        else:
            self.screens[self.scene].handle_event(e)

    # ----------------------------------------------------------------- update
    def update(self, dt):
        self.fade = max(0.0, self.fade - dt / 320)
        self.process_pending()
        if self.scene != "game":
            self.screens[self.scene].update(dt)
            return
        self.bump = max(0, getattr(self, "bump", 0) - dt)
        won = self.is_won()
        if won and self.held:
            self.held = []                            # plus de touches maintenues après victoire
        if won and not getattr(self, "_won_played", False):
            self.sound.play("win")
        self._won_played = won
        if self.anim:
            self.anim["t"] += dt
            if self.anim["t"] >= self.anim["dur"]:
                self.anim = None
        # coup pré-saisi ou touche maintenue => déplacement continu et fluide
        if self.anim is None and self.path is None and not self.machine_open:
            d, self.queued = self.queued, None
            if d is None and self.held:
                d = self.held[-1]
            if d:
                self.try_move(d)
        if self.playing and self.path:
            self.sim_timer += dt
            delay = C.SPEEDS[self.speed_idx]
            while self.sim_timer >= delay and self.playing:
                self.sim_timer -= delay
                if not self._advance(1):
                    self.playing = False

    # ---------------------------------------------------------------- dessin
    def draw_board(self):
        bw = self.board_w()
        board = pygame.Rect(0, 0, bw, C.BOARD_H + 20)
        pygame.draw.rect(self.screen, C.BOARD_BG, board)
        st, L, t = self.current, self.current.layout, self.tile
        ox = (bw - L.width * t) // 2
        oy = C.BOARD_TOP + (C.BOARD_H + 20 - C.BOARD_TOP - L.height * t) // 2
        a, skin, now = self.assets, self.assets.skin, pygame.time.get_ticks()
        scr = self.screen

        # sol + murs + portes (couche pré-dessinée)
        if self.static is not None:
            scr.blit(self.static, (ox, oy))
        else:
            for (r, c) in L.inside:
                scr.blit(a.get("floor", t), (ox + c * t, oy + r * t))
            for (r, c) in L.visible_walls:
                scr.blit(a.get("wall", t), (ox + c * t, oy + r * t))

        # cibles (drapeau animé)
        for (r, c) in L.targets:
            pos = (ox + c * t, oy + r * t)
            if skin.ok:
                scr.blit(skin.anim(skin.flag, now // 160 + r + c, t), pos)
            else:
                scr.blit(a.get("target", t), pos)

        # lueur des torches (scintillement) puis torches animées
        for (r, c), orient in self.torches:
            if skin.ok:
                cx, cy = ox + c * t + t // 2, oy + r * t + t // 2
                g = skin.glow(t)
                flick = 0.78 + 0.22 * math.sin(now / 90.0 + r * 3 + c * 5) \
                    + 0.06 * math.sin(now / 37.0 + c)
                g.set_alpha(max(0, min(255, int(255 * flick))))
                scr.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2))
        for (r, c), orient in self.torches:
            if skin.ok:
                pos = (ox + c * t, oy + r * t)
                fr = now // 110 + r * 2 + c
                if orient == "left":      # mur de gauche : la torche est posée sur le montant
                    scr.blit(skin.anim(skin.side_torch, fr, t, flip=True), (pos[0] - int(t * 0.1), pos[1]))
                elif orient == "right":
                    scr.blit(skin.anim(skin.side_torch, fr, t), pos)
                else:
                    scr.blit(skin.anim(skin.torch, fr, t), pos)

        # position visuelle (interpolée) du joueur et de la caisse poussée
        pr, pc = st.player
        vr, vc, moving, prog = float(pr), float(pc), False, 0.0
        moved_box = None
        if self.anim:
            an = self.anim
            prog = min(1.0, an["t"] / an["dur"])
            (r0, c0), (r1, c1) = an["p0"], an["p1"]
            vr, vc = r0 + (r1 - r0) * prog, c0 + (c1 - c0) * prog
            moving = True
            if an["box"]:
                (br0, bc0), (br1, bc1) = an["box"]
                moved_box = (br1, bc1, br0 + (br1 - br0) * prog, bc0 + (bc1 - bc0) * prog)

        shadow = pygame.Surface((t, t), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (t * 0.18, t * 0.72, t * 0.64, t * 0.2))

        for (r, c) in st.boxes:
            if moved_box and (r, c) == moved_box[:2]:
                fr, fc = moved_box[2], moved_box[3]
            else:
                fr, fc = r, c
            x, y = ox + fc * t, oy + fr * t
            name = "box_on_target" if (r, c) in L.targets else "box"
            scr.blit(shadow, (x, y))
            scr.blit(a.get(name, t), (x, y))

        # joueur : marche (2 frames + petit saut) ou respiration au repos
        if moving:
            frame = 1 if prog > 0.5 else 0
            hop = -math.sin(prog * math.pi) * t * 0.16
        else:
            frame = (now // 450) % 2
            hop = 0
        bump = getattr(self, "bump", 0)
        shove = 0
        if bump > 0 and not moving:                       # on se cogne contre un mur
            shove = math.sin(bump / 140 * math.pi) * t * 0.07
        dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[self.facing]
        x = ox + vc * t + dc * shove
        y = oy + vr * t + hop + dr * shove
        scr.blit(shadow, (ox + vc * t, oy + vr * t))
        scr.blit(a.player(self.facing, frame, t), (x, y))

        if self.is_won():
            veil = pygame.Surface((bw, 120), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 175))
            self.screen.blit(veil, (0, C.BOARD_H + 20 - 120))
            txt = self.f_big.render("NIVEAU RÉSOLU !", True, C.ACCENT)
            self.screen.blit(txt, txt.get_rect(center=(bw // 2,
                                                      C.BOARD_H + 20 - 92)))

    def text(self, s, pos, font=None, color=C.TEXT):
        img = (font or self.f_norm).render(s, True, color)
        self.screen.blit(img, pos)

    def draw_topbar(self):
        name = LEVELS[self.level_idx]["name"]
        lab = self.f_bold.render(f"{name}  ({self.level_idx + 1}/{len(LEVELS)})", True, C.TEXT)
        self.screen.blit(lab, lab.get_rect(center=(C.WIN_W // 2, 26)))

    def draw_panel(self):
        x, w = C.PANEL_X, C.PANEL_W
        if not self.machine_mode():
            return
        title = self.f_title.render("SOKOBAN", True, C.ACCENT)
        self.screen.blit(title, (x, 12))

        name = LEVELS[self.level_idx]["name"]
        lab = self.f_bold.render(f"{name}  ({self.level_idx + 1}/{len(LEVELS)})", True, C.TEXT)
        self.screen.blit(lab, lab.get_rect(center=(x + w // 2, 76)))

        machine = self.shown is not None or self.path is not None
        if not machine:                      # mode manuel : panneau épuré
            return
        top = 208
        box = pygame.Rect(x, top, w, 168)
        pygame.draw.rect(self.screen, C.PANEL_BG, box, border_radius=8)
        pygame.draw.rect(self.screen, C.PANEL_BORDER, box, 1, border_radius=8)
        y = box.y + 8
        if self.busy:
            dots = "." * (1 + (pygame.time.get_ticks() // 400) % 3)
            self.text(self.busy_label + dots, (box.x + 10, y), self.f_norm, C.ACCENT)
            y += 24
        res = self.shown
        if res is None:
            self.text("À toi de jouer !", (box.x + 10, y), self.f_bold, C.ACCENT); y += 26
            self.text(f"Coups : {self.moves}", (box.x + 10, y)); y += 22
            self.text(f"Poussées : {self.pushes}", (box.x + 10, y)); y += 22
            self.text("Flèches / ZQSD = bouger", (box.x + 10, y), self.f_small, C.TEXT_DIM); y += 18
            self.text("U = annuler   R = recommencer", (box.x + 10, y), self.f_small, C.TEXT_DIM)
        else:
            self.text(f"Machine : {res.algo}", (box.x + 10, y), self.f_bold, C.ACCENT); y += 26
            if res.status == "ok":
                self.text(f"Coût de la solution : {res.cost}", (box.x + 10, y)); y += 22
                self.text(f"Nœuds développés : {res.expanded:,}", (box.x + 10, y)); y += 22
                self.text(f"Nœuds générés : {res.generated:,}", (box.x + 10, y)); y += 22
                self.text(f"Temps : {res.time * 1000:.1f} ms", (box.x + 10, y)); y += 22
                self.text(f"Étape : {self.sim_index} / {len(self.path) - 1}", (box.x + 10, y),
                          self.f_norm, C.GOOD)
            else:
                self.text(self.message, (box.x + 10, y), self.f_norm, C.BAD); y += 22
                self.text(f"Nœuds développés : {res.expanded:,}", (box.x + 10, y))

        # tableau comparatif (seulement si la machine a déjà travaillé sur ce niveau)
        if not any((self.level_idx, n) in self.results for n in self.compare_algos):
            self.text("Espace : lecture/pause   Échap : niveaux", (x, C.WIN_H - 28),
                      self.f_small, C.TEXT_DIM)
            return
        ty = box.bottom + 16
        self.text("Comparaison (niveau actuel)", (x, ty), self.f_bold)
        ty += 28
        cols = [x, x + 62, x + 128, x + 220]
        for cx, h in zip(cols, ["Algo", "Coût", "Étapes", "Temps"]):
            self.text(h, (cx, ty), self.f_small, C.TEXT_DIM)
        ty += 20
        pygame.draw.line(self.screen, C.PANEL_BORDER, (x, ty), (x + w, ty))
        ty += 6
        for name in self.compare_algos:
            r = self.results.get((self.level_idx, name))
            color = C.ACCENT if (r and r is self.shown) else C.TEXT
            if r is None:
                row = [name, "-", "-", "-"]
            elif r.status != "ok":
                row = [name, "échec", f"{r.expanded:,}", f"{r.time:.2f}s"]
            else:
                row = [name, str(r.cost), f"{r.expanded:,}", f"{r.time * 1000:.0f} ms"]
            for cx, v in zip(cols, row):
                self.text(v, (cx, ty), self.f_norm, color)
            ty += 24
        self.text("Espace : lecture/pause   Échap : niveaux", (x, C.WIN_H - 28),
                  self.f_small, C.TEXT_DIM)

    def draw_controls(self):
        """Fond de la barre de lecture + jauge de vitesse (mode machine)."""
        if self.path is None:
            return
        draw_toolbar_bg(self.screen, self.transport_rect, radius=14, border="all")
        draw_separator(self.screen, self.sep_x, self.transport_rect.y + 12, self.transport_rect.bottom - 12)
        r = self.speed_rect
        for k in range(len(C.SPEEDS)):
            seg = pygame.Rect(r.x + 8 + k * 18, 0, 14, 8 + k * 3)
            seg.bottom = r.centery + 10
            on = k <= self.speed_idx
            pygame.draw.rect(self.screen, C.ACCENT if on else C.BTN, seg, border_radius=3)

    def draw_machine_menu(self):
        self.machine_btn.draw(self.screen, self.f_btn)
        if not self.machine_open:
            return
        n = len(self.menu_buttons)
        rect = pygame.Rect(10, 52, 226, 28 + n * 40 + 14)
        pygame.draw.rect(self.screen, (14, 15, 24), rect.move(0, 4), border_radius=12)
        pygame.draw.rect(self.screen, C.PANEL_BG, rect, border_radius=12)
        pygame.draw.rect(self.screen, C.PANEL_BORDER, rect, 1, border_radius=12)
        self.text("QUEL ALGORITHME ?", (22, 62), self.f_small, C.TEXT_DIM)
        for b in self.menu_buttons:
            b.draw(self.screen, self.f_btn)

    def draw(self):
        if self.scene != "game":
            self.screens[self.scene].draw(self.screen)
            self.draw_fade()
            Button.draw_tip(self.screen, self.f_small)
            pygame.display.flip()
            return
        self.screen.fill(C.BG)
        self.draw_board()
        bar_w = C.PANEL_X - 12 if self.machine_mode() else C.WIN_W
        draw_toolbar_bg(self.screen, pygame.Rect(0, 0, bar_w, 52))        # barre d'outils du haut
        if self.machine_mode():
            pygame.draw.rect(self.screen, C.PANEL_BORDER,
                             (C.PANEL_X - 12, 0, 1, C.WIN_H))
            self.draw_panel()
        else:
            self.draw_topbar()
        self.draw_controls()
        for b in self.buttons:
            b.draw(self.screen, self.f_btn)
        if self.busy and not self.machine_mode():
            lab = self.f_norm.render(self.busy_label + "...", True, C.ACCENT)
            pill = lab.get_rect(center=(C.WIN_W // 2, 78)).inflate(28, 14)
            pygame.draw.rect(self.screen, C.PANEL_BG, pill, border_radius=14)
            pygame.draw.rect(self.screen, C.ACCENT, pill, 1, border_radius=14)
            self.screen.blit(lab, lab.get_rect(center=pill.center))
        self.draw_machine_menu()
        self.draw_fade()
        Button.draw_tip(self.screen, self.f_small)
        pygame.display.flip()

    # --------------------------------------------------------------- boucle
    def run(self):
        while self.running:
            dt = self.clock.tick(C.FPS)
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
