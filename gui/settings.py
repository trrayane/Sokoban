"""Sauvegarde des options et de la progression dans settings.json."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "settings.json"
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
