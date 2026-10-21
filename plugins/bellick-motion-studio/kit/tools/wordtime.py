"""Per-word caption timing from the speech audio.
Usage: python3 -I wordtime.py <media> <phrases.json> <out words.json>
phrases.json: [[start, end, "confirmed text of that phrase"], ...]  (start/end from asr.py segments)
Words are spread across the voiced frames of each phrase, weighted by syllables."""
import sys, json, re, subprocess, numpy as np
src, phr_path, out = sys.argv[1:4]
x = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',src,'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True).stdout, np.float32)
hop = 160; n = len(x)//hop
db = 20*np.log10(np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)]))
thr = db.max()-30
SPECIAL = {'ai':2,'paybox':2,'agent':2,'bnb':3,'sol':1,'usdc':4,'ansem':2,'x402':4,'permission':3,'approve':2,'decline':2}
def syl(w):
    w = re.sub(r'[^a-z0-9]','',w.lower())
    if w in SPECIAL: return SPECIAL[w]
    return max(1, len(re.findall(r'[aeiouy]+',w)) - (1 if w.endswith('e') and len(w)>3 and not w.endswith('le') else 0))
words = []
for a, b, txt in json.load(open(phr_path)):
    i0, i1 = int(a*100), int(b*100)
    v = np.convolve((db[i0:i1] > thr).astype(float), np.ones(5)/5, 'same') > 0.2
    cum = np.cumsum(v); tot = max(cum[-1], 1)
    ws = txt.split(); wt = np.array([syl(w) for w in ws], float); edges = np.concatenate([[0], np.cumsum(wt)/wt.sum()])
    at = lambda f: round(a + min(int(np.searchsorted(cum, f*tot)), len(v)-1)/100, 2)
    for j, w in enumerate(ws): words.append({'w': w, 's': at(edges[j]+1e-6), 'e': at(edges[j+1])})
json.dump(words, open(out, 'w'))
print(' '.join(f"{w['w']}@{w['s']}" for w in words))
