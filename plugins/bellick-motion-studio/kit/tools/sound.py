"""Bellick Motion Studio sound engine (optional step): original music beds and sound effects,
synthesised from scratch (no samples, so no licences or copyright claims), plus a mixer that sits
music under the voice and ducks it while someone speaks. Works with the user's own track too.

  list   python3 -I sound.py list
  cues   python3 -I sound.py cues content.json --template motion|ugc --duration D [--end E] --out sfx.json
  make   python3 -I sound.py make --duration D [--end E] [--mood calm|upbeat|minimal|none] [--sfx sfx.json] [--key-of calm] [--seed 7] --out-dir snd
  mix    python3 -I sound.py mix --video v4k.mp4 --duration D --out final.mp4
             [--voice clip.mp4|vo.wav] [--voice-kind own|ai] [--music snd/music.wav|their_track.mp3]
             [--music-start 0] [--sfx snd/sfx.wav] [--music-level -17] [--duck 9] [--sfx-level -5]

sfx.json is a list of cues: {"t": seconds, "sfx": name, "gain": 1.0, "dur": seconds (riser/whoosh only), "pan": -1..1}.
Levels in mix are dB relative to the speaking voice. Needs numpy and ffmpeg only."""
import sys, json, argparse, subprocess, wave, os, tempfile, numpy as np

SR = 48000
TAU = 2 * np.pi


# ---------------------------------------------------------------- helpers
def mhz(m): return 440.0 * 2 ** ((m - 69) / 12)
def tarr(n): return np.arange(n) / SR
def N(sec): return max(1, int(round(sec * SR)))


def fft_filter(x, gain_fn):
    n = len(x); M = 1 << int(np.ceil(np.log2(n + 2)))
    X = np.fft.rfft(x, M); f = np.fft.rfftfreq(M, 1 / SR)
    return np.fft.irfft(X * gain_fn(f), M)[:n]


def lp(fc, o=2): return lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * o))
def hp(fc, o=2): return lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * o))


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x * (peak / m) if m > 1e-9 else x


def pan2(x, p=0.0):
    p = np.clip(np.broadcast_to(p, x.shape), -1, 1); a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)])


def place(buf, x, start):
    """Add stereo x (2,n) into buf (2,M) starting at sample `start` (may be negative)."""
    s = int(start); a = max(0, -s); b = min(x.shape[1], buf.shape[1] - s)
    if b > a: buf[:, s + a:s + b] += x[:, a:b]


def edge_fade(x, a=0.002, r=0.01):
    n = x.shape[-1]; fa, fr = min(n, N(a)), min(n, N(r))
    x[..., :fa] *= np.linspace(0, 1, fa); x[..., n - fr:] *= np.linspace(1, 0, fr); return x


def swept_noise(dur, fc_fn, width, rng):
    """Noise whose band centre follows fc_fn(u), u = 0..1 over the sound (overlap-add of shaped spectra)."""
    n = N(dur); B, H = 1024, 256; win = np.hanning(B); f = np.fft.rfftfreq(B, 1 / SR)
    out = np.zeros(n + B)
    for i in range(0, n, H):
        fc = fc_fn(i / n)
        spec = (rng.standard_normal(len(f)) + 1j * rng.standard_normal(len(f))) * np.exp(-0.5 * (np.log2(np.maximum(f, 20) / fc) / width) ** 2)
        out[i:i + B] += np.fft.irfft(spec, B) * win
    return norm(out[:n])


def reverb_ir(rng, decay=2.2, bright=0.45, pre=0.014):
    n = N(decay * 1.1); t = tarr(n); ir = np.zeros((2, n))
    for c in range(2):
        w = rng.standard_normal(n)
        ir[c] = w * np.exp(-t * 6.9 / (decay * bright)) + fft_filter(w, lp(2500, 1)) * np.exp(-t * 6.9 / decay) * 1.6
    ir[:, :N(pre)] = 0
    ir = np.stack([fft_filter(ir[c], hp(140, 2)) for c in range(2)])
    return ir / np.sqrt((ir ** 2).sum() / 2)


def convolve(x, ir):
    n, m = x.shape[1], ir.shape[1]; M = 1 << int(np.ceil(np.log2(n + m)))
    return np.stack([np.fft.irfft(np.fft.rfft(x[c], M) * np.fft.rfft(ir[c], M), M)[:n] for c in range(2)])


def write_wav(path, x):
    x = np.clip(x, -1, 1); d = (x.T * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())


def decode(path):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    if r.returncode or not r.stdout: sys.exit(f'Could not read audio from {path}: {r.stderr.decode()[-300:]}')
    return np.frombuffer(r.stdout, '<f4').reshape(-1, 2).T.astype(np.float64)


