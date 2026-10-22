"""Render a built page frame-by-frame (headless Chromium) and encode H.264.
stills  : python3 render.py page.html stills 0,2.5,5
estimate: python3 render.py page.html estimate all      (times a few real frames per quality, prints minutes)
video   : python3 render.py page.html video out.mp4 --quality preview|hd|4k [--dur N] [--fps 30]
Qualities scale the page's design size (short side 1080):
  preview = 720 short side, fast encode (for checking motion and timing)
  hd      = 1080 short side (Full HD)
  4k      = 2160 short side (4K UHD)
--scale N still works for custom sizes. Duration defaults to window.DURATION set by the template."""
import os, subprocess, argparse, json, time
from playwright.sync_api import sync_playwright

Q = {'preview': dict(scale=2 / 3, shot='jpeg', crf='20', preset='veryfast', label='Fast preview (720p)'),
     'hd': dict(scale=1, shot='png', crf='16', preset='medium', label='Full HD (1080p)'),
     '4k': dict(scale=2, shot='png', crf='14', preset='slow', label='4K UHD (2160p)')}

ap = argparse.ArgumentParser(); ap.add_argument('page'); ap.add_argument('mode'); ap.add_argument('arg')
ap.add_argument('--quality', choices=list(Q)); ap.add_argument('--scale', type=float); ap.add_argument('--dur', type=float); ap.add_argument('--fps', type=int, default=30)
a = ap.parse_args(); page = os.path.abspath(a.page); here = os.path.dirname(page)
html = open(page).read(); i = html.index('window.CFG='); cfg = json.JSONDecoder().raw_decode(html[i + len('window.CFG='):])[0]
w, h = cfg['format']['w'], cfg['format']['h']


def settings(qname=None, scale=None):
    q = dict(Q[qname or 'hd'])
    if scale and not qname: q.update(scale=scale, shot='png', crf='14' if scale > 1 else '16', preset='slow' if scale > 1 else 'medium')
    return q


def even(x): return int(round(x / 2) * 2)


def encoder(q, out):
    W, H = even(w * q['scale']), even(h * q['scale']); lvl = '5.2' if W * H > 1920 * 1088 else '4.2'
    vf = ['-vf', f'scale={W}:{H}:flags=lanczos'] if (W, H) != (w * q['scale'], h * q['scale']) else []
    return ['ffmpeg', '-y', '-v', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-', *vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-crf', q['crf'], '-preset', q['preset'], '-profile:v', 'high', '-level', lvl, '-movflags', '+faststart', *(['-f', 'mp4'] if out == os.devnull else []), out], (W, H)


def shoot(pg, q):
    return pg.screenshot(type='jpeg', quality=92) if q['shot'] == 'jpeg' else pg.screenshot(type='png')


with sync_playwright() as p:
    b = p.chromium.launch(); errs = []

    def open_page(scale):
        pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=scale); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + page); pg.wait_for_function('window.READY===true', timeout=30000); pg.evaluate('document.fonts.ready.then(()=>1)')
        return pg

    if a.mode == 'stills':
        pg = open_page(1)
        for t in [float(x) for x in a.arg.split(',')]:
            pg.evaluate(f'render({t})'); pg.screenshot(path=os.path.join(here, f'still_{t:06.2f}.png'))
        print(json.dumps({'w': w, 'h': h, 'page_errors': errs[:3]}))
    elif a.mode == 'estimate':
        names = list(Q) if a.arg == 'all' else a.arg.split(',')
        res = {}
        for qn in names:
            q = settings(qn); pg = open_page(q['scale']); dur = a.dur or pg.evaluate('window.DURATION'); n = int(round(a.fps * dur))
            cmd, (W, H) = encoder(q, os.devnull); ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            # time short runs of consecutive frames (like the real render) at three points in the video
            el = 0.0; k = 0
            for c in (0.2, 0.5, 0.8):
                f0 = int(n * c); pg.evaluate(f'render({f0 / a.fps})'); ff.stdin.write(shoot(pg, q))  # warm-up, not timed
                t0 = time.time()
                for j in range(1, 7):
                    pg.evaluate(f'render({(f0 + j) / a.fps})'); ff.stdin.write(shoot(pg, q)); k += 1
                el += time.time() - t0
            t0 = time.time(); ff.stdin.close(); ff.wait(); el += time.time() - t0; per = el / k; pg.close()
            secs = per * n * 1.1 + 10  # 10% headroom plus start-up
            res[qn] = {'label': Q[qn]['label'], 'size': f'{W}x{H}', 'frames': n, 'sec_per_frame': round(per, 2), 'minutes': round(secs / 60, 1)}
        if '4k' in res:
            res['4k+hd'] = {'label': '4K plus a Full HD copy', 'size': res['4k']['size'] + ' + ' + (res.get('hd', {}).get('size') or f'{w}x{h}'),
                            'minutes': round(res['4k']['minutes'] + max(0.5, res['4k']['frames'] / 30 * 0.04), 1)}
        print(json.dumps({'duration': dur, 'qualities': res}, indent=1))
        print('Note: times are measured on this workspace right now; other jobs running at the same time slow it down.')
    else:
        q = settings(a.quality, a.scale); pg = open_page(q['scale']); dur = a.dur or pg.evaluate('window.DURATION')
        cmd, (W, H) = encoder(q, a.arg); ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
        n = int(round(a.fps * dur))
        for k in range(n):
            pg.evaluate(f'render({k / a.fps})'); ff.stdin.write(shoot(pg, q))
            if k and k % (a.fps * 5) == 0: print(f'progress {k}/{n} frames, {time.time() - t0:.0f}s', flush=True)
        ff.stdin.close(); ff.wait()
        print(json.dumps({'w': W, 'h': H, 'quality': a.quality or f'scale {a.scale}', 'duration': dur, 'seconds': round(time.time() - t0), 'page_errors': errs[:3]}))
    b.close()
