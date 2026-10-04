#!/usr/bin/env python3
"""Render PNG frames of an animated SVG at chosen timestamps.

Usage:
  python render_frames.py file.svg --times 0,2.5,5,7.5 --out run/frames [--width 1200] [--sheet]

  --times   comma-separated seconds (default 0,25%,50%,75% of the longest dur found)
  --width   viewport width in px (height follows the SVG aspect ratio)
  --sheet   also write contact_sheet.png with all frames in a grid (needs Pillow)

How it works: loads the SVG in headless Chromium (Playwright), pauses SMIL with
pauseAnimations()/setCurrentTime(t) and CSS animations via document.getAnimations(),
then screenshots. View the PNGs to confirm the traveller is on its rail, glows light up
at the right moments, arrows touch their targets, and nothing overlaps text.
Requires: pip install playwright && playwright install chromium.
Optional (contact sheet only): pip install pillow
"""
import argparse
import os
import re
import sys


def longest_dur(text):
    durs = []
    for m in re.finditer(r'dur="([\d.]+)(ms|s)"', text):
        v = float(m.group(1))
        durs.append(v / 1000 if m.group(2) == "ms" else v)
    for m in re.finditer(r"animation:[^;}]*?([\d.]+)(ms|s)", text):
        v = float(m.group(1))
        durs.append(v / 1000 if m.group(2) == "ms" else v)
    return max(durs) if durs else 4.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--times", default=None)
    ap.add_argument("--out", default="run/frames")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed; skip frame capture and rely on the lint output.")
        return 2

    text = open(args.svg, encoding="utf-8").read()
    if args.times:
        times = [float(t) for t in args.times.split(",") if t.strip()]
    else:
        d = longest_dur(text)
        times = [0, d * 0.25, d * 0.5, d * 0.75]

    m = re.search(r'viewBox="[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', text)
    aspect = (float(m.group(2)) / float(m.group(1))) if m else 0.5
    height = max(1, int(args.width * aspect))

    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.svg))[0]
    html = (
        "<!doctype html><html><body style='margin:0;background:#000'>"
        f"<div id='wrap' style='width:{args.width}px;height:{height}px'>{text}</div></body></html>"
    )
    # strip an XML prolog if present so it can be inlined in HTML
    html = re.sub(r"<\?xml[^>]*\?>", "", html)

    files = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": height})
        page.set_content(html)
        page.evaluate(
            """() => { const s = document.querySelector('svg');
                      s.setAttribute('width','100%'); s.setAttribute('height','100%'); }"""
        )
        for t in times:
            page.evaluate(
                """(t) => {
                    const s = document.querySelector('svg');
                    s.pauseAnimations(); s.setCurrentTime(t);
                    document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
                }""",
                t,
            )
            page.wait_for_timeout(60)
            out = os.path.join(args.out, f"{base}_t{t:05.2f}s.png")
            page.screenshot(path=out)
            files.append(out)
            print(out)
        browser.close()

    if args.sheet and files:
        try:
            from PIL import Image
            imgs = [Image.open(f) for f in files]
            cols = 2
            rows = (len(imgs) + cols - 1) // cols
            w, h = imgs[0].size
            sheet = Image.new("RGB", (w * cols, h * rows), "black")
            for i, im in enumerate(imgs):
                sheet.paste(im, ((i % cols) * w, (i // cols) * h))
            sp = os.path.join(args.out, f"{base}_contact_sheet.png")
            sheet.save(sp)
            print(sp)
        except ImportError:
            print("Pillow not installed; contact sheet skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