# ---------------------------------------------------------------- moods (original progressions)
MOODS = {
    'calm': dict(desc='Soft pads, gentle plucks, light shaker. Explainers, tutorials, trust.', bpm=84, tonic=74,
                 prog=[[50, 57, 61, 64, 66], [47, 54, 57, 61, 62], [43, 50, 54, 57, 61], [45, 52, 55, 59, 62]],
                 arp=[0, 2, 1, 3, None, 2, 4, 1], arp_div=2, pluck_tau=0.32, fc=2200, drums='soft', bass='held', pump=0.0),
    'upbeat': dict(desc='Bright four-on-the-floor pulse with claps and fast arps. Launches, hype, product drops.', bpm=112, tonic=81,
                   prog=[[45, 52, 55, 60, 64], [41, 48, 52, 57, 60], [48, 55, 59, 62, 64], [43, 50, 52, 59, 62]],
                   arp=[0, 2, 4, 2, 1, 3, 4, 3, 0, 2, 4, 2, 1, 3, 5, 3], arp_div=4, pluck_tau=0.16, fc=3000, drums='groove', bass='eighths', pump=0.45),
    'minimal': dict(desc='Sparse felt-piano notes, warm sub, soft ticks. Calm, premium, voice-first.', bpm=92, tonic=76,
                    prog=[[40, 47, 51, 56, 59], [37, 44, 47, 52, 56], [45, 52, 56, 61, 64], [47, 54, 56, 59, 64]],
                    arp=[0, None, 2, None, 3, None, 1, None], arp_div=2, pluck_tau=0.6, fc=1500, drums='tick', bass='halves', pump=0.0),
}


def chord_osc(freq, n, fc, K=22):
    ph = TAU * freq * tarr(n) + np.random.default_rng(int(freq * 100)).uniform(0, TAU)
    out = np.zeros(n)
    for k in range(1, K + 1):
        if k * freq > 9000: break
        out += (1 / k) / np.sqrt(1 + (k * freq / fc) ** 4) * np.sin(k * ph)
    return out


def drum(kind, rng):
    if kind == 'kick':
        n = N(0.45); t = tarr(n); f = 46 + 85 * np.exp(-t / 0.032)
        x = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.17) + fft_filter(rng.standard_normal(n), hp(3000)) * np.exp(-t / 0.003) * 0.15
    elif kind == 'shaker':
        n = N(0.12); t = tarr(n); env = np.minimum(1, t / 0.006) * np.exp(-t / 0.035)
        x = fft_filter(rng.standard_normal(n), lambda f: np.exp(-0.5 * (np.log2(np.maximum(f, 20) / 7000) / 0.6) ** 2)) * env
    elif kind == 'hat':
        n = N(0.09); t = tarr(n); x = fft_filter(rng.standard_normal(n), hp(8000, 3)) * np.exp(-t / 0.025)
    elif kind == 'clap':
        n = N(0.3); t = tarr(n); e = np.zeros(n)
        for d in (0, 0.009, 0.019): e += (t >= d) * np.exp(-np.maximum(0, t - d) / 0.006)
        e += (t >= 0.022) * 0.5 * np.exp(-np.maximum(0, t - 0.022) / 0.09)
        x = fft_filter(rng.standard_normal(n), lambda f: np.exp(-0.5 * (np.log2(np.maximum(f, 20) / 1500) / 0.8) ** 2)) * e
    else:  # tick
        n = N(0.05); t = tarr(n); x = np.sin(TAU * 1900 * t) * np.exp(-t / 0.008) + fft_filter(rng.standard_normal(n), hp(4000)) * np.exp(-t / 0.004) * 0.4
    return norm(edge_fade(x, 0.0005, 0.005))


