# Tastify — Hybrid Restaurant Recommendation System

A full-stack hybrid recommendation engine that combines **content-based filtering** and **collaborative filtering** to deliver personalized restaurant recommendations.

> Built by **Ekagra Ramola** & **Hitesh Kandari**

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  React +    │     │           FastAPI Backend                │
│  Vite       │────▶│                                          │
│  Frontend   │     │  ┌────────────┐  ┌───────────────────┐   │
│  (Port 3000)│     │  │ Auth/CRUD  │  │ Recommendation    │   │
│             │◀────│  │ Routes     │  │ Engine            │   │
└─────────────┘     │  └────────────┘  │  ┌─────────────┐  │   │
                    │                  │  │Content-Based│  │   │
                    │  ┌────────────┐  │  │(Cosine Sim) │  │   │
                    │  │ MongoDB    │  │  ├─────────────┤  │   │
                    │  │ (hybrid_rec│  │  │Collaborative│  │   │
                    │  │  database) │  │  │(Pearson+SVD)│  │   │
                    │  └────────────┘  │  ├─────────────┤  │   │
                    │                  │  │Hybrid Scorer│  │   │
                    │                  │  │(α weighting)│  │   │
                    │                  │  └─────────────┘  │   │
                    │                  └───────────────────┘   │
                    │              (Port 8000)                 │
                    └──────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, React Router, Axios, Lucide Icons |
| Backend | Python, FastAPI, Uvicorn |
| Database | MongoDB (via Motor async driver) |
| ML/Engine | Pandas, NumPy, Scikit-learn (cosine similarity, TruncatedSVD) |
| Auth | JWT (python-jose), bcrypt |

## Hybrid Scoring Formula

```
Hybrid Score = α × Content Score + (1 − α) × Collaborative Score
```

- **α = 1.0** → New user (pure content-based, cold-start)
- **α = 0.75** → 1–4 ratings
- **α = 0.60** → 5–9 ratings
- **α = 0.50** → 10+ ratings (full hybrid)

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running on `localhost:27017`

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Seed Database
```bash
cd backend
python -m seed.seed_data
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Demo Credentials (after seeding)
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hybridrec.com | password123 |
| User | any seeded user, e.g. `priya.patel@example.com` | password123 |

## Deploying to Render

A `render.yaml` Blueprint is included at the repo root. It provisions two services:

- **`tastify-api`** — FastAPI backend (Python web service, SQLAlchemy + PostgreSQL)
- **`tastify-web`** — React frontend (static site)

### Steps

1. **PostgreSQL database** (free, no card required — pick one):
   - **Neon** (recommended): [neon.tech](https://neon.tech) → sign up → **Create project** → copy the connection string
   - **Supabase**: [supabase.com](https://supabase.com) → new project → **Connect** → copy the URI
   - **Render Postgres**: Render Dashboard → **New → PostgreSQL** (free tier expires after ~30 days)
   - Convert the string for SQLAlchemy: `postgresql://user:pass@host/db` → `postgresql+asyncpg://user:pass@host/db`

2. **Deploy via Blueprint**:
   - Push this repo to GitHub
   - Render Dashboard → **New → Blueprint** → select the repo
   - Render reads `render.yaml` and creates both services
   - Fill in the `sync: false` env vars on `tastify-api`:
     - `DATABASE_URL` — your Postgres connection string (with `+asyncpg`)
     - `SECRET_KEY` — `openssl rand -hex 32`
   - On `tastify-web` → **Settings → Redirects/Rewrites**, add:
     - Source `/*` → Destination `/index.html` → Action **Rewrite** (required for React Router deep links)

3. **Seed the production database** (run locally once):
   ```powershell
   cd backend
   $env:DATABASE_URL="postgresql+asyncpg://user:pass@host/dbname"  # PowerShell
   python -m seed.seed_data
   ```

4. **Verify**: open the `tastify-web` URL — the frontend auto-connects to `tastify-api` via `VITE_API_URL` (injected from the backend service's host).

> **Note**: Render free-tier services spin down after ~15 min idle (first request takes ~30–60s to wake). Upgrade to a paid instance for always-on availability.
> **Local dev**: no database setup needed — the backend defaults to a local SQLite file (`backend/hybrid_rec.db`). Tables are auto-created on startup; run `python -m seed.seed_data` once to populate data.

## Features

- 🧠 **Content-Based Filtering** — Cosine similarity on cuisine, price, ambience, tags
- 👥 **Collaborative Filtering** — Pearson correlation + TruncatedSVD fallback
- ⚙️ **Tunable Hybrid Engine** — Adjustable α slider for real-time blending
- 🧊 **Cold-Start Handling** — Dynamic α that shifts toward content-based for new users
- 📍 **Location-Aware** — Haversine distance filtering by city/coordinates
- ⭐ **Interactive Ratings** — Rate restaurants, avg auto-recalculated
- 🔍 **Search & Filter** — By cuisine, price range, area, and keyword
- 🎨 **Premium Dark UI** — Glassmorphism, micro-animations, responsive
- 🛡️ **JWT Auth** — Secure registration, login, admin-protected routes
- 📊 **Admin Dashboard** — Restaurant CRUD, user stats, management

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login & get JWT |
| GET | `/api/auth/me` | Current user profile |
| PUT | `/api/auth/preferences` | Update taste preferences |
| GET | `/api/restaurants` | List restaurants (with filters) |
| GET | `/api/restaurants/search?q=` | Search by keyword |
| GET | `/api/restaurants/:id` | Restaurant details |
| POST | `/api/ratings` | Submit/update rating |
| GET | `/api/ratings/me` | User's ratings |
| GET | `/api/recommendations` | Hybrid recommendations |
| POST | `/api/interactions` | Log implicit feedback |
| GET | `/api/stats` | Platform statistics |

## Project Structure

```
Hybrid_Rec/
├── backend/
│   ├── engine/           # Recommendation algorithms
│   │   ├── content_based.py
│   │   ├── collaborative.py
│   │   ├── hybrid.py
│   │   └── preprocess.py
│   ├── models/           # Pydantic schemas
│   ├── routes/           # API endpoints
│   ├── seed/             # Database seeding
│   ├── config.py
│   ├── database.py
│   └── main.py
├── frontend/
│   └── src/
│       ├── api/          # Axios API client
│       ├── components/   # Reusable UI components
│       ├── pages/        # Route pages
│       ├── App.jsx
│       └── index.css     # Design system
└── README.md
```
