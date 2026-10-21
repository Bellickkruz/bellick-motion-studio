# content.json schema

All times are in seconds on the video timeline. Colours, fonts and the logo come from the brand and product files, never from content.json.

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

Icons: check, arrow, spark, bolt, shield, clock, chart, chat, wallet, lock, user, globe, heart, star, key, search, cart, play.

### Storyboard patterns that work
- **Hook (0–2s):** a `statement` of the promise, or a `hero` waking up, or a `phone` already typing.
- **Into the product:** a `logo` with `out: "dive"`, then a `flow` or `cards` with `in: "flash"`.
- **Proof:** a `counter` or `compare`.
- **Action with user control:** a `phone` with a `sheet` and `freeze` over the waiting window.
- **Close:** the end card is automatic at `endAt`.