def make_music(mood, dur, end, seed=7):
    M = MOODS[mood]; rng = np.random.default_rng(seed)
    beat = 60 / M['bpm']; bar = 4 * beat; n = N(dur + 0.05)
    end = min(max(end, min(dur, 1.5)), dur)
    pad, bass, arp, drums = (np.zeros((2, n)) for _ in range(4))
    # chord schedule up to `end`, then resolve to the tonic chord
    sched, t, i = [], 0.0, 0
    while t < end - 0.05:
        sched.append([t, min(t + bar, end), M['prog'][i % len(M['prog'])]]); t += bar; i += 1
    if len(sched) > 1 and sched[-1][1] - sched[-1][0] < bar * 0.5: sched[-2][1] = sched[-1][1]; sched.pop()
    final = [end, dur, M['prog'][0]]
    for si, (s, e, ch) in enumerate(sched + [final]):
        last = si == len(sched); rel = 1.2 if not last else 0.05
        L = (e - s) + rel; m = N(L); tt = tarr(m) + s
        intro = np.clip(tt / max(bar, 0.1), 0, 1)
        fc = M['fc'] * (0.35 + 0.65 * intro ** 1.5) * (1 + 0.18 * np.sin(TAU * tt / (2 * bar)))
        if last: fc = np.full(m, M['fc'] * 1.15)
        att = 0.25 if last else min(0.5, (e - s) / 2)
        env = np.minimum(1, tarr(m) / att); env *= np.clip((s + L - tt) / rel, 0, 1) if not last else 1
        for k, note in enumerate(ch):
            f = mhz(note); w = 1.0 if k else 0.7
            for cents, p in ((-7, -0.55), (0, 0.0), (7, 0.55)):
                place(pad, pan2(chord_osc(f * 2 ** (cents / 1200), m, fc) * env * w, p), N(s))
        # bass
        bn = ch[0] - 12 if ch[0] - 12 >= 33 else ch[0]; bf = mhz(bn)
        if last or M['bass'] == 'held': hits = [(s, e - s)]
        elif M['bass'] == 'halves': hits = [(x, 2 * beat) for x in np.arange(s, e - 0.01, 2 * beat)]
        else: hits = [(x, beat / 2) for x in np.arange(s, e - 0.01, beat / 2)]
        for hs, hl in hits:
            mm = N(hl + 0.3); u = tarr(mm)
            x = np.sin(TAU * bf * u) + 0.22 * np.sin(2 * TAU * bf * u) + 0.08 * np.sin(3 * TAU * bf * u)
            ev = np.minimum(1, u / 0.03) * np.clip((hl + 0.3 - u) / 0.3, 0, 1) * (np.exp(-u / 0.25) * 0.6 + 0.4 if M['bass'] == 'eighths' and not last else 1)
            place(bass, pan2(x * ev), N(hs))
        # arp / plucks
        pool = sorted(ch[1:]) + [sorted(ch[1:])[0] + 12, sorted(ch[1:])[1] + 12]
        stepd = beat / M['arp_div']
        if last:
            notes = [(end + 0.02 + j * 0.16, M['tonic'] - 12 + d) for j, d in enumerate((0, 7, 12))]
        else:
            notes = [(s + j * stepd, pool[M['arp'][j % len(M['arp'])] % len(pool)] + 12)
                     for j in range(int(round((e - s) / stepd))) if M['arp'][j % len(M['arp'])] is not None]
        for j, (ns, note) in enumerate(notes):
            if ns > dur - 0.3: continue
            f = mhz(note); tau = M['pluck_tau'] * (2.5 if last else 1); mm = N(tau * 6); u = tarr(mm)
            x = (np.sin(TAU * f * u) + 0.35 * np.sin(2 * TAU * f * u) * np.exp(-u / (tau * 0.5)) + 0.12 * np.sin(3 * TAU * f * u) * np.exp(-u / (tau * 0.3)))
            x *= np.minimum(1, u / 0.004) * np.exp(-u / tau) * rng.uniform(0.7, 1.0)
            jitter = rng.normal(0, 0.004); p = 0.3 if j % 2 else -0.3
            place(arp, pan2(x, p), N(ns + jitter))
            for k2, (dl, fb) in enumerate(((0.75 * beat, 0.32), (1.5 * beat, 0.12))):
                place(arp, pan2(x * fb, -p if k2 == 0 else p), N(ns + dl))
    # drums
    kicks = []
    style = M['drums']; nbars = int(np.ceil(end / bar)); start_bar = 1 if end > 3 * bar else 0
    pats = {'soft': {'kick': [0, 10], 'shaker': [2, 6, 10, 14], 'tick': []},
            'groove': {'kick': [0, 4, 8, 12], 'clap': [4, 12], 'hat': [2, 6, 10, 14]},
            'tick': {'kick': [0], 'tick': [4, 12], 'shaker': [2, 6, 10, 14]}}[style]
    vel = {'kick': 0.8 if style == 'groove' else 0.5, 'clap': 0.5, 'hat': 0.35, 'shaker': 0.3, 'tick': 0.25}
    samples = {k: drum(k, rng) for k in pats}
    for b in range(start_bar, nbars):
        for k, steps in pats.items():
            for st in steps:
                ht = b * bar + st * beat / 4
                if ht > end - beat: continue
                v = vel[k] * rng.uniform(0.85, 1.0); ht += rng.normal(0, 0.003)
                place(drums, pan2(samples[k] * v, {'hat': 0.25, 'shaker': -0.2}.get(k, 0)), N(ht))
                if k == 'kick': kicks.append(ht)
    if M['pump'] and kicks:
        g = np.ones(n); tt = tarr(n)
        for kt in kicks:
            a = N(kt); seg = tt[a:a + N(0.4)] - kt; g[a:a + len(seg)] = np.minimum(g[a:a + len(seg)], 1 - M['pump'] * np.exp(-seg / 0.11))
        pad *= g; bass *= g
    ir = reverb_ir(rng, 2.6 if mood != 'upbeat' else 1.8)
    pad, bass, arp, drums = norm(pad), norm(bass), norm(arp), norm(drums)
    mix = pad * 0.55 + bass * 0.36 + arp * 0.34 + drums * 0.42
    mix += convolve(pad * 0.18 + arp * 0.45 + drums * 0.08, ir) * 0.32
    mix = np.stack([fft_filter(mix[c], hp(42, 3)) for c in range(2)])
    tt = tarr(n); mix *= np.clip((dur - 0.05 - tt) / 1.4, 0, 1)
    mix = np.tanh(norm(mix, 0.9) * 1.25) / np.tanh(1.25)
    return norm(mix, 0.89)


