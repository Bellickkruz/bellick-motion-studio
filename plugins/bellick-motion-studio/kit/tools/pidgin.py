"""Detect Nigerian Pidgin (Naija) in a transcript and flag likely mis-hearings.
Usage: python3 -I pidgin.py <transcript.json from asr.py>   (or any text file)
Prints a JSON report: {"pidgin_score", "verdict", "markers", "suspects"}.
- pidgin_score: Pidgin markers per 100 words. verdict: "english" (< 2), "mixed" (2-6), "pidgin" (> 6).
- suspects: English-looking words the English-trained recogniser often produces in place of Pidgin
  (for example "they" for dey, "what in" for wetin, "a big" for abeg), with the likely Pidgin word.
When the verdict is mixed or pidgin, re-run asr.py with --pidgin and compare the two passes."""
import sys, json, re

MARKERS = {  # word: weight (strong markers count more)
    'wetin': 3, 'abeg': 3, 'una': 3, 'dey': 3, 'sabi': 3, 'wahala': 3, 'comot': 3, 'pikin': 3, 'oya': 3, 'jare': 3,
    'abi': 2, 'sha': 2, 'sef': 2, 'shey': 2, 'ehen': 2, 'ehn': 2, 'wey': 2, 'dem': 1.5, 'na': 1.5, 'don': 1.5, 'am': 1,
    'chop': 2, 'waka': 2, 'yarn': 2, 'gist': 1.5, 'japa': 3, 'yawa': 3, 'sapa': 3, 'gbege': 3, 'kpatakpata': 3,
    'ogbonge': 3, 'mumu': 2, 'oga': 1.5, 'bros': 1, 'padi': 2, 'wan': 2, 'fit': 1, 'go': 0, 'o': 1, 'nawa': 3, 'ginger': 1,
    'kolo': 2, 'sotey': 3, 'katakata': 3, 'gbam': 3, 'shakara': 3, 'ment': 2, 'ehya': 3, 'chai': 2, 'haba': 2,
}
PHRASES = {  # multi-word Pidgin patterns
    r'\bhow far\b': 2, r'\bno wahala\b': 3, r'\bmake we\b': 3, r'\bmake una\b': 3, r'\bno be\b': 2, r'\be don\b': 3,
    r'\bi don\b': 2, r'\bdem don\b': 3, r'\bwell well\b': 2, r'\be no easy\b': 2, r'\bi go\b': 1, r'\bwe go\b': 1,
    r'\bna so\b': 3, r'\bna im\b': 3, r'\bna him\b': 2, r'\be be like\b': 3, r'\bi dey\b': 3, r'\be dey\b': 3,
    r'\bwetin dey\b': 3, r'\bfor where\b': 2, r'\bsay make\b': 3, r'\bno vex\b': 3, r'\bmy guy\b': 1,
}
SUSPECTS = [  # (regex on lower-case text, likely Pidgin)
    (r'\b(i|you|we|e|dem|they|he|she) (they|day|the) (go|come|do|talk|tell|see|want|make|happen|live)\b', 'dey'),
    (r'\bwhat in\b|\bwet in\b|\bwhat ting\b|\bwhaddin\b', 'wetin'),
    (r'\ba big\b|\babig\b|\bah beg\b|\buh beg\b', 'abeg'),
    (r'\byou nah\b|\byou na\b|\boona\b|\bu na\b', 'una'),
    (r'\bnah\b|\bnow (so|be|him|im)\b', 'na'),
    (r'\bcome out\b(?=.*\b(dey|na|una)\b)', 'comot'),
    (r'\bsabby\b|\bsubby\b|\bsaab\b', 'sabi'),
    (r'\bwa hala\b|\bwahalla\b|\bwahala\b', 'wahala'),
    (r'\boh ya\b|\boy ya\b|\boyah\b', 'oya'),
    (r'\bmake we\b|\bmake you\b', 'make we / make una'),
    (r'\b(see|tell|give|pay|show) (him|them|um)\b(?=.*\b(dey|na|una|abeg|wetin)\b)', 'am'),
    (r'\bit done\b|\bhe done\b|\bthey done\b', 'e don / dem don'),
]

def text_of(path):
    raw = open(path, encoding='utf-8').read()
    try:
        j = json.loads(raw)
        if isinstance(j, list): return ' '.join(x.get('text', x.get('w', '')) if isinstance(x, dict) else (x[-1] if isinstance(x, list) else str(x)) for x in j)
    except Exception: pass
    return raw

def analyse(t):
    low = re.sub(r"[^\w' ]+", ' ', t.lower()); words = low.split(); n = max(1, len(words))
    found = {}; score = 0.0
    for w in words:
        if w in MARKERS and MARKERS[w]: found[w] = found.get(w, 0) + 1; score += MARKERS[w]
    for rx, wt in PHRASES.items():
        k = len(re.findall(rx, low))
        if k: found[rx.replace('\\b', '')] = k; score += wt * k
    sus = []
    for rx, guess in SUSPECTS:
        for m in re.finditer(rx, low): sus.append({'heard': m.group(0), 'maybe': guess})
    per100 = round(100 * score / n, 1)
    verdict = 'pidgin' if per100 > 6 else ('mixed' if per100 >= 2 or len(sus) >= 3 else 'english')
    return {'words': n, 'pidgin_score': per100, 'verdict': verdict, 'markers': found, 'suspects': sus[:30]}

if __name__ == '__main__':
    print(json.dumps(analyse(text_of(sys.argv[1])), indent=1, ensure_ascii=False))
