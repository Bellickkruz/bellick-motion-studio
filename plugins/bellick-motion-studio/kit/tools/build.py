"""Assemble a renderable page from a template + brand + product + content (+ words).
python3 -I build.py --template motion|ugc|<path/template.html> --brand brand.json --product product.json
                    --content content.json [--words words.json] --format 1080x1920 [--frames DIR --frame-count N --fps 30] --out page.html
Brand/product image paths are resolved relative to their JSON files. Prints the page duration."""
import argparse, json, os, sys, glob
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
for a in ['--template', '--brand', '--product', '--content', '--words', '--format', '--frames', '--out']: ap.add_argument(a)
ap.add_argument('--frame-count', type=int, default=0); ap.add_argument('--fps', type=int, default=30)
a = ap.parse_args()
tpl = a.template if a.template.endswith('.html') else os.path.join(K, 'templates', a.template, 'template.html')
def load(p): return json.load(open(p)) if p else {}
brand, product, content = load(a.brand), load(a.product), load(a.content)
words = load(a.words) if a.words else []
def asset(base_json, rel):
    if not rel: return None
    p = rel if os.path.isabs(rel) else os.path.join(os.path.dirname(os.path.abspath(base_json)), rel)
    if not os.path.exists(p): sys.exit(f'missing asset: {p}')
    return 'file://' + p
w, h = map(int, a.format.lower().split('x'))
frames = os.path.abspath(a.frames) if a.frames else None
fc = a.frame_count or (len(glob.glob(os.path.join(frames, 'f*.jpg'))) if frames else 0)
cfg = {'brand': brand, 'product': product, 'content': content, 'words': words, 'format': {'w': w, 'h': h},
       'assets': {'logo': asset(a.product, product.get('logo')) if a.product else None, 'avatar': asset(a.brand, brand.get('avatar')) if a.brand else None,
                  'frames': ('file://' + frames) if frames else None, 'frameCount': fc, 'fps': a.fps}}
# fonts
reg = json.load(open(os.path.join(K, 'fonts', 'fonts.json')))
want = {(brand.get('font') or {}).get('heading', 'Poppins'), (brand.get('font') or {}).get('body', 'Poppins'), 'Poppins'}
css = []
for fam in want:
    if fam not in reg: print(f'warning: font {fam} not bundled, falling back to Poppins', file=sys.stderr); continue
    for f in reg[fam]:
        css.append("@font-face{font-family:'%s';src:url('file://%s');font-weight:%s;font-style:normal}" % (fam, os.path.join(K, 'fonts', f['file']), f['weight']))
s = open(tpl).read()
s = s.replace('/*__FONTS__*/', '\n'.join(css)).replace('/*__CORE_CSS__*/', open(os.path.join(K, 'templates', '_shared', 'core.css')).read())
s = s.replace('/*__CFG__*/', 'window.CFG=' + json.dumps(cfg) + ';').replace('/*__CORE_JS__*/', open(os.path.join(K, 'templates', '_shared', 'core.js')).read())
open(a.out, 'w').write(s)
dur = content.get('duration') or ((fc / a.fps + (content.get('endGap') or .25) + 3.2) if fc else (words[-1]['e'] + 4 if words else 8))
print(json.dumps({'page': os.path.abspath(a.out), 'w': w, 'h': h, 'duration': round(dur, 2)}))