# ---------------------------------------------------------------- sound effects
def sfx_whoosh(rng, dur=0.6, hi=2800, **_):
    u = np.linspace(0, 1, N(dur)); pk = 0.45
    env = np.where(u < pk, (u / pk) ** 2, ((1 - u) / (1 - pk)) ** 1.6)
    a = swept_noise(dur, lambda q: 260 * (hi / 260) ** (q / pk) if q < pk else hi * (1 - 0.65 * (q - pk) / (1 - pk)), 0.7, rng)
    b = swept_noise(dur, lambda q: 110 + 300 * q, 0.6, rng) * 0.45
    return pan2((a + b) * env, np.linspace(-0.6, 0.6, len(u))), pk * dur


def sfx_swish(rng, dur=0.32, **_):
    u = np.linspace(0, 1, N(dur)); env = np.sin(np.pi * u) ** 2
    x = swept_noise(dur, lambda q: 1800 + 4500 * np.sin(np.pi * q), 0.5, rng) * env
    return pan2(x, np.linspace(0.4, -0.4, len(u))), 0.5 * dur


def sfx_riser(rng, dur=1.0, **_):
    u = np.linspace(0, 1, N(dur)); t = tarr(len(u))
    x = swept_noise(dur, lambda q: 300 * (7000 / 300) ** q, 0.55, rng) * u ** 2.2
    f = 180 * (1100 / 180) ** u; x += 0.3 * np.sin(TAU * np.cumsum(f) / SR) * u ** 2
    x = edge_fade(norm(x), 0.01, 0.012)
    return pan2(x, 0.3 * np.sin(TAU * 2.5 * t)), dur


def sfx_impact(rng, **_):
    n = N(1.2); t = tarr(n); f = 40 + 72 * np.exp(-t / 0.08)
    sub = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.42)
    thump = np.sin(TAU * 118 * t) * np.exp(-t / 0.12) * 0.5
    nz = [fft_filter(rng.standard_normal(n), lp(2600)) * np.exp(-t / 0.11) * 0.5 for _ in range(2)]
    x = np.stack([sub + thump + nz[0], sub + thump + nz[1]])
    return edge_fade(x, 0.0008, 0.05), 0.0


def tone(f, n, partials=((1, 1, 1),), base_tau=0.2):
    t = tarr(n); out = np.zeros(n)
    for r, a, d in partials: out += a * np.sin(TAU * f * r * t) * np.exp(-t / (base_tau * d))
    return out * np.minimum(1, t / 0.002)


def sfx_click(rng, **_):
    n = N(0.05); t = tarr(n)
    x = np.sin(TAU * 3100 * t) * np.exp(-t / 0.012) * 0.6 + np.sin(TAU * 620 * t) * np.exp(-t / 0.01) * 0.6 + fft_filter(rng.standard_normal(n), hp(3500)) * np.exp(-t / 0.003) * 0.5
    return pan2(edge_fade(x, 0.0003, 0.004)), 0.0


def sfx_key(rng, **_):
    n = N(0.03); t = tarr(n); f = rng.uniform(2300, 3400)
    x = np.sin(TAU * f * t) * np.exp(-t / 0.006) + fft_filter(rng.standard_normal(n), hp(4000)) * np.exp(-t / 0.002) * 0.6
    return pan2(edge_fade(x, 0.0003, 0.003) * rng.uniform(0.6, 1), rng.uniform(-0.2, 0.2)), 0.0


def sfx_send(rng, **_):
    n = N(0.22); t = tarr(n); f = 520 * (1450 / 520) ** np.minimum(1, t / 0.09)
    x = np.sin(TAU * np.cumsum(f) / SR) * np.minimum(1, t / 0.004) * np.exp(-t / 0.07)
    return pan2(edge_fade(x)), 0.0


def sfx_pop(rng, **_):
    n = N(0.14); t = tarr(n); k = rng.uniform(0.92, 1.08); f = (320 + 950 * np.exp(-t / 0.012)) * k
    x = np.sin(TAU * np.cumsum(f) / SR) * np.minimum(1, t / 0.001) * np.exp(-t / 0.05)
    return pan2(edge_fade(x), rng.uniform(-0.25, 0.25)), 0.0


def sfx_tick(rng, **_):
    n = N(0.04); t = tarr(n)
    x = np.sin(TAU * 1650 * t) * np.exp(-t / 0.007) + fft_filter(rng.standard_normal(n), hp(5000)) * np.exp(-t / 0.002) * 0.3
    return pan2(edge_fade(x, 0.0003, 0.004)), 0.0


def sfx_thud(rng, **_):
    n = N(0.25); t = tarr(n); f = 120 + 110 * np.exp(-t / 0.02)
    x = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.09) + fft_filter(rng.standard_normal(n), lp(1200)) * np.exp(-t / 0.006) * 0.4
    return pan2(edge_fade(x, 0.0005)), 0.0


BELL = ((1, 1, 1), (2.0, 0.5, 0.62), (3.0, 0.22, 0.4), (4.2, 0.14, 0.24), (5.43, 0.08, 0.14))


