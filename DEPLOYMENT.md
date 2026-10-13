# Vercel deployment

Deploy from the repository root with the FastAPI framework preset. The explicit
`tool.vercel.entrypoint` selects `web_app:app`; the root `app.py` and `api/`
directory are older deployment paths and are excluded. Python 3.12 matches CI.
Runtime dependencies come from the root `requirements.txt`.

The homepage, `/health`, local code templates, and webhook inspection work
without provider credentials. AI generation, documentation answers, and error
diagnosis require `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` in the deployment's
environment. Use an account-supported model. Do not add keys to source control.
No deployment or fixture test establishes live provider availability.

After deployment, verify `/health`, the homepage and static assets, JSON and
form submissions to `/api/generate`, and `/api/webhook`. Without AI credentials,
provider-dependent requests must return a clear 503 error.
