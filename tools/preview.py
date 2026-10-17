"""Make a review image: the strip on a sky background at 3x with labels, plus animated GIFs."""
import sys, numpy as np
from PIL import Image, ImageDraw
path, cw, ch, names, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(','), sys.argv[5]
anims = [a.split(':') for a in sys.argv[6:]]  # name:i,j,k:ms
im = Image.open(path).convert('RGBA'); a = np.array(im)
Z = 3; n = a.shape[1] // cw
sky = (124, 182, 236, 255); ground = (92, 160, 60, 255)
def cell(i):
    c = a[:, i*cw:(i+1)*cw]
    bg = np.zeros_like(c); bg[...] = sky
    return np.where(c[..., 3:4] > 0, c, bg)
per_row = 10
rows = (n + per_row - 1) // per_row
W = per_row * (cw*Z + 10); H = rows * (ch*Z + 24)
sheet = Image.new('RGB', (W, H), (250, 250, 247)); d = ImageDraw.Draw(sheet)
for i in range(n):
    x = (i % per_row) * (cw*Z + 10); y = (i // per_row) * (ch*Z + 24)
    sheet.paste(Image.fromarray(cell(i)[..., :3]).resize((cw*Z, ch*Z), Image.NEAREST), (x, y))
    d.text((x + 2, y + ch*Z + 4), f'{i} {names[i] if i < len(names) else ""}', fill=(40, 40, 40))
sheet.save(out + '_sheet.png')
for name, idx, ms in anims:
    fr = [Image.fromarray(cell(int(k))[..., :3]).resize((cw*4, ch*4), Image.NEAREST) for k in idx.split(',')]
    fr[0].save(f'{out}_{name}.gif', save_all=True, append_images=fr[1:], duration=int(ms), loop=0)
