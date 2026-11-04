# Avvai heritage UI release candidate

Updated 4 November 2026. This packages the existing app; it does not make unapproved providers or sample listings live.

## Build and run without Docker

From the repository root:

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
.venv/Scripts/python.exe -m uvicorn backend.web:app --host 0.0.0.0 --port 8000 --workers 1
```

On a Linux host, install `backend/requirements.txt` and use `python -m uvicorn` instead of the Windows virtual-environment path. Do not start a second server on an occupied port. The existing Vite development server is separate and is not needed for this build.

The same service serves `/veeramangai`, `/api/*`, `/health` and the frontend assets. Deep links such as `/veeramangai/login` work on reload. Unknown API paths and missing assets remain HTTP 404, not HTML. Use HTTPS through the hosting provider's proxy. Keep one worker/replica for this demo because Journey Watch currently contains process-local state.

## Docker packaging

The root Dockerfile builds the frontend then runs FastAPI as a non-root user. The design asset folder is included. Local `.env` files, training weights and development tooling are excluded from the build context.

Set these **public build arguments** in the host's build settings:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY` (the public anon key, never the service key)
- `VITE_MAPTILER_KEY` (optional public map key)

```powershell
docker build --build-arg VITE_SUPABASE_URL --build-arg VITE_SUPABASE_ANON_KEY --build-arg VITE_MAPTILER_KEY -t avvai .
docker run --rm --env-file .env -p 8000:8000 avvai
```

The unvalued build arguments above read the named variables from the shell environment. Configure them before building. The image supports the host's `PORT` runtime variable. Provider secrets and the Supabase service key belong only in runtime secrets, not build arguments. No Docker engine was available in this session, so the Docker image itself has not been built or run; the compiled frontend and ASGI serving path were checked separately.

## Host configuration that remains necessary

1. Set the public HTTPS address in Supabase Auth's site URL and allowed redirect URLs, including the login confirmation destination. Existing authenticated frontend code uses the same Supabase project as the backend.
2. Set `PUBLIC_BACKEND_URL` to the permanent HTTPS address, replacing the temporary ngrok address. Update external webhook callback addresses to that host.
3. Preserve existing server-side provider keys using the host's secret manager. Do not expose `.env` or the service key through the frontend.
4. Apply and verify the pending database migrations against the intended project before claiming partner offers work. Supply verified partner and NSS records; the UI intentionally excludes sample rows from verified matches.
5. Email notifications: `VM_NOTIFICATIONS_ENABLED` is currently true locally, but `VM_N8N_NOTIFICATIONS_URL` and `VM_N8N_WEBHOOK_SECRET` are absent. Set a valid HTTPS workflow URL, a matching secret of at least 32 characters, configure Gmail OAuth in n8n and verify opt-in delivery before announcing email as live.
6. `VM_N8N_GUIDE_URL` is present, but `N8N_ORCHESTRATOR_URL` is absent. These are different paths. The browser check received fallback agent guidance, not evidence of Gemini/Hermes inference. Verify the model and workflow separately.
7. Textbee credentials are present; actual SMS delivery was not tested or triggered in this UI pass. Test with an explicitly consenting recipient. Do not equate configuration with confirmed delivery.
8. DigiLocker is an official external link, not OAuth document retrieval. Partner approval is still needed for API access.
9. A local Hermes/Ollama process is not included in the Docker image. A remote deployment needs an intentionally configured reachable inference service, or it uses the existing fallback. LoRA files do not prove deployed inference.
10. Retain `DEMO_MODE=true` and test-only payment keys for this demonstration. Production needs durable trip scheduling, verified data, an operator contact, retention/deletion procedures and final service terms. The app's new information pages explicitly state these limitations.

## Checks performed

- Production frontend build succeeds; existing chunk-size warnings remain.
- Lint exits successfully with existing warnings.
- 245 backend tests pass, including eight new deep-link/static-serving checks.
- Desktop/mobile browser checks: ten support entries, four selectable histories, Tamil preference persistence, login screen, connections screen, guest request creation and visibility, guest journey-planner link. No browser exceptions or mobile horizontal overflow in the checked flow.
- Agent request returned backend fallback guidance. No external email, SMS, payments or application submissions were sent by these checks.
- Fontshare Satoshi and Clash Display loaded in the browser; local Noto Tamil remains the Tamil/fallback font.

## Historical copy

The home page reuses `frontend/public/veeramangai/queens.png`. It is labelled artistic interpretation. Kundavai is identified as a princess. Source links live with the copy in `HeritagePaths.jsx`: PIB for Velu Nachiyar, Smithsonian for Sembiyan Mahadevi, reporting on Mangammal's public works, and Tamil Nadu Archives for Kundavai's hospital patronage. Their connection to modern app features is our design interpretation, not a historical claim.
