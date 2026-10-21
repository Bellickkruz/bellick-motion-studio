"""Render a built page frame-by-frame (headless Chromium) and encode H.264.
stills: python3 render.py page.html stills 0,2.5,5
video : python3 render.py page.html video out.mp4 [--scale 2] [--dur N] [--fps 30]
Size comes from the page (window.CFG.format); --scale 2 doubles it (1080x1920 -> 2160x3840 = 4K).
Duration defaults to window.DURATION set by the template."""
import os, subprocess, argparse, json
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('page'); ap.add_argument('mode'); ap.add_argument('arg')
ap.add_argument('--scale', type=float, default=1); ap.add_argument('--dur', type=float); ap.add_argument('--fps', type=int, default=30)
a = ap.parse_args(); page = os.path.abspath(a.page); here = os.path.dirname(page)
html = open(page).read(); i = html.index('window.CFG='); cfg = json.JSONDecoder().raw_decode(html[i + len('window.CFG='):])[0]
w, h = cfg['format']['w'], cfg['format']['h']
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=a.scale)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + page); pg.wait_for_function('window.READY===true', timeout=30000); pg.evaluate('document.fonts.ready.then(()=>1)')
    dur = a.dur or pg.evaluate('window.DURATION')
    if a.mode == 'stills':
        for t in [float(x) for x in a.arg.split(',')]:
            pg.evaluate(f'render({t})'); pg.screenshot(path=os.path.join(here, f'still_{t:06.2f}.png'))
    else:
        W, H = int(w * a.scale), int(h * a.scale); lvl = '5.2' if W * H > 1920 * 1088 else '4.2'
        ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                               '-crf', '14', '-preset', 'slow', '-profile:v', 'high', '-level', lvl, '-movflags', '+faststart', a.arg], stdin=subprocess.PIPE)
        for k in range(int(round(a.fps * dur))):
            pg.evaluate(f'render({k / a.fps})'); ff.stdin.write(pg.screenshot(type='png'))
        ff.stdin.close(); ff.wait()
    print(json.dumps({'w': w, 'h': h, 'scale': a.scale, 'duration': dur, 'page_errors': errs[:3]}))
    b.close()
