#!/usr/bin/env python3
"""MinuteLead featured-image render API.
  GET /featured?title=<post title>&seed=<int>&w=<width>  -> image/png (1200x675 by default)
  GET /health                                            -> {"ok": true}
Classifies the title to a trade scene and rasterizes the SVG with cairosvg (no Chrome)."""
import hashlib, re, cairosvg, mlscene, stock
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse

app = FastAPI(title="MinuteLead Render")

def _slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return (s[:60].rstrip("-")) or "minutelead-featured"

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/featured")
def featured(title: str = "", seed: int = -1, w: int = 1200):
    if seed < 0:                                   # deterministic per-title if Make sends no seed
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 100000
    try:
        svg, slug, bespoke = mlscene.title_to_svg(title, seed)
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=int(w * 9 / 16))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    fname = f"{_slugify(title)}.png"               # media filename from the post title
    return Response(content=png, media_type="image/png",
                    headers={"X-Scene": slug, "X-Bespoke": str(bespoke),
                             "Content-Disposition": f'inline; filename="{fname}"'})

@app.get("/stock")
def stock_route(title: str = "", seed: int = -1, w: int = 1200):
    if seed < 0:
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 100000
    fname = f"{_slugify(title)}.jpg"
    try:
        jpg, credit = stock.stock_featured(title, seed, w)
        credit = credit.encode("latin-1", "ignore").decode("latin-1")
        return Response(content=jpg, media_type="image/jpeg",
                        headers={"X-Photo-Credit": credit[:400], "X-Source": "pexels",
                                 "Content-Disposition": f'inline; filename="{fname}"'})
    except Exception as e:
        # fall back to the branded scene so the pipeline never breaks
        resp = featured(title, seed, w)
        reason = f"{type(e).__name__}: {e}"[:300].encode("latin-1", "ignore").decode("latin-1")
        resp.headers["X-Fallback-Reason"] = reason
        resp.headers["X-Key-Present"] = "yes" if stock.PEXELS_KEY else "no"
        return resp

