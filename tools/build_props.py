"""Pack props into the game's props sheet: each prop is fitted to its slot and stands on the bottom edge."""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/art/tools')
from pack import *
SLOTS = [('hut', 0, 43, 44), ('house', 45, 66, 60), ('tower', 113, 102, 280), ('temple', 217, 65, 80),
         ('granary', 284, 47, 56), ('catapult', 333, 60, 48), ('horse', 395, 56, 48), ('sign', 453, 39, 48)]
H = 280
def build(out, srcs):
    sheet = np.zeros((H, 494, 4), np.uint8)
    for name, x0, w, h in SLOTS:
        src = srcs[name]
        a = np.array(Image.open(src).convert('RGBA'))
        if not src.endswith('_cell.png'): a = clean(a)
        ys, xs = np.nonzero(a[..., 3] > 0); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        s = min((w - 2) / a.shape[1], (h - 2) / a.shape[0])
        g = downscale(a, s); g = defringe(boost(g, 1.1, 1.0)); g = add_outline(fill_small_holes(g, 6))
        gh, gw = g.shape[:2]
        ox = x0 + (w - gw) // 2; oy = H - gh
        reg = sheet[oy:oy + gh, ox:ox + gw]; m = g[..., 3] > 0; reg[m] = g[m]
        print(name, gw, gh)
    Image.fromarray(sheet, 'RGBA').save(out)
if __name__ == '__main__':
    import json; build(sys.argv[1], json.loads(sys.argv[2]))
