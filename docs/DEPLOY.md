# Deployment

## Netlify (recommended — works with a private repo)

The site is a static build: run the scraper, publish the `site/` folder.

1. Connect the GitHub repo at [netlify.com](https://www.netlify.com)
2. Netlify reads `netlify.toml` automatically:
   - **Build:** `pip install -r requirements.txt && python3 scraper/run.py`
   - **Publish:** `site`
3. Optional env vars (Site settings → Environment variables):
   - `CONGRESS_API_KEY` — Congress.gov bills (defaults to `DEMO_KEY`)
   - `REGULATIONS_API_KEY` — Regulations.gov (defaults to `DEMO_KEY`)

Every push to `main` triggers a fresh deploy with updated feed data.

---

## GitHub Pages (requires a public repo)

GitHub Pages is **not available on free private repos**. The workflow in `.github/workflows/deploy.yml` builds on every push and daily cron, but the deploy job only runs when the repo is **public**.

### Enable GitHub Pages

1. **Settings → General → Danger Zone** → change visibility to **Public**
2. **Settings → Pages** → Source: **GitHub Actions**
3. Re-run the workflow: Actions → “Deploy to GitHub Pages” → Run workflow

Live URL: `https://chlocc.github.io/enforcement-radar/`

### Optional secrets (Settings → Secrets and variables → Actions)

| Secret | Purpose |
|--------|---------|
| `CONGRESS_API_KEY` | Congress.gov API (omit to use `DEMO_KEY`) |
| `REGULATIONS_API_KEY` | Regulations.gov API (omit to use `DEMO_KEY`) |

---

## Local preview

```bash
pip install -r requirements.txt
python3 scraper/run.py
python3 serve.py   # http://localhost:8000
```

Copy `.env.example` to `.env` if you want your own API keys locally.
