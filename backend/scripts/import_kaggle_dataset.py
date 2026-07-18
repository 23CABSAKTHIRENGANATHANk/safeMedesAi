"""
High-performance utility to import multiple Kaggle CSV datasets into the Supabase database.
Uses bulk inserts and in-memory caches to run 100x faster.

Place all your CSV files in a folder named 'datasets/' in the root directory.

Run this script:
    .venv\Scripts\python backend\scripts\import_kaggle_dataset.py
"""
import os
import sys
import glob
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, '.env'))

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file.")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_csv_file(file_path):
    print("\n" + "=" * 60)
    print(f"Processing file: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to read CSV file {file_path}: {e}")
        return

    # Load existing medicines and manufacturers from Supabase to prevent duplicates in memory (blazing fast!)
    print("Loading existing records from Supabase to build cache...")
    try:
        meds_res = client.table('medicines').select('name').execute()
        existing_meds = {r['name'].lower().strip() for r in meds_res.data}
        
        mfg_res = client.table('manufacturers').select('id, name').execute()
        mfg_cache = {r['name'].lower().strip(): r['id'] for r in mfg_res.data}
    except Exception as e:
        print(f"Warning: Failed to load existing records cache: {e}. Running without cache.")
        existing_meds = set()
        mfg_cache = {}

    print("Columns found in CSV:", list(df.columns))
    
    # Map columns case-insensitively or dynamically
    col_mapping = {}
    
    # Try to find a precise drug name column first
    for col in df.columns:
        c_lower = col.lower()
        if any(keyword in c_lower for keyword in ['drug_name', 'medicine_name', 'brand_name', 'generic_name', 'product_name']):
            col_mapping['name'] = col
            break
            
    # Fallback to column with 'name' (excluding links/metadata)
    if 'name' not in col_mapping:
        for col in df.columns:
            c_lower = col.lower()
            if 'name' in c_lower and not any(x in c_lower for x in ['link', 'url', 'id', 'class', 'category', 'desc', 'image', 'review', 'rating']):
                col_mapping['name'] = col
                break
                
    # Fallback to column with 'drug' (excluding links/metadata)
    if 'name' not in col_mapping:
        for col in df.columns:
            c_lower = col.lower()
            if 'drug' in c_lower and not any(x in c_lower for x in ['link', 'url', 'id', 'class', 'category', 'desc', 'image', 'review', 'rating']):
                col_mapping['name'] = col
                break

    # Find form, strength, and manufacturer columns
    for col in df.columns:
        c_lower = col.lower()
        if 'form' in c_lower or 'type' in c_lower:
            col_mapping['form'] = col
        elif 'strength' in c_lower or 'dose' in c_lower:
            col_mapping['strength'] = col
        elif 'manufacturer' in c_lower or 'company' in c_lower:
            col_mapping['manufacturer'] = col

    name_col = col_mapping.get('name')
    if not name_col:
        print(f"Warning: Could not identify a 'name' or 'drug' column in {os.path.basename(file_path)}. Skipping this file.")
        return

    print(f"Mapping columns: {col_mapping}")
    
    new_manufacturers = set()
    rows_to_import = []
    seen_signatures = set()
    
    # First pass: identify unique manufacturers and clean data
    for index, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == 'nan':
            continue
            
        form = str(row[col_mapping['form']]).strip() if 'form' in col_mapping else None
        strength = str(row[col_mapping['strength']]).strip() if 'strength' in col_mapping else None
        manufacturer = str(row[col_mapping['manufacturer']]).strip() if 'manufacturer' in col_mapping else None
        
        if form and form.lower() == 'nan': form = None
        if strength and strength.lower() == 'nan': strength = None
        if manufacturer and manufacturer.lower() == 'nan': manufacturer = None

        # Build unique signature to prevent duplicates inside the batch payload
        sig = (
            name.lower().strip(),
            (manufacturer or '').lower().strip(),
            (form or '').lower().strip(),
            (strength or '').lower().strip()
        )
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)
        
        # In-memory deduplication against database existing names
        if name.lower().strip() in existing_meds:
            continue
            
        if manufacturer and manufacturer.lower().strip() not in mfg_cache:
            new_manufacturers.add(manufacturer.strip())
            
        rows_to_import.append({
            'name': name,
            'form': form,
            'strength': strength,
            'manufacturer_name': manufacturer,
            'row_idx': index
        })

    # Bulk insert new manufacturers
    if new_manufacturers:
        print(f"Found {len(new_manufacturers)} new manufacturers. Inserting in bulk...")
        mfg_payload = [{'name': m} for m in new_manufacturers]
        for i in range(0, len(mfg_payload), 100):
            chunk = mfg_payload[i:i+100]
            try:
                res = client.table('manufacturers').insert(chunk).execute()
                for r in res.data:
                    mfg_cache[r['name'].lower().strip()] = r['id']
            except Exception as e:
                print(f"Failed to bulk insert manufacturer chunk: {e}")

    # Bulk insert medicines in batches of 200
    batch_size = 200
    meds_payload = []
    success_count = 0
    skipped_count = len(df) - len(rows_to_import)
    
    print(f"Inserting {len(rows_to_import)} new medicines...")
    for item in rows_to_import:
        mfg_id = None
        if item['manufacturer_name']:
            mfg_id = mfg_cache.get(item['manufacturer_name'].lower().strip())
            
        meds_payload.append({
            'name': item['name'],
            'form': item['form'],
            'strength': item['strength'],
            'manufacturer_id': mfg_id,
            'metadata': {'source': 'kaggle_import', 'file': os.path.basename(file_path)}
        })
        
        if len(meds_payload) >= batch_size:
            try:
                client.table('medicines').insert(meds_payload).execute()
                success_count += len(meds_payload)
                print(f"Imported {success_count} medicines...")
            except Exception as e:
                print(f"Batch insert failed, attempting row-by-row fallback for this batch: {e}")
                for row_payload in meds_payload:
                    try:
                        client.table('medicines').insert(row_payload).execute()
                        success_count += 1
                    except Exception as err:
                        pass
            meds_payload = []

    # Insert remaining
    if meds_payload:
        try:
            client.table('medicines').insert(meds_payload).execute()
            success_count += len(meds_payload)
        except Exception as e:
            for row_payload in meds_payload:
                try:
                    client.table('medicines').insert(row_payload).execute()
                    success_count += 1
                except Exception as err:
                    pass

    print(f"Import completed for {os.path.basename(file_path)}: {success_count} imported, {skipped_count} skipped/duplicates.")

def main():
    datasets_dir = os.path.join(REPO_ROOT, 'datasets')
    
    csv_files = []
    if os.path.exists(datasets_dir):
        csv_files.extend(glob.glob(os.path.join(datasets_dir, '*.csv')))
    
    csv_files.extend(glob.glob(os.path.join(REPO_ROOT, '*.csv')))
    csv_files = list(set(csv_files))
    
    if not csv_files:
        print("No CSV files found in the root directory or in the 'datasets/' directory.")
        return
        
    print(f"Found {len(csv_files)} CSV file(s) to process:")
    for f in csv_files:
        print(f" - {os.path.basename(f)}")
        
    for file_path in csv_files:
        import_csv_file(file_path)

if __name__ == '__main__':
    main()
