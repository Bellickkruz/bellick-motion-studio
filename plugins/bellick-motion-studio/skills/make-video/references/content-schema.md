# content.json schema

All times are in seconds on the video timeline. Colours, fonts and the logo come from the brand and product files, never from content.json.

## Looks and variety (both templates)
Every video has a **look**, a full visual personality covering type, cards, captions, background and transitions. Each video also gets a **seed** that varies layout details: wipe and entry directions, background shapes, radar positions and so on. Two videos in the same look and brand still come out different.

| look | feel | captions | background | default scene transition |
|---|---|---|---|---|
| `soft` | Rounded cards, soft glows, gentle rises | Words flip up | Soft colour glows + particles | rise (direction varies) |
| `bold` | Heavy uppercase display type (Archivo), hard offset shadows, punchy | Words slam in, active word in an accent box | Big tilted colour blocks | slam + flash, hard cut out |
| `editorial` | Calm magazine feel, serif display (Fraunces), hairlines, italics on accent words | Words rise out of a mask, active word underlined | Paper lines + one outline circle | wipe (direction varies) |
| `glass` | Frosted translucent cards, colour orbs, depth | Captions in a frosted pill | Moving colour orbs + particles | blur in / blur out |

- `"look"` in content.json picks it (default: `brand.style.look`, else `soft`).
- `"seed"`: any integer. Omit it to derive one from the words, so a new video gets new variations automatically. Change it to reshuffle the variations without changing the look.
- `brand.style.lock_fonts: true` keeps the brand's own fonts in every look. `"displayFont"` picks a bundled font for display text.
- A scene's own `in` and `out` still override the look's transitions.

## Shared fields
```json
{
  "footnote": "Illustrative flow · …",        // optional small text (falls back to none)
  "keywords": ["AI", "approve"],              // extra caption words to highlight (product name is automatic)
  "captions": {"mode": "light|video", "y": 0.16, "size": 92, "off": false}  // optional overrides; y = fraction of height, size at 1080 scale
}
```

## Template `ugc` (captions & graphics on the user's footage)
Duration = clip length + 3.2s end card (set `endGap` to add a pause before the end card).
Layout adapts to shape: portrait puts captions mid-frame and callouts in the lower half; landscape puts captions in the lower third and callouts in a right-hand column; square puts callouts at the bottom.
```json
{
  "callouts": [
    {"type": "prompt", "t0": 0, "t1": 7.2, "slot": 0, "text": "Swap my BNB → SOL", "typeDur": 1.6, "sendAt": 2.4, "placeholder": "Ask your agent…", "label": "PROMPT"},
    {"type": "transform", "t0": 2.85, "t1": 11, "slot": 1, "from": "BNB", "to": "SOL", "label": "Prepared by your AI agent",
     "pulses": [[0, 4.44], [1, 5.43]], "compactAt": 7.25,
     "action": {"button": "Approve", "tapAt": 6.1, "result": "Submitted", "passkey": true}},
    {"type": "card", "t0": 3, "t1": 6, "slot": 2, "title": "Zero fees", "sub": "On your first 3 orders", "icon": "spark"},
    {"type": "stat", "t0": 6, "t1": 9, "slot": 1, "from": 0, "to": 2400, "prefix": "", "suffix": "+", "label": "creators onboard", "countDur": 1.2},
    {"type": "chip", "t0": 9, "t1": 10.5, "slot": 3, "text": "Available on iOS", "icon": "check"}
  ]
}
```
- `slot` sets the stacking order (lower slots sit higher). Visible callouts stack with a gap, so use `compactAt` on a transform card to shrink it when the next one arrives.
- `pulses`: `[token index, time]` makes a token bounce when it's spoken.
- `→` in prompt text renders as a drawn arrow.
- `action.passkey` shows a key ring after the tap. Only use it if the product really uses a passkey for that action.

## Template `motion` (full motion design)
```json
{
  "duration": 15.5, "endAt": 12.4,           // the end card starts at endAt (default duration-3.2)
  "freeze": [[7.4, 10.9]],                   // ambient particles stop during these windows (the "waiting for you" pause)
  "scenes": [ {"type": "…", "t0": 0, "t1": 2.2, "in": "fade|rise|zoom|flip|flash", "out": "fade|zoom|dive", "...params"} ]
}
```
Scene times are absolute. Inside a scene, any `at` value is relative to that scene's `t0`. Leave about 0.05s between scenes. `out: "dive"` zooms the scene ×14 into a white flash, and the next scene should use `in: "flash"`. `diveOrigin: [x, y]` (as fractions) sets the dive point.

