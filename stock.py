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

# hand-curated Pexels photo ids per theme (visually reviewed 2026-07-13)
CURATED = {
    "phone":       [31387781, 8487722, 8961131, 1078879],
    "texting":     [1083931, 7641426, 1458283, 4831],
    "night":       [12635003, 12700835, 38556982, 7511796],
    "schedule":    [7581018, 7580934, 162583, 6172482],
    "hvac":        [5463575, 32497161, 5463587, 27134985],
    "plumber":     [7859953, 29226620, 17063686, 7162333],
    "electrician": [27928762, 32497160, 27928761, 28950842],
    "roofer":      [33404248, 37677394, 38028508, 31762405],
    "locksmith":   [13963754, 101808, 14721, 115642],
    "contractor":  [8961296, 8482551, 3680959, 4981810],
    "handshake":   [8486896, 5622309, 8469935, 6720550],
    "reception":   [6812426, 4269269, 6809657, 6812434],
}
DEFAULT_MIX = CURATED["phone"] + CURATED["contractor"] + CURATED["texting"] + CURATED["schedule"]

# ordered title -> theme rules (first match wins)
THEME_RULES = [
    (r"\bhvac\b|\bfurnace\b|\bno heat\b|\bair condition", "hvac"),
    (r"\bplumb|\bwater heater\b|\bdrain\b|\bleak", "plumber"),
    (r"\belectric|\bpanel\b|\bwiring\b", "electrician"),
    (r"\broof", "roofer"),
    (r"\blocksmith\b|\blockout\b", "locksmith"),
    (r"\breview|\breputation\b|\bwin(s|ning)?\b", "handshake"),
    (r"\bafter hours\b|\bnight\b|\bovernight\b|\b24.?7\b", "night"),
    (r"\bbook(ing|ed|s)?\b|\bschedul|\bcalendar\b|\bappointment|\bestimate", "schedule"),
    (r"\breception|\banswering service\b", "reception"),
    (r"\btext(ing)?\b|\bsms\b", "texting"),
    (r"\bcontractor|\bconstruction\b|\btrades\b", "contractor"),
    (r"\bcall|\bphone\b|\brespond|\bresponse\b|\banswer|\bmissed\b|\bvoicemail\b", "phone"),
]


def pick_photo_id(title, seed=0):
    t = (title or "").lower()
    for pat, theme in THEME_RULES:
        if _re.search(pat, t):
            ids = CURATED[theme]
            return ids[seed % len(ids)], theme
    return DEFAULT_MIX[seed % len(DEFAULT_MIX)], "default"


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
    pid, theme = pick_photo_id(title, seed)
    p = json.loads(_get("https://api.pexels.com/v1/photos/%d" % pid,
                        headers={"Authorization": PEXELS_KEY}))
    src = p["src"].get("large2x") or p["src"]["large"]
    img = _get(src)
    credit = "%s via Pexels (%s) [theme:%s]" % (p.get("photographer", ""), p.get("url", ""), theme)
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
