#!/usr/bin/env python3
"""MinuteLead scene engine — turns a post TITLE into an on-brand, text-free SVG scene.
Two tiers:
  • BESPOKE: the ~10 hand-built trade scenes (reused from generate.py) for top verticals.
  • GENERIC: any other local-service vertical → a branded scene with the trade ICON as the
    big hero + the universal missed-call→booked story. Scales to "everything local".
Emits strict-XML SVG (quoted attrs) so cairosvg can rasterize it on a tiny host."""
import os, sys, re
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                                   # deploy: generate.py copied alongside
sys.path.insert(0, os.path.dirname(_HERE))                  # local dev: generate.py in parent
import generate as g   # reuse components + bespoke COMPOSE (no Chrome at import time)

NV="#15233B"; OR="#F2960F"; GR="#2FBF71"; CO="#E0664F"; BL="#EAF0F6"; CR="#FBF8F2"

# ---------------- trade icon library (24x24) — (path, is_fill) ----------------
ICONS = {
 "wrench":("M21 4a5 5 0 0 1-6 6L7 18l-3-3 8-8a5 5 0 0 1 6-6l-3 3 2 2 3-2z",0),
 "house":("M3 11 12 3l9 8M5 10v9h14v-9",0),
 "phone":("M5 4h4l2 5-3 2a11 11 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z",0),
 "calendar":("M5 5h14v15H5zM5 9h14M9 3v4M15 3v4",0),
 "headset":("M5 13v-1a7 7 0 0 1 14 0v1M4 13h4v6H6a2 2 0 0 1-2-2zM20 13h-4v6h2a2 2 0 0 1 2-2z",0),
 "funnel":("M3 4h18l-7 9v6l-4 2v-8z",0),
 "handshake":("M3 9l4-2 5 4 5-4 4 2M7 11l4 3 3-3M11 14l-1 4",0),
 "roof":("M2 12 12 4l10 8M6 11v8h12v-8",0),
 "paint":("M5 4h11v5H5zM10 9v3a2 2 0 0 1-2 2H7v7h3v-7",0),
 "tree":("M12 2l5 8h-3l4 6H6l4-6H7zM12 16v6",0),
 "bug":("M9 8a3 3 0 0 1 6 0M12 8v11M6 12h12M7 7 5 5M17 7l2-2M5 12 3 11M19 12l2-1M7 17l-2 2M17 17l2 2",0),
 "sparkle":("M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z",0),
 "garage":("M3 10 12 5l9 5v9H3zM6 13h12v6H6z",0),
 "fence":("M4 9l2-3 2 3v9H4zM10 9l2-3 2 3v9h-4zM16 9l2-3 2 3v9h-4M3 13h18",0),
 "wave":("M3 8c3-2 6 2 9 0s6-2 9 0M3 14c3-2 6 2 9 0s6-2 9 0",0),
 "floor":("M3 8h18v11H3zM3 13h18M9 8v11M15 8v11",0),
 "window":("M5 4h14v16H5zM12 4v16M5 12h14",0),
 "hammer":("M13 7l4 4-9 9-4-4zM13 7l3-3 4 4-3 3",0),
 "solar":("M5 5h14l-2 9H7zM4 18h16M9 5l-1 9M15 5l1 9M4 9h16",0),
 "mower":("M3 14h10l2-5h4v5h2v3H3zM7 17a2 2 0 1 0 .1 0M15 17a2 2 0 1 0 .1 0",0),
 "snow":("M12 2v20M2 12h20M5 5l14 14M19 5 5 19",0),
 "drop":("M12 3C12 3 5 11 5 15a7 7 0 0 0 14 0C19 11 12 3 12 3z",0),
 "bolt":("M13 2 4 14h6l-2 8 12-13h-7z",1),
 "car":("M5 16l1-6h12l1 6M3 16h18v3h-3v-1H6v1H3zM7 13h10",0),
 "tow":("M3 16l1-6h7l1 6M3 16h11v3H3zM14 9h4l3 4v3h-3",0),
 "truck":("M3 7h11v9H3zM14 10h4l3 3v3h-7zM6 19a2 2 0 1 0 .1 0M17 19a2 2 0 1 0 .1 0",0),
 "box":("M3 7l9-4 9 4-9 4zM3 7v9l9 4 9-4V7M12 11v9",0),
 "key":("M10 10a4 4 0 1 0-.1 0M12 12l8 8M17 17l2 2M19 15l2 2",0),
 "scissors":("M6 6a3 3 0 1 0 .1 0M6 18a3 3 0 1 0 .1 0L20 4M8 8l12 12",0),
 "tooth":("M7 3C4 3 4 7 5 11s1 9 3 9 1-4 3-4 1 4 3 4 2-5 3-9 1-8-3-8c-2 0-2 1-3 1s-1-1-3-1z",0),
 "pulse":("M3 12h4l2-6 4 13 2-7 2 0h4",0),
 "scale":("M12 3v18M7 21h10M12 7l-6 2 3 5a3 3 0 0 1-6 0l3-5M12 7l6 2-3 5a3 3 0 0 0 6 0l-3-5",0),
 "calc":("M6 3h12v18H6zM9 7h6M8 11h2M14 11h2M8 15h2M14 14v4",0),
 "dumbbell":("M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10",0),
 "paw":("M6 12a2 2 0 1 0 .1 0M18 12a2 2 0 1 0 .1 0M9 7a2 2 0 1 0 .1 0M15 7a2 2 0 1 0 .1 0M12 13c-3 0-5 2-5 4a3 3 0 0 0 3 3h4a3 3 0 0 0 3-3c0-2-2-4-5-4z",0),
 "camera":("M4 8h3l2-2h6l2 2h3v11H4zM12 16a3 3 0 1 0 .1 0",0),
 "shield":("M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z",0),
 "spray":("M5 8h6l8-3v12l-8-3H5zM5 12H3M9 4h3",0),
}