def sfx_blip(rng, tonic=74, **_):
    out = np.zeros(N(0.4))
    for j, m in enumerate((tonic + 7, tonic + 12)):
        x = tone(mhz(m), N(0.25), ((1, 1, 1), (2, 0.2, 0.5)), 0.07); out[N(j * 0.075):N(j * 0.075) + len(x)] += x
    return pan2(edge_fade(out)), 0.0


def sfx_success(rng, tonic=74, **_):
    out = np.zeros(N(0.9))
    for j, m in enumerate((tonic, tonic + 7, tonic + 12)):
        x = tone(mhz(m), N(0.7), ((1, 1, 1), (4, 0.3, 0.15), (2, 0.15, 0.5)), 0.22); s = N(j * 0.07); out[s:s + len(x)] += x * (0.8 + 0.1 * j)
    return pan2(edge_fade(out), 0.1), 0.0


def sfx_chime(rng, tonic=74, **_):
    n = N(3.2); out = np.zeros((2, n))
    for j, (m, p) in enumerate(((tonic + 12, -0.25), (tonic + 19, 0.25))):
        f = mhz(m); x = tone(f, n - N(j * 0.06), BELL, 1.6) + 0.5 * tone(f + 1.3, n - N(j * 0.06), BELL, 1.4)
        place(out, pan2(x * (1 - 0.25 * j), p), N(j * 0.06))
    return edge_fade(out, 0.001, 0.2), 0.0


