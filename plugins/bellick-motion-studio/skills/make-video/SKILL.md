---
name: make-video
description: Makes a branded Bellick Motion Studio video in the style the user picks (full motion design, partial with graphics over their footage, or partial with mixed cuts between footage and animation), with optional AI voiceover and 4K export in the original's aspect ratio. Use when a user uploads a video or script to turn into content, asks for captions, motion graphics, a voiceover, a re-export, or a 4K version.
---

# Make a video

`KIT` is the plugin's `kit` folder, two levels above this skill's base directory. Work in a fresh job folder. The brand (`brand.json`) and product (`product.json`) must exist first (see brand-setup and product-setup). Read `references/content-schema.md` before writing any content file, and `references/voice.md` before an AI voiceover.

## Step 0: let the user choose the style
Before transcribing, ask the user to pick one of the three styles below. Use AskUserQuestion when it's available, otherwise a numbered list. Show each with its one-line description. Recommend **Partial: mixed cuts** for a talking-head clip and **Full motion design** for a script with no video. Skip the question only if the user already named a style.

| Choice | One-line description for the user | Needs | Template | How it's built |
|---|---|---|---|---|
| **Full motion design** | "Everything is animated. Your voice (or an AI voice) narrates and your face isn't shown." | A clip's audio, a script, or a transcript | `motion` | Scenes only: hero gem, logo dive, flow, cards, counter, phone, before/after, checklist, statement |
| **Partial: graphics over your footage** | "You stay on screen the whole time, with captions and animated cards on top." | Their clip | `ugc` | Full-frame footage, word-timed captions, callout cards (prompt bar, A→B transform with approve tap, feature card, stat, chip) |
| **Partial: mixed cuts** | "The video cuts between you on camera and full-screen animated scenes, for example your face for the hook and the call to action, and animation for the explanation." | Their clip | `motion` + `--frames` | `footage` scenes (full-frame, or framed as a card) interleaved with animated scenes on one timeline; captions switch style automatically |

For mixed cuts, plan the footage moments in the storyboard. Footage works best for the hook (the first 2–3 seconds, so a face stops the scroll), any line with strong emotion or a personal claim, and the call to action. Use animation for explanations, numbers, product flows and lists. Aim for roughly 30–50% footage. Transitions: footage to animation with `out: "zoom"`, a logo `dive` and `in: "flash"`, or a `card`-style footage scene to bring the person back framed over the brand background.

Script-only jobs (no clip) can only be Full motion design. Say so if they ask for a partial style, and offer to use a clip if they have one.

## Pipeline
1. **Set up tools once per chat:** `bash $KIT/tools/setup.sh` (add `voice` when an AI voice is needed). If it fails because downloads are blocked, ask for a transcript and skip to step 4.
2. **Inspect the clip:** `python3 -I $KIT/tools/ratio.py clip.mp4` gives the source shape and the design size (short side 1080). **Always use that design size, so the export matches the original's shape.** Make a contact sheet (`ffmpeg -i clip.mp4 -vf "fps=1/2,scale=240:-1,tile=8x2" -frames:v 1 sheet.jpg`) and look at it, to note where the face sits and what's visible.
3. **Transcribe:** `python3 -I $KIT/tools/asr.py clip.mp4 tr`, then a second pass with shorter windows:
   ```python
   import sys; sys.path.insert(0, "$KIT/tools"); import asr
   x = asr.load("clip.mp4")
   for a, b in asr.speech_segments(x, max_len=3.6): print(a, b, asr.transcribe(x[int(a*16000):int(b*16000)]))
   ```
   Compare the two passes. Brand names, tickers and slang are often misheard (for example "PayBox" came back as "pay box" and "K-Box", "BNB" as "BMB", and "SOL" as "Soul"). **Send the transcript with timestamps, list every uncertain word, and ask the user to confirm.** Never guess silently.
4. **Fact-check** the confirmed script against `product.json`: flag lines that hit `avoid_claims` or state unconfirmed facts. Their spoken words stay, but on-screen graphics use safe wording, and the `footnote` covers simplifications.
5. **Storyboard:** a table of time, spoken line, visual and accuracy note, opened with the chosen style. For mixed cuts, mark each row **On camera** or **Animated**. For animated scenes, pick scenes from the library that make each line visible, one idea per scene, with at least one transformation moment (a dive, a morph, or a freeze and release). Include the hook in frame 1. Propose, then wait for **"start"**.
6. **Build:**
   - Phrases file `phr.json`: `[[start, end, "confirmed text"], …]` using the ASR segment times. Then `python3 -I $KIT/tools/wordtime.py clip.mp4 phr.json words.json`.
   - Write `content.json` (see the schema). Time every visual to the word that triggers it, using `words.json`.
   - For both partial styles, extract frames at the design size: `ffmpeg -i clip.mp4 -vf "fps=30,scale=W:H:flags=lanczos" -q:v 2 frames/f%04d.jpg`, and pass `--frames frames` to build.py. Mixed cuts uses the `motion` template with `footage` scenes. Its `duration` is the clip length plus about 3.2s, with `endAt` just after the last word.
   - Build the page: `python3 -I $KIT/tools/build.py --template ugc|motion --brand brand.json --product product.json --content content.json --words words.json --format WxH [--frames frames] --out page.html`
7. **Stills check:** `python3 $KIT/tools/render.py page.html stills t1,t2,…` (one per beat), tile them into a sheet, and **look at it yourself**. Check that captions stay clear of the mouth and face, text is readable and not clipped, nothing overlaps, colours are brand-only and the logo is untouched. Fix, then send the sheet to the user.
8. **Render** (in the background, since it takes minutes):
   - 4K: `python3 $KIT/tools/render.py page.html video v4k.mp4 --scale 2`
   - Mux the audio. With the user's voice, use `-i clip.mp4` and this filter:
     `highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=DUR,afade=t=out:st=END:d=0.8`
     Use `-c:v copy -c:a aac -b:a 256k -ac 2 -t DUR -movflags +faststart`.
   - Make the 1080 copy: scale the 4K output down with `lanczos`, `-crf 14 -preset slow`.
   - Name the files `<Product>_<Style>_4K_<W>x<H>.mp4` and `<Product>_<Style>_<W>x<H>.mp4`, where Style is `FullMotion`, `Overlay` or `MixedCuts`.
9. **Verify before sending:** `ffprobe` each file (size must equal the design size ×2 and ×1, and duration must be right), check loudness is about −16 LUFS (`ffmpeg -i f.mp4 -af ebur128 -f null -`), and sample 6–9 frames across the video into a sheet and look at them. Then send the files as downloads, so previews don't compress them.
10. **Close:** one line on what was made, the disclosure reminder, and an offer of changes.

## Changes after delivery
Edit `content.json` or `words.json`, rebuild, re-check the affected stills, re-render and re-verify. When a caption word is corrected, regenerate `words.json` from the corrected phrase text.

## Quality bar
- Kinetic captions, three words at a time, with the active word in the accent colour and keywords highlighted. The hook is visible in frame 1.
- For product flows that involve user approval, never show the action completing before approval. Outcomes read "Submitted" or "Done", never guaranteed results unless the product facts support them.
- Keep movement purposeful: one idea per scene, transitions that carry meaning (a dive *into* the product, a freeze while waiting for the user), and generous negative space.
