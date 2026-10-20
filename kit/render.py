"""Render a daily poster: python3 render.py post.json out.png
post.json keys: headline (HTML, lines split with <br>), highlight (plain text),
subline (HTML, <em> allowed), element (inline SVG markup for a 560x600 viewBox),
optional head_size (default 112) and hl_size (default 104)."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

kit = pathlib.Path(__file__).resolve().parent
post = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = pathlib.Path(sys.argv[2]).resolve()

html = (kit / "template.html").read_text()
for key, val in {
    "HEADLINE": post["headline"], "HIGHLIGHT": post["highlight"],
    "SUBLINE": post["subline"], "ELEMENT": post["element"],
    "HEAD_SIZE": str(post.get("head_size", 112)), "HL_SIZE": str(post.get("hl_size", 104)),
}.items():
    html = html.replace("{{" + key + "}}", val)

page_file = kit / "_page.html"
page_file.write_text(html)
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
    pg.locator(".poster").screenshot(path=str(out))
    b.close()
print(f"rendered {out}")
