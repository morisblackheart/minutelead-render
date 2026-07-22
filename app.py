#!/usr/bin/env python3
"""MinuteLead featured-image render API.
  GET /featured?title=<post title>&seed=<int>&w=<width>  -> image/png (1200x675 by default)
  GET /health                                            -> {"ok": true}
Classifies the title to a trade scene and rasterizes the SVG with cairosvg (no Chrome)."""
import hashlib, re, cairosvg, mlscene, stock, gptimg
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse

app = FastAPI(title="MinuteLead Render")

def _slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return (s[:60].rstrip("-")) or "minutelead-featured"

@app.get("/health")
def health():
    import generate as _g
    return {"ok": True, "code": "openai-v12-cast", "scenes": len(_g.COMPOSE),
            "openai": bool(gptimg.OPENAI_KEY)}

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
    """Vector featured image with palette rotation (photo mode retired by owner preference)."""
    return featured(title, seed, w)

@app.get("/ai")
def ai_route(title: str = "", seed: int = -1, w: int = 1200, quality: str = "medium",
             style: str = "photo", grad: int = 0, pid: int = 0, spread: int = -1):
    """OpenAI (gpt-image-1) featured image. style=photo (photorealistic, default) or
    style=illus (flat brand vector). grad=1 adds the navy bottom gradient under the logo.
    Falls back to the vector scene on ANY failure so the daily pipeline never breaks
    (reason exposed in X-Fallback-Reason)."""
    if seed < 0:
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 100000
    try:
        png, theme, variant, subject = gptimg.gen(title, seed, w, quality=quality,
                                                  style=style, grad=bool(grad), pid=pid,
                                                  spread=None if spread < 0 else spread)
        fname = f"{_slugify(title)}-ai1.png"
        return Response(content=png, media_type="image/png",
                        headers={"X-Source": "openai", "X-Theme": theme,
                                 "X-Style": style, "X-Variant": str(variant),
                                 "X-Bespoke": "1" if subject != "library" else "0",
                                 "X-Subject": subject[:180].encode("ascii", "ignore").decode(),
                                 "Content-Disposition": f'inline; filename="{fname}"'})
    except Exception as e:
        resp = featured(title, seed, w)          # vector fallback tier
        resp.headers["X-Source"] = "vector-fallback"
        resp.headers["X-Fallback-Reason"] = str(e)[:300]
        return resp
