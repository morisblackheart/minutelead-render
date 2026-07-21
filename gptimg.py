"""OpenAI (gpt-image-1) featured-image generator with MinuteLead brand treatment.

GET /ai?title=<post title>&seed=<int>&w=<width>&quality=<medium|high>
       &style=<photo|illus>&grad=<0|1>
  1. Classifies the title -> theme (reuses stock.THEME_RULES, adds a `reporting` theme).
  2. Builds a brand-locked prompt: fixed STYLE preamble + per-theme subject + seed-varied
     compositional hint (so the same theme differs across posts).
  3. Calls the OpenAI Images API (gpt-image-1, 1536x1024) -> base64 PNG.
  4. cover_crop to 1200x675, applies the brand treatment.

Two styles:
  * `illus` -- flat vector, locked to the brand palette on the warm paper background.
  * `photo` -- photorealistic editorial photography (default). Deliberately steered away
    from the "AI look": no vignette, no radial glow, no HDR, no glossy CGI sheen. Screens
    and signage are kept illegible so the model never renders garbled text.

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
from PIL import Image, ImageDraw

import stock  # reuse THEME_RULES, cover_crop, brand_treatment, LOGO_SVG, _stable

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


# ---- style preambles ------------------------------------------------------
ILLUS_STYLE = (
    "Flat modern vector illustration, minimalist and clean, one clear subject centered with "
    "generous negative space, soft long shadows, rounded friendly shapes. Warm off-white paper "
    "background (#FBF8F2) with a faint soft radial glow (#FDEAD0) at the top center. Strictly limited "
    "brand palette: navy #15233B, orange #F2960F, deep orange #D9850B, green #2FBF71 and #1B8A55, "
    "coral #E0664F, muted gray #5B6677, tan #A99B82, light blue #EAF0F6. "
    "Absolutely no text, no letters, no words, no numbers, no logos, no watermarks, no UI chrome. "
    "No photorealism, no 3D rendering. Editorial, calm, professional. "
)

# Steered hard against the "AI look". The negative list is doing real work here:
# vignette/glow/HDR/CGI-sheen are the giveaways that read as AI-generated.
PHOTO_STYLE = (
    "A vivid, colourful photorealistic editorial photograph, shot on a full-frame DSLR with a 35mm "
    "lens, beautiful natural light. Rich, saturated, lively colour with real depth and punch, like a "
    "well-graded magazine feature -- bright and full of life, never flat, dull, muted, grey or washed "
    "out. Authentic real-world texture and honest materials. Evenly exposed across the entire frame. "
    "Absolutely no vignette, no darkened corners or edge falloff, no radial glow, no spotlight effect. "
    "No HDR halos, no glossy CGI sheen, no plastic or waxy skin, no over-sharpening, no bloom. "
    "Candid and unposed, not a stiff stock-photo look. "
    "When people appear, show genuine warm natural expressions and real skin texture with visible "
    "pores and fine lines -- never airbrushed, never mannequin-like. Correct natural hands. "
    "No text, letters, words, numbers, signage, logos, watermarks, or legible screen content anywhere "
    "in the frame. Any screen is off or shows an indistinct blur. "
)

# ---- prompt libraries -----------------------------------------------------
ILLUS_PROMPTS = {
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
    # NB: do NOT ask for a specific number of stars. gpt-image-1 cannot count
    # reliably -- "five stars filling left to right" gave 4 filled + 1 empty, and
    # "exactly five, all filled" gave 4 + a thumbs-up. Both read as a 4-star
    # rating on posts about 5-star reviews. Design the count out: one hero star.
    "handshake": "One large solid gold star as the hero subject, with a small green check badge beside it, a happy-outcome reputation feel.",
    "reporting": "A clean bar chart trending upward, the tallest bar green, an upward arrow, suggesting recovered revenue.",
    "default": "A local-service business owner's phone on a warm desk with a small green checkmark card, a general 'inbound handled' feel.",
}

# Each theme holds a LIST of interchangeable subjects, picked by seed. This is what
# stops repetition: `phone` matches 6 of the 24 live posts and `schedule` 4, so a
# single subject per theme would put six near-identical photos down the blog grid.
# Themes that recur most carry the most variants.
PHOTO_PROMPTS = {
    "reception": [
        "A friendly receptionist wearing a headset at a bright front desk, smiling naturally, leafy green plants and warm wood tones around her, sunlight through a window.",
        "A cheerful small-business owner in a colourful shirt answering a desk phone in a bright airy office, genuine warm smile, vivid greenery behind.",
    ],
    "phone": [
        "A tradesperson in a bright orange work shirt smiling as he checks his smartphone in a sunlit workshop, colourful tools on a pegboard behind him.",
        "A smartphone resting on the dashboard of a service van, vivid blue sky and green trees through the windshield, warm sunlight across the dash.",
        "A smiling homeowner in a bright colourful kitchen taking a phone call, sunlight, a bowl of fruit and green plants on the counter.",
        "A smartphone on a clipboard on a pickup tailgate, a bright red toolbox and yellow tape measure beside it, vivid daylight.",
        "A young tradesperson in a high-visibility vest grinning while looking at his phone outside a house, brilliant blue sky, green lawn.",
        "A smartphone face-up on a workshop bench beside a brightly coloured mug, warm golden light raking across colourful tools.",
    ],
    "texting": [
        "A tradesperson in a colourful plaid shirt smiling as he taps out a text on his phone at a sunlit job site, screen an indistinct blur.",
        "Close view of hands in tan work gloves holding a phone, screen an indistinct blur, vivid orange safety vest and green grass behind.",
    ],
    "night": [
        "A service van parked outside a suburban house at golden dusk, warm amber porch light, deep blue and violet sky, rich saturated colour.",
        "A friendly tradesperson smiling at a brightly lit front door in the evening, warm golden porch light, deep blue twilight sky behind.",
        "A suburban street at dusk under a vivid orange and purple sky, a service van with glowing tail lights, warm lit windows in the houses.",
    ],
    "schedule": [
        "A bright airy office desk with an open planner, a colourful mug and a vase of fresh flowers, sunlight streaming across, writing not legible.",
        "A smiling business owner marking a wall calendar in a bright colourful office, natural happy expression, markings not legible.",
        "A tablet on a desk showing an indistinct blurred grid, beside a bright orange notebook and a green plant, sunlit and vivid.",
        "A tradesperson in a bright work shirt smiling with a clipboard on a truck tailgate, vivid blue sky, writing not legible.",
    ],
    "hvac": [
        "An outdoor residential HVAC condenser beside a house, vivid green lawn and colourful garden, brilliant blue sky, crisp sunlight.",
        "A technician in a blue uniform smiling while servicing a home HVAC unit, bright sunlight, green shrubs, vivid colour.",
    ],
    "plumber": [
        "A plumber in a bright blue shirt smiling while working under a modern kitchen sink, warm interior light, colourful tiles.",
        "Gleaming copper pipes and a bright red shutoff valve in a clean utility room, warm light, rich saturated colour.",
    ],
    "electrician": [
        "An electrician in an orange high-visibility vest smiling beside an open electrical panel, bright even light, colourful wiring.",
        "Coils of vividly coloured electrical wire and tools laid out on a workbench, bright daylight, rich saturated colour.",
    ],
    "roofer": [
        "A roofer in a bright safety vest working on a residential roof under a brilliant blue sky, warm sunlight, vivid colour.",
        "A residential roof with warm terracotta shingles against a vivid blue sky, bright sunlight, green treetops at the edge.",
    ],
    "locksmith": [
        "A locksmith in a colourful work shirt smiling while fitting a new deadbolt on a front door, warm daylight.",
        "A polished brass deadbolt and keys on a brightly painted front door, warm golden light, rich colour.",
    ],
    "contractor": [
        "A contractor in a bright orange vest and hard hat smiling in front of a pickup truck at a suburban home, vivid blue sky.",
        "A colourful tool belt and yellow hard hat on a tailgate at a job site, brilliant sunlight, green lawn.",
        "Two tradespeople in colourful workwear talking and laughing together at a residential job site, warm sunlight, vivid colour.",
    ],
    "handshake": [
        "A smiling homeowner and a tradesperson shaking hands warmly in a sunlit front doorway, both faces clearly visible with genuine happy expressions, vivid colour.",
        "A happy homeowner smiling broadly beside a friendly tradesperson on a front porch, both faces visible, warm golden light, rich colour.",
    ],
    "reporting": [
        "A smiling small-business owner at a bright desk with a laptop, screen an indistinct blur, colourful notebook and a green plant, sunlight.",
        "A laptop angled away so its screen is not visible on a bright colourful desk with a plant and a warm mug, vivid daylight.",
    ],
    "default": [
        "A brightly coloured service van parked on a sunny residential street, vivid blue sky, green lawns, a phone on the driver's seat.",
        "A cheerful home-service business owner smiling in a bright office with a closed laptop, a colourful mug and van keys.",
        "A service van in a driveway on a brilliant sunny day, vivid colour, green trees and blue sky.",
    ],
}

# seed-varied compositional hints, per style
ILLUS_HINTS = [
    "Elements arranged diagonally across the frame.",
    "Centered symmetrical composition.",
    "Subject slightly left with open space on the right.",
    "Subject slightly right with open space on the left.",
    "Subject high in the frame with a wide calm foreground.",
]
PHOTO_HINTS = [
    "Shot straight on at eye level.",
    "Shot from a slightly low angle.",
    "Shot from a high three-quarter angle looking down.",
    "Subject offset to the left with clean open space on the right.",
    "Subject offset to the right with clean open space on the left.",
]

# A second seed-varied axis, independent of subject and framing. Light is what
# stops 24 posts reading as one long grey afternoon.
PHOTO_LIGHT = [
    "Warm golden-hour sunlight with long soft shadows and rich amber tones.",
    "Brilliant crisp midday sun under a vivid blue sky, strong clean colour.",
    "Bright luminous overcast light, soft but richly saturated.",
    "Warm sunlight streaming through a window, glowing and colourful.",
    "Fresh clear morning light with vivid, punchy colour.",
]

STYLES = {
    "illus": (ILLUS_STYLE, ILLUS_PROMPTS, ILLUS_HINTS),
    "photo": (PHOTO_STYLE, PHOTO_PROMPTS, PHOTO_HINTS),
}


def variant_index(theme, seed, style="photo"):
    """Which subject variant a given seed selects. Exposed so the backfill planner
    can choose seeds that avoid repeating a subject in adjacent posts."""
    _, prompts, _ = STYLES.get(style, STYLES["photo"])
    subs = prompts.get(theme, prompts["default"])
    if isinstance(subs, str):
        return 0
    return stock._stable(seed) % len(subs)


def build_prompt(title, theme, seed, style="photo"):
    preamble, prompts, hints = STYLES.get(style, STYLES["photo"])
    subs = prompts.get(theme, prompts["default"])
    if isinstance(subs, str):
        subs = [subs]
    subject = subs[stock._stable(seed) % len(subs)]
    # offset each axis so subject, framing and light don't move in lockstep
    hint = hints[stock._stable(seed + 7) % len(hints)]
    light = ""
    if style == "photo":
        light = " " + PHOTO_LIGHT[stock._stable(seed + 13) % len(PHOTO_LIGHT)]
    return preamble + subject + " " + hint + light


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
    x, y = w - logo_px - margin, h - logo_px - margin - bar_h

    # The logo tile is navy, so on a dark photo (dusk, dim workshop) it sinks into
    # the background and the brand mark disappears. Sample what's actually behind
    # it and, only when that's dark, lay down a soft light chip for contrast.
    # Light images are left exactly as-is.
    patch = im.crop((x, y, x + logo_px, y + logo_px)).convert("L")
    if sum(patch.getdata()) / (logo_px * logo_px) < 110:
        pad = max(3, logo_px // 14)
        chip = Image.new("RGBA", (logo_px + pad * 2, logo_px + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(chip).rounded_rectangle(
            [0, 0, chip.size[0] - 1, chip.size[1] - 1],
            radius=int(logo_px * 0.28), fill=(251, 248, 242, 225))
        im.paste(chip, (x - pad, y - pad), chip)

    im.paste(logo, (x, y), logo)
    return im.convert("RGB")


# ---- public entrypoint ----------------------------------------------------
def gen(title, seed, w=1200, quality="medium", style="photo", grad=False):
    """Returns (png_bytes, theme). Raises on any OpenAI/decode failure so the
    /ai route can fall back to the vector scene.

    grad=True uses stock.brand_treatment (navy bottom gradient + logo), which
    aids logo legibility over a busy photo; grad=False is logo + baseline only.
    """
    h = int(w * 9 / 16)
    theme = classify(title)
    prompt = build_prompt(title, theme, seed, style)
    raw = _openai_image(prompt, quality=quality)
    im = Image.open(io.BytesIO(raw))
    im = stock.cover_crop(im, w, h)
    im = stock.brand_treatment(im) if grad else brand_treatment_logo(im)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue(), theme, variant_index(theme, seed, style)
