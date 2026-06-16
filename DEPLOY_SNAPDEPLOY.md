# Deploy with SnapDeploy (template)

This file explains how to deploy this Flask app to SnapDeploy using the provided `Dockerfile` and `snapdeploy.yaml` template.

Prerequisites
- Docker installed locally (for building/testing)
- Access/credentials to your SnapDeploy account (API key or dashboard)
- `requirements.txt` present and valid

Steps
1. (Optional) Build and run locally with Docker to verify:

```bash
docker build -t nia-jaya:local .
docker run -p 8000:8000 --env FLASK_ENV=production --env SUPABASE_URL=${SUPABASE_URL} --env SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY} nia-jaya:local
```

2. Prepare environment variables in SnapDeploy dashboard or via CLI. Required variables:
  - `FLASK_SECRET_KEY` (generate a strong random string)
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` (keep secret)
  - `SESSION_COOKIE_SECURE` (true when using HTTPS)

3. Upload repository to SnapDeploy (connect Git) or push a Docker image and use `snapdeploy.yaml` to configure service.

4. Deploy and monitor logs. Verify the app starts and `Config.validate()` does not fail (ensure `SUPABASE_SERVICE_ROLE_KEY` is set).

5. After successful deploy, test login and key routes (`/barang`, `/keuangan`, `/stock-opname`).

Notes
- We removed older `render.yaml` and Zeabur docs to avoid confusion; keep backups if needed.
- For production, consider persisting refresh tokens in a secure DB and rotating secrets.
