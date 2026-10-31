# Science Game Kit homepage: working notes for Claude

This repo is only the kit's front door: `index.html`, hand-written, no build step, no dependencies. The games live in
their own repos (methodical-card-game, major-revisions-card-game, red-flag-card-game, all under UA-SMARTLab); the kit
conventions are in Methodical's CLAUDE.md and my general rules in `~/.claude/CLAUDE.md`.

- The card pictures in `assets/cards/` are rendered from each game's print sheets by `tools/card_images.py`; never
  draw or edit them by hand. Which cards are shown is `SHOWCASE` in that script.
- Games are listed in the order a study meets them: plan it (Methodical), review it (Major Revisions), read it (Red Flag).
  Each tile takes its game's accent colour from that game's app tokens, in light and dark.
- Counts, player numbers and languages on a tile come from that game's README and RULES; update them when those change.
- Preview: `.claude/launch.json` serves this folder on 127.0.0.1:8794.
