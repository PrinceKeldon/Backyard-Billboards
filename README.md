# Happy Hour Hub

**Happy Hour Hub** is a community-driven Flask web application that aggregates, displays, and curates happy hour deals from bars and restaurants across Berlin, Germany. Users can browse deals by neighbourhood, search by keyword, submit their own discoveries, upvote their favourites, and explore curated "hidden gem" venues — all through a cheerful, colour-customisable interface.

---

## Table of Contents

1. [What the App Does](#what-the-app-does)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Routes & Pages](#routes--pages)
6. [Data Model](#data-model)
7. [Key Modules](#key-modules)
8. [Environment Variables & Secrets](#environment-variables--secrets)
9. [Running the App](#running-the-app)
10. [Deployment](#deployment)
11. [Known Issues & Notes](#known-issues--notes)

---

## What the App Does

Happy Hour Hub is a Berlin-focused directory of happy hour deals. The application:

- Displays a searchable, filterable list of happy hour deals across Berlin's neighbourhoods (districts).
- Lets visitors browse deals active after 10 PM on a dedicated **Late Night Deals** page.
- Showcases a community-curated **Hidden Gems** section for lesser-known venues.
- Lets anyone submit deals manually, and lets logged-in users flag their submission as a hidden gem.
- Allows visitors to **upvote** deals they find valuable.
- Shows a rich **venue detail page** for each deal, including an auto-generated venue image, AI-produced venue description, nearby similar deals, and Google Maps data where available.
- Generates dynamic **Open Graph social-share images** for every deal.
- Offers a **colour palette customiser** so users can personalise the site's theme — stored in their browser's localStorage.

---

## Features

| Feature | Description |
|---|---|
| Deal listing | Paginated, sortable list of all happy hour deals |
| District filter | Filter deals by Berlin neighbourhood (Mitte, Kreuzberg, Neukölln, etc.) |
| Keyword search | Search by venue name, deal text, location, or district |
| Late-night deals | Dedicated view for deals available after 22:00 / 10 PM |
| Hidden Gems | Community-submitted, voted-on secret venues with descriptions and tips |
| Deal submission | Public form to add a new deal; optionally mark it as a hidden gem |
| User accounts | Register, log in, log out via Flask-Login |
| Upvoting | Any visitor can upvote a deal; vote counts are stored persistently |
| Venue detail page | Per-venue page with deal info, AI description, generated image, and similar deals |
| OG image generation | Dynamic JPEG social-share images generated with Pillow |
| AI descriptions | OpenAI-powered venue descriptions and recommendations |
| Colour palette customiser | Choose from Default, Sunset, Ocean, Forest, or Neon themes; changes persist in localStorage |
| Health check endpoint | `/health` endpoint returning app and database status as JSON |
| In-memory caching | 5-minute TTL cache reduces redundant database calls |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web framework | Flask 3.0 |
| Authentication | Flask-Login, Werkzeug password hashing |
| Database | Netlify Database (PostgreSQL-compatible) |
| ORM / DB client | `psycopg2` direct PostgreSQL client |
| AI | OpenAI API (`openai` package) |
| Image generation | Pillow (PIL) |
| Web scraping | Requests, BeautifulSoup4, Trafilatura |
| Frontend | Bootstrap 5 (official CDN), Font Awesome, Vanilla JavaScript |
| Colour theming | Custom JS (`color_palette_v2.js`) + CSS variables + localStorage |
| WSGI server | Gunicorn 23 |
| Deployment | Standard WSGI host / Gunicorn |

---

## Project Structure

```
.
├── app.py                    # Main Flask application — all routes, caching, image generation
├── db.py                     # DealDB class — all database read/write operations
├── models.py                 # User model (Flask-Login integration, password hashing)
├── scraper.py                # YelpScraper — generates Berlin deal data from curated venue list
├── google_maps_scraper.py    # GoogleMapsScraper — enriches deals with Maps data
├── ai_recommendations.py     # OpenAI integration — venue descriptions & recommendations
├── utils.py                  # Helper functions (time-ago formatting, date formatting)
├── wsgi.py                   # Production WSGI entry point (gunicorn uses this)
├── main.py                   # Development entry point (direct Python execution)
├── reset_app.py              # Utility script to clear the database
├── run.py / run.sh           # Alternative run helpers
├── requirements.txt          # Python dependencies
├── Procfile                  # Deployment process definition
├── gunicorn_config.py        # Gunicorn configuration (workers, port binding)
│
├── templates/
│   ├── base.html             # Shared layout — navbar, colour palette modal, flash messages
│   ├── index.html            # Home page — deal cards, filters, search bar
│   ├── deal_detail.html      # Individual venue detail page
│   ├── hidden_gems.html      # Hidden Gems listing with pagination
│   ├── late_night_deals.html # Late-night deals listing
│   ├── submit.html           # Public deal submission form
│   ├── submit_hidden_gem.html# Dedicated hidden gem submission form
│   ├── login.html            # Login page
│   ├── signup.html           # Registration page
│   └── error.html            # Generic error page
│
└── static/
    ├── css/
    │   └── style.css         # Global styles, CSS custom properties for theming
    ├── js/
    │   ├── color_palette_v2.js  # Colour palette system — predefined themes, localStorage
    │   ├── color_palette.js     # Legacy palette file (superseded by v2)
    │   ├── ai_recommendations.js # Client-side AI recommendation display helpers
    │   └── main.js              # General UI interactions
    └── img/
        └── og-default.jpg    # Fallback Open Graph image
```

---

## Routes & Pages

| Method | Route | Page / Action | Auth required |
|---|---|---|---|
| GET | `/` | Home — deal listing with search and district filter | No |
| POST | `/scrape` | Trigger deal scraping (adds new deals to DB) | No |
| GET | `/late-night-deals` | Deals available after 22:00 | No |
| GET | `/hidden-gems` | Community hidden gems, paginated (10 per page) | No |
| GET | `/deal/<business_name>` | Individual venue detail page | No |
| GET | `/submit` | Manual deal submission form | No |
| POST | `/submit` | Process a new deal (regular or hidden gem) | No |
| GET | `/submit-hidden-gem` | Dedicated hidden gem submission form | No |
| POST | `/submit-hidden-gem` | Process a hidden gem submission | Yes (login required) |
| POST | `/upvote/<business_name>` | Increment upvote count for a deal | No |
| GET | `/login` | Login page | No |
| POST | `/login` | Authenticate user | No |
| GET | `/signup` | Registration page | No |
| POST | `/signup` | Create new user account | No |
| GET | `/logout` | Log out current user | Yes |
| GET | `/health` | JSON health check (DB status, deal count) | No |
| GET | `/og-image/<business_name>` | Dynamic OG social-share image (JPEG) | No |

---

## Data Model

All data is stored in **Netlify Database** (PostgreSQL-compatible). The `db.py` module now uses `psycopg2` to read and write users, venues, and deals.

See `db/schema.sql` for an example PostgreSQL schema compatible with the current `db.py` table layout.

### Deal record

The key is the **business name** (string). The value is a dictionary:

| Field | Type | Description |
|---|---|---|
| `deal` | str | Full deal description text |
| `location` | str | Street address |
| `scraped_at` | str | ISO timestamp of when it was added |
| `has_accurate_location` | bool | Whether the address is verified |
| `votes` | int | Community upvote count |
| `district` | str | Berlin neighbourhood (e.g. "Kreuzberg") |
| `rating` | float | Google Maps star rating (optional) |
| `reviews_count` | int | Number of Google Maps reviews (optional) |
| `place_type` | str | Establishment type (optional) |
| `price_level` | int | Price level 1–4 (optional) |
| `google_maps_url` | str | Link to Google Maps page (optional) |
| `is_hidden_gem` | bool | Whether it is a community hidden gem |
| `hidden_gem_description` | str | Why this place is special (optional) |
| `hidden_gem_tips` | str | Insider tips (optional) |
| `submitted_by` | str | Username of submitter (optional) |
| `submission_type` | str | `"regular"` or `"hidden_gem"` |

### User record

The key is the **username** (string). The value is a dictionary:

| Field | Type | Description |
|---|---|---|
| `username` | str | Unique login name |
| `email` | str | Email address |
| `password_hash` | str | Werkzeug-hashed password |

---

## Key Modules

### `app.py`
The heart of the application (1,561 lines). Contains:
- Flask app initialisation and configuration
- In-memory cache (`cache` dict, 5-minute TTL, functions `get_cached_data` / `clear_cache`)
- All route handlers
- `generate_venue_image()` — creates a styled 1200×630 JPEG for venue detail pages using Pillow
- `generate_og_deal_image()` — creates Open Graph share images
- Rate limiter (2-second minimum interval between scrape triggers)
- Jinja2 custom filters (`urlencode`, `to_time_ago`)

### `db.py` — `DealDB`
Wraps Netlify Database / PostgreSQL via `psycopg2`. Key methods:

| Method | Description |
|---|---|
| `add_deal(name, deal, location, **kwargs)` | Insert or overwrite a deal record |
| `get_deal(name)` | Fetch a single deal by business name |
| `get_all_deals()` | Return all deal records as a list, sorted newest-first |
| `delete_deal(name)` | Remove a deal |
| `upvote_deal(name)` | Increment the vote counter |
| `get_top_voted_deals(limit)` | Return deals sorted by vote count |
| `get_hidden_gems(district, limit)` | Return hidden gem deals, sorted by votes |
| `get_late_night_deals(limit)` | Return deals active after 22:00, detected by keyword matching |
| `add_user(username, email, password_hash)` | Create a user record |
| `get_user(username)` | Retrieve a user record |

### `scraper.py` — `YelpScraper`
Generates deal data from a **curated, hardcoded dataset** of real Berlin venues (not live Yelp scraping). For Berlin, it uses precise street addresses and district tags. For other cities it falls back to randomly generated plausible venue names. Key methods:

- `get_region_for_location(location)` — maps a location string to a regional data set
- `generate_deals_for_region(region_data, location, count)` — produces deal records
- `scrape(location, enrich_with_google)` — top-level method called by the `/scrape` route

### `models.py` — `User`
Flask-Login `UserMixin` subclass. Stores no data itself; delegates all persistence to `DealDB`. Key static methods: `User.get(user_id)`, `User.create(username, email, password)`.

### `ai_recommendations.py`
Calls the OpenAI API to generate:
- `get_ai_recommendation(deal_data)` — personalised recommendation text for a venue
- `get_venue_description(business_name, deal_data)` — a short atmospheric venue description

### `color_palette_v2.js`
Client-side theming engine. On page load it:
1. Reads the saved palette name from `localStorage` (key: `hhh_current_palette`)
2. Applies the palette by updating CSS custom properties on `document.documentElement`
3. Populates the palette selector dropdown in the modal
4. Listens for changes and persists selections

Five built-in palettes: **Default** (yellow/red/cream), **Sunset**, **Ocean**, **Forest**, **Neon**.

---

## Environment Variables & Secrets

| Secret / Variable | Purpose |
|---|---|
| `SESSION_SECRET` | Flask session signing key |
| `OPENAI_API_KEY` | OpenAI API access for AI venue descriptions |
| `DATABASE_URL` | PostgreSQL URL for Netlify Database / Postgres storage |
| `NETLIFY_DB_URL` | Alternative Netlify Database URL environment variable |
| `PGDATABASE`, `PGHOST`, `PGPASSWORD`, `PGPORT`, `PGUSER` | PostgreSQL connection parts for database access if your deployment uses them |
| `TELEGRAM_BOT_TOKEN` | Legacy Telegram integration (removed from active code) |
| `TELEGRAM_CHAT_ID` | Legacy Telegram integration (removed from active code) |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Used to push code to GitHub (not needed at runtime) |

App-level flags set in `app.py` at startup (not secrets):

| Variable | Value | Meaning |
|---|---|---|
| `ENABLE_GOOGLE_MAPS_SCRAPING` | `"true"` | Enables Google Maps enrichment on scrape |
| `GOOGLE_MAPS_ENRICHMENT_LIMIT` | `"2"` | Max deals enriched per scrape request |
| `DEFAULT_LOCATION` | `"Berlin, Germany"` | Default scraping location |
| `RESTRICT_TO_BERLIN` | `"true"` | Filters out non-Berlin deals at display time |

---

## Running the App

### Development (direct Python)

```bash
python main.py
```

The app starts on `http://localhost:5000` with Flask's debug mode enabled when running via `python main.py`.

### Development (Gunicorn, standard workflow)

The **Start application** workflow runs:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Production (WSGI entry point)

```bash
gunicorn wsgi:application
```

`wsgi.py` imports `app` from `app.py` and exposes it as `application` for WSGI compatibility. The `Procfile` uses:

```
web: gunicorn wsgi:application
```

### Adding Deals

Navigate to `/submit` and fill in the business name, deal description, address, and district. Optionally tick **"Hidden Gem"** to have it appear on the Hidden Gems page (requires a description).

To populate the database with the built-in Berlin venue dataset, POST to `/scrape` from the home page's admin panel or directly with:

```bash
curl -X POST http://localhost:5000/scrape -d "location=Berlin"
```

---

## Deployment

The front end is now built for standard web hosting and uses official Bootstrap CDN assets rather than Replit-specific theme styles. The project can be deployed to any WSGI-compatible host using `gunicorn wsgi:application`. Gunicorn binds to the `PORT` environment variable (defaulting to `8000` in `gunicorn_config.py`, `5000` in the workflow command).

### Deploying to Netlify

1. **Connect your repository** to Netlify via GitHub, GitLab, or Bitbucket
2. **Set build command:** `pip install -r requirements.txt && python main.py` (or use a Netlify Functions wrapper)
3. **Set publish directory:** root or specify as needed
4. **Add environment variables** in Netlify UI (Settings → Build & deploy → Environment):
   - `NETLIFY_DB_URL`: Your Netlify Database PostgreSQL connection string
   - `SESSION_SECRET`: Flask session signing key (random string)
   - `OPENAI_API_KEY`: OpenAI API key for AI recommendations

For Netlify Functions (recommended for Python):
- Use `netlify/functions/app.py` or similar structure
- Ensure `db.py` imports work in the Functions context
- Reference `NETLIFY_DB_URL` in environment variables

The GitHub repository mirror is at: https://github.com/PrinceKeldon/Backyard-Billboards

---

## Known Issues & Notes

- **Deal data is generated, not live-scraped.** The `YelpScraper` class produces deals from a hardcoded list of 30+ real Berlin venues. There is no live connection to Yelp or Google Maps search — Google Maps data is used only to enrich existing entries when the scrape endpoint is called.
- **UUID-based IDs.** Venues and deals are now created with UUIDs, so duplicate names no longer serve as the primary key in the Netlify Database storage.
- **"Backyard Billboards" references.** Some internal strings (generated images, footer text) still reference the earlier project name. These are cosmetic and do not affect functionality.
- **Duplicate `get_time_ago` in `utils.py`.** The file defines the function twice (different implementations). The second definition takes precedence at runtime.
- **Cache is in-process.** With multiple Gunicorn workers, each worker has its own cache. Setting `workers = 1` in `gunicorn_config.py` avoids stale cross-worker cache issues.
- **Color palette changes are browser-local.** The chosen theme is saved in `localStorage` and does not sync across devices or users.
