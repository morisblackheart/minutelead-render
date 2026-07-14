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

import re as _re

# trade in title -> specific work imagery (word-boundary regex, checked first)
TRADES = [
    (r"\bhvac\b|\bfurnace\b|\bno heat\b|\bair condition", "hvac technician air conditioner"),
    (r"\bplumb|\bpipe\b|\bwater heater\b|\bleak", "plumber working pipes"),
    (r"\belectric|\bpanel\b|\bwiring\b", "electrician working electrical panel"),
    (r"\broof", "roofer shingles construction"),
    (r"\blocksmith\b|\blockout\b", "locksmith keys door"),
    (r"\blandscap|\blawn\b", "landscaping crew working"),
    (r"\bclean(er|ing)\b", "professional cleaning service"),
    (r"\bdent(al|ist)", "dental clinic"),
    (r"\blaw\b|\blegal\b|\battorney\b", "law office desk"),
    (r"\breal estate\b|\brealtor\b", "real estate agent house keys"),
    (r"\bsalon\b|\bspa\b|\bbarber\b", "hair salon interior"),
    (r"\bgym\b|\bfitness\b", "gym equipment trainer"),
    (r"\bauto repair\b|\bmechanic\b|\bbody shop\b|\bauto shop\b|\bcar repair\b", "car mechanic garage"),
    (r"\bpest\b", "pest control technician"),
    (r"\brestoration\b", "water damage restoration"),
    (r"\bcontractor|\bconstruction\b|\btrades\b|\bestimate", "contractor construction site"),
]

# topic themes when no trade is named
TOPICS = [
    (r"\breview|\breputation\b", "customer handshake happy service"),
    (r"\bafter hours\b|\bnight\b|\bovernight\b", "work van night technician"),
    (r"\bbook(ing|ed)?\b|\bschedul|\bcalendar\b|\bappointment", "planner calendar scheduling tools"),
]

# generic titles rotate through trade imagery (variety from our verticals,
# not another stock person on a phone)
GENERIC_POOL = [
    "plumber service van tools",
    "electrician tool belt working",
    "hvac technician equipment",
    "roofing workers house",
    "contractor tools workshop",
    "handyman toolbox home repair",
    "service technician front door customer",
    "tradesman work van street",
]


def pick_query(title, seed=0):
    t = (title or "").lower()
    for pat, q in TRADES:
        if _re.search(pat, t):
            return q
    for pat, q in TOPICS:
        if _re.search(pat, t):
            return q
    return GENERIC_POOL[seed % len(GENERIC_POOL)]


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
    q = pick_query(title, seed)
    api = ("https://api.pexels.com/v1/search?query=%s&orientation=landscape&size=large&per_page=80"
           % urllib.parse.quote(q))
    data = json.loads(_get(api, headers={"Authorization": PEXELS_KEY}))
    photos = data.get("photos") or []
    if not photos:
        raise RuntimeError("no pexels results for %r" % q)
    p = photos[(seed * 7) % len(photos)]
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
