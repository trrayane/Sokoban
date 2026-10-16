"""Sons et musique (pygame.mixer). Si l'audio n'est pas disponible, le jeu continue en silence.

Les fichiers sont dans assets/sounds/ : step, push, bump, target, undo, click, win, music
(.wav ou .ogg). Remplacez-les par les vôtres, ou lancez  python tools/generate_sounds.py
"""
from pathlib import Path

import pygame

SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
NAMES = ["step", "push", "bump", "target", "undo", "click", "win"]
VOLUMES = {"step": 0.5, "push": 0.8, "bump": 0.5, "target": 0.7, "undo": 0.5,
           "click": 0.5, "win": 0.9}
MUSIC_VOLUME = 0.35


class Sound:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.ok = False
        self.sfx = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.ok = True
        except pygame.error:
            return
        for n in NAMES:
            for ext in ("wav", "ogg"):
                p = SOUND_DIR / f"{n}.{ext}"
                if p.exists():
                    try:
                        s = pygame.mixer.Sound(str(p))
                        s.set_volume(VOLUMES[n])
                        self.sfx[n] = s
                    except pygame.error:
                        pass
                    break
        self.music_path = next((SOUND_DIR / f"music.{e}" for e in ("ogg", "wav")
                                if (SOUND_DIR / f"music.{e}").exists()), None)
        self.update_music()

    def play(self, name):
        if self.ok and self.enabled and name in self.sfx:
            self.sfx[name].play()

    def update_music(self):
        if not self.ok or not self.music_path:
            return
        try:
            if self.enabled:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(str(self.music_path))
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()
        except pygame.error:
            pass

    def toggle(self):
        self.enabled = not self.enabled
        self.update_music()
        return self.enabled
