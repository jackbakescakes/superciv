"""Build an era hero sheet (64x66 cells, the hero.png frame order) from Gemini crops.
Each source image is scaled so the soldier's helmet/head comes out the same width,
since Gemini draws the character at a different size in every image.
usage: build_era_hero.py out.png map.json
map.json: {"frames": {"idle": "mA_00", ...}, "head_px": 12, "head_mode": "grey"}"""
import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/art/tools')
from pack import *
from build_hero import breathe, blink, draw_star

ORDER = ['idle', 'run0', 'run1', 'run2', 'run3', 'jump', 'fall', 'attack', 'idle2', 'blink', 'hurt', 'wall',
         'clubwind', 'shove', 'spearthrust', 'spearready', 'run4', 'run5', 'run6']
CW, CH = 64, 66

def head_width(a, mode):
    al = a[..., 3] > 0
    ys = np.nonzero(al.any(1))[0]; t, b = ys.min(), ys.max()
    rgb = a[..., :3].astype(int)
    if mode == 'grey':
        m = (rgb.max(-1) - rgb.min(-1) < 30) & (rgb.mean(-1) > 70) & (rgb.mean(-1) < 200) & al
    else:
        m = al
    band = m[t:t + int(.18 * (b - t))]
    xs = np.nonzero(band.any(0))[0]
    return (xs.max() - xs.min()) if len(xs) else None

def build(out, cfg):
    frames = cfg['frames']; mode = cfg.get('head_mode', 'grey'); target = cfg['head_px']
    load = lambda n: clean(np.array(Image.open(f'/home/claude/art/cut/{n}.png')))
    groups = {}
    for n in set(frames.values()):
        groups.setdefault(n.rsplit('_', 1)[0], []).append(n)
    gscale = {}
    for g, names in groups.items():
        ws = [w for w in (head_width(load(n), mode) for n in names) if w]
        gscale[g] = target / np.median(ws)
    gscale.update(cfg.get('scale_override', {}))
    cells = []
    for name in ORDER:
        src = frames[name]; s = gscale[src.rsplit('_', 1)[0]] * cfg.get('frame_scale', {}).get(name, 1)
        a = load(src)
        if a.shape[1] * s + 2 > CW: s = (CW - 2) / a.shape[1]
        g = downscale(a, s)
        g = defringe(boost(g, 1.12, 1.0))
        g = add_outline(fill_small_holes(g, 14))
        if name == 'idle2' and frames[name] == frames['idle']: g = breathe(g)
        if name == 'blink' and frames[name] == frames['idle']: g = blink(g)
        c, clipped, off = place(CW, CH, g, anchor_x(g))
        print(name, src, g.shape[1], g.shape[0], 'clipped' if clipped else '')
        cells.append(c)
    Image.fromarray(np.concatenate(cells, 1), 'RGBA').save(out)
    print({k: round(v, 4) for k, v in gscale.items()})

if __name__ == '__main__':
    build(sys.argv[1], json.load(open(sys.argv[2])))