def sfx_shimmer(rng, tonic=74, dur=0.8, **_):
    n = N(dur + 0.6); out = np.zeros((2, n)); scale = [0, 2, 4, 7, 9]
    k = 12
    for j in range(k):
        u = (j / (k - 1)) ** 0.7; s = u * dur * 0.95
        m = tonic + 12 + scale[j % 5] + 12 * (j // 5)
        x = tone(mhz(m), N(0.5), ((1, 1, 1), (2, 0.15, 0.4)), 0.12) * (0.3 + 0.7 * u)
        place(out, pan2(x, rng.uniform(-0.6, 0.6)), N(s))
    air = swept_noise(dur, lambda q: 6000 + 4000 * q, 0.5, rng) * np.linspace(0, 1, N(dur)) ** 2 * 0.25
    place(out, pan2(air), 0)
    return edge_fade(out, 0.002, 0.1), dur


SFX = {'whoosh': (sfx_whoosh, 0.55, 0.2, 'Airy sweep as a scene or card arrives (peak lands on the cue)'),
       'swish': (sfx_swish, 0.35, 0.15, 'Short high sweep for cards, callouts and small moves'),
       'riser': (sfx_riser, 0.45, 0.25, 'Builds up and ends on the cue (use before an impact or a dive)'),
       'impact': (sfx_impact, 0.85, 0.35, 'Deep hit for a flash, dive landing or big reveal'),
       'click': (sfx_click, 0.5, 0.05, 'Button tap'),
       'key': (sfx_key, 0.16, 0.04, 'One keystroke (cues generates one per typed character)'),
       'send': (sfx_send, 0.38, 0.12, 'Message sent'),
       'pop': (sfx_pop, 0.38, 0.1, 'Bubble or item popping in'),
       'tick': (sfx_tick, 0.14, 0.05, 'Counter tick'),
       'thud': (sfx_thud, 0.32, 0.1, 'Soft drop for statement words'),
       'blip': (sfx_blip, 0.3, 0.18, 'Two-note "on" for toggles, states and passkey prompts (tuned to the music)'),
       'success': (sfx_success, 0.36, 0.3, 'Rising three notes for approved, done or a finished count (tuned)'),
       'chime': (sfx_chime, 0.42, 0.5, 'Bell for logo reveals and the end card (tuned)'),
       'shimmer': (sfx_shimmer, 0.28, 0.5, 'Sparkle run that ends on the cue, often before a chime (tuned)')}


def make_sfx(cues, dur, tonic, seed=7):
    rng = np.random.default_rng(seed); n = N(dur + 0.05); dry = np.zeros((2, n)); send = np.zeros((2, n))
    for c in sorted(cues, key=lambda c: c['t']):
        if c['sfx'] not in SFX: print(f"  skipped unknown sfx '{c['sfx']}'"); continue
        fn, g, s, _ = SFX[c['sfx']]; kw = {'tonic': tonic}
        if 'dur' in c: kw['dur'] = float(c['dur'])
        x, anchor = fn(rng, **kw); x = norm(x) * g * float(c.get('gain', 1))
        if 'pan' in c: x = pan2(x.mean(0) * 1.2, float(c['pan']))
        st = N(float(c['t']) - anchor); place(dry, x, st); place(send, x * s, st)
    out = dry + convolve(send, reverb_ir(rng, 2.0)) * 0.5
    return out


# ---------------------------------------------------------------- automatic cue sheet from content.json
def cues_from_content(ct, template, dur, end):
    q = []
    def add(t, s, **kw):
        if 0 <= t < dur: q.append(dict(t=round(float(t), 3), sfx=s, **kw))
    def typing(t0, t1, text):
        chars = [c for c in text]
        for i, ch in enumerate(chars):
            if ch.strip(): add(t0 + (i / max(1, len(chars))) * (t1 - t0), 'key')
    def counting(t0, cd, a, b):
        steps = int(min(14, max(4, abs(b - a)))) if b != a else 0
        for k in range(1, steps):
            add(t0 + cd * (1 - (1 - k / steps) ** (1 / 3)), 'tick')
        add(t0 + cd, 'success', gain=0.8)
    if template == 'motion':
        sc = ct.get('scenes', [])
        for i, s in enumerate(sc):
            t0, t1, ty = s['t0'], s['t1'], s['type']; tin = s.get('in') or ('fade' if ty == 'footage' else 'rise')
            prev_dive = i > 0 and sc[i - 1].get('out') == 'dive'
            if t0 > 0.05:
                if tin == 'flash' and not prev_dive: add(t0, 'impact', gain=0.7)
                elif tin == 'zoom': add(t0 + 0.12, 'whoosh')
                elif tin in ('rise', 'flip'): add(t0 + 0.15, 'whoosh', gain=0.7)
                elif tin == 'fade': add(t0 + 0.15, 'whoosh', gain=0.45)
            if s.get('out') == 'dive':
                add(t1 + 0.5, 'riser', dur=round(min(1.2, t1 - t0 + 0.3), 2)); add(t1 + 0.52, 'impact')
            elif s.get('out') == 'zoom': add(t1 + 0.2, 'whoosh', gain=0.6)
            at = lambda x: t0 + x
            if ty == 'hero':
                add(at(0.75), 'shimmer', dur=0.6, gain=0.8)
                for st in s.get('states', [])[1:]: add(at(st['at']), 'blip', gain=0.7)
            elif ty == 'logo': add(at(0.3), 'chime')
            elif ty == 'flow':
                for k in range(len(s.get('nodes', []))): add(at(0.1 + k * 0.3 + 0.08), 'pop')
                for a in s.get('active', []): add(at(a['at']), 'blip', gain=0.8)
            elif ty == 'cards':
                for k, it in enumerate(s.get('items', [])): add(at((it.get('at') if it.get('at') is not None else 0.15 + k * s.get('stagger', 0.45)) + 0.1), 'swish')
            elif ty == 'counter': counting(at(0.2), s.get('countDur', 1.6), s.get('from', 0), s.get('to', 100))
            elif ty == 'phone':
                ta = s.get('typeAt', 0); text = s.get('prompt', '')
                sa = s['sendAt'] if s.get('sendAt') is not None else ta + len(text) * 0.06 + 0.3
                if text: typing(at(ta), at(ta + max(0.3, sa - ta - 0.2)), text); add(at(sa), 'send')
                for r in s.get('replies', []): add(at(r['at']), 'pop')
                sh = s.get('sheet')
                if sh:
                    add(at(sh.get('at', 0) + 0.12), 'swish', gain=0.8)
                    if sh.get('buttons'): add(at((sh.get('buttonsAt') if sh.get('buttonsAt') is not None else sh.get('at', 0) + 0.5) + 0.1), 'pop', gain=0.7)
                    tap = sh.get('tapAt')
                    if tap is not None:
                        add(at(tap), 'click')
                        if sh.get('passkey'): add(at(tap + 0.3), 'blip', gain=0.7); add(at(tap + 0.85), 'success')
                    for st in sh.get('status', []):
                        stl = st.get('style', 'wait')
                        if stl == 'ok' and not (tap is not None and sh.get('passkey') and abs(st['at'] - tap - 0.85) < 0.5): add(at(st['at']), 'success', gain=0.8)
                        elif stl == 'done': add(at(st['at']), 'pop')
            elif ty == 'compare':
                sw = s.get('switchAt', 1.2); add(at(sw + 0.1), 'whoosh', gain=0.7); add(at(sw + 0.6), 'blip', gain=0.7)
            elif ty == 'checklist':
                for k in range(len(s.get('items', []))): add(at(0.3 + k * s.get('stagger', 0.5) + 0.27), 'pop')
            elif ty == 'podium':
                for k, pl in enumerate(s.get('places', [])[:3]): add(at((pl.get('at') if pl.get('at') is not None else .3 + k * .5) + .1), 'thud')
                E = s.get('extras')
                if E:
                    for k in range(min(12, E.get('count', 0))): add(at((E.get('at') if E.get('at') is not None else 2) + k * E.get('stagger', .2)), 'pop', gain=0.4)
            elif ty == 'radar':
                add(at(0.2), 'whoosh', gain=0.6)
                for k, it in enumerate(s.get('items', [])[:6]): add(at(it.get('at') if it.get('at') is not None else .4 + k * .35), 'blip', gain=0.5)
                if s.get('listAt') is not None: add(at(s['listAt'] + .05), 'swish', gain=0.7)
                if s.get('result'): add(at((s['result'].get('at') if s['result'].get('at') is not None else (s.get('listAt') or 1) + 1.2)), 'success', gain=0.8)
            elif ty == 'screen':
                add(at(0.15), 'whoosh', gain=0.6)
                if s.get('chip'): add(at(s['chip'].get('at', 1)), 'pop', gain=0.8)
            elif ty == 'series':
                for k in range(min(5, s.get('total', 5))): add(at(.9 + k * s.get('stagger', .45)), 'swish', gain=0.6)
                if s.get('chip'): add(at(s['chip'].get('at', 3)), 'pop')
            elif ty == 'footage' and s.get('punch'):
                add(at(s['punch'][0]), 'impact', gain=0.5)
            elif ty == 'statement':
                for k in range(min(8, len((s.get('text') or '').split()))): add(at(0.1 + k * 0.09 + 0.12), 'thud', gain=0.6 if k else 0.9)
    else:  # ugc callouts
        for c in ct.get('callouts', []):
            t0 = c.get('t0', 0); ty = c.get('type')
            if t0 > 0.05: add(t0 + 0.12, 'swish')
            if ty == 'prompt':
                td = c.get('typeDur', 1.3); typing(max(0.0, t0), t0 + td, c.get('text', ''))
                if c.get('sendAt'): add(c['sendAt'], 'send')
            elif ty == 'transform':
                for _, pt in c.get('pulses', []): add(pt + 0.12, 'pop')
                a = c.get('action')
                if a and a.get('tapAt') is not None:
                    add(a['tapAt'], 'click')
                    if a.get('passkey'): add(a['tapAt'] + 0.3, 'blip', gain=0.7); add(a['tapAt'] + 0.85, 'success')
                    else: add(a['tapAt'] + 0.4, 'success', gain=0.8)
            elif ty == 'stat': counting(t0 + 0.2, c.get('countDur', 1.2), c.get('from', 0), c.get('to', 0))
            elif ty in ('card', 'chip'): add(t0 + 0.25, 'pop', gain=0.8)
    for o in ct.get('overlays', []):
        add(o.get('t0', 0) + .1, 'swish', gain=0.7)
        if o.get('type') == 'button' and o.get('tapAt') is not None: add(o['tapAt'], 'click'); add(o['tapAt'] + .1, 'blip', gain=0.6)
    if end is not None and end < dur:
        add(end + 0.25, 'shimmer', dur=0.7); add(end + 0.25, 'chime')
    # de-duplicate: same family within 0.18s keeps the louder one
    fam = {'whoosh': 'w', 'swish': 'w', 'impact': 'i', 'pop': 'p', 'blip': 'b', 'success': 'b'}
    q.sort(key=lambda c: c['t']); out = []
    for c in q:
        f = fam.get(c['sfx'])
        clash = next((o for o in reversed(out[-6:]) if f and fam.get(o['sfx']) == f and c['t'] - o['t'] < 0.18), None)
        if clash:
            if c.get('gain', 1) > clash.get('gain', 1): out[out.index(clash)] = c
            continue
        out.append(c)
    return out


# ---------------------------------------------------------------- mixer
def frames_db(x, hop=0.05):
    m = x.mean(0); h = N(hop); k = len(m) // h
    r = np.sqrt((m[:k * h].reshape(k, h) ** 2).mean(1) + 1e-12); return 20 * np.log10(r)


def loudness(x, tmp):
    """True EBU R128 loudness via ffmpeg: (integrated LUFS, list of momentary LUFS every 0.1s)."""
    p = os.path.join(tmp, 'meas.wav'); pk = np.abs(x).max()
    if pk < 1e-7: return -70.0, []
    write_wav(p, x / pk * 0.5)  # measure at a safe level, then correct back
    off = 20 * np.log10(pk / 0.5)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    mom = [float(l.split(' M:')[1].split()[0]) + off for l in r.splitlines() if ' M:' in l and 'TARGET' in l]
    I = float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
    return I + off, [m for m in mom if m > -60]


def fit(x, n):
    return x[:, :n] if x.shape[1] >= n else np.pad(x, ((0, 0), (0, n - x.shape[1])))


def do_mix(a):
    D = a.duration; n = N(D); tmp = tempfile.mkdtemp(prefix='bms_mix_')
    voice = None
    if a.voice:
        chain = ('highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120' if a.voice_kind == 'own'
                 else 'acompressor=threshold=-18dB:ratio=2:attack=5:release=100')
        vp = os.path.join(tmp, 'voice.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.voice, '-vn', '-af', chain, '-ac', '2', '-ar', str(SR), vp], check=True)
        voice = fit(decode(vp), n)
    ref = loudness(voice, tmp)[0] if voice is not None else -20.0
    report = {'voice_lufs': round(ref, 1)}
    total = np.zeros((2, n)) if voice is None else voice.copy()
    if a.music:
        m = decode(a.music)[:, N(a.music_start):]
        if m.shape[1] < n:  # loop a short track with a crossfade
            reps = [m]; xf = N(1.0)
            while sum(r.shape[1] for r in reps) < n + xf: reps.append(m)
            out = reps[0]
            for r in reps[1:]:
                w = np.linspace(0, 1, xf); out = np.concatenate([out[:, :-xf], out[:, -xf:] * (1 - w) + r[:, :xf] * w, r[:, xf:]], 1)
            m = out
        m = fit(m, n); tt = tarr(n); m = m * np.minimum(1, tt / 0.15) * np.clip((D - 0.1 - tt) / 1.5, 0, 1)
        g = 10 ** ((ref + a.music_level - loudness(m, tmp)[0]) / 20); m *= g
        if voice is not None and a.duck > 0:
            d = frames_db(voice); on = (d > ref - 14).astype(float)
            env = np.zeros_like(on); s = 0.0
            for i, v in enumerate(on): s = s + (v - s) * (0.6 if v > s else 0.1); env[i] = s
            gain = 10 ** (-a.duck * np.interp(tarr(n), np.arange(len(env)) * 0.05 + 0.025, env) / 20)
            m *= gain
        report['music_lu_under_voice'] = round(loudness(m, tmp)[0] - ref, 1)
        total += m
    if a.sfx:
        s = fit(decode(a.sfx), n); _, mom = loudness(s, tmp)
        if mom:
            s *= 10 ** ((ref + a.sfx_level - max(mom)) / 20); total += s
            report['loudest_sfx_lu_under_voice'] = round(-a.sfx_level, 1)
    mp = os.path.join(tmp, 'mix.wav'); pk = np.abs(total).max()
    write_wav(mp, total / max(1.0, pk / 0.97))
    # two-pass loudnorm (linear) to -16 LUFS, then mux with the untouched video stream
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', mp, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    af = f"[1:a]{ln},aresample={SR},apad=whole_dur={D},afade=t=out:st={max(0, D - 0.8):.2f}:d=0.8[a]"
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-i', mp, '-filter_complex', af, '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
           '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-t', str(D), '-movflags', '+faststart', a.out]
    subprocess.run(cmd, check=True)
    report['out'] = a.out; print(json.dumps(report))


# ---------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('list')
    c = sp.add_parser('cues'); c.add_argument('content'); c.add_argument('--template', choices=['motion', 'ugc'], required=True)
    c.add_argument('--duration', type=float); c.add_argument('--end', type=float); c.add_argument('--out', required=True)
    m = sp.add_parser('make'); m.add_argument('--duration', type=float, required=True); m.add_argument('--end', type=float)
    m.add_argument('--mood', default='calm', choices=list(MOODS) + ['none']); m.add_argument('--sfx'); m.add_argument('--key-of', choices=list(MOODS))
    m.add_argument('--seed', type=int, default=7); m.add_argument('--out-dir', required=True)
    x = sp.add_parser('mix'); x.add_argument('--video', required=True); x.add_argument('--duration', type=float, required=True); x.add_argument('--out', required=True)
    x.add_argument('--voice'); x.add_argument('--voice-kind', choices=['own', 'ai'], default='own'); x.add_argument('--music'); x.add_argument('--music-start', type=float, default=0)
    x.add_argument('--sfx'); x.add_argument('--music-level', type=float, default=-22); x.add_argument('--duck', type=float, default=10); x.add_argument('--sfx-level', type=float, default=-8)
    a = p.parse_args()
    if a.cmd == 'list':
        print('Music moods:'); [print(f'  {k:8s} {v["bpm"]} BPM  {v["desc"]}') for k, v in MOODS.items()]
        print('Sound effects:'); [print(f'  {k:8s} {v[3]}') for k, v in SFX.items()]
    elif a.cmd == 'cues':
        ct = json.load(open(a.content)); D = a.duration or ct.get('duration')
        if not D: sys.exit('Pass --duration (the ugc template has no duration in content.json).')
        E = a.end if a.end is not None else ct.get('endAt', D - 3.2 if a.template == 'motion' else None)
        q = cues_from_content(ct, a.template, D, E); json.dump(q, open(a.out, 'w'), indent=0)
        counts = {}
        for c in q: counts[c['sfx']] = counts.get(c['sfx'], 0) + 1
        print(f'{len(q)} cues -> {a.out}: ' + ', '.join(f'{k} x{v}' for k, v in counts.items()))
    elif a.cmd == 'make':
        os.makedirs(a.out_dir, exist_ok=True); E = a.end if a.end is not None else max(0.5, a.duration - 3.2)
        tonic = MOODS[a.key_of or (a.mood if a.mood in MOODS else 'calm')]['tonic']
        if a.mood != 'none':
            write_wav(os.path.join(a.out_dir, 'music.wav'), make_music(a.mood, a.duration, E, a.seed)); print('music ->', os.path.join(a.out_dir, 'music.wav'))
        if a.sfx:
            s = make_sfx(json.load(open(a.sfx)), a.duration, tonic, a.seed); write_wav(os.path.join(a.out_dir, 'sfx.wav'), norm(s, 0.89)); print('sfx ->', os.path.join(a.out_dir, 'sfx.wav'))
    else:
        if not (a.music or a.sfx): sys.exit('Nothing to add: pass --music and/or --sfx.')
        do_mix(a)


if __name__ == '__main__':
    main()
