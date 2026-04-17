# Happy Hour Hub — Project Memory

## What This Is
A Flask web app displaying Berlin happy hour deals. Community features include upvoting, hidden gem submissions, and user accounts. See README.md for full documentation.

## Entry Points
- Development: `python main.py` or `gunicorn --bind 0.0.0.0:5000 --reload main:app`
- Production: `gunicorn wsgi:application` (Procfile + wsgi.py)

## Architecture
- **app.py** — All Flask routes (1,561 lines), in-memory cache (5-min TTL), image generation
- **db.py** — DealDB wraps Replit KV store (`replit.db`); business name is the primary key
- **models.py** — User model (Flask-Login, Werkzeug hashing), data stored in KV store
- **scraper.py** — YelpScraper generates deals from a hardcoded Berlin venue list (not live Yelp)
- **ai_recommendations.py** — OpenAI venue descriptions
- **utils.py** — `get_time_ago()` Jinja filter (defined twice — second definition wins)

## Key Design Decisions
- Storage: Replit KV store for all deals and users. PostgreSQL is configured (DATABASE_URL set) but unused for deal/user data.
- Deal primary key = business name string. Duplicate name = overwrite.
- Berlin-only: Non-Berlin deals and USD prices are filtered out at display time.
- Cache is in-process; Gunicorn is set to 1 worker to avoid stale cross-worker cache.
- Color palette customiser saves to localStorage (not server-side).

## Secrets Required at Runtime
- `SESSION_SECRET` — Flask session key
- `OPENAI_API_KEY` — AI venue descriptions

## GitHub
https://github.com/PrinceKeldon/Backyard-Billboards

## Known Issues
- "Backyard Billboards" name appears in some generated image text (cosmetic legacy)
- `utils.py` has duplicate `get_time_ago` function definitions
- `flask-sqlalchemy` installed but not used for deal storage
