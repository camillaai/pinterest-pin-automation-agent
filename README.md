# Pinterest Pin Automator

Turn this week's Wix blog posts into Pinterest pins automatically.

Built for the AI Agents for Founders Challenge (HETIC 2026, deadline Dec 18, 2026, online). It is a real workflow, not a demo idea: Jinyi publishes Shopdeals posts on Wix every week, then makes a vertical pin for each one by hand. This agent does that step.

## Connected accounts

- **Wix blog (source):** [Shopdeals on Wix](https://shoponlinedeals.wixsite.com/2023)
- **Pinterest (destination):** [@janeluocbrealty](https://www.pinterest.com/janeluocbrealty/)
  - [Baby Best Buys](https://www.pinterest.com/janeluocbrealty/baby-best-buys/)
  - [Coupons & Cash Back](https://www.pinterest.com/janeluocbrealty/coupons-cash-back/)

Pins link back to their own Wix post, never to the homepage.

## What it does

1. Pulls recent Wix posts (Shopdeals)
2. Skips posts already pinned, using `data/seen.json`
3. For each new post, makes a vertical 1000x1500 pin image with text overlay
4. Writes a Pinterest title, description, hook, tags, CTA and board
5. Links the pin back to its own Wix post, never to the homepage
6. Dry-run by default. It does not post to Pinterest without a token.

## This week's demo input (real posts, verified Nov 25, 2026)

- Baby Gear Black Friday Deals 2026: Strollers, Car Seats & More
  https://shoponlinedeals.wixsite.com/2023/post/baby-gear-black-friday-deals-2026-strollers-car-seats-more
  Published 2026-11-25. Board: Baby Best Buys.
- Temu Games 2026: Play Farmland, Fishland & More to Get FREE Stuff
  https://shoponlinedeals.wixsite.com/2023/post/temu-games-2026-free-stuff
  Published 2026-11-25. Board: Coupons & Cash Back.

These two were manually pinned on Nov 25, 2026, so the demo uses `--force` to replay them. In a normal run they would be skipped as already pinned.

## Run it

```bash
pip install -r requirements.txt
python3 pin_automator.py --force
```

Output:

- `pins/baby-gear-black-friday-deals-2026-strollers-car-seats-more.png` (1000x1500)
- `pins/temu-games-2026-free-stuff.png` (1000x1500)
- `pins.json` - title, description, tags, board, link and image for each pin

Check a pin before posting:

```bash
python3 pin_automator.py --force --dry-run
```

## Fetch fresh posts from Wix

Set these, then run with `--fetch-wix`:

```bash
export WIX_API_KEY="your-wix-api-key"
export WIX_SITE_ID="your-wix-site-id"
python3 pin_automator.py --fetch-wix --days 7
```

Without them, it uses `data/week-posts.json`.

## Posting to Pinterest

Pinterest posting needs a Pinterest API access token with pin write access. That is a separate approval in the Pinterest developer account, so this repo does not post by itself yet.

```bash
export PINTEREST_ACCESS_TOKEN="..."
python3 pin_automator.py --post
```

Without a token, `--post` stops and tells you to post the generated `pins/*.png` files in the Pinterest browser flow, with the title, description and link from `pins.json`. That is the current manual step this agent is built to replace once the token is approved.

## Files

- `pin_automator.py` - the agent: fetch, dedup, pin image, copy, manifest
- `data/week-posts.json` - this week's real Wix posts
- `data/seen.json` - slugs already pinned, to skip
- `pins/` - generated pin images (local only, gitignored)
- `pins.json` - generated manifest (local only, gitignored)

## Hackathon fit

AI Agents for Founders: an agent that gives a solo founder back time. One command turns a week of posts into ready-to-post pins, with the same rules she already uses: vertical 1000x1500, text overlay, hook + CTA, tags, and a link back to the article.
