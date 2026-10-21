---
name: brand-setup
description: Sets up a creator's brand for Bellick Motion Studio videos from their logo, colours and fonts, including an interactive colour-wheel Brand Studio page. Use when a user wants to set up, change or check their brand, colours, fonts, logo or avatar for Bellick Motion Studio, or uploads a logo for that purpose.
---

# Brand setup

Goal: a `brand.json` describing the creator's look (colours by role, fonts, shape, credit line, avatar, colours to avoid) that every Bellick Motion Studio video uses. `KIT` is the plugin's `kit` folder, two levels above this skill's base directory.

## Steps
1. **Collect** the creator's name (or handle), their avatar or profile image (optional; used small beside the credit), their logo (optional), any brand colours or fonts they already have, and colours they never want. Ask in one short message, and accept whatever they have.
2. **Pull colours from the logo** when one is provided: `python3 -I $KIT/tools/palette.py <logo> palette.json`. It returns the logo's main colours and a proposed palette by role, with contrast checks. If the user named exact colours, those win.
3. **Open the Brand Studio** so the user can mix the brand themselves:
   - Copy `$KIT/studio/brand-studio.html` into the job folder.
   - Replace the JSON inside `<script type="application/json" id="prefill">` with: `{"example": false, "brand": {name, credit, colors, font, style, avoid_colors}, "logo_swatches": [hex…], "product": {"name": …, "tagline": …}}`. Fill it from the user's answers and the palette proposal; use the product they promote if known.
   - Publish it as an artifact (icon: `palette`). If artifacts aren't available, send the HTML file instead and tell them to open it in a browser.
   - Tell them: pick a role, use the colour wheel, the matching-colour chips or the logo swatches, watch the readability checks and the live preview, then press **Copy brand settings** and paste the result into the chat. The page also lets them upload a logo directly and choose from 14 bundled fonts.
4. **Read the pasted settings** (a block beginning `BELLICK MOTION STUDIO BRAND SETTINGS`), then validate:
   - text on background and on cards: contrast of 4.5 or more;
   - accent and muted text on background: contrast of 3 or more (the video engine darkens accent words automatically when needed, but warn if the accent is very light);
   - no role colour falls in an `avoid_colors` family;
   - fonts must be in `$KIT/fonts/fonts.json`, otherwise fall back to Poppins and say so.

   Report problems in one short list, and suggest a fix colour for each.
5. **Write `brand.json`** in this shape (see `$KIT/examples/bellick-kruz-paybox/brand.json`):
   ```json
   {"name": "…", "credit": "Created by …", "avatar": "avatar.png",
    "colors": {"background":"#…","text":"#…","primary":"#…","accent":"#…","soft":"#…","softer":"#…","surface":"#FFFFFF","muted":"#…"},
    "avoid_colors": ["…"], "font": {"heading":"Poppins","body":"Poppins"},
    "style": {"mood":"…","background":"glow|flat|grid","corner":40}, "rules": ["…"]}
   ```
   Image paths are relative to `brand.json`. Copy the avatar beside it as `avatar.png` (crop it square first).
6. **Proof it.** Render one still in the new brand so they can see it in motion: build the `motion` template with a two-scene sample content (`statement` + `cards`) and `KIT/examples/bellick-kruz-paybox/product.json` replaced by their product if known. Use the commands in the make-video skill.
7. **Hand back a brand pack:** zip `brand.json` and the images as `brand-pack-<name>.zip` and send it. Tell them to upload it at the start of future Bellick Motion Studio chats, because a new chat starts with nothing.

## Colour roles (what each one controls)
| Role | Used for |
|---|---|
| background | Canvas behind everything, and the end card |
| text | Headlines, captions, card titles |
| primary | 3D objects (the gem), token circles, icons |
| accent | Buttons, the active caption word, glowing lines, highlights |
| soft / softer | Glows, borders, faint fills |
| surface | Cards and phone screens |
| muted | Labels, small print, footnotes |
