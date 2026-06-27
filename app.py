#!/usr/bin/env python3
"""MinuteLead featured-image render API.
  GET /featured?title=<post title>&seed=<int>&w=<width>  -> image/png (1200x675 by default)
  GET /health                                            -> {"ok": true}
Classifies the title to a trade scene and rasterizes the SVG with cairosvg (no Chrome)."""
import hashlib, cairosvg, mlscene
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse

app = FastAPI(title="MinuteLead Render")

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
    return Response(content=png, media_type="image/png",
                    headers={"X-Scene": slug, "X-Bespoke": str(bespoke),
                             "Content-Disposition": 'inline; filename="featured.png"'})
