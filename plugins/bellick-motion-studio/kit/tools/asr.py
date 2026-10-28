"""Transcribe speech with Whisper (sherpa-onnx export) using only numpy + onnxruntime.
Usage: python3 -I asr.py <media file> <out prefix> [--pidgin] [--prompt "text"] [--vocab "PayBox, Market Radar"]
  --pidgin  primes the recogniser with Nigerian Pidgin, so it keeps words like dey, wetin, abeg, una
            instead of forcing them into English ("they", "what in", "a big", "you nah")
  --prompt  any priming text (style, spelling, names)   --vocab  names and brand words to spell correctly
Writes <prefix>.json (phrase segments with times) and <prefix>.srt
"""
import sys, json, base64, subprocess
import numpy as np, onnxruntime as ort

import os
M = os.path.join(os.environ.get('KIT_MODELS', os.path.expanduser('~/.motion-studio/models')), 'sherpa-onnx-whisper-small.en', 'small.en-')
SR = 16000

def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def mel_filters(n_mels=80, n_fft=400):
    f_sp, min_log_hz, min_log_mel, logstep = 200 / 3, 1000.0, 15.0, np.log(6.4) / 27
    def h2m(f):
        f = np.asarray(f, float); m = f / f_sp
        return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-9) / min_log_hz) / logstep, m)
    def m2h(m):
        m = np.asarray(m, float); f = f_sp * m
        return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), f)
    fft = np.linspace(0, SR / 2, n_fft // 2 + 1)
    mel_f = m2h(np.linspace(h2m(0), h2m(SR / 2), n_mels + 2))
    fdiff = np.diff(mel_f); ramps = mel_f[:, None] - fft[None, :]
    w = np.zeros((n_mels, len(fft)))
    for i in range(n_mels):
        w[i] = np.maximum(0, np.minimum(-ramps[i] / fdiff[i], ramps[i + 2] / fdiff[i + 1]))
    w *= (2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels]))[:, None]
    return w

FB = mel_filters()
WIN = np.hanning(401)[:-1]

def features(x):
    xp = np.pad(x, 200, mode='reflect')
    n = 1 + (len(xp) - 400) // 160
    idx = np.arange(400)[None, :] + 160 * np.arange(n)[:, None]
    spec = np.abs(np.fft.rfft(xp[idx] * WIN, axis=1)) ** 2
    spec = spec[:-1]
    mel = spec @ FB.T
    log = np.log10(np.maximum(mel, 1e-10))
    log = np.maximum(log, log.max() - 8.0)
    mel = (log + 4.0) / 4.0
    mel = np.pad(mel, ((0, 1500), (0, 0)))
    if mel.shape[0] > 3000:
        mel = np.pad(mel[:2950], ((0, 50), (0, 0)))
    return mel.T[None].astype(np.float32)

so = ort.SessionOptions(); so.intra_op_num_threads = 4
enc = ort.InferenceSession(M + 'encoder.onnx', so, providers=['CPUExecutionProvider'])
dec = ort.InferenceSession(M + 'decoder.onnx', so, providers=['CPUExecutionProvider'])
meta = enc.get_modelmeta().custom_metadata_map
L, CTX, ST = int(meta['n_text_layer']), int(meta['n_text_ctx']), int(meta['n_text_state'])
EOT, SOT, NOTS, NOSP, TRN, BLANK = (int(meta[k]) for k in ['eot', 'sot', 'no_timestamps', 'no_speech', 'translate', 'blank_id'])
SOTSEQ = list(map(int, meta['sot_sequence'].split(','))) + [NOTS]
SOTPREV = int(meta.get('sot_prev', 50360))
TOK = {}
for line in open(M + 'tokens.txt'):
    t, i = line.split(); TOK[int(i)] = t
BYTES = {}
for i, t in TOK.items():
    try: BYTES.setdefault(base64.b64decode(t), i)
    except Exception: pass
MAXB = max(len(b) for b in BYTES)

