"""Render the cards shown on the kit homepage as PNG images, from each game's own print sheets.

The homepage never redraws a card: it shows pictures of the real ones, so a card on the homepage always looks like the
card in the game. Run this after a game's cards change (and after that game's own `python tools/build.py`):

    python tools/card_images.py ../methodical-card-game ../red-flag-card-game ../major-revisions-card-game

Each argument is a game's folder; the folder name picks its cards from SHOWCASE. Standard library only, plus a local
Chrome or Edge in headless mode. The images go to assets/cards/<game>-<code>.png (520 x 727 px, transparent corners).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cards"

# Per game: its slug on the homepage and the card codes to show (a prompt card, then the answer that fits it).
# "back" is the game's card back.
SHOWCASE = {
    "methodical-card-game": ("methodical", ["back", "MTH-Q07", "MTH-D08", "MTH-B05"]),
    "red-flag-card-game": ("red-flag", ["back", "RF-C17", "RF-F13", "RF-K06"]),
    "major-revisions-card-game": ("major-revisions", ["back", "MR-P04", "MR-R17", "MR-4A-F"]),
}

W, H = 520, 727  # 63 x 88 mm at 520/63 px per mm

# Keeps only the chosen card, sized to fill the window, and re-runs the sheet's own fitCards after the fonts load.
ISOLATE = """<style>
html, body { margin: 0 !important; padding: 0 !important; background: transparent !important; }
:root, body { --card-u: calc(100vw / 63); }
#kit-shot { position: fixed; inset: 0; }
#kit-shot .tcg { margin: 0 !important; box-shadow: none !important; }
</style>
<script>
addEventListener("DOMContentLoaded", () => {
  const pick = [...document.querySelectorAll(".tcg")].find(CHOOSE);
  if (!pick) { document.title = "NOT FOUND"; return; }
  const box = document.createElement("div");
  box.id = "kit-shot";
  box.appendChild(pick);
  document.body.replaceChildren(box);
  fitCards();
  if (document.fonts) document.fonts.ready.then(() => fitCards());
});
</script>
"""


def browser():
    for exe in ("chrome", "msedge", "google-chrome", "chromium"):
        if shutil.which(exe):
            return shutil.which(exe)
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if Path(p).exists():
            return p
    sys.exit("No Chrome or Edge found: install one, or add it to PATH, then run this again.")


def render(exe, sheet, code, png, tmp):
    if code == "back":
        choose = 'c => c.classList.contains("back")'
    else:
        choose = f'c => !c.classList.contains("back") && c.textContent.includes({code!r})'
    html = sheet.read_text(encoding="utf-8")
    # <base> keeps the sheet's relative links working from the temporary copy.
    head = f'<base href="{sheet.parent.as_uri()}/">' + ISOLATE.replace("CHOOSE", choose)
    page = Path(tmp) / f"{png.stem}.html"
    page.write_text(html.replace("<head>", "<head>" + head, 1), encoding="utf-8")
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                    "--allow-file-access-from-files", f"--user-data-dir={Path(tmp) / 'profile'}",
                    f"--window-size={W},{H}", "--default-background-color=00000000",
                    "--virtual-time-budget=10000", f"--screenshot={png}", page.as_uri()],
                   capture_output=True, timeout=120)
    if not png.exists():
        sys.exit(f"{png.name}: the browser saved no image. Check that {sheet} opens in a browser.")


FAN = ["methodical-MTH-D08", "major-revisions-MR-R17", "red-flag-RF-F13"]  # one card per game, for READMEs


def fan(exe, tmp):
    """assets/kit-fan.png: one card from each game, fanned, on a transparent background."""
    imgs = "".join(f'<img src="{(OUT / f"{n}.png").as_uri()}" style="--r:{r}deg;--x:{x}px">'
                   for n, r, x in zip(FAN, (-14, 0, 14), (-150, 0, 150)))
    page = Path(tmp) / "fan.html"
    page.write_text('<!doctype html><style>html,body{margin:0;background:transparent}'
                    'img{position:absolute;left:50%;top:30px;width:230px;margin-left:-115px;border-radius:12px;'
                    'transform:translateX(var(--x)) rotate(var(--r));box-shadow:0 6px 16px rgba(0,0,0,.25)}</style>'
                    + imgs, encoding="utf-8")
    png = ROOT / "assets" / "kit-fan.png"
    png.unlink(missing_ok=True)
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                    "--allow-file-access-from-files", f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=660,400",
                    "--default-background-color=00000000", "--virtual-time-budget=5000", f"--screenshot={png}", page.as_uri()],
                   capture_output=True, timeout=120)
    print("saved", png.relative_to(ROOT))


def main(folders):
    if not folders:
        sys.exit(__doc__)
    exe = browser()
    if folders == ["--fan"]:
        with tempfile.TemporaryDirectory() as tmp:
            fan(exe, tmp)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for folder in (Path(f).resolve() for f in folders):
            if folder.name not in SHOWCASE:
                sys.exit(f"{folder}: not a kit game. Known games: {', '.join(SHOWCASE)}.")
            slug, codes = SHOWCASE[folder.name]
            for code in codes:
                sheet = folder / "print" / ("backs.html" if code == "back" else "cards.html")
                if code != "back" and code not in sheet.read_text(encoding="utf-8"):
                    sys.exit(f"{folder.name}: no card {code} in {sheet}. Update SHOWCASE in this file.")
                png = OUT / f"{slug}-{re.sub(r'[^A-Za-z0-9-]', '', code)}.png"
                png.unlink(missing_ok=True)
                render(exe, sheet, code, png, tmp)
                print("saved", png.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
