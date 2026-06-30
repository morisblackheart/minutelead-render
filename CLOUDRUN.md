# Deploy the MinuteLead render service to Google Cloud Run

This is your **"running on Google Cloud" proof** for the Google for Startups Cloud Program.
The service is already a container; this just stands it up on Cloud Run. It scales to zero, so
it costs ~nothing until a render runs (your daily blog image), and that consumption is real GCP usage.

You have **no local `gcloud` or Docker**, so the easiest path is **Cloud Shell** (browser, gcloud
preinstalled, nothing to install). Cloud Build does the image build — no Docker needed anywhere.

---

## One-time setup (~10 min)

1. **Create a project** at https://console.cloud.google.com (top bar → project dropdown → New Project).
   Note the **Project ID** (e.g. `minutelead-prod`).
2. **Enable billing** on it (Billing → link a billing account). Once your Startup credits are granted,
   they attach to this billing account and get spent first.
3. Open **Cloud Shell** (terminal icon, top-right of the console). It already has `gcloud`.

## Get this code into Cloud Shell

Pick one:
- **From GitHub** (if you push `render_service/` to a repo): `git clone <repo-url> && cd <repo>`
- **Upload**: Cloud Shell → `⋮` menu → *Upload* the contents of `render_service/`, then `cd` into it.

## Deploy

```bash
export PROJECT_ID=<your-project-id>     # e.g. minutelead-prod
export REGION=us-central1               # optional, this is the default
chmod +x deploy-cloudrun.sh
./deploy-cloudrun.sh
```

First deploy builds the image via Cloud Build (~3-4 min). When it finishes it prints your service URL,
e.g. `https://minutelead-render-xxxxxxxx-uc.a.run.app`. Open the printed **Test** URL — you should get a
branded pest-control image, same as today.

## Point your automation at it

In the **Make** scenario, change the render HTTP module URL from
`https://minutelead-render.onrender.com/featured?...` to your new
`https://minutelead-render-...run.app/featured?...` (keep the same `?title=&seed=` query).
That's the only change; everything downstream is identical.

---

## What this gives the application

> "Our blog/content rendering service runs in production on **Cloud Run**, built from a container via
> **Cloud Build**."

True the moment this finishes. It's Tier 0 of the GCP plan — the prospecting pipeline (Cloud Run job +
BigQuery + Places API) and the Vertex AI / Gemini lead-scoring layer are the next two pieces.

## Notes
- **Public on purpose** (`--allow-unauthenticated`): Make calls it directly, same as the Render setup.
  If you want to lock it down later, put it behind an API key or Cloud Run IAM + a service account.
- **Cost**: at one render/day this stays in cents/month — well inside the Start-tier credits.
- **Updating scenes**: edit `mlscene.py` / `generate.py`, re-run `./deploy-cloudrun.sh`.
- You can keep the Render deployment live in parallel during the switch; cut over when the Cloud Run
  URL tests good, then retire Render.