def encode(text):
    """Greedy longest-match tokenisation (close to Whisper's BPE; fine for priming prompts)."""
    b = text.encode('utf-8'); i = 0; out = []
    while i < len(b):
        for k in range(min(MAXB, len(b) - i), 0, -1):
            j = BYTES.get(b[i:i + k])
            if j is not None: out.append(j); i += k; break
        else: i += 1
    return out

PIDGIN_PROMPT = ("Oya, make we yarn. Wetin dey happen? Abeg, una no go believe am. E don happen o. "
                 "Na so e be, I dey tell una. Dem don pay am, e sweet well well. No wahala, I go show una sha. "
                 "Una sabi say na correct thing? Make una follow me, abi?")
PROMPT_IDS = None
di = [i.name for i in dec.get_inputs()]; do = [o.name for o in dec.get_outputs()][:3]

def transcribe(seg):
    ck, cv = enc.run(None, {enc.get_inputs()[0].name: features(seg)})
    kc = np.zeros((L, 1, CTX, ST), np.float32); vc = kc.copy()
    pre = ([SOTPREV] + PROMPT_IDS[-200:]) if PROMPT_IDS else []
    toks = np.array([pre + SOTSEQ], np.int64); off = np.zeros(1, np.int64)
    out = []
    for step in range(CTX):
        logits, kc, vc = dec.run(do, dict(zip(di, [toks, kc, vc, ck, cv, off])))
        off += toks.shape[1]
        lg = logits[0, -1].copy()
        for b in (NOTS, SOT, NOSP, TRN): lg[b] = -np.inf
        if step == 0: lg[EOT] = -np.inf; lg[BLANK] = -np.inf
        t = int(lg.argmax())
        if t == EOT or len(out) > 220: break
        out.append(t); toks = np.array([[t]], np.int64)
    s = b''.join(base64.b64decode(TOK[i]) for i in out if i in TOK)
    return s.decode('utf-8', 'ignore').strip()

def speech_segments(x, max_len=24.0):
    hop = int(0.02 * SR); n = len(x) // hop
    e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(e)
    thr = max(db.max() - 38, -55)
    act = db > thr
    segs = []; i = 0
    while i < n:
        if act[i]:
            j = i
            while j < n and (act[j] or (j + 18 < n and act[j:j + 18].any())): j += 1
            segs.append([i, j]); i = j
        else: i += 1
    out = []
    for a, b in segs:
        a = max(0, a - 8); b = min(n, b + 8)
        if (b - a) * 0.02 < 0.15: continue
        while (b - a) * 0.02 > max_len:
            lo = a + int(max_len * 0.6 / 0.02); hi = a + int(max_len / 0.02)
            cut = lo + int(np.argmin(db[lo:hi])); out.append((a, cut)); a = cut
        out.append((a, b))
    return [(a * 0.02, b * 0.02) for a, b in out]

def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f'{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)) % 1000:03}'

if __name__ == '__main__':
    args = sys.argv[1:]; opt = {}
    for k in ('--prompt', '--vocab'):
        if k in args: i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    pidgin = '--pidgin' in args; args = [a for a in args if a != '--pidgin']
    ptxt = ' '.join(filter(None, [PIDGIN_PROMPT if pidgin else '', opt.get('--prompt', ''), (opt['--vocab'] + '.') if opt.get('--vocab') else '']))
    if ptxt: PROMPT_IDS = encode(' ' + ptxt.strip())
    x = load(args[0]); pre = args[1]
    segs = []
    for a, b in speech_segments(x):
        text = transcribe(x[int(a * SR):int(b * SR)])
        if text: segs.append({'start': round(a, 2), 'end': round(b, 2), 'text': text}); print(f'[{a:6.2f}-{b:6.2f}] {text}', flush=True)
    json.dump(segs, open(pre + '.json', 'w'), indent=1)
    with open(pre + '.srt', 'w') as f:
        for k, s in enumerate(segs, 1): f.write(f"{k}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n")
