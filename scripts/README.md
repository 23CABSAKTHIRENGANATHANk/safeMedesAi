# CDSCO Scraper

This directory contains a production-ready scraper skeleton to collect CDSCO datasets (approved medicines, alerts, NSQ lists, recalls), download PDFs, extract tables, clean data and store in Supabase.

Prerequisites
- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`
- Create `.env` from `.env.example` and set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

Run
```bash
cd scripts
pip install -r requirements.txt
python cdsco_scraper.py
```

Notes
- Replace placeholder CDSCO URLs in `cdsco_scraper.py` with the real endpoints.
- The scraper uses `pdfplumber` to extract simple tables; for complex tables consider `camelot` or `tabula`.
- The Supabase client uses the service role key for upserts — store it securely and do not expose it client-side.

Deployment
- Run in a scheduled environment (Cloud Run, ECS, or a VM) with a scheduler (cron, Cloud Scheduler).
- Add monitoring/alerting for repeated failures and metrics exports.
