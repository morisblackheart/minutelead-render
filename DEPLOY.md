# Deploy the MinuteLead render service (one-time, ~10 min)

This folder is self-contained: `app.py` (API), `mlscene.py` (engine), `generate.py` (scene art),
`requirements.txt`, `Dockerfile`, `render.yaml`. Host it on **Render.com** free tier.

## Steps
1. **Put this folder in a Git repo.**
   - Easiest: a new GitHub repo containing the *contents* of `render_service/` at the repo root.
   - (Claude can do this for you with the `gh` CLI if you're signed in — just ask.)
2. **Create a Render account** → https://render.com (free, GitHub sign-in).
3. **New → Blueprint** → connect the repo. Render reads `render.yaml` and creates the web service
   (Docker, free plan, health check `/health`). Click **Apply**.
4. Wait for the first build (~3-4 min). You'll get a URL like
   `https://minutelead-render.onrender.com`.
5. **Test it** in a browser:
   `https://minutelead-render.onrender.com/featured?title=Pest%20Control%20Missed%20Call&seed=3`
   → you should see a branded pest-control image.

## Endpoint
```
GET /featured?title=<post title>&seed=<int>&w=<width>
   → image/png (1200x675).  seed drives layout variation (pass the WP post id).
   Response header X-Scene tells you which scene was chosen.
GET /health → {"ok": true}
```

## Notes
- **Free tier sleeps** after 15 min idle; first request after sleep takes ~30-50s to wake.
  For a once-a-day post that's fine. (Upgrade to the $7/mo plan for always-on if you want.)
- **Adding/adjusting trades:** edit `mlscene.py` (`TRADE_ICON` keyword map / `ICONS` library),
  push to the repo, Render auto-deploys. New verticals "just work" via the default `wrench` icon
  even before you add a specific one.
- If you change the bespoke scenes in the main `generate.py`, re-copy it here:
  `cp ../generate.py ./generate.py` and push.
