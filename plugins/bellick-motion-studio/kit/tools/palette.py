"""Extract brand colours from a logo and propose a palette with contrast checks.
python3 -I palette.py <logo image> [out.json]"""
import sys, json, colorsys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGBA'); im.thumbnail((300, 300))
a = np.array(im).reshape(-1, 4).astype(float); a = a[a[:, 3] > 128][:, :3]
if len(a) == 0: sys.exit('no opaque pixels')
# k-means (deterministic init on luminance quantiles)
k = 6; lum = a @ [.299, .587, .114]; cent = np.array([a[np.argsort(lum)[int(q * (len(a) - 1))]] for q in np.linspace(0, 1, k)])
for _ in range(20):
    d = ((a[:, None, :] - cent[None]) ** 2).sum(-1); lab = d.argmin(1)
    cent = np.array([a[lab == i].mean(0) if (lab == i).any() else cent[i] for i in range(k)])
share = np.bincount(lab, minlength=k) / len(a)
hexc = lambda c: '#%02X%02X%02X' % tuple(int(round(x)) for x in c)
sw = []
for c, s in sorted(zip(cent, share), key=lambda x: -x[1]):
    hh, ll, ss = colorsys.rgb_to_hls(*(c / 255)); sw.append({'hex': hexc(c), 'share': round(float(s), 3), 'sat': round(ss, 2), 'light': round(ll, 2)})
def L(hx):
    c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]; return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def cr(x, y): a_, b_ = L(x), L(y); return round((max(a_, b_) + .05) / (min(a_, b_) + .05), 2)
def hls(h, l, s): return hexc(np.array(colorsys.hls_to_rgb(h, l, s)) * 255)
colourful = [x for x in sw if x['sat'] > .25 and .15 < x['light'] < .85 and x['share'] > .02]
base = colourful[0]['hex'] if colourful else sw[0]['hex']
hh, ll, ss = colorsys.rgb_to_hls(*[int(base[i:i + 2], 16) / 255 for i in (1, 3, 5)])
second = colourful[1]['hex'] if len(colourful) > 1 else hls(hh, min(.62, ll + .12), min(1, ss * 1.1 + .1))
prop = {'background': hls(hh, .965, min(ss, .35) * .6), 'text': hls(hh, .14, min(ss, .7)), 'primary': hls(hh, min(max(ll, .32), .5), max(ss, .45)),
        'accent': second, 'soft': hls(hh, .82, min(ss, .6)), 'softer': hls(hh, .92, min(ss, .6)), 'surface': '#FFFFFF', 'muted': hls(hh, .48, min(ss, .25))}
checks = {'text_on_background': cr(prop['text'], prop['background']), 'white_on_primary': cr('#FFFFFF', prop['primary']), 'accent_on_background': cr(prop['accent'], prop['background'])}
out = {'swatches': sw, 'proposed': prop, 'contrast': checks, 'note': 'AA needs >=4.5 for body text, >=3 for large text/graphics'}
print(json.dumps(out, indent=1))
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
