"""OpenAI (gpt-image-1) featured-image generator with MinuteLead brand treatment.

GET /ai?title=<post title>&seed=<int>&w=<width>&quality=<medium|high>
  1. Classifies the title -> theme (reuses stock.THEME_RULES, adds a `reporting` theme).
  2. Builds a brand-locked prompt: fixed STYLE preamble + per-theme subject + seed-varied
     compositional hint (so the same theme differs across posts).
  3. Calls the OpenAI Images API (gpt-image-1, 1536x1024) -> base64 PNG.
  4. cover_crop to 1200x675, applies the logo mark + orange baseline (NO navy gradient:
     AI illustrations are already rich; the gradient was only for photo-text legibility).
  5. Returns PNG bytes + the chosen theme.

The /ai route falls back to the vector scene on ANY failure so the pipeline never breaks.
OPENAI_API_KEY lives only as a Cloud Run env var (never committed).
"""
import base64
import io
import json
import os
import urllib.error
import urllib.request

import cairosvg
from PIL import Image

import stock  # reuse THEME_RULES, cover_crop, LOGO_SVG, _stable

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_URL = "https://api.openai.com/v1/images/generations"

# ---- classifier -----------------------------------------------------------
# `reporting` isn't a stock/Pexels theme (no curated photos), so it lives here.
# It is checked LAST (before `default`): "recovery/revenue" language pervades
# MinuteLead titles that are really about a trade or the phone, so trade/phone/
# schedule themes must win first. Reporting only catches leftover ROI/earnings titles.
AI_THEME_RULES = stock.THEME_RULES + [
    (r"\breport(s|ing|ed)?\b|\brevenue\b|\broi\b|\bearn|\bprofit|\brecover(ed|y|ing)?\b|\bworth\b|\bbottom line\b", "reporting"),
]


def classify(title):
    t = (title or "").lower()
    for pat, theme in AI_THEME_RULES:
        if stock._re.search(pat, t):
            return theme
    return "default"


# ---- prompt library (§6) --------------------------------------------------
STYLE = (
    "Flat modern vector illustration, minimalist and clean, one clear subject centered with "
    "generous negative space, soft long shadows, rounded friendly shapes. Warm off-white paper "
    "background (#FBF8F2) with a faint soft radial glow (#FDEAD0) at the top center. Strictly limited "
    "brand palette: navy #15233B, orange #F2960F, deep orange #D9850B, green #2FBF71 and #1B8A55, "
    "coral #E0664F, muted gray #5B6677, tan #A99B82, light blue #EAF0F6. "
    "Absolutely no text, no letters, no words, no numbers, no logos, no watermarks, no UI chrome. "
    "No photorealism, no 3D rendering. Editorial, calm, professional. "
)

THEME_PROMPTS = {
    "reception": "A friendly rounded phone or headset icon glowing softly, a small speech bubble with a green check, suggesting a call answered instantly.",
    "phone": "A smartphone with a missed-call badge turning into a green checkmark, a soft orange pulse ring around it, one small notification card.",
    "texting": "A phone showing two chat bubbles, one incoming gray and one outgoing orange, with a green check, suggesting an instant text reply.",
    "night": "A calm night scene: a crescent moon, a softly lit phone or small service van, a clock showing late hours, reassuring not gloomy.",
    "schedule": "A clean calendar with one day highlighted green and a small booked-appointment card, suggesting a job booked into the schedule.",
    "hvac": "A stylized HVAC condenser unit or thermostat, warm-to-cool comfort motif, a small green checkmark, clean and modern.",
    "plumber": "A stylized faucet or pipe fitting with a water droplet, a small booked-job card, clean and friendly.",
    "electrician": "A stylized electrical panel or lightning bolt with a spark, a small confirmation card, modern and safe-looking.",
    "roofer": "A stylized house roof with shingles and a sun, a small booked card, bright and approachable.",
    "locksmith": "A stylized door lock and key with a small green check, calm and trustworthy, a hint of night.",
    "contractor": "A stylized hub with lines routing several small leads into a single calendar or booked card, suggesting lead flow captured.",
    # NB: must be all five stars COMPLETELY filled -- "filling left to right" made
    # gpt-image-1 render 4 filled + 1 empty, which reads as a 4-star review.
    "handshake": "Exactly five identical gold stars in a row, every one of them completely filled in solid gold, none empty or partially filled, with a happy-outcome feel.",
    "reporting": "A clean bar chart trending upward, the tallest bar green, an upward arrow, suggesting recovered revenue.",
    "default": "A local-service business owner's phone on a warm desk with a small green checkmark card, a general 'inbound handled' feel.",
}

# seed-varied compositional hints so the same theme looks different across posts
COMPOSITION_HINTS = [
    "Elements arranged diagonally across the frame.",
    "Centered symmetrical composition.",
    "Subject slightly left with open space on the right.",
    "Subject slightly right with open space on the left.",
    "Subject high in the frame with a wide calm foreground.",
]


def build_prompt(title, theme, seed):
    subject = THEME_PROMPTS.get(theme, THEME_PROMPTS["default"])
    hint = COMPOSITION_HINTS[stock._stable(seed) % len(COMPOSITION_HINTS)]
    return STYLE + subject + " " + hint


# ---- OpenAI call ----------------------------------------------------------
def _openai_image(prompt, size="1536x1024", quality="medium", timeout=120):
    if not OPENAI_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }).encode()
    req = urllib.request.Request(
        OPENAI_URL, data=body, method="POST",
        headers={"Authorization": "Bearer " + OPENAI_KEY,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # surface the API's real message (e.g. billing_hard_limit_reached) in
        # X-Fallback-Reason -- a bare "HTTP Error 400" is undiagnosable from Make.
        try:
            err = json.loads(e.read()).get("error", {})
            detail = "%s: %s" % (err.get("code") or e.code, err.get("message", ""))
        except Exception:
            detail = "HTTP %s" % e.code
        raise RuntimeError("openai %s" % detail) from None
    return base64.b64decode(data["data"][0]["b64_json"])


# ---- brand treatment: logo mark + orange baseline (NO navy gradient) -------
def brand_treatment_logo(im):
    w, h = im.size
    im = im.convert("RGB")

    # thin orange baseline
    bar_h = max(4, h // 130)
    bar = Image.new("RGBA", (w, bar_h), (242, 150, 15, 255))
    im = im.convert("RGBA")
    im.paste(bar, (0, h - bar_h), bar)

    # logo mark bottom-right
    logo_px = max(56, h // 9)
    logo_png = cairosvg.svg2png(bytestring=stock.LOGO_SVG.encode(),
                                output_width=logo_px, output_height=logo_px)
    logo = Image.open(io.BytesIO(logo_png)).convert("RGBA")
    margin = h // 22
    im.paste(logo, (w - logo_px - margin, h - logo_px - margin - bar_h), logo)
    return im.convert("RGB")


# ---- public entrypoint ----------------------------------------------------
def gen(title, seed, w=1200, quality="medium"):
    """Returns (png_bytes, theme). Raises on any OpenAI/decode failure so the
    /ai route can fall back to the vector scene."""
    h = int(w * 9 / 16)
    theme = classify(title)
    prompt = build_prompt(title, theme, seed)
    raw = _openai_image(prompt, quality=quality)
    im = Image.open(io.BytesIO(raw))
    im = stock.cover_crop(im, w, h)
    im = brand_treatment_logo(im)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue(), theme