# ---------------- keyword → slug classifier ----------------
# Priority: a SPECIFIC TRADE always wins over the generic THEME (every Soro title contains a
# theme like "missed call"/"lead response"/"booking"; the trade is what should drive the image).
BESPOKE = set(g.COMPOSE.keys())
HVAC="hvac-missed-call-lead-recovery-that-books-jobs"
# 1) real top-tier trades → reuse the hand-built bespoke scenes
TRADE_BESPOKE = {
 "hvac":HVAC,"furnace":HVAC,"air condition":HVAC,"heating":HVAC,"a/c":HVAC,
 "plumb":"24-7-ai-answering-service-for-plumbers","electric":"electrician-text-back-automation-that-books-jobs",
 "roof":"roofer-inbound-lead-follow-up-automation","locksmith":"locksmith-after-hours-lead-response-that-wins",
}
# 2) long-tail trades → generic scene with this icon (everything local)
TRADE_ICON = {
 "paint":"paint","landscap":"tree","lawn":"mower","tree service":"tree","pest":"bug","exterminat":"bug",
 "clean":"sparkle","maid":"sparkle","janitor":"sparkle","carpet":"sparkle","garage door":"garage",
 "fenc":"fence","pool":"wave","floor":"floor","tile":"floor","window":"window","glass":"window",
 "handyman":"hammer","carpentr":"hammer","remodel":"hammer","solar":"solar","gutter":"roof","masonry":"house",
 "concrete":"house","pressure wash":"spray","power wash":"spray","automotive":"car","auto repair":"car",
 "auto body":"car","car wash":"car","mechanic":"car","detailing":"car",
 "towing":"tow","moving":"truck","junk":"box","haul":"box","salon":"scissors","barber":"scissors","hair":"scissors",
 "dent":"tooth","ortho":"tooth","chiro":"pulse","med spa":"pulse","medspa":"pulse","clinic":"pulse","therap":"pulse",
 "law":"scale","attorney":"scale","legal":"scale","account":"calc","bookkeep":"calc","tax ":"calc",
 "real estate":"house","realtor":"house","fitness":"dumbbell","gym":"dumbbell","personal train":"dumbbell",
 "pet":"paw","vet":"paw","groom":"paw","photo":"camera","security":"shield","alarm":"shield","appliance":"wrench",
 "garage":"garage","irrigation":"drop","sprinkler":"drop","septic":"drop","drain":"drop","water heater":"drop",
}
# 3) theme-only fallback (titles with NO specific trade) → bespoke story scenes
THEME_BESPOKE = {
 "missed call":"how-to-stop-losing-leads-from-missed-calls","qualif":"ai-lead-qualification-for-home-services",
 "after hours":"after-hours-answering-service-for-contractors","after-hours":"after-hours-answering-service-for-contractors",
 "answering":"after-hours-answering-service-for-contractors","estimate":"automated-estimate-booking-for-contractors",
 "booking":"automated-estimate-booking-for-contractors","schedul":"automated-estimate-booking-for-contractors",
 "contractor":"best-lead-response-system-for-contractors","service business":"best-lead-response-system-for-contractors",
 "lead response":"best-lead-response-system-for-contractors","lead":"best-lead-response-system-for-contractors",
}
def classify(title):
    t=(title or "").lower()
    for kw,slug in TRADE_BESPOKE.items():
        if kw in t: return slug, True
    for kw,slug in TRADE_ICON.items():
        if kw in t: return slug, False
    for kw,slug in THEME_BESPOKE.items():
        if kw in t: return slug, True
    return "wrench", False   # default generic local-service icon

