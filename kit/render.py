"""Render a daily poster: python3 render.py post.json out.png

style "v2" (default for new posts, "Daily brief" paper style) keys:
  kicker   short category label, e.g. "AI infra"
  read     tiny mono note next to kicker, e.g. "what changed"
  headline HTML, lines split with <br>; ONE word may be wrapped in <i> (italic serif accent)
  old      the "before" phrase, shown struck through with a minus sign
  highlight the "after" phrase, shown big italic serif on the signal-lime block
  subline  HTML, one <em> allowed
  tags     list of 2-3 short labels (mono pills)
  element  inline SVG markup for a 600x600 viewBox, bottom-right, may bleed off the right edge
  issue    optional, e.g. "No. 004" (auto: count of posts)
  date     optional, e.g. "22.10.2026" (auto from file name)
  head_size (default 112), hl_size (default 112)

style "v1" (legacy dark grid): headline, highlight, subline, element, head_size, hl_size.
"""
import json, sys, pathlib, re, html as htmlmod
from playwright.sync_api import sync_playwright

kit = pathlib.Path(__file__).resolve().parent
src = pathlib.Path(sys.argv[1]).resolve()
post = json.loads(src.read_text())
out = pathlib.Path(sys.argv[2]).resolve()
style = post.get("style", "v1")

if style == "v2":
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", src.stem)
    date = post.get("date") or (f"{m[3]}.{m[2]}.{m[1]}" if m else "")
    n = len(list(src.parent.glob("*.json")))
    tags = "".join(f"<span>{htmlmod.escape(t)}</span>" for t in post.get("tags", []))
    subs = {
        "HEADLINE": post["headline"], "HIGHLIGHT": post["highlight"], "OLD": post["old"],
        "SUBLINE": post["subline"], "ELEMENT": post["element"], "TAGS": tags,
        "KICKER": post.get("kicker", "Tech"), "READ": post.get("read", "what changed"),
        "ISSUE": post.get("issue", f"No. {n:03d}"), "DATE": date,
        "HEAD_SIZE": str(post.get("head_size", 112)), "HL_SIZE": str(post.get("hl_size", 112)),
    }
    tpl = "template_v2.html"
else:
    subs = {
        "HEADLINE": post["headline"], "HIGHLIGHT": post["highlight"],
        "SUBLINE": post["subline"], "ELEMENT": post["element"],
        "HEAD_SIZE": str(post.get("head_size", 112)), "HL_SIZE": str(post.get("hl_size", 104)),
    }
    tpl = "template.html"

page = (kit / tpl).read_text()
for key, val in subs.items():
    page = page.replace("{{" + key + "}}", val)

page_file = kit / "_page.html"
page_file.write_text(page)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto(page_file.as_uri())
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(300)
    # fail loudly if the highlight phrase overflows the poster
    w = pg.evaluate("document.querySelector('.hl').getBoundingClientRect().right")
    if w > 1040:
        sys.exit(f"highlight too wide ({w:.0f}px): shorten it or lower hl_size")
    if style == "v2":
        bottom = pg.evaluate("Math.max(...[...document.querySelectorAll('.body > *')].map(e => e.getBoundingClientRect().bottom))")
        if bottom > 1230:
            sys.exit(f"copy too tall ({bottom:.0f}px): shorten headline/subline or lower head_size")
    pg.locator(".poster").screenshot(path=str(out))
    b.close()
page_file.unlink(missing_ok=True)
print(f"rendered {out}")
