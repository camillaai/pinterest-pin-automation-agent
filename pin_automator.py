#!/usr/bin/env python3
"""Pinterest Pin Automator: turn this week's Wix posts into Pinterest pins.

Rules, from the owner's standing workflow:
- vertical pin, 1000x1500, text overlay
- hook + CTA, tags, link back to its own Wix post
- skip anything already pinned (data/seen.json)
- dry-run by default, no Pinterest post without a token
"""
import argparse
import json
import os
import textwrap
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
DATA = BASE / "data" / "week-posts.json"
SEEN = BASE / "data" / "seen.json"
OUT_DIR = BASE / "pins"
MANIFEST = BASE / "pins.json"
WIX_SITE_ID = os.environ.get("WIX_SITE_ID", "")

# Soft pastel palette for baby-friendly pins, dark text panel for readability.
BG_TOP = (255, 241, 242)
BG_BOTTOM = (224, 242, 254)
PANEL = (255, 255, 255)
TITLE_COLOR = (31, 41, 55)
HOOK_COLOR = (190, 24, 93)
BADGE_BG = (220, 38, 38)
BADGE_FG = (255, 255, 255)


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def fetch_wix_posts(days=7):
    """Fetch recent Wix blog posts. Needs WIX_API_KEY. Returns [] if unset."""
    key = os.environ.get("WIX_API_KEY")
    if not key:
        print("No WIX_API_KEY set, using data/week-posts.json instead.")
        return load_json(DATA, [])
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp = requests.post(
        "https://www.wixapis.com/blog/v3/posts/query",
        headers={"Authorization": key, "wix-site-id": WIX_SITE_ID},
        json={"query": {"sort": [{"fieldName": "firstPublishedDate", "order": "DESC"}],
                      "paging": {"limit": 20}}},
        timeout=30,
    )
    resp.raise_for_status()
    posts = []
    for p in resp.json().get("posts", []):
        if p.get("firstPublishedDate", "") < since:
            continue
        slug = p["slug"]
        posts.append({
            "id": p["id"],
            "title": p["title"],
            "slug": slug,
            "url": f"https://shoponlinedeals.wixsite.com/2023/post/{slug}",
            "excerpt": p.get("excerpt", ""),
            "firstPublishedDate": p.get("firstPublishedDate", ""),
            "cover_image": (p.get("media", {}).get("wixMedia", {}).get("image", {}) or {}).get("url", ""),
            "hook": "",
            "badge": "",
            "board": "Coupons & Cash Back",
            "tags": [],
        })
    return posts


def make_pin(post, out_path):
    """Make a 1000x1500 pin: cover image on top, text panel below."""
    width, height = 1000, 1500
    img = Image.new("RGB", (width, height), BG_TOP)
    draw = ImageDraw.Draw(img)

    # Pastel gradient background
    for y in range(height):
        t = y / height
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Cover image, top 820px, cropped to fill
    cover_url = post.get("cover_image", "")
    if cover_url:
        try:
            r = requests.get(cover_url, timeout=20)
            r.raise_for_status()
            cover = Image.open(BytesIO(r.content)).convert("RGB")
            # center crop to 1000x820
            cw, ch = cover.size
            target = 1000 / 820
            if cw / ch > target:
                nw = int(ch * target)
                x0 = (cw - nw) // 2
                cover = cover.crop((x0, 0, x0 + nw, ch))
            else:
                nh = int(cw / target)
                y0 = (ch - nh) // 2
                cover = cover.crop((0, y0, cw, y0 + nh))
            cover = cover.resize((1000, 820))
            img.paste(cover, (0, 0))
        except Exception as e:
            print(f"  cover image failed ({e}), using pastel background")

    # White text panel
    draw.rounded_rectangle([(40, 860), (960, 1460)], radius=36, fill=PANEL)

    def font(size, bold=True):
        for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                     "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"]:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    y = 900
    badge = post.get("badge", "")
    if badge:
        draw.rounded_rectangle([(70, y), (70 + 34 + len(badge) * 17, y + 56)], radius=28, fill=BADGE_BG)
        draw.text((88, y + 12), badge, font=font(28), fill=BADGE_FG)
        y += 80

    title = post["title"]
    for line in textwrap.wrap(title, width=28)[:4]:
        draw.text((70, y), line, font=font(52), fill=TITLE_COLOR)
        y += 66

    hook = post.get("hook", "")
    if hook:
        y += 12
        for line in textwrap.wrap(hook, width=36)[:2]:
            draw.text((70, y), line, font=font(32), fill=HOOK_COLOR)
            y += 44

    draw.text((70, 1380), "Tap to read the full guide  >", font=font(28, bold=False), fill=(107, 114, 128))
    img.save(out_path)
    return out_path


def build_copy(post):
    title = post["title"]
    hook = post.get("hook", "") or post.get("excerpt", "")
    desc = f"{hook}. Read the full guide: {post['url']}"
    return {
        "title": title,
        "description": desc,
        "tags": post.get("tags", []),
        "board": post.get("board", "Coupons & Cash Back"),
        "link": post["url"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-wix", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--force", action="store_true", help="replay posts already in seen.json (demo)")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--post", action="store_true", help="post to Pinterest, needs PINTEREST_ACCESS_TOKEN")
    args = ap.parse_args()

    posts = fetch_wix_posts(args.days) if args.fetch_wix else load_json(DATA, [])
    seen = set(load_json(SEEN, []))
    print(f"Found {len(posts)} posts, {len(seen)} already pinned.")

    if args.post and not os.environ.get("PINTEREST_ACCESS_TOKEN"):
        print("No PINTEREST_ACCESS_TOKEN set. Stopping before posting.")
        print("Generated pins are in pins/, with copy in pins.json.")
        print("Post them in the Pinterest browser flow until the API token is approved.")
        # still generate, then stop before the post step
        args.post = False

    OUT_DIR.mkdir(exist_ok=True)
    manifest = []
    made = skipped = 0
    for post in posts:
        slug = post["slug"]
        if slug in seen and not args.force:
            print(f"Skip (already pinned): {slug}")
            skipped += 1
            continue
        copy = build_copy(post)
        out_path = OUT_DIR / f"{slug}.png"
        make_pin(post, out_path)
        print(f"Made: {out_path}  1000x1500  board={copy['board']}")
        manifest.append({**copy, "slug": slug, "image": str(out_path), "status": "dry-run"})
        made += 1

    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"Done: {made} made, {skipped} skipped. Manifest: {MANIFEST}")
    if args.post:
        print("Posting step is not wired to a live Pinterest token in this prototype.")
        print("See README.md for the token approval step.")


if __name__ == "__main__":
    main()
