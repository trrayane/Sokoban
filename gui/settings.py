"""Sauvegarde des options et de la progression dans settings.json."""
import json
import sys
from pathlib import Path

# Dans l'exécutable (.exe), settings.json est écrit à côté du .exe
# (le dossier du programme est le seul endroit inscriptible).
if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).resolve().parent
else:
    BASE = Path(__file__).resolve().parent.parent
PATH = BASE / "settings.json"
DEFAULTS = {"speed": 2, "algo": "BFS", "fullscreen": False, "sound": True, "completed": []}


def load():
    data = dict(DEFAULTS)
    try:
        data.update(json.loads(PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return data


def save(data):
    try:
        PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass
