# Music and sound effects (optional)

Sound is **opt-in**. Add music or sound effects only when the user chose them for this video. Many creators keep their own audio or add sound in their editing app, so "No added sound" is always a full, equal option, and the default when they don't answer.

`KIT/tools/sound.py` needs only numpy and ffmpeg, and no downloads. Everything it makes is synthesised from scratch, so the built-in music and effects are original, with no samples or licences, and no copyright claims on X, TikTok, Instagram or YouTube.

## What the user can choose
| Choice | What happens |
|---|---|
| **No added sound** | The current pipeline: their voice (or the AI voice) only. |
| **Built-in music** | An original bed in one of three moods (below), ducked under the voice and resolving on the end card. |
| **Sound effects** | Whooshes, taps, typing, pops, chimes and so on, timed automatically to the animation. |
| **Their own track** | They upload an audio or video file, and it's mixed under the voice with the same ducking. It loops with a crossfade if it's too short, and fades out at the end. They can pick a start point. Remind them that they need the rights to it, and that platforms may mute or claim copyrighted music. |

Music (built-in or their own) and effects combine freely.

Moods (`python3 -I sound.py list`):
- `calm` (84 BPM): soft pads, gentle plucks and a light shaker. Good for explainers, tutorials and trust.
- `upbeat` (112 BPM): a four-on-the-floor pulse with claps and fast arps. Good for launches, hype and drops.
- `minimal` (92 BPM): sparse felt-piano notes, a warm sub and soft ticks. Good for premium or voice-first videos.

Suggest a mood in the storyboard from the product's tone, and let the user change it. Tonal effects (blip, success, chime, shimmer) are tuned to the chosen mood's key. With their own track or no music, they use `calm`'s key, or `--key-of` to pick another.

## Pipeline
Render the video **silent** first (`vsilent.mp4`), so sound can be changed later without re-rendering.

1. **Cue sheet** (effects only): `python3 -I $KIT/tools/sound.py cues content.json --template motion|ugc --duration D --end E --out sfx.json`. With lockup captions, add `--words words.json`: each word in `lockups.boom` gets a `boom` (a deep sub-bass hit, up to `lockups.booms`, default 8), and other big words get a short `thump`, at most one every 2.5s. Both sit below the voice's range, but still check the mix by transcribing it.
   - `E` is when the end card starts: `endAt` for motion, or the clip length (plus `endGap`) for ugc.
   - It prints a count per effect. Read `sfx.json` and trim anything that would be busy: for example, drop key ticks if the typing is very fast, or a whoosh fighting a strong spoken word.
   - Custom scenes need hand-written cues: `{"t": 3.8, "sfx": "whoosh"}`, with optional `gain` (0–1.5), `dur` (whoosh, riser, shimmer) and `pan` (−1 to 1).
2. **Make the stems:** `python3 -I $KIT/tools/sound.py make --duration D --end E --mood calm|upbeat|minimal|none [--sfx sfx.json] --out-dir snd`. This takes about 5–10 seconds per 15 seconds of video.
3. **Mix and mux:** `python3 -I $KIT/tools/sound.py mix --video vsilent.mp4 --duration D --out final.mp4 --voice clip.mp4 --voice-kind own [--music snd/music.wav | --music their_track.mp3 --music-start 12] [--sfx snd/sfx.wav]`.
   - Use `--voice-kind ai` with `vo.wav`.
   - It cleans the voice, measures true loudness (EBU R128), sets the music 22 LU under the voice and ducks it a further 10 dB while someone speaks, keeps the loudest effect 8 LU under the voice, places the effects, and normalises to −16 LUFS with a two-pass loudnorm. The video stream is copied untouched.
   - Make the 1080 copy from `final.mp4` as usual.
   - Levels: `--music-level` (default −22, use −18 for a louder bed and −26 for a barely-there one), `--duck` (default 10) and `--sfx-level` (default −8). It prints the result, for example `music_lu_under_voice: -28.8`. The voice must always be clearly on top, so if the user says the music or effects feel loud, lower them 3–4 dB at a time and re-mix.
4. **Verify:** run the transcript check on the final file (`asr.py final.mp4 chk`). Every line must still come through. If the music masks words, lower `--music-level` or raise `--duck`. Check that loudness is about −16 LUFS.

## Storyboard
When sound is on, add a **Sound** column (for example "whoosh in", "tap + passkey blip", "chime on logo"), and name the mood or "your track".

## Changes after delivery
Changing the mood, levels, effects or track only needs steps 2–3 on the kept silent `vsilent.mp4`, which takes seconds and needs no re-render. Removing sound means muxing the plain voice again.