| type | what it shows | params |
|---|---|---|
| `hero` | Faceted 3D gem in brand colours, orbit ring, glow, status chip; blooms open on entry | `label`, `states: [{at, text}]`, `spin` (default .6), `bloom` (true), `dim: [from, to]` (greys and freezes it; use it for "waiting") |
| `logo` | Product logo with sheen and pulse rings; optional name | `name: true|"text"`, `size` (.42) — pair with `out: "dive"` to fly *into* the product |
| `flow` | 2–4 nodes on a glowing path with travelling pulses; vertical zigzag in portrait, horizontal in landscape | `nodes: [{label, icon}]`, `active: [{at, node}]` |
| `cards` | Up to 4 feature cards flipping in with a glow | `items: [{title, sub, icon, at?}]`, `stagger` (.45) |
| `counter` | Big number counting up inside a progress ring | `from`, `to`, `prefix`, `suffix`, `decimals`, `label`, `countDur`, `ring` (0–1) |
| `phone` | Phone with prompt typing, sent bubble, replies, and a review sheet with status pills, buttons, cursor tap and passkey ring | `prompt`, `typeAt`, `sendAt`, `placeholder`, `replies: [{at, text}]`, `sheet: {at, title, by, rows: [[k, v]], status: [{at, text, style: wait|ok|done}], buttons: [ghost, primary], buttonsAt, hoverDecline, tapAt, passkey, passkeyText}` |
| `compare` | Before (greyed) vs after (brand, glowing) cards; side by side in landscape, stacked in portrait | `before: {title, lines}`, `after: {title, lines}`, `switchAt` |
| `checklist` | Items ticking in one by one | `title`, `items`, `stagger` |
| `statement` | Huge kinetic headline, word by word | `text`, `accent: [words]`, `size` |
| `footage` | The creator's own video, synced to the timeline (mixed cuts); needs `--frames` at build | `style: "full"` (full-frame, captions switch to on-video style automatically) or `"card"` (framed card over the brand background, with gentle breathing), `label` (chip above a card) |

### Mixed cuts example (portrait clip, 10.9s of speech)
```json
{"duration": 14.3, "endAt": 11.1, "scenes": [
  {"type": "footage", "t0": 0, "t1": 2.2, "style": "full", "out": "zoom"},
  {"type": "logo", "t0": 2.25, "t1": 3.05, "name": true, "in": "zoom", "out": "dive"},
  {"type": "flow", "t0": 3.1, "t1": 5.35, "in": "flash", "nodes": [{"label": "Market A", "icon": "chart"}, {"label": "Route selected", "icon": "check"}]},
  {"type": "phone", "t0": 5.4, "t1": 8.65, "prompt": "Swap USDC → SOL", "sendAt": 0.3, "sheet": {"at": 0.4, "title": "Review request", "buttons": ["Decline", "Approve"]}},
  {"type": "footage", "t0": 8.7, "t1": 11.0, "style": "card", "label": "Your call", "in": "zoom"}
]}
```
A scene starting at 0 is fully visible on frame 1. Captions use `captions.videoY` and `videoSize` over footage, and `y` and `size` over animation.

### Scenes added in v0.6
| type | what it shows | params |
|---|---|---|
| `podium` | Prize/ranking podium, 2–1–3, columns rise on cue; optional row of extra chips | `title`, `places: [{amount, label?, at}]` (1st first), `extras: {label, count, value, at, stagger}` |
| `radar` | Radar sweep that pings items, then shrinks to a compared list with bars and a result chip | `items: [{label, at, value?0-1}]`, `listAt`, `listTitle`, `result: {text, at}` |
| `screen` | The user's own **screen recording** playing inside a clean window frame | `src` (folder of `s0001.jpg…`, relative to content.json), `aspect` (width/height of the crop), `title` (window bar text), `start`, `dark` (default true), `chip: {text, at, icon}` |
| `series` | Fan of numbered video thumbnails ("01/13"), for announcing a series | `title` (may contain `<br>`), `sub`, `total`, `stagger`, `chip: {text, at, icon}` |

Upgrades to existing scenes:
- `counter`: `dots` draws N winner or item dots popping around the ring, and `badge` adds a chip above it.
- `footage`: `punch: [at, scale]` is a quick punch-in zoom for an emphatic line.

**Screen recordings: privacy first.** Before extracting frames, look at a frame and crop out anything personal: email addresses, balances, wallet addresses, names, notifications. The crop goes in the ffmpeg command, which also sets the playback speed (here 11s of recording, played back over the scene):
`ffmpeg -ss 1 -i rec.mov -t 11 -vf "fps=12.5,crop=W:H:X:Y" -q:v 2 scr/s%04d.jpg`, then set `aspect` to W/H. Frames play back at 30fps from `start`, so pick the extraction fps to fit the scene length.

### Overlays (any template)
Chips and buttons that sit on top of whatever is on screen, including full-frame footage:
```json
"overlays": [
  {"type": "chip", "t0": 0.45, "t1": 3.0, "y": 0.07, "logo": true, "text": "PayBox Hackathon", "sub": "Winners announced · Fri 23 Oct"},
  {"type": "chip", "t0": 7.5, "t1": 8.3, "y": 0.07, "icon": "search", "text": "Market Radar", "sub": "My build"},
  {"type": "button", "t0": 51.2, "t1": 52.7, "y": 0.85, "icon": "user", "text": "Follow", "tapAt": 51.75, "tapText": "Following"},
  {"type": "button", "t0": 53.0, "t1": 55.3, "y": 0.85, "light": true, "icon": "arrow", "text": "Share"}
]
```
`y` is a fraction of the height. Keep overlays clear of the captions (on footage, captions sit around `captions.videoY`) and of the face.

Icons: check, arrow, spark, bolt, shield, clock, chart, chat, wallet, lock, user, globe, heart, star, key, search, cart, play.

### Storyboard patterns that work
- **Hook (0–2s):** a `statement` of the promise, or a `hero` waking up, or a `phone` already typing.
- **Into the product:** a `logo` with `out: "dive"`, then a `flow` or `cards` with `in: "flash"`.
- **Proof:** a `counter` or `compare`.
- **Action with user control:** a `phone` with a `sheet` and `freeze` over the waiting window.
- **Close:** the end card is automatic at `endAt`.
