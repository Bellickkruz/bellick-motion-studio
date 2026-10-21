# AI voiceover (Kokoro)

Use an AI voice only when there's no voice from the user. Run `bash $KIT/tools/setup.sh voice` first.

## Voices
- `af_heart`: calm, warm female (the default)
- `am_michael`: steady male
- Other English voices in the model: af_bella, af_nicole, af_sarah, am_adam, am_fenrir, am_puck, bf_emma, bm_george (British). Offer a short sample before committing.

## Writing the lines
There's no automatic phonemiser, so write each line as US phonemes in misaki style:
- Diphthongs are capital letters: **A**=eɪ (day), **I**=aɪ (my), **O**=oʊ (go), **W**=aʊ (now), **Y**=ɔɪ (boy).
- Use ɹ for r, ʃ ʒ ʧ ʤ θ ð ŋ as in IPA, and ə for schwa.
- Put `ˈ` (primary stress) or `ˌ` (secondary stress) immediately before the stressed vowel.
- Keep punctuation (`, . ? …`) for natural pauses.

Worked examples:
| Word | Phonemes |
|---|---|
| AI | `ˌAˈI` |
| PayBox | `pˈAbˌɑks` |
| passkey | `pˈæski` (not `pˈæsˌki`, which came out as "passakey") |
| approve | `əpɹˈuv` |
| prepare | `pɹipˈɛɹ` |
| transaction | `tɹænzˈækʃən` |
| wallet | `wˈɑlət` |
| USDC | `jˌuˌɛsdˌiˈsi` |
| SOL (Solana) | `sˈOl` |

`lines.json`: `{"l1": "wˈʌt ɪf jʊɹ ˌAˈI kʊd pɹipˈɛɹ ɐ tɹænzˈækʃən fɔɹ jˈu?", "l2": "…"}`

## Generate, place, verify
1. `cd job && python3 -I $KIT/tools/tts.py af_heart 1.0 vo lines.json` prints each clip's length. Adjust the speed (0.9–1.15) or split lines to fit the scenes.
2. `cues.json`: `[["l1", 0.25], ["l2", 3.9], …]` gives each line's start on the timeline. Then run `python3 -I $KIT/tools/mix.py vo cues.json vo.wav DURATION`, which warns on overlaps and cut-offs.
3. **Verify by transcribing the result:** `python3 -I $KIT/tools/asr.py vo.wav check`. Every line must come back right, especially brand words, numbers and tickers (spelling variations like "Paybox" are fine). Fix any phonemes that come back wrong, and regenerate.
4. Build `words.json` for the captions from the voiceover itself: phrases from `vo.wav.timing.json` plus the line text, then `wordtime.py vo.wav phr.json words.json`.
5. Mux `vo.wav` with the same audio filter as the make-video skill, using `highpass=f=70` for female voices and `f=60` for male.
6. Tell the user which brand words you checked, and that they should listen once before posting.
