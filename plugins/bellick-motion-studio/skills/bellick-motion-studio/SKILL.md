---
name: bellick-motion-studio
description: Entry point for Bellick Motion Studio, a branded video maker for creators. Use when someone says "Bellick Motion Studio" or "Motion Studio", wants to make a branded video, add captions, motion graphics, music or sound effects to a clip, turn a script into an animated video, set up their brand or the product they promote, or asks what Bellick Motion Studio can do.
---

# Bellick Motion Studio

Bellick Motion Studio turns a creator's talking-head clips and scripts into finished, branded motion-design videos. It handles transcription, captions, animated graphics, optional AI voiceover, optional music and sound effects (original built-in sounds or the creator's own track) and an export in the quality the creator picks (preview, Full HD or 4K), in the creator's own brand, for any product they promote.

## Locate the kit
The tools, templates, fonts and examples live in the plugin's `kit` folder, two levels above this skill's base directory (`<base>/../../kit`). Set `KIT` to that absolute path for every command. Work in a fresh folder under the working directory (for example `./ms-job-<name>`). Never write inside `KIT`.

## Guided setup: one step at a time
Every new video starts with a short guided setup. Ask **one step per message**, wait for the answer, confirm it in one line, then move to the next step. Never bundle several steps' questions into one message.

Open each step with a header and a progress line, then the step's question (use AskUserQuestion when it's available, otherwise a numbered list):

> **Step 3 of 8 · Your product**
> ✓ Video · ✓ Brand · ● Product · ○ Style · ○ Voice · ○ Music · ○ Effects · ○ Quality

| # | Step | What to ask | Done automatically when |
|---|---|---|---|
| 1 | **Video** | "Drop your clip, or paste your script." Note its length and shape. | They already sent a clip or script |
| 2 | **Brand** | Run the **brand-setup** skill (its own questions all belong to this step) | A brand pack or `brand.json` is already in the chat |
| 3 | **Product** | Run the **product-setup** skill, or offer "Skip: this video doesn't promote a product" | A product pack is in the chat, or they said it promotes nothing |
| 4 | **Style & look** | Full motion design, graphics over footage, or mixed cuts; then the look: Soft, Bold, Editorial, Glass, or Surprise me (details in make-video) | Script with no clip: only Full motion design fits, so tick it and say why |
| 5 | **Voice** | Their own recorded voice, or an AI voice (calm female or steady male, English only) | Their clip already has them speaking: "✓ Voice: yours, from the clip" |
| 6 | **Music** | No music (first), built-in music (calm, upbeat or minimal), or their own track | A brand pack says they always want none |
| 7 | **Effects** | No sound effects (first), or add sound effects | Same as Music |
| 8 | **Quality** | Fast preview 720p, Full HD, 4K, or 4K + Full HD, each with a rough time (see make-video) | They already named a quality |

Rules:
- **Skip, don't re-ask.** When a step is already settled, show it ticked with the answer (for example "✓ Brand: loaded from your pack") and go straight on to the next open step in the same message.
- **Short.** Each step message is the header, the progress line, one sentence of context and the question. Mark no option as recommended in steps 6–8.
- **If the user answers several steps at once,** accept them all, tick them, and continue from the first open step.
- **If they're away or say "just go",** use the defaults (no music, no effects, 4K + Full HD) and list them in the summary.
- **After step 8, send a summary** of all eight choices in one compact list, then move into production. Production has its own approval gates (transcript, storyboard, "start", stills), and those messages can carry a matching progress line: `✓ Setup · ● Transcript · ○ Storyboard · ○ Stills · ○ Render`.
- Returning users with a brand pack typically see steps 1–3 ticked and answer only the rest.

Users keep their setup between chats as **brand packs**: zips holding `brand.json` or `product.json` plus their images. When a user uploads a pack, unzip it into the job folder and tick steps 2 and 3.

## Route the request
- A new video, a script, a narration or a re-export: run the guided setup above, then the **make-video** skill.
- Only setting up or changing a brand: **brand-setup**. Only a product: **product-setup**. These run as one-off tasks, outside the steps.
- If the user only wants to see what the plugin does, offer the preloaded example (see below).

## The preloaded example
`KIT/examples/bellick-kruz-paybox/` holds a complete working setup: brand (Bellick Kruz: cream background, purple palette, Poppins, avatar), product (PayBox by MoonPay, with verified facts, safe claims and claims to avoid), a finished example video (`example-video-landscape.mp4`), and two custom templates made for that brand. Use it to:
- show new users what Bellick Motion Studio makes (send the example video);
- run a demo render in the example brand;
- copy its structure when writing new brand and product files.

It's an example. Never apply its brand or product to another user's video unless they ask.

## Ground rules for every job
- **Guided steps.** Setup questions come one at a time as numbered steps (see above).
- **Approval gates.** Confirm the transcript, then the storyboard, and **build only after the user says "start"** (or clearly approves). Rendering takes minutes, so get the direction right first.
- **The export matches the original video's shape.** A video made from a clip uses the clip's aspect ratio exactly (`tools/ratio.py`). For a script with no video, ask which shape they want (vertical 9:16, landscape 16:9, square 1:1, or 4:5), defaulting to 9:16.
- **Their brand, exactly.** Use only the brand's colours and fonts. Never use colours listed in `avoid_colors`. Never recolour the product logo when `logo_rule` says so.
- **Accuracy.** On-screen claims must stay within the product's `facts` and `safe_claims`, and must never use its `avoid_claims`. Flag risky claims in the user's own script, but leave their spoken words as they said them.
- **Disclosure.** When the product file has a `disclosure` (for example `#ad`), the end card shows it. Remind the user that the post text needs it too.
- **Sound is opt-in.** Music and sound effects are added only when the user picks them for that video. "No added sound" is always offered and is the default.
- **Plain language.** Talk about videos, brands, captions and scenes. Don't mention file paths or JSON unless the user asks.

## Requirements to tell users about when relevant
- Code execution and file creation must be enabled in their Claude settings.
- The first transcription or AI voice in a chat downloads about 1GB of models from GitHub (about 2 minutes) using `KIT/tools/setup.sh`. If their workspace blocks GitHub downloads, they can paste their transcript instead and supply their own voice recording.
- Transcription and AI voice are English only.
- Exports come in three qualities: a fast 720p preview, Full HD or 4K. Before rendering, the plugin measures this workspace's speed and shows the time each one will take. As a rough guide, a 15-second video takes about 1–2 minutes as a preview, 3–4 in Full HD and 8–10 in 4K.
