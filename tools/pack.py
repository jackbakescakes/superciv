"""Pack extracted sprites into an exact-cell horizontal strip.

Art is built at game resolution (cell/2) then doubled with nearest-neighbour,
so every art pixel is a crisp 2x2 block (2 sheet pixels per game pixel).
"""
import numpy as np
from PIL import Image

OUTLINE = (34, 18, 10, 255)

def clean(a):
    a = a.copy()
    al = a[..., 3] > 0
    # remove long thin vertical lines (e.g. a wall Gemini drew)
    h = a.shape[0]
    for x in range(a.shape[1]):
        col = al[:, x]
        if col.sum() > 0.7 * h:
            # only kill if neighbours are mostly empty (a 1-3px line)
            l = al[:, max(0, x - 4)].sum() if x >= 4 else 0
            r = al[:, min(a.shape[1] - 1, x + 4)].sum()
            if min(l, r) < 0.3 * h:
                a[:, x, 3] = 0
    return a

def downscale(a, s):
    """Area-average downscale with premultiplied alpha, hard alpha threshold."""
    im = Image.fromarray(a, 'RGBA')
    w, h = im.size
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    f = a.astype(np.float32) / 255.0
    pm = f.copy(); pm[..., :3] *= pm[..., 3:4]
    pim = Image.fromarray((pm * 255).astype(np.uint8), 'RGBA').resize((nw, nh), Image.BOX)
    p = np.array(pim).astype(np.float32) / 255.0
    alpha = p[..., 3]
    rgb = np.where(alpha[..., None] > 1e-3, p[..., :3] / np.maximum(alpha[..., None], 1e-3), 0)
    out = np.zeros((nh, nw, 4), np.uint8)
    out[..., :3] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(alpha > 0.45, 255, 0)
    return out

def boost(a, sat=1.18, contrast=1.08):
    """Push toward the bright saturated SNES palette."""
    from colorsys import rgb_to_hsv, hsv_to_rgb
    im = Image.fromarray(a, 'RGBA')
    hsv = np.array(im.convert('RGB').convert('HSV')).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
    rgb = np.array(Image.fromarray(hsv.astype(np.uint8), 'HSV').convert('RGB')).astype(np.float32)
    rgb = np.clip((rgb - 128) * contrast + 128, 0, 255)
    out = a.copy(); out[..., :3] = rgb.astype(np.uint8)
    return out

def add_outline(a):
    al = a[..., 3] > 0
    pad = np.pad(al, 1)
    nb = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    ring = nb & ~al
    out = a.copy()
    out[ring] = OUTLINE
    return out

def darken_edges(a, amt=0.55):
    """Inner edge pixels that border transparency get darkened, so the
    silhouette keeps a chunky dark line after downscaling."""
    al = a[..., 3] > 0
    pad = np.pad(al, 1)
    inner = al & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    out = a.copy().astype(np.float32)
    out[inner, :3] *= amt
    return out.clip(0, 255).astype(np.uint8)

def quantize(frames, k=28):
    """Shared palette across all frames (consistent colours, no AA noise)."""
    pix = np.concatenate([f[f[..., 3] > 0][:, :3] for f in frames])
    strip = Image.fromarray(pix.reshape(1, -1, 3).astype(np.uint8), 'RGB')
    pal = strip.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = []
    for f in frames:
        rgb = Image.fromarray(f[..., :3], 'RGB').quantize(palette=pal, dither=Image.Dither.NONE).convert('RGB')
        g = f.copy(); g[..., :3] = np.array(rgb)
        g[f[..., 3] == 0] = 0
        out.append(g)
    return out

def anchor_x(a, mode='legs'):
    al = a[..., 3] > 0
    ys, xs = np.nonzero(al)
    if mode == 'all' or len(xs) == 0:
        return xs.mean()
    h = a.shape[0]
    top = ys.min(); bot = ys.max()
    band = ys > top + 0.55 * (bot - top)
    return np.median(xs[band])

def place(cell_w, cell_h, sprite, ax, dx=0, bottom_pad=0, lift=0):
    """Place sprite in a cell: feet on bottom row, anchor at centre."""
    cell = np.zeros((cell_h, cell_w, 4), np.uint8)
    h, w = sprite.shape[:2]
    ys = np.nonzero(sprite[..., 3].any(1))[0]
    bot = ys.max() + 1
    oy = cell_h - bottom_pad - bot - lift
    ox = int(round(cell_w / 2 - ax)) + dx
    # clamp so nothing is cut off horizontally if it can fit
    xs = np.nonzero(sprite[..., 3].any(0))[0]
    l, r = xs.min(), xs.max() + 1
    if r - l <= cell_w:
        ox = min(max(ox, -l), cell_w - r)
    clipped = False
    for y in range(h):
        cy = y + oy
        if not (0 <= cy < cell_h):
            if sprite[y, :, 3].any(): clipped = True
            continue
        for x in range(w):
            if sprite[y, x, 3]:
                cx = x + ox
                if 0 <= cx < cell_w:
                    cell[cy, cx] = sprite[y, x]
                else:
                    clipped = True
    return cell, clipped, ox + ax - cell_w / 2

def up2(a):
    return np.repeat(np.repeat(a, 2, 0), 2, 1)

def defringe(a):
    out=a.copy(); r,g,b=[a[...,i].astype(int) for i in range(3)]
    m=(a[...,3]>0)&(((r-g>55)&(b-g>35)&(b>r*0.55))|((b>g+18)&(r>g+25)&(b>60)))
    out[m]=OUTLINE
    return out

def fill_small_holes(a, max_area=6, color=(244, 240, 226, 255)):
    from scipy import ndimage
    al = a[..., 3] > 0
    holes = ndimage.binary_fill_holes(al) & ~al
    lab, n = ndimage.label(holes)
    out = a.copy()
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() <= max_area:
            ys = np.nonzero(al.any(1))[0]
            head = ys.min() + 0.4 * (ys.max() - ys.min())
            out[m] = color if np.nonzero(m)[0].mean() < head else OUTLINE
    return out
