import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/art/tools')
from pack import *

S = 0.21
CW, CH = 64, 66
# sheet order -> (source crop, options)
FRAMES = [
    ('idle',        'idle_00', {}),
    ('run0',        'runB_01', {}),
    ('run1',        'runB_02', {}),
    ('run2',        'runB_03', {}),
    ('run3',        'runC_00', {}),
    ('jump',        'idle_03', {}),
    ('fall',        'misc_00', {}),
    ('attack',      'atk2_00', {'feet_ignore_bright': True}),
    ('idle2',       'idle_00', {'breathe': True}),
    ('blink',       'idle_00', {'blink': True}),
    ('hurt',        'misc_01', {}),
    ('wall',        'misc_02', {}),
    ('clubwind',    'attack_00', {}),
    ('shove',       'misc_03', {}),
    ('spearthrust', 'attack_02', {'trim_left': 0}),
    ('spearready',  'attack_03', {}),
    ('run4',        'runD_00', {}),
    ('run5',        'runD_01', {}),
    ('run6',        'runD_03', {}),
]

def breathe(a):
    """Upper body 1px lower: shift rows above the belt down by one."""
    al = a[..., 3] > 0
    ys = np.nonzero(al.any(1))[0]
    top, bot = ys.min(), ys.max()
    cut = top + int((bot - top) * 0.62)
    out = a.copy()
    out[top + 1:cut + 1] = a[top:cut]
    out[top] = 0
    return out

def blink(a):
    """Close the eyes: near-white eye pixels in the head -> lid line."""
    out = a.copy()
    al = a[..., 3] > 0
    ys = np.nonzero(al.any(1))[0]
    top, bot = ys.min(), ys.max()
    head = slice(top, top + int((bot - top) * 0.4))
    rgb = a[head, :, :3].astype(int)
    white = (rgb.min(-1) > 135) & ((rgb.max(-1) - rgb.min(-1)) < 40) & al[head]
    yy, xx = np.nonzero(white)
    if len(yy) == 0:
        return out
    skin = np.array([228, 150, 100, 255], np.uint8)
    lid = np.array([90, 45, 25, 255], np.uint8)
    for y, x in zip(yy + top, xx):
        out[y, x] = skin
    # also the dark pupil next to it
    y0, y1 = (yy + top).min(), (yy + top).max()
    x0, x1 = xx.min(), xx.max()
    for y in range(y0 - 1, y1 + 2):
        for x in range(x0 - 1, x1 + 3):
            px = out[y, x]
            if px[3] and px[:3].astype(int).sum() < 150 and y < y1 + 1:
                out[y, x] = skin
    for x in range(x0 - 1, x1 + 2):
        out[y1, x] = lid
    return out

STAR = [
    "...O...",
    "..OYO..",
    "OOOWOOO",
    ".OWWWO.",
    "..OWO..",
    ".OY.YO.",
    "O.....O",
]
def draw_star(cell):
    al = cell[..., 3] > 0
    ys, xs = np.nonzero(al)
    # club head = rightmost opaque pixels in the bottom third
    low = ys > cell.shape[0] * 0.66
    tx = xs[low].max()
    cx = min(cell.shape[1] - 4, tx)
    cy = cell.shape[0] - 4
    col = {'O': (60, 30, 10, 255), 'Y': (255, 214, 64, 255), 'W': (255, 252, 210, 255)}
    out = cell.copy()
    for j, row in enumerate(STAR):
        for i, ch in enumerate(row):
            if ch == '.': continue
            y, x = cy - 3 + j, cx - 3 + i
            if 0 <= y < cell.shape[0] and 0 <= x < cell.shape[1]:
                out[y, x] = col[ch]
    return out

def load(name):
    a = np.array(Image.open(f'/home/claude/art/cut/{name}.png'))
    return clean(a)

def process(a, opt):
    s = S
    w = a.shape[1] * S + 2
    if w > CW:  # too wide for the cell: shrink this frame a little so nothing is cut off
        s = max(0.2, S * (CW - 2) / (a.shape[1] * S))
    g = downscale(a, s)
    g = defringe(boost(g, 1.15, 1.0))
    g = add_outline(fill_small_holes(g, 14))
    xs = np.nonzero(g[..., 3].any(0))[0]
    over = (xs.max() + 1 - xs.min()) - CW
    if over > 0:  # trim the back edge (spear butt / back heel), re-close the outline
        g = g[:, xs.min() + over:]
        col = g[:, 0, 3] > 0
        g[col, 0] = OUTLINE
    if opt.get('breathe'): g = breathe(g)
    if opt.get('blink'): g = blink(g)
    return g

def build(out_path):
    cells = []; report = []
    base_ax = None
    for name, src, opt in FRAMES:
        g = process(load(src), opt)
        ax = anchor_x(g)
        lift = 0
        if opt.get('feet_ignore_bright'):
            rgb = g[..., :3].astype(int)
            bright = (rgb[..., 0] > 200) & (rgb[..., 1] > 180)
            solid = (g[..., 3] > 0) & ~bright
            fb = np.nonzero(solid.any(1))[0].max()
            ab = np.nonzero((g[..., 3] > 0).any(1))[0].max()
            lift = -(ab - fb)
        if opt.get('feet_ignore_bright'):
            g = g.copy(); g[bright] = 0
            lift = 0
        cell, clipped, off = place(CW, CH, g, ax, lift=lift)
        if opt.get('feet_ignore_bright'):
            cell = draw_star(cell)
        cells.append(cell)
        report.append((name, src, g.shape[1], g.shape[0], round(off, 1), clipped))
    sheet = np.concatenate(cells, 1)
    Image.fromarray(sheet, 'RGBA').save(out_path)
    return report

if __name__ == '__main__':
    for r in build(sys.argv[1]): print(r)
