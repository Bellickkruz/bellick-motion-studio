---
name: product-setup
description: Researches and records the product a creator promotes (facts, safe claims, claims to avoid, logo rules, tagline, disclosure) so Bellick Motion Studio videos stay accurate. Use when a user names a product, brand deal or sponsor they're making content for, or wants to update what a video may claim about it.
---

# Product setup

Goal: a reviewed `product.json` that keeps every on-screen claim accurate. `KIT` is the plugin's `kit` folder, two levels above this skill's base directory.

## Steps
1. **Ask** for the product name, its website, its logo (and whether the logo may be recoloured or must stay as supplied), the tagline or core message the creator wants, and the paid-promotion disclosure their deal requires (for example `#ad` or `Paid partnership`). Ask in one message.
2. **Research** the product on the web: what it does, launch dates, key features, limits, and which regions or platforms it supports. Prefer the maker's own pages and reputable coverage, and keep the source links. If a connector for the product is available in the session, use it to check live facts (for example supported tokens or plans).
3. **Draft** these fields:
   - `facts`: short, verifiable statements, each one checked.
   - `safe_claims`: lines the video can show on screen.
   - `avoid_claims`: overstatements to never show (for example "best price", "guaranteed", "instant", "every user", or a feature that isn't confirmed).
   - `keywords`: words to highlight in captions.
   - `footnote`: a short on-screen qualifier, when the visuals simplify how the product works (for example "Illustrative flow").
4. **Review with the user.** Show the facts and claims in plain language, and list anything you couldn't confirm. They approve or edit the list.
5. **Write `product.json`** (see `$KIT/examples/bellick-kruz-paybox/product.json`):
   ```json
   {"name":"…","maker":"…","logo":"logo.png","logo_style":"tile|plain","logo_rule":"…","url":"…","tagline":"…","one_liner":"…",
    "disclosure":"#ad","footnote":"…","keywords":["…"],"facts":["…"],"safe_claims":["…"],"avoid_claims":["…"],"sources":["…"],"checked":"YYYY-MM-DD"}
   ```
   - `logo_style: "tile"` shows the logo in a rounded square with a light sheen, like an app icon. Use `plain` for wordmarks and transparent logos.
   - The video engine never recolours the logo.
6. **Hand back a product pack:** zip `product.json` and the logo as `product-pack-<name>.zip`, and tell the user to re-upload it in future chats. Facts go stale, so re-check them when `checked` is more than about a month old.
