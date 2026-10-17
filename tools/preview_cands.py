import glob, numpy as np
from PIL import Image
import sys; sys.path.insert(0,'tools')
from pack import *
fs = sorted(glob.glob('cut/*.png'))
S = 0.21
tiles=[]
for f in fs:
    a = clean(np.array(Image.open(f)))
    g = downscale(a, S)
    g = defringe(boost(g,1.15,1.0))
    g = add_outline(g)
    c,clip,_ = place(50,66,g,anchor_x(g))
    t = c
    t = np.where(t[...,3:4]>0, t, np.array([110,170,230,255],np.uint8))
    tiles.append((f,t, clip))
cols=8
rows=(len(tiles)+cols-1)//cols
W,H=50*4,66*4
sheet=Image.new('RGB',(cols*(W+8),rows*(H+20)),(255,255,255))
from PIL import ImageDraw
d=ImageDraw.Draw(sheet)
for i,(f,t,clip) in enumerate(tiles):
    x=(i%cols)*(W+8); y=(i//cols)*(H+20)
    sheet.paste(Image.fromarray(t[...,:3]).resize((W,H),Image.NEAREST),(x,y))
    d.text((x,y+H+2),f.split('/')[-1][:-4]+(' CLIP' if clip else ''),fill=(0,0,0))
sheet.save('preview_cands.png')
