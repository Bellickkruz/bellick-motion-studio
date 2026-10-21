---
name: bellick-motion-studio
description: Entry point for Bellick Motion Studio, a branded video maker for creators. Use when someone says "Bellick Motion Studio" or "Motion Studio", wants to make a branded video, add captions or motion graphics to a clip, turn a script into an animated video, set up their brand or the product they promote, or asks what Bellick Motion Studio can do.
---

# Bellick Motion Studio

Bellick Motion Studio turns a creator's talking-head clips and scripts into finished, branded motion-design videos. It handles transcription, captions, animated graphics, optional AI voiceover and a 4K export, in the creator's own brand, for any product they promote.

## Locate the kit
The tools, templates, fonts and examples live in the plugin's `kit` folder, two levels above this skill's base directory (`<base>/../../kit`). Set `KIT` to that absolute path for every command. Work in a fresh folder under the working directory (for example `./ms-job-<name>`). Never write inside `KIT`.

## Route the request
1. **No brand on file in this chat** (no `brand.json` uploaded or created yet): run the **brand-setup** skill first. If the user only wants to see what the plugin does, offer the preloaded example (see below).
2. **No product on file** (no `product.json`): run the **product-setup** skill. Skip this only for videos that promote nothing.
3. **Brand and product ready**: run the **make-video** skill for a video, or for a script, a narration or an export.

Users keep their setup between chats as **brand packs**: zips holding `brand.json` or `product.json` plus their images. When a user uploads a pack, unzip it into the job folder and continue straight to make-video.

## The preloaded example
`KIT/examples/bellick-kruz-paybox/` holds a complete working setup: brand (Bellick Kruz: cream background, purple palette, Poppins, avatar), product (PayBox by MoonPay, with verified facts, safe claims and claims to avoid), a finished example video (`example-video-landscape.mp4`), and two custom templates made for that brand. Use it to:
- show new users what Bellick Motion Studio makes (send the example video);
- run a demo render in the example brand;
- copy its structure when writing new brand and product files.

It's an example. Never apply its brand or product to another user's video unless they ask.

## Ground rules for every job
- **Approval gates.** Confirm the transcript, then the storyboard, and **build only after the user says "start"** (or clearly approves). Rendering takes minutes, so get the direction right first.
- **The export matches the original video's shape.** A video made from a clip uses the clip's aspect ratio exactly (`tools/ratio.py`). For a script with no video, ask which shape they want (vertical 9:16, landscape 16:9, square 1:1, or 4:5), defaulting to 9:16.
- **Their brand, exactly.** Use only the brand's colours and fonts. Never use colours listed in `avoid_colors`. Never recolour the product logo when `logo_rule` says so.
- **Accuracy.** On-screen claims must stay within the product's `facts` and `safe_claims`, and must never use its `avoid_claims`. Flag risky claims in the user's own script, but leave their spoken words as they said them.
- **Disclosure.** When the product file has a `disclosure` (for example `#ad`), the end card shows it. Remind the user that the post text needs it too.
- **Plain language.** Talk about videos, brands, captions and scenes. Don't mention file paths or JSON unless the user asks.

## Requirements to tell users about when relevant
- Code execution and file creation must be enabled in their Claude settings.
- The first transcription or AI voice in a chat downloads about 1GB of models from GitHub (about 2 minutes) using `KIT/tools/setup.sh`. If their workspace blocks GitHub downloads, they can paste their transcript instead and supply their own voice recording.
- Transcription and AI voice are English only.
- A 15-second 4K render takes about 5–10 minutes.