# ---------------- generic icon scene (any vertical) ----------------
def _icon_svg(path,fill,x,y,size,stroke="#fff"):
    inner = (f'<path d="{path}" fill="{stroke}"/>' if fill else
             f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24">{inner}</svg>'

def generic_scene(icon_slug, seed=0, night=False):
    path,fill = ICONS.get(icon_slug, ICONS["wrench"])
    left = (seed % 2 == 0)          # tile side alternates
    tcx = 700 if left else 500
    tile = (f'<circle cx="{tcx}" cy="330" r="150" fill="url(#glow)"/>'
            f'<rect x="{tcx-95}" y="235" width="190" height="190" rx="46" fill="{NV}"/>'
            + _icon_svg(path,fill,tcx-58,272,116)
            + f'<circle cx="{tcx+72}" cy="252" r="17" fill="{OR}"/><circle cx="{tcx+72}" cy="252" r="17" fill="none" stroke="{NV}" stroke-width="3"/>'
            + g.badge_check(tcx+72,252,9))
    sx = 180 if left else 860       # supporting cluster opposite the tile
    supports = g.missed_tag(sx,196) + g.card_booked(sx,360)
    link = g.spark(tcx-95 if left else tcx+95, 330, sx+150 if left else sx, 410)
    return tile + supports + link

# ---------------- assemble + rasterize-ready SVG ----------------
def _wrap(body, night, seed):
    gx = "82%" if seed % 2 == 0 else "18%"
    if night:
        sky = ('<ellipse cx="600" cy="150" rx="640" ry="220" fill="#2A3A57" opacity="0.12"/>'
               + g.stars([(120,80,2.6),(1080,70,2.2),(60,150,2),(1040,150,2.4)]))
    else:
        cx = 1010 if seed % 2 == 0 else 190
        sky = f'<circle cx="{cx}" cy="120" r="150" fill="#F4DFC2" opacity="0.5"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">'
      f'<defs>'
      f'<radialGradient id="paper" cx="{gx}" cy="6%" r="120%"><stop offset="0" stop-color="#FDEAD0"/><stop offset="55%" stop-color="#FBF8F2"/></radialGradient>'
      f'<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#F2960F" stop-opacity="0.26"/><stop offset="70%" stop-color="#F2960F" stop-opacity="0"/></radialGradient>'
      f'<linearGradient id="screen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FBF6EE"/></linearGradient>'
      f'</defs>'
      f'<rect width="1200" height="675" fill="url(#paper)"/>{sky}'
      f'{g.ground(330,180)}{g.ground(860,210)}{body}</svg>')

_ATTR = re.compile(r'(\s[\w:-]+)=([^\s"\'>]+)')
def _xml_safe(svg):  # quote any bare HTML-style attributes so it's well-formed XML
    return _ATTR.sub(lambda m: f'{m.group(1)}="{m.group(2)}"', svg)

def title_to_svg(title, seed=0):
    slug, bespoke = classify(title)
    if bespoke:
        fn, night = g.COMPOSE[slug]
        body = fn(seed % 2)
    else:
        night = ("after hours" in (title or "").lower()) or ("24/7" in (title or "")) or ("overnight" in (title or "").lower())
        body = generic_scene(slug, seed=seed, night=night)
    return _xml_safe(_wrap(body, night, seed)), slug, bespoke
