# Calendar AI — Clockwise Replacement

AI-powered calendar management for Circle employees. Replaces Clockwise with self-hosted,
Google Calendar-connected features backed by Claude AI.

## Features

- **Focus Time Blocks** — Claude analyzes your week and creates optimal deep work blocks
- **Meeting Optimization** — AI suggests (or auto-applies) meeting moves to reduce fragmentation
- **Smart Scheduling Links** — Calendly-style booking pages respecting your availability and focus time
- **Slack Status Sync** — Auto-update your Slack status based on your current calendar event
- **Gong Auto-Record** — Detect Teams meetings and auto-add `circle@assistant.gong.io` as attendee

## Quick Start (Local Dev)

### Prerequisites
- Docker + Docker Compose
- Google Cloud Console project with OAuth 2.0 credentials
- Slack app with OAuth and slash commands
- Anthropic API key

### 1. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_SIGNING_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
ANTHROPIC_API_KEY=sk-ant-...

# Generate an encryption key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<output above>

# Generate a secret key:
python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<output above>
```

### 2. Start everything

```bash
docker-compose up --build
```

This will:
1. Start PostgreSQL
2. Run Alembic migrations (create all tables)
3. Start FastAPI backend on `http://localhost:8000`
4. Start React frontend on `http://localhost:5173`

### 3. Connect your calendar

1. Open `http://localhost:5173`
2. Click **Sign in with Google** — authorize Calendar access
3. Go to **Preferences** to set your work hours, focus goals, etc.
4. Click **Optimize with AI** on the dashboard

### 4. Connect Slack (optional)

In the Dashboard, click the Slack connection link (or go to `/auth/slack/login`).
Register these slash commands in your Slack app pointing to `POST {BACKEND_URL}/slack/commands`:
- `/focus-time`
- `/optimize`
- `/schedule`
- `/calendar`
- `/connect-calendar`

## API Reference

- `GET /auth/google/login` — Start Google OAuth
- `POST /optimize/run` — Run Claude optimization for current user
- `GET /calendar/events?days=7` — Fetch calendar events
- `POST /calendar/sync-gong` — Sync Gong invites for Teams meetings
- `GET /schedule/{slug}/availability` — Public: get available slots
- `POST /schedule/{slug}/book` — Public: book a slot
- `POST /slack/commands` — Slack slash command handler
- `GET /health` — Health check

## Production Deployment (Google Cloud Run)

### Prerequisites
- GCP project with Cloud Run, Cloud SQL (PostgreSQL), Cloud Build, Secret Manager enabled
- `gcloud` CLI configured

### 1. Create secrets

```bash
for secret in secret-key encryption-key database-url google-client-id google-client-secret \
  slack-client-id slack-client-secret slack-signing-secret slack-bot-token anthropic-api-key; do
  gcloud secrets create calai-$secret --replication-policy="automatic"
done
```

Then populate each secret with `gcloud secrets versions add calai-{name} --data-file=-`.

### 2. Deploy via Cloud Build

```bash
gcloud builds submit --config cloudbuild.yaml
```

### 3. Set up Cloud Scheduler for daily optimization

```bash
gcloud scheduler jobs create http calai-daily-optimize \
  --schedule="0 6 * * 1-5" \
  --uri="https://calai-backend-URL/optimize/run-all" \
  --message-body="" \
  --oidc-service-account-email=SA@PROJECT.iam.gserviceaccount.com \
  --location=us-central1
```

### 4. Update Google & Slack OAuth redirect URIs to production URLs

## Architecture

```
Browser → React (Vite) → FastAPI (Python) → PostgreSQL
                              ↓
                         Google Calendar API
                         Slack API
                         Claude API (Anthropic)
```

All OAuth tokens are AES-256 encrypted at rest using Fernet before storage in PostgreSQL.
The `ENCRYPTION_KEY` environment variable is the only decryption key — never commit it.

## Security Notes

- Tokens encrypted with Fernet (AES-256-CBC + HMAC-SHA256)
- Sessions are signed cookies (HttpOnly, SameSite=Lax, Secure in prod)
- Slack requests verified via HMAC signature
- CORS restricted to `FRONTEND_URL`
- In production, `ENVIRONMENT=production` enables secure cookie flags and OIDC auth for scheduled jobs
