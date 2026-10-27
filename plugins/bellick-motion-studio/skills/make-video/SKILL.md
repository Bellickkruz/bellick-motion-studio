---
name: make-video
description: Makes a branded Bellick Motion Studio video in the style the user picks (full motion design, partial with graphics over their footage, or partial with mixed cuts between footage and animation), with optional AI voiceover, optional music and sound effects (built-in or their own track), and a choice of export quality (fast 720p preview, Full HD or 4K, each with a measured time estimate) in the original's aspect ratio. Use when a user uploads a video or script to turn into content, asks for captions, motion graphics, a voiceover, music, sound effects, a re-export, or a 4K version.
---

# Make a video

`KIT` is the plugin's `kit` folder, two levels above this skill's base directory. Work in a fresh job folder. The brand (`brand.json`) and product (`product.json`) must exist first (see brand-setup and product-setup). Read `references/content-schema.md` before writing any content file, `references/voice.md` before an AI voiceover, and `references/sound.md` before adding music or sound effects.

## Creative direction: every video is a one-off
The creator's brand stays fixed: colours, fonts, logo rules, background rules, credit and disclosure. **Everything else is designed fresh for each video.** The scene library and looks are building blocks, not a menu. A finished video should not feel like a filled-in template, and no two videos should feel alike.

Before the storyboard, find the video's **concept**:
1. **The core idea in one line.** What is this video really about? (For example: "13 people turned a weekend of vibe coding into $20,000.")
2. **A visual metaphor taken from that idea**, not a stock one: a podium for a prize split, a radar for a market scanner, a ledger filling up for payouts, a lock clicking open for approval. Ask what this specific story looks like.
3. **One signature moment** that only this video has: a transformation, a reveal or a visual pun that carries the main point. It's the frame people would screenshot.
4. **A motion personality** that fits the tone (calm and precise, punchy, playful, cinematic), expressed through the look, the pacing and the transitions.

Open the storyboard with these four lines.

**Build what the idea needs.** If no library scene expresses the concept, write a **custom scene** for this video (see "Custom scenes" in `references/content-schema.md`). The signature moment is usually custom. Use the creator's own material wherever possible: their footage, screen recordings and screenshots, real numbers and real product names, after the fact and privacy checks.

**Never repeat yourself for the same creator.**
- Don't reuse the previous video's concept, signature moment, opening, storyboard shape or look.
- A brand pack can keep a short `history` list in `brand.json` (date, concept, signature moment, look). Read it, avoid it, and add the new video to it in the pack you hand back.
- If the creator says two videos feel the same, change the concept and the signature moment, not just the colours.

## Setup steps (asked one at a time)
The choices below are asked as numbered steps, one per message, following the **guided setup** in the bellick-motion-studio skill: 1 Video, 2 Brand, 3 Product, 4 Style, 5 Voice, 6 Music, 7 Effects, 8 Quality. This section holds the content for steps 4–8. Don't ask any of them before the earlier steps are done, and don't ask two in one message.

### Step 4: style
Ask the user to pick one of the three styles below, showing each with its one-line description. Recommend **Partial: mixed cuts** for a talking-head clip and **Full motion design** for a script with no video. Skip the question only if the user already named a style.

| Choice | One-line description for the user | Needs | Template | How it's built |
|---|---|---|---|---|
| **Full motion design** | "Everything is animated. Your voice (or an AI voice) narrates and your face isn't shown." | A clip's audio, a script, or a transcript | `motion` | Scenes only: hero gem, logo dive, flow, cards, counter, phone, before/after, checklist, statement |
| **Partial: graphics over your footage** | "You stay on screen the whole time, with captions and animated cards on top." | Their clip | `ugc` | Full-frame footage, word-timed captions, callout cards (prompt bar, A→B transform with approve tap, feature card, stat, chip) |
| **Partial: mixed cuts** | "The video cuts between you on camera and full-screen animated scenes, for example your face for the hook and the call to action, and animation for the explanation." | Their clip | `motion` + `--frames` | `footage` scenes (full-frame, or framed as a card) interleaved with animated scenes on one timeline; captions switch style automatically |

**Then, in the same step, the look.** Ask which look the video should have: **Soft**, **Bold**, **Editorial**, **Glass**, **Reel** or **Night** (one-line feel for each, from `references/content-schema.md`), plus **"Surprise me"**. AskUserQuestion has room for 4 options, so offer the 3 that best fit the product's tone plus "Surprise me", and name the others in the question text. Don't offer **Night** when the brand fixes its background.
- For "Surprise me", pick a look that differs from their last video. A brand pack's `brand.json` can record `"last_looks"`; update it in the pack you hand back.
- Never default every video to the same look.
- Within a look, a new video automatically gets new variations (`seed`), and changing the seed reshuffles them. Use that when a creator says two videos "feel the same".

For mixed cuts, plan the footage moments in the storyboard. Footage works best for the hook (the first 2–3 seconds, so a face stops the scroll), any line with strong emotion or a personal claim, and the call to action. Use animation for explanations, numbers, product flows and lists. Aim for roughly 30–50% footage. Transitions: footage to animation with `out: "zoom"`, a logo `dive` and `in: "flash"`, or a `card`-style footage scene to bring the person back framed over the brand background.

Script-only jobs (no clip) can only be Full motion design. Say so if they ask for a partial style, and offer to use a clip if they have one.

### Step 5: voice
- If the clip has them speaking, tick it automatically ("✓ Voice: yours, from the clip").
- For a script, ask: record their own voice and upload it, or use an AI voice: calm female (`af_heart`) or steady male (`am_michael`), English only. Offer a 5-second sample before committing (see `references/voice.md`).

### Steps 6 and 7: music, then sound effects (optional, never automatic)
Two separate steps, with **no option marked as recommended**:
- **Step 6, Music:**
  - "No music (keep my audio as it is)", listed first.
  - "Built-in music": original, copyright-free. Calm, upbeat or minimal; suggest one in the storyboard.
  - "My own track": they upload it.
- **Step 7, Sound effects:** "No sound effects", listed first, or "Add sound effects": whooshes, taps, typing, pops and chimes, timed to the animation.

If they skip these steps, are away, or just say "go", add no sound. Never add music or effects they didn't choose. Skip the questions if they already said what they want, and if a brand pack says they always want none, don't ask again unless they bring it up.

### Step 8: export quality
Ask before production, with a rough time for each based on the video's length. These times come from a typical workspace, as seconds of rendering per second of video: preview about 4, Full HD about 13, 4K about 60, and 4K + Full HD about 62. Round up to whole minutes, and say they're rough until measured.
- Example for a 15-second clip: "Fast preview, 720p (~1 min)", "Full HD, 1080p (~4 min)", "4K UHD (~15 min)", "4K + Full HD copy (~16 min)".
- Each option gets its one-line purpose (see pipeline step 8).
- Mark none as recommended. If they don't answer, use 4K + Full HD.

After step 8, send the setup summary (all eight choices) and start the pipeline.

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
5. **Storyboard:** a table of time, spoken line, visual and accuracy note, opened with the chosen style and look (plus a Sound column and the mood or "your track" when sound is on). For mixed cuts, mark each row **On camera** or **Animated**. For animated scenes, pick scenes from the library that make each line visible, one idea per scene, and vary the scene mix from the creator's previous video (podium, radar, screen, series, counter, phone, flow, cards, compare, checklist, statement with its text animations, logo, hero, bounce, curve, morph, marquee, particles, field, screens3d, ticks, chips), with at least one transformation moment (a dive, a morph, or a freeze and release). Include the hook in frame 1. Propose, then wait for **"start"**.
6. **Build:**
   - Phrases file `phr.json`: `[[start, end, "confirmed text"], …]` using the ASR segment times. Then `python3 -I $KIT/tools/wordtime.py clip.mp4 phr.json words.json`.
   - Write `content.json` (see the schema). Time every visual to the word that triggers it, using `words.json`.
   - For both partial styles, extract frames at the design size: `ffmpeg -i clip.mp4 -vf "fps=30,scale=W:H:flags=lanczos" -q:v 2 frames/f%04d.jpg`, and pass `--frames frames` to build.py. Mixed cuts uses the `motion` template with `footage` scenes. Its `duration` is the clip length plus about 3.2s, with `endAt` just after the last word.
   - Build the page: `python3 -I $KIT/tools/build.py --template ugc|motion --brand brand.json --product product.json --content content.json --words words.json --format WxH [--frames frames] --out page.html`
7. **Stills check:** `python3 $KIT/tools/render.py page.html stills t1,t2,…` (one per beat), tile them into a sheet, and **look at it yourself**. Check that captions stay clear of the mouth and face, text is readable and not clipped, nothing overlaps, colours are brand-only and the logo is untouched. Fix, then send the sheet to the user.
8. **Confirm the export time (quality was picked in setup step 8):**
   - Measure render speed on this workspace: `python3 $KIT/tools/render.py page.html estimate all`. It times a few real frames at each quality (under a minute) and prints the minutes each export will take. Run it while nothing else is rendering, or the numbers come out high.
   - Tell the user the measured time and a ready-by time for the quality they chose. If it's much longer than the rough setup estimate (more than about 1.5×), offer the choice again with the measured times in the labels, for example "Fast preview, 720p (~3 min)", "Full HD, 1080p (~8 min)", "4K UHD (~25 min)", "4K + Full HD copy (~26 min)". The option lines are:
     - Preview: to check motion and timing before a final export.
     - Full HD: sharp on phones and on X, and the quickest final.
     - 4K: the sharpest, for YouTube or re-editing.
     - 4K + Full HD: both files from one render.
   - Mark none as recommended. If the user doesn't answer, use 4K + Full HD. Remind them that a quick preview now and a 4K export once they're happy is a good habit for long videos, and that a re-export only re-renders: nothing else is redone.
   - While it renders, tell them when to expect it (for example "about 8 minutes, ready around 14:20"). If they ask partway through, check `progress` in the render log and give an updated time.
9. **Render** (in the background, since it takes minutes):
   - `python3 $KIT/tools/render.py page.html video vsilent.mp4 --quality preview|hd|4k` (for "4K + Full HD" render `4k`). It prints progress every 5 seconds of video.
   - **If they chose music or effects:** keep `vsilent.mp4` silent and follow `references/sound.md` (cue sheet, stems, `sound.py mix`). This replaces the mux below, and the result is checked by transcribing it.
   - **Otherwise,** mux the audio. With the user's voice, use `-i clip.mp4` and this filter:
     `highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=DUR,afade=t=out:st=END:d=0.8`
     Use `-c:v copy -c:a aac -b:a 256k -ac 2 -t DUR -movflags +faststart`.
   - For "4K + Full HD", make the 1080 copy by scaling the finished 4K file down with `lanczos`, `-crf 14 -preset slow` (about a minute). A downscaled copy looks sharper than rendering at 1080.
   - Name the files `<Product>_<Style>_<Quality>_<W>x<H>.mp4`, where Style is `FullMotion`, `Overlay` or `MixedCuts` and Quality is `Preview`, `FullHD` or `4K`.
10. **Verify before sending:** `ffprobe` each file (size must equal the design size × the quality: preview ×2/3, Full HD ×1, 4K ×2, and duration must be right), check loudness is about −16 LUFS (`ffmpeg -i f.mp4 -af ebur128 -f null -`), and sample 6–9 frames across the video into a sheet and look at them. Then send the files as downloads, so previews don't compress them.
11. **Close:** one line on what was made, the disclosure reminder, and an offer of changes (and, after a preview, an offer to export in Full HD or 4K).

**Variety rules:** don't open two consecutive videos for the same creator with the same scene type, and don't reuse a storyboard shape. Mix full-frame footage, framed footage cards, punch-ins and overlays. Prefer the creator's own material: a screen recording beats an illustration when they provide one (after the privacy crop).

## Changes after delivery
Edit `content.json` or `words.json`, rebuild, re-check the affected stills, re-render and re-verify. Sound-only changes (adding, removing or swapping music, effects or levels) reuse the silent `vsilent.mp4` and only re-mix, which takes seconds. When a caption word is corrected, regenerate `words.json` from the corrected phrase text.

## Quality bar
- Kinetic captions, three words at a time, with the active word in the accent colour and keywords highlighted. The hook is visible in frame 1.
- For product flows that involve user approval, never show the action completing before approval. Outcomes read "Submitted" or "Done", never guaranteed results unless the product facts support them.
- Keep movement purposeful: one idea per scene, transitions that carry meaning (a dive *into* the product, a freeze while waiting for the user), and generous negative space.
