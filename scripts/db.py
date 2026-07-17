import os
import logging
from supabase import create_client
from typing import Optional, Dict, Any

log = logging.getLogger("cdsco.db")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    log.warning("Supabase credentials not set. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in env.")

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_manufacturer(client, data: Dict[str, Any]):
    # unique by lower(name)
    name = data.get("name")
    if not name:
        raise ValueError("manufacturer name required")
    res = client.table('manufacturers').upsert({**data}).execute()
    return res

def upsert_medicine(client, data: Dict[str, Any]):
    # rely on unique index to avoid duplicates
    res = client.table('medicines').upsert({**data}).execute()
    return res

def insert_alert(client, data: Dict[str, Any]):
    return client.table('drug_alerts').insert({**data}).execute()

def insert_recall(client, data: Dict[str, Any]):
    return client.table('drug_recalls').insert({**data}).execute()

def insert_scan(client, data: Dict[str, Any]):
    return client.table('scan_history').insert({**data}).execute()

def insert_report(client, data: Dict[str, Any]):
    return client.table('reports').insert({**data}).execute()
