# Super Civ

A browser platformer that crosses Super Mario World (SNES, 1990) with Civilization II. Gather apples, gold and science on 60-second daylight runs, then grow your city through five eras, from clubs to space flight.

Open `index.html` in a browser to play (serve the folder so the sprites in `assets/` load).

## Art

Sprites are Gemini pixel art cut into fixed-size strips, drawn at 2 sheet pixels per game pixel.

| Sheet | Cell | Frames |
| --- | --- | --- |
| `hero.png` | 64x66 | idle, run0-3, jump, fall, attack, idle2, blink, hurt, wall, clubwind, shove, spearthrust, spearready, run4-6 |
| `hero1-4.png` | 50x66 | same order, era versions (to be redrawn at 64x66) |
| `horse.png`, `warhorse.png` | 64x52 | idle, gallop0-3, jump |
| `raider*.png` | 56x55 | walk0-3, windup, strike, hurt, carry |
| `brute.png` | 74x83 | walk0-3, windup, smash, carry |

`tools/` holds the scripts that key out Gemini's magenta background and pack the strips.
