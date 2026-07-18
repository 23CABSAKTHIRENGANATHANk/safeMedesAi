<p align="center">
  <img src="public/logo.png" alt="SafeMeds AI Logo" width="80" />
</p>

<h1 align="center">SafeMeds AI</h1>

<p align="center">
  <strong>Verify Medicines. Protect Lives.</strong><br/>
  A regulatory-grade medicine verification platform powered by live records from CDSCO, US FDA &amp; WHO GSMS.
</p>

<p align="center">
  <a href="https://github.com/23CABSAKTHIRENGANATHANk/safeMedesAi/actions/workflows/ci.yml">
    <img src="https://github.com/23CABSAKTHIRENGANATHANk/safeMedesAi/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/react-19-blue?logo=react" alt="React 19" />
  <img src="https://img.shields.io/badge/fastapi-0.110+-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/python-3.11-yellow?logo=python" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [CI/CD](#-cicd)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**SafeMeds AI** is a full-stack medicine verification platform that cross-references drug names against three major global regulatory authorities in real time:

| Authority | Coverage | Source |
|-----------|----------|--------|
| **CDSCO** | India — Central Drugs Standard Control Organisation | Banned/recalled drug lists, enforcement notices |
| **US FDA** | United States — Food & Drug Administration | Enforcement reports, recall database |
| **WHO GSMS** | Global — World Health Organization | Global Surveillance & Monitoring System alerts |

### The No-Prediction Policy

SafeMeds AI **never** flags a medicine based on similarity, statistical inference, or crowd-sourced sentiment. A medicine is only classified as **Unsafe** when a definitive record exists in at least one of the three authorities. In every other case, it returns **Safe** (no matching record) or **Unknown** (insufficient data) — never a guess.

---

## ✨ Key Features

- 🔬 **Multi-Authority Verification** — Every query is cross-referenced against CDSCO, US FDA, and WHO GSMS records in a single pass
- ⚡ **Instant Safety Alerts** — Unsafe matches trigger a full-screen alert with authority, batch number, and reason
- 📡 **Real-Time Data Ingestion** — Regulatory feeds are scraped and updated continuously via scheduled background jobs
- 🏥 **Built for Healthcare** — Designed for prescribers, pharmacists, and patients
- 🔒 **Zero PII Collection** — No account required, no personal data stored
- 📊 **Transparent Results** — Every result cites the specific regulatory authority and enforcement record

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│          (Vite + TanStack Router + Tailwind)         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Verify   │  │  About   │  │   How It Works    │  │
│  │  Page     │  │  Page    │  │   Page            │  │
│  └─────┬────┘  └──────────┘  └───────────────────┘  │
│        │                                             │
│        ▼                                             │
│  ┌──────────────────────────────┐                    │
│  │   API Service (fetch client) │                    │
│  └──────────────┬───────────────┘                    │
└─────────────────┼───────────────────────────────────┘
                  │  HTTP /api/*
                  ▼
┌─────────────────────────────────────────────────────┐
│               FastAPI Backend                        │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ /api/    │  │  Verification │  │   Scheduler   │  │
│  │ verify   │──│  Service      │  │  (APScheduler)│  │
│  └──────────┘  └──────┬───────┘  └───────┬───────┘  │
│                       │                  │           │
│                       ▼                  ▼           │
│  ┌────────────────────────────────────────────────┐  │
│  │              Scrapers Layer                     │  │
│  │  ┌────────┐  ┌─────────┐  ┌────────────────┐  │  │
│  │  │ CDSCO  │  │ US FDA  │  │  WHO GSMS      │  │  │
│  │  └────────┘  └─────────┘  └────────────────┘  │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                              │
│                       ▼                              │
│  ┌────────────────────────────────────────────────┐  │
│  │     Supabase PostgreSQL / SQLite (dev)         │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **Vite** | Build tool & dev server |
| **TanStack Router** | File-based routing |
| **TanStack Query** | Server state management |
| **Tailwind CSS 4** | Utility-first styling |
| **Radix UI** | Accessible component primitives |
| **Recharts** | Data visualization |
| **Zod** | Runtime schema validation |
| **Lucide React** | Icon library |

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Runtime |
| **FastAPI** | API framework |
| **SQLAlchemy** | ORM & database toolkit |
| **APScheduler** | Background job scheduling |
| **BeautifulSoup4** | HTML parsing for web scraping |
| **pdfplumber** | PDF extraction (CDSCO gazette notices) |
| **Supabase** | PostgreSQL database (production) |
| **SQLite** | Local development database |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 20.x
- **Python** ≥ 3.11
- **npm** (comes with Node.js)
- **Git**

### 1. Clone the repository

```bash
git clone https://github.com/23CABSAKTHIRENGANATHANk/safeMedesAi.git
cd safeMedesAi
```

### 2. Frontend setup

```bash
# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 3. Backend setup

```bash
cd backend

# Create a virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in your values
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

```env
PORT=8000
HOST=0.0.0.0

# Supabase PostgreSQL connection string
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

CORS_ORIGINS=["http://localhost:5173","https://safe-medes-ai.vercel.app"]
```

### Frontend (`.env`)

```env
VITE_API_URL=http://localhost:8000/api
```

- Use `http://localhost:8000/api` during local development when the backend runs on port `8000`.
- In production on Vercel, the app can use the relative API path `/api` if `vercel.json` is enabled and the backend is reachable through the rewrite.

> **⚠️ Important:** Never commit `.env` files to version control. Use `backend/.env.example` as a template.

---

## ☁️ Deployment

### Frontend: Vercel

This React/Vite app can be deployed on Vercel using the root project folder.

- `vercel.json` contains a rewrite for `/api/*` to the deployed backend on Render.
- Set the Vercel framework preset to `Vite` or use the detected settings.
- If you are not using the built-in rewrite, set `VITE_API_URL=https://<your-backend-url>/api`.

No extra build step is required beyond Vercel's default `npm install` and `npm run build`.

### Backend: Render

The backend is configured for Render with `render.yaml` at the repo root.

- Create a new Render service and connect the repository.
- Render will use `backend` as the service root.
- The build command is:

```bash
pip install -r requirements.txt
```

- The start command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Add the following environment variables in Render:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL` (optional; local SQLite fallback is supported)
  - `CORS_ORIGINS` (e.g. `["https://<your-frontend-domain>"]`)
  - `GEMINI_API_KEY` / `GEMINI_ENDPOINT` or `OPENAI_API_KEY`

### Notes

- The backend uses `FastAPI` and runs on port `$PORT`.
- The frontend should target the backend via `VITE_API_URL`.
- If you deploy backend to `https://api.example.com`, set frontend env to `https://api.example.com/api`.

---

## 📡 API Reference

### Health Check

```
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "service": "SafeMeds AI Backend",
  "version": "1.0.0"
}
```

### Verify Medicine

```
POST /api/verify
```

**Request Body:**
```json
{
  "name": "Paracetamol",
  "manufacturer": "Optional Manufacturer Name",
  "batch": "Optional Batch Number"
}
```

**Response:**
```json
{
  "status": "safe | unsafe | unknown",
  "name": "Paracetamol",
  "batch": "BATCH123",
  "authority": "CDSCO",
  "reason": "Reason if unsafe"
}
```

### List Medicines

```
GET /api/medicines?page=1&limit=20
```

### Search Medicines

```
GET /api/search?medicine=paracetamol&page=1&limit=20
```

### Get Alerts

```
GET /api/alerts?page=1&limit=20
```

### Get Recalls

```
GET /api/recalls?page=1&limit=20
```

---

## 📁 Project Structure

```
safeMedesAi/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline (build + typecheck + backend verify)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── verify.py       # Verification endpoint
│   │   │   └── medicines.py    # Medicines CRUD endpoints
│   │   ├── scrapers/
│   │   │   ├── cdsco.py        # CDSCO scraper
│   │   │   ├── usfda.py        # US FDA scraper
│   │   │   ├── who.py          # WHO GSMS scraper
│   │   │   ├── pdf_utils.py    # PDF extraction utilities
│   │   │   └── supabase_client.py
│   │   ├── services/           # Business logic layer
│   │   ├── models/             # SQLAlchemy models
│   │   ├── database.py         # DB engine & session
│   │   ├── scheduler.py        # APScheduler config
│   │   └── main.py             # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── src/
│   ├── components/             # Reusable UI components
│   ├── routes/
│   │   ├── index.tsx           # Homepage
│   │   ├── verify.tsx          # Medicine verification page
│   │   ├── about.tsx           # About & data integrity policy
│   │   ├── features.tsx        # Features showcase
│   │   └── how-it-works.tsx    # How it works guide
│   ├── services/
│   │   └── api.ts              # API client service
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities
│   └── styles.css              # Global styles
├── public/                     # Static assets
├── index.html                  # HTML entry point
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .gitignore
```

---

## 🔄 CI/CD

The project uses **GitHub Actions** for continuous integration:

| Job | Description |
|-----|-------------|
| **Frontend** | `npm ci` → TypeScript type check → Vite production build |
| **Backend** | Python 3.11 setup → Install dependencies → Run verification script |

The pipeline runs on every push and pull request to the `main` branch.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'feat: add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Guidelines

- Follow the existing code style (Prettier + ESLint for frontend)
- Write descriptive commit messages using [Conventional Commits](https://www.conventionalcommits.org/)
- Update documentation for any API or UI changes
- Ensure CI passes before requesting review

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with 💚 for safer medicines worldwide
</p>
