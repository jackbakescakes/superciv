"""Extract sprites from a Gemini magenta-background sheet.
usage: extract.py in.png outprefix [maxy]
Writes outprefix_00.png ... (RGBA crops, left-to-right), one per sprite in the
top band (y < maxy)."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

def key_magenta(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    # magenta-ish: high r and b, low g
    mag = (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)
    # pinkish anti-alias fringe
    fringe = (r > 140) & (b > 110) & (g < 140) & (r - g > 70) & (b - g > 50)
    return mag | fringe

def extract(path, maxy=None, min_area=1500):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)
    if maxy: a = a[:maxy]
    bg = key_magenta(a)
    fg = ~bg
    # drop long thin horizontal lines (a ground line Gemini sometimes draws)
    for y in range(fg.shape[0]):
        if fg[y].mean() > 0.5:
            above = fg[max(0, y - 4)].mean(); below = fg[min(fg.shape[0] - 1, y + 4)].mean()
            if min(above, below) < 0.35: fg[y] = False
    # drop thin stray lines (grid lines / wall line): open slightly
    lab, n = ndimage.label(ndimage.binary_dilation(fg, iterations=3))
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        area = (lab[sl] == i + 1).sum()
        if area < min_area: continue
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if h < 60: continue
        crop = a[sl].copy()
        m = fg[sl] & (lab[sl] == i + 1)
        crop[..., 3] = np.where(m, 255, 0)
        out.append(((sl[0].start + sl[0].stop) / 2, sl[1].start, crop))
    # reading order: rows top to bottom (a new row when the centre drops by > 40% of a sprite), then left to right
    out.sort(key=lambda t: t[0])
    rows, cur = [], []
    for o in out:
        if cur and o[0] - cur[-1][0] > 0.4 * o[2].shape[0]: rows.append(cur); cur = []
        cur.append(o)
    if cur: rows.append(cur)
    return [o[2] for r in rows for o in sorted(r, key=lambda t: t[1])]

if __name__ == '__main__':
    maxy = int(sys.argv[3]) if len(sys.argv) > 3 else None
    sprites = extract(sys.argv[1], maxy)
    for i, c in enumerate(sprites):
        Image.fromarray(c).save(f'{sys.argv[2]}_{i:02d}.png')
        print(i, c.shape[1], c.shape[0])
