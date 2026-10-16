"""
Build de l'exécutable Windows :  python build.py

Génère un icône .ico à partir du sprite du joueur, puis produit
dist/Sokoban.exe  (fichier unique, autonome : il suffit de le double-cliquer).

Dépendances :  pip install pyinstaller pillow
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
EXE = DIST / "Sokoban.exe"


def make_icon():
    from PIL import Image

    src = ROOT / "assets" / "player_down_0.png"
    out = ROOT / "icon.ico"
    img = Image.open(src).convert("RGBA")
    sizes = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    img.save(out, format="ICO", sizes=sizes)
    print(f"icône -> {out.name} {img.size} (nettoyée)")
    return out


def build(icon):
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", "Sokoban",
        "--icon", str(icon),
        "--add-data", f"{ROOT / 'assets'};assets",
        "--add-data", f"{ROOT / 'levels'};levels",
        "--collect-data", "pygame",
        "--hidden-import", "pygame",
        str(ROOT / "main.py"),
    ]
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == "__main__":
    icon = make_icon()
    build(icon)
    if EXE.exists():
        size = EXE.stat().st_size / 1024 / 1024
        print(f"\nOK -> {EXE}  ({size:.1f} Mo)")
    else:
        sys.exit("build échoué : Sokoban.exe introuvable")
