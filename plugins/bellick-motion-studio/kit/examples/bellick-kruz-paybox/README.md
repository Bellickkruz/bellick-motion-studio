# Example: Bellick Kruz × PayBox

A complete Bellick Motion Studio setup, preloaded so new users can see what the plugin makes.

- `brand.json` + `avatar.png`: Bellick Kruz's brand. Cream background, purple palette, Poppins; never green, mint, teal or coral.
- `product.json` + `paybox_tile.png`: PayBox by MoonPay. Verified facts (checked 21 Oct 2026), safe claims, claims to avoid, and #ad disclosure. The logo stays in its original black and white.
- `example-video-landscape.mp4`: the showcase video. Bellick's clip with word-timed captions, swap cards, an approval tap and the PayBox end card.
  - Note: it was made before the "export matches the original's shape" rule (the source clip is vertical). New videos keep the original's shape.
  - Note: it says "swap from BNB to SOL". BNB swap support in PayBox was not confirmed when this example was made.
- `custom-templates/`: two bespoke pieces made for this brand (16:9 explainer; 9:16 full motion design). They're standalone pages: open one and call `render(t)`, or render with `tools/render.py` after injecting words (`motion-9x16.html` has a `__WORDS__` placeholder; use `motion-9x16.words.json`).
