"""Place generated voice lines on their scene cues and write one mono WAV.
python3 -I mix.py <prefix> <cues.json> <out.wav> <duration_seconds>
cues.json: [["line_key", start_seconds], ...] using the same keys as lines.json (clips are <prefix>_<key>.npy from tts.py).
Prints each line's placement and warns on overlaps; trims silence from every clip."""
import sys, json, wave, numpy as np
pre, cues_path, out, dur = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
SR = 24000; track = np.zeros(int(dur * SR), np.float32); prev = 0; timing = []
for key, t in json.load(open(cues_path)):
    a = np.load(f'{pre}_{key}.npy'); idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - int(.03 * SR)): idx[-1] + int(.08 * SR)].copy(); f = int(.012 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    s = int(t * SR); e = min(len(track), s + len(a)); track[s:e] += a[:e - s]
    print(f'{key}: {t:.2f}-{e / SR:.2f}s' + ('  OVERLAP with previous line' if s < prev else '') + ('  CUT OFF at video end' if s + len(a) > len(track) else ''))
    timing.append([key, t, round(e / SR, 2)]); prev = e
track /= max(1e-6, np.abs(track).max()) / 0.89
with wave.open(out, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((track * 32767).astype(np.int16).tobytes())
json.dump(timing, open(out + '.timing.json', 'w'))
