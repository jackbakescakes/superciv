"""Generic strip builder: python3 build_simple.py out.png CW CH src1,src2,... [scale]
Uniform scale so the widest frame fits; feet on the bottom row, centred on body mass."""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/art/tools')
from pack import *

def build(out, cw, ch, srcs, scale=None, anchor='all', recolor=None):
    imgs = [clean(np.array(Image.open(f'/home/claude/art/cut/{s}.png'))) for s in srcs]
    if scale is None:
        scale = min(min((cw - 2) / a.shape[1], (ch - 2) / a.shape[0]) for a in imgs)
    cells = []
    for a in imgs:
        g = downscale(a, scale)
        g = defringe(boost(g, 1.12, 1.0))
        g = add_outline(fill_small_holes(g, 10))
        if recolor: g = recolor(g)
        c, clipped, _ = place(cw, ch, g, anchor_x(g, anchor))
        if clipped: print('clipped', a.shape)
        cells.append(c)
    Image.fromarray(np.concatenate(cells, 1), 'RGBA').save(out)
    return scale

if __name__ == '__main__':
    s = build(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(','),
              float(sys.argv[5]) if len(sys.argv) > 5 else None)
    print('scale', round(s, 4))
