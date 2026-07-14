"""Stock-photo featured images with MinuteLead brand treatment.

GET /stock?title=<post title>&seed=<int>&w=<width>
  1. Derives a search query from the title (vertical keywords -> realistic trade photos).
  2. Pulls a landscape photo from Pexels (PEXELS_API_KEY env var; free key at pexels.com/api).
  3. Cover-crops to 16:9, applies a navy bottom gradient + the MinuteLead logo mark.
  4. Returns JPEG. Photographer credit is exposed in the X-Photo-Credit header.
Falls back to the branded SVG scene (mlscene) if the key is missing or Pexels errors,
so the Make pipeline never breaks.
"""
import io
import os
import json
import urllib.parse
import urllib.request

import cairosvg
from PIL import Image

PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")

NAVY = (21, 35, 59)

# title keyword -> photo search query (checked in order, first hit wins)
QUERIES = [
    (("hvac", "furnace", "heat", "air condition", "ac "), "hvac technician working"),
    (("plumb", "pipe", "water heater", "leak"), "plumber working under sink"),
    (("electri", "panel", "wiring"), "electrician working panel"),
    (("roof", "shingle"), "roofer working on roof"),
    (("locksmith", "lockout"), "locksmith door lock"),
    (("landscap", "lawn"), "landscaper working"),
    (("clean",), "cleaning service professional"),
    (("dental", "dentist"), "dental clinic reception"),
    (("law", "legal"), "law office professional"),
    (("real estate",), "real estate agent client"),
    (("salon", "spa"), "salon front desk"),
    (("gym", "fitness"), "gym front desk"),
    (("auto", "mechanic", "repair shop"), "auto mechanic shop"),
    (("contractor", "estimate", "job site", "trades"), "contractor construction worker"),
    (("call", "phone", "reception", "answering", "text", "voicemail"), "tradesperson answering phone"),
    (("book", "schedul", "calendar", "appointment"), "small business owner phone calendar"),
    (("review", "reputation"), "happy customer handshake service"),
    (("lead", "follow up", "inquir", "customer"), "small business owner working phone"),
]
DEFAULT_QUERY = "tradesperson at work small business"

LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="16 16 164 164">
<rect x="16" y="16" width="164" height="164" rx="36" fill="#15233B"/>
<circle cx="98" cy="98" r="50" stroke="#36b6ff" stroke-width="5" fill="none"/>
<path d="M98 48V61" stroke="#36b6ff" stroke-width="5" stroke-linecap="round"/>
<path d="M148 98H135" stroke="#36b6ff" stroke-width="5" stroke-linecap="round"/>
<path d="M98 148V135" stroke="#36b6ff" stroke-width="5" stroke-linecap="round"/>
<path d="M48 98H61" stroke="#36b6ff" stroke-width="5" stroke-linecap="round"/>
<path d="M98 48 A50 50 0 0 1 131 61" stroke="#F2960F" stroke-width="7" stroke-linecap="round" fill="none"/>
<path d="M96 64 L78 104 L95 104 L80 138 L116 94 L98 94 Z" fill="#F2960F"/>
</svg>"""


def pick_query(title):
    t = (title or "").lower()
    for keys, q in QUERIES:
        if any(k in t for k in keys):
            return q
    return DEFAULT_QUERY


UA = "MinuteLeadRender/1.0 (+https://minutelead.ca)"


def _get(url, headers=None, timeout=20):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_pexels(title, seed):
    """Returns (image_bytes, credit_str). Raises on any failure."""
    if not PEXELS_KEY:
        raise RuntimeError("PEXELS_API_KEY not set")
    q = pick_query(title)
    api = ("https://api.pexels.com/v1/search?query=%s&orientation=landscape&size=large&per_page=15"
           % urllib.parse.quote(q))
    data = json.loads(_get(api, headers={"Authorization": PEXELS_KEY}))
    photos = data.get("photos") or []
    if not photos:
        raise RuntimeError("no pexels results for %r" % q)
    p = photos[seed % len(photos)]
    src = p["src"].get("large2x") or p["src"]["large"]
    img = _get(src)
    credit = "%s via Pexels (%s)" % (p.get("photographer", ""), p.get("url", ""))
    return img, credit


def cover_crop(im, w, h):
    """Scale + center-crop to exactly w x h."""
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    im = im.resize((max(1, round(sw * scale)), max(1, round(sh * scale))), Image.LANCZOS)
    sw, sh = im.size
    x = (sw - w) // 2
    y = (sh - h) // 2
    return im.crop((x, y, x + w, y + h))


def brand_treatment(im):
    """Navy bottom gradient + logo mark bottom-right + thin orange baseline."""
    w, h = im.size
    im = im.convert("RGB")

    # bottom gradient: transparent -> navy, over the lower 34%
    grad_h = int(h * 0.34)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i in range(grad_h):
        alpha = int(185 * (i / grad_h) ** 1.4)
        row = Image.new("RGBA", (w, 1), NAVY + (alpha,))
        overlay.paste(row, (0, h - grad_h + i))
    im = Image.alpha_composite(im.convert("RGBA"), overlay)

    # thin orange baseline
    bar = Image.new("RGBA", (w, max(4, h // 130)), (242, 150, 15, 255))
    im.paste(bar, (0, h - bar.size[1]), bar)

    # logo mark bottom-right
    logo_px = max(56, h // 9)
    logo_png = cairosvg.svg2png(bytestring=LOGO_SVG.encode(),
                                output_width=logo_px, output_height=logo_px)
    logo = Image.open(io.BytesIO(logo_png)).convert("RGBA")
    margin = h // 22
    im.paste(logo, (w - logo_px - margin, h - logo_px - margin - bar.size[1]), logo)
    return im.convert("RGB")


def stock_featured(title, seed, w=1200):
    """Returns (jpeg_bytes, credit, used_stock: bool)."""
    h = int(w * 9 / 16)
    raw, credit = fetch_pexels(title, seed)   # raises on failure -> caller falls back
    im = Image.open(io.BytesIO(raw))
    im = cover_crop(im, w, h)
    im = brand_treatment(im)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=88, optimize=True)
    return out.getvalue(), credit
