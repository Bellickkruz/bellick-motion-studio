# Bellick Motion Studio

Turn talking-head clips and scripts into branded motion-design videos, for any creator and any product.

## What it does
- **Brand setup:** pull colours from a logo, then mix the brand in the interactive **Brand Studio**. It has a colour wheel, matching colours, readability checks, 14 fonts and a live preview. The brand is saved as a reusable brand pack.
- **Product setup:** researches the product being promoted and records facts, safe claims, claims to avoid, logo rules and the #ad disclosure, so videos stay accurate.
- **Captions & graphics:** upload a clip; it's transcribed, you confirm the words, and it gets word-timed kinetic captions, animated callout cards and a branded end card.
- **Full motion design:** turns a clip's transcript or a script into a fully animated video from a scene library (3D gem, logo dive, flow, feature cards, counter, phone with approval sheet, before/after, checklist, kinetic statement).
- **Voice & export:** optional AI voiceover (checked by transcribing it back), and 4K + 1080 exports that match the original video's shape (vertical, landscape, square or 4:5).

## How to use
Say "Bellick Motion Studio" or "make a branded video from this clip" in Claude. The first time, it walks you through brand and product setup. Next time, upload your brand and product packs to skip setup.

## Requirements
- A paid Claude plan with code execution and file creation enabled.
- The first transcription or AI voice in a chat downloads about 1GB of open-source models from GitHub (Whisper small.en, Kokoro). If GitHub downloads are blocked, paste a transcript and use your own voice.
- English transcription and voice only.

## What's inside
- `skills/`: bellick-motion-studio (start here), brand-setup, product-setup, make-video
- `kit/templates/`: `ugc` and `motion` templates and the shared brand runtime
- `kit/tools/`: transcription, word timing, palette extraction, ratio matching, page build, render, voice and mix
- `kit/studio/brand-studio.html`: the Brand Studio page
- `kit/fonts/`: 14 open-licence font families (OFL licences included)
- `kit/examples/bellick-kruz-paybox/`: the preloaded example brand, product and video

Created by Bellick Kruz.
