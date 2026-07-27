import os
import sys
import json
import logging
import argparse
import pandas as pd

# Setup paths and environment
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)

for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, '.env'), override=False)
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, '.env'), override=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s -- %(message)s')
log = logging.getLogger('import_datasets')

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.medicine import MedicineRecord
from backend.app.scrapers.supabase_client import get_client

def get_db_session():
    return SessionLocal()

def import_local_sqlite(datasets_dir, reset=False):
    log.info("Starting local SQLite import...")
    Base.metadata.create_all(bind=engine)
    db = get_db_session()
    
    if reset:
        log.info("Resetting local SQLite database (deleting all existing records)...")
        try:
            db.query(MedicineRecord).delete()
            db.commit()
            log.info("Local SQLite database cleared successfully.")
        except Exception as e:
            log.error(f"Failed to clear local SQLite database: {e}")
            db.rollback()
            
    # Load existing names to avoid duplicates
    log.info("Loading existing medicines from local SQLite database...")
    existing = db.query(MedicineRecord.name).all()
    seen_names = {r[0].lower().strip() for r in existing}
    log.info(f"Loaded {len(seen_names)} existing local records.")
    
    # 1. Processing updated_indian_medicine_data.csv (253k rows)
    indian_csv = os.path.join(datasets_dir, "updated_indian_medicine_data.csv")
    if os.path.exists(indian_csv):
        log.info(f"Processing {os.path.basename(indian_csv)}...")
        chunk_size = 20000
        count = 0
        inserted_count = 0
        
        for chunk in pd.read_csv(indian_csv, chunksize=chunk_size):
            records = []
            for _, row in chunk.iterrows():
                name = str(row.get('name', '')).strip()
                if not name or name.lower() == 'nan':
                    continue
                
                name_clean = name.strip()
                name_lower = name_clean.lower()
                
                # Check cache
                if name_lower in seen_names:
                    continue
                seen_names.add(name_lower)
                
                mfr = str(row.get('manufacturer_name', '')).strip()
                if not mfr or mfr.lower() == 'nan':
                    mfr = None
                
                desc = str(row.get('medicine_desc', '')).strip()
                side_effects = str(row.get('side_effects', '')).strip()
                salt = str(row.get('salt_composition', '')).strip()
                price = str(row.get('price', '')).strip()
                
                reason_parts = []
                if salt and salt.lower() != 'nan':
                    reason_parts.append(f"Composition: {salt}")
                if price and price.lower() != 'nan':
                    reason_parts.append(f"Price: Rs {price}")
                if side_effects and side_effects.lower() != 'nan':
                    reason_parts.append(f"Side Effects: {side_effects}")
                if desc and desc.lower() != 'nan':
                    reason_parts.append(f"Description: {desc}")
                    
                reason = " | ".join(reason_parts) if reason_parts else "Regulatory record verified."
                
                records.append({
                    'name': name_clean,
                    'batch': None,
                    'manufacturer': mfr,
                    'status': 'safe',
                    'authority': 'CDSCO (India)',
                    'reason': reason
                })
            
            if records:
                db.bulk_insert_mappings(MedicineRecord, records)
                db.commit()
                inserted_count += len(records)
            count += len(chunk)
            log.info(f"Processed {count} rows. Inserted {inserted_count} new Indian medicines.")
    
    # 2. Processing medicine_dataset.csv (50k rows)
    med_csv = os.path.join(datasets_dir, "medicine_dataset.csv")
    if os.path.exists(med_csv):
        log.info(f"Processing {os.path.basename(med_csv)}...")
        chunk_size = 20000
        count = 0
        inserted_count = 0
        
        for chunk in pd.read_csv(med_csv, chunksize=chunk_size):
            records = []
            for _, row in chunk.iterrows():
                name = str(row.get('Name', '')).strip()
                if not name or name.lower() == 'nan':
                    continue
                
                name_clean = name.strip()
                name_lower = name_clean.lower()
                
                if name_lower in seen_names:
                    continue
                seen_names.add(name_lower)
                
                mfr = str(row.get('Manufacturer', '')).strip()
                if not mfr or mfr.lower() == 'nan':
                    mfr = None
                    
                form = str(row.get('Dosage Form', '')).strip()
                strength = str(row.get('Strength', '')).strip()
                category = str(row.get('Category', '')).strip()
                indication = str(row.get('Indication', '')).strip()
                classification = str(row.get('Classification', '')).strip()
                
                reason_parts = []
                if form and form.lower() != 'nan':
                    reason_parts.append(f"Form: {form}")
                if strength and strength.lower() != 'nan':
                    reason_parts.append(f"Strength: {strength}")
                if category and category.lower() != 'nan':
                    reason_parts.append(f"Category: {category}")
                if indication and indication.lower() != 'nan':
                    reason_parts.append(f"Indication: {indication}")
                if classification and classification.lower() != 'nan':
                    reason_parts.append(f"Classification: {classification}")
                    
                reason = " | ".join(reason_parts) if reason_parts else "Regulatory record verified."
                
                records.append({
                    'name': name_clean,
                    'batch': None,
                    'manufacturer': mfr,
                    'status': 'safe',
                    'authority': 'FDA/Global Reference',
                    'reason': reason
                })
            
            if records:
                db.bulk_insert_mappings(MedicineRecord, records)
                db.commit()
                inserted_count += len(records)
            count += len(chunk)
            log.info(f"Processed {count} rows. Inserted {inserted_count} new global medicines.")

    # 3. Processing drugs_side_effects_drugs_com.csv (2.9k rows)
    side_csv = os.path.join(datasets_dir, "drugs_side_effects_drugs_com.csv")
    if os.path.exists(side_csv):
        log.info(f"Processing {os.path.basename(side_csv)}...")
        try:
            df = pd.read_csv(side_csv)
            records = []
            inserted_count = 0
            for _, row in df.iterrows():
                name = str(row.get('drug_name', '')).strip()
                if not name or name.lower() == 'nan':
                    continue
                
                name_clean = name.strip()
                name_lower = name_clean.lower()
                
                if name_lower in seen_names:
                    continue
                seen_names.add(name_lower)
                
                generic = str(row.get('generic_name', '')).strip()
                brands = str(row.get('brand_names', '')).strip()
                condition = str(row.get('medical_condition', '')).strip()
                side_effects = str(row.get('side_effects', '')).strip()
                
                reason_parts = []
                if generic and generic.lower() != 'nan':
                    reason_parts.append(f"Generic Name: {generic}")
                if brands and brands.lower() != 'nan':
                    reason_parts.append(f"Brand Names: {brands}")
                if condition and condition.lower() != 'nan':
                    reason_parts.append(f"Condition: {condition}")
                if side_effects and side_effects.lower() != 'nan':
                    reason_parts.append(f"Side Effects: {side_effects}")
                    
                reason = " | ".join(reason_parts) if reason_parts else "Regulatory record verified."
                
                records.append({
                    'name': name_clean,
                    'batch': None,
                    'manufacturer': None,
                    'status': 'safe',
                    'authority': 'Drugs.com',
                    'reason': reason
                })
            
            if records:
                db.bulk_insert_mappings(MedicineRecord, records)
                db.commit()
                inserted_count += len(records)
            log.info(f"Inserted {inserted_count} new Drugs.com medicines.")
        except Exception as e:
            log.error(f"Error processing side effects CSV: {e}")

    # 4. Processing drug-enforcement-0001-of-0001.json (recalls)
    recalls_json = os.path.join(datasets_dir, "drug-enforcement-0001-of-0001.json")
    if os.path.exists(recalls_json):
        log.info(f"Processing {os.path.basename(recalls_json)}...")
        try:
            with open(recalls_json, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                results = data.get('results', [])
                
                records = []
                for item in results:
                    openfda = item.get('openfda', {})
                    
                    # Extract name
                    brand_names = openfda.get('brand_name', [])
                    generic_names = openfda.get('generic_name', [])
                    
                    drug_names = list(set(brand_names + generic_names))
                    if not drug_names:
                        # Fallback: extract from product description
                        desc = item.get('product_description', '')
                        if desc:
                            first_word = desc.split()[0].replace(',', '').replace(';', '').strip()
                            if len(first_word) > 2:
                                drug_names = [first_word]
                                
                    if not drug_names:
                        continue
                        
                    mfr = item.get('recalling_firm', '')
                    recall_num = item.get('recall_number', '')
                    reason = item.get('reason_for_recall', 'Drug recall notice.')
                    
                    for dname in drug_names:
                        records.append({
                            'name': dname.strip(),
                            'batch': recall_num,
                            'manufacturer': mfr,
                            'status': 'unsafe',
                            'authority': 'US FDA Recall',
                            'reason': reason
                        })
                
                if records:
                    db.bulk_insert_mappings(MedicineRecord, records)
                    db.commit()
                    log.info(f"Inserted {len(records)} recall/unsafe records into SQLite database.")
        except Exception as e:
            log.error(f"Error processing recalls JSON: {e}")

    # 5. Processing drug-drugsfda-0001-of-0001.json (approved labels)
    labels_json = os.path.join(datasets_dir, "drug-drugsfda-0001-of-0001.json")
    if os.path.exists(labels_json):
        log.info(f"Processing {os.path.basename(labels_json)}...")
        try:
            with open(labels_json, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                results = data.get('results', [])
                
                records = []
                inserted_count = 0
                for item in results:
                    openfda = item.get('openfda', {})
                    brand_names = openfda.get('brand_name', [])
                    generic_names = openfda.get('generic_name', [])
                    
                    names = list(set(brand_names + generic_names))
                    if not names:
                        continue
                        
                    mfrs = openfda.get('manufacturer_name', [])
                    mfr = mfrs[0] if mfrs else None
                    
                    # Extract form and route from products if available
                    products = item.get('products', [])
                    form_route = ""
                    if products:
                        form = products[0].get('dosage_form', '')
                        route = products[0].get('route', '')
                        if form and route:
                            form_route = f"Dosage Form: {form} | Route: {route}"
                        elif form:
                            form_route = f"Dosage Form: {form}"
                    
                    for name in names:
                        name_clean = name.strip()
                        name_lower = name_clean.lower()
                        if name_lower in seen_names:
                            continue
                        seen_names.add(name_lower)
                        
                        records.append({
                            'name': name_clean,
                            'batch': None,
                            'manufacturer': mfr,
                            'status': 'safe',
                            'authority': 'US FDA Approved',
                            'reason': form_route or "FDA Approved record."
                        })
                        
                if records:
                    db.bulk_insert_mappings(MedicineRecord, records)
                    db.commit()
                    inserted_count += len(records)
                log.info(f"Inserted {inserted_count} new FDA approved medicines into SQLite database.")
        except Exception as e:
            log.error(f"Error processing approved labels JSON: {e}")

    # Check total records count
    total_count = db.query(MedicineRecord).count()
    log.info(f"SQLite local import completed. Total records now: {total_count}")
    db.close()

def import_supabase(datasets_dir):
    log.info("Starting Supabase import...")
    try:
        client = get_client()
        log.info("Successfully connected to Supabase client.")
    except Exception as e:
        log.error(f"Supabase client connection failed: {e}")
        return

    # We will bulk insert some common unique Indian/global brand names to Supabase to update it.
    # Note: Inserting 300k records via REST API is too slow/resource-heavy, so we will focus on
    # seeding the top 500 medicines, recalls, and warnings.
    log.info("Loading Top Indian Medicines for Supabase upload...")
    indian_csv = os.path.join(datasets_dir, "updated_indian_medicine_data.csv")
    if os.path.exists(indian_csv):
        df = pd.read_csv(indian_csv, nrows=1000) # Seed top 1000 most popular ones
        
        # Load existing medicines to prevent duplicates
        try:
            res = client.table('medicines').select('name').execute()
            existing_meds = {r['name'].lower().strip() for r in res.data}
        except Exception:
            existing_meds = set()
            
        meds_payload = []
        mfg_cache = {}
        
        log.info("Inserting popular manufacturers and medicines to Supabase...")
        for _, row in df.iterrows():
            name = str(row.get('name', '')).strip()
            if not name or name.lower() == 'nan':
                continue
                
            name_clean = name.strip()
            name_lower = name_clean.lower()
            if name_lower in existing_meds:
                continue
            existing_meds.add(name_lower)
            
            mfr = str(row.get('manufacturer_name', '')).strip()
            mfg_id = None
            if mfr and mfr.lower() != 'nan':
                mfr_clean = mfr.strip()
                mfr_lower = mfr_clean.lower()
                if mfr_lower not in mfg_cache:
                    try:
                        # Find or insert
                        m_res = client.table('manufacturers').select('id').eq('name', mfr_clean).execute()
                        if m_res.data:
                            mfg_id = m_res.data[0]['id']
                        else:
                            ins_res = client.table('manufacturers').insert({'name': mfr_clean}).execute()
                            if ins_res.data:
                                mfg_id = ins_res.data[0]['id']
                        mfg_cache[mfr_lower] = mfg_id
                    except Exception:
                        pass
                else:
                    mfg_id = mfg_cache[mfr_lower]

            desc = str(row.get('medicine_desc', '')).strip()
            side_effects = str(row.get('side_effects', '')).strip()
            salt = str(row.get('salt_composition', '')).strip()
            price = str(row.get('price', '')).strip()
            
            meds_payload.append({
                'name': name_clean,
                'form': 'Tablet',
                'strength': salt[:100] if salt else None,
                'manufacturer_id': mfg_id,
                'primary_identifier': str(row.get('id')),
                'metadata': {
                    'price': price,
                    'side_effects': side_effects,
                    'description': desc,
                    'source': 'indian_medicine_import'
                }
            })
            
            if len(meds_payload) >= 100:
                try:
                    client.table('medicines').insert(meds_payload).execute()
                except Exception as e:
                    log.warning(f"Failed to batch insert medicines chunk: {e}")
                meds_payload = []
                
        if meds_payload:
            try:
                client.table('medicines').insert(meds_payload).execute()
            except Exception as e:
                log.warning(f"Failed to insert final medicines chunk: {e}")
                
        log.info("Supabase import completed for top 1000 medicines.")

def main():
    parser = argparse.ArgumentParser(description="MedVerify Dataset Importer")
    parser.add_argument('--supabase', action='store_true', help="Import to Supabase in addition to local SQLite")
    parser.add_argument('--local-only', action='store_true', default=True, help="Import to local SQLite fallback database (default: True)")
    parser.add_argument('--reset', action='store_true', help="Reset (delete) local SQLite database before import to populate metadata cleanly")
    
    args = parser.parse_args()
    datasets_dir = os.path.join(REPO_ROOT, "datasets")
    
    if not os.path.exists(datasets_dir):
        log.error(f"Datasets directory not found: {datasets_dir}")
        sys.exit(1)
        
    log.info(f"Using datasets directory: {datasets_dir}")
    
    # Run SQLite import
    import_local_sqlite(datasets_dir, reset=args.reset)
    
    # Run Supabase import if requested
    if args.supabase:
        import_supabase(datasets_dir)
        
if __name__ == '__main__':
    main()
