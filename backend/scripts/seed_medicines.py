"""
Seed script: Populates the medicines table with a comprehensive dataset.

Sources:
  1. OpenFDA drug labels (generic/brand names) - up to 10 pages = 1000 records
  2. Curated list of common Indian medicines (Paracetamol, Amoxicillin, etc.)
  3. OpenFDA enforcement (recalled drugs -> drug_recalls)

Run:
    .venv\Scripts\python backend\scripts\seed_medicines.py
"""
import os
import sys
import time
import logging

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, '.env'), override=False)
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, '.env'), override=True)

for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s -- %(message)s')
log = logging.getLogger('seed')

import requests
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    log.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────────────────────────
# Common Indian + Global medicines that MUST be in the approved list
# ─────────────────────────────────────────────────────────────────
COMMON_MEDICINES = [
    # Indian brand names and generic names
    {"name": "Paracetamol", "form": "Tablet", "strength": "500mg"},
    {"name": "Paracetamol", "form": "Tablet", "strength": "650mg"},
    {"name": "Dolo 650", "form": "Tablet", "strength": "650mg"},
    {"name": "Crocin", "form": "Tablet", "strength": "500mg"},
    {"name": "Calpol", "form": "Tablet", "strength": "500mg"},
    {"name": "Crocin Advance", "form": "Tablet", "strength": "500mg"},
    {"name": "Amoxicillin", "form": "Capsule", "strength": "250mg"},
    {"name": "Amoxicillin", "form": "Capsule", "strength": "500mg"},
    {"name": "Mox", "form": "Capsule", "strength": "250mg"},
    {"name": "Novamox", "form": "Capsule", "strength": "250mg"},
    {"name": "Azithromycin", "form": "Tablet", "strength": "250mg"},
    {"name": "Azithromycin", "form": "Tablet", "strength": "500mg"},
    {"name": "Zithromax", "form": "Tablet", "strength": "250mg"},
    {"name": "Azee", "form": "Tablet", "strength": "500mg"},
    {"name": "Ibuprofen", "form": "Tablet", "strength": "400mg"},
    {"name": "Ibuprofen", "form": "Tablet", "strength": "200mg"},
    {"name": "Brufen", "form": "Tablet", "strength": "400mg"},
    {"name": "Combiflam", "form": "Tablet", "strength": "400mg/325mg"},
    {"name": "Metformin", "form": "Tablet", "strength": "500mg"},
    {"name": "Metformin", "form": "Tablet", "strength": "850mg"},
    {"name": "Glycomet", "form": "Tablet", "strength": "500mg"},
    {"name": "Glucophage", "form": "Tablet", "strength": "500mg"},
    {"name": "Ciprofloxacin", "form": "Tablet", "strength": "250mg"},
    {"name": "Ciprofloxacin", "form": "Tablet", "strength": "500mg"},
    {"name": "Ciplox", "form": "Tablet", "strength": "250mg"},
    {"name": "Cifran", "form": "Tablet", "strength": "500mg"},
    {"name": "Omeprazole", "form": "Capsule", "strength": "20mg"},
    {"name": "Omez", "form": "Capsule", "strength": "20mg"},
    {"name": "Pantoprazole", "form": "Tablet", "strength": "40mg"},
    {"name": "Pan D", "form": "Capsule", "strength": "40mg"},
    {"name": "Pantodac", "form": "Tablet", "strength": "40mg"},
    {"name": "Cetirizine", "form": "Tablet", "strength": "10mg"},
    {"name": "Cetzine", "form": "Tablet", "strength": "10mg"},
    {"name": "Alerid", "form": "Tablet", "strength": "10mg"},
    {"name": "Atorvastatin", "form": "Tablet", "strength": "10mg"},
    {"name": "Atorvastatin", "form": "Tablet", "strength": "20mg"},
    {"name": "Atorvastatin", "form": "Tablet", "strength": "40mg"},
    {"name": "Lipitor", "form": "Tablet", "strength": "20mg"},
    {"name": "Storvas", "form": "Tablet", "strength": "10mg"},
    {"name": "Dexamethasone", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Dexona", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Prednisolone", "form": "Tablet", "strength": "5mg"},
    {"name": "Wysolone", "form": "Tablet", "strength": "5mg"},
    {"name": "Aspirin", "form": "Tablet", "strength": "75mg"},
    {"name": "Aspirin", "form": "Tablet", "strength": "150mg"},
    {"name": "Ecosprin", "form": "Tablet", "strength": "75mg"},
    {"name": "Disprin", "form": "Tablet", "strength": "300mg"},
    {"name": "Metronidazole", "form": "Tablet", "strength": "400mg"},
    {"name": "Metrogyl", "form": "Tablet", "strength": "400mg"},
    {"name": "Flagyl", "form": "Tablet", "strength": "400mg"},
    {"name": "Ranitidine", "form": "Tablet", "strength": "150mg"},
    {"name": "Rantac", "form": "Tablet", "strength": "150mg"},
    {"name": "Zantac", "form": "Tablet", "strength": "150mg"},
    {"name": "Domperidone", "form": "Tablet", "strength": "10mg"},
    {"name": "Domperidone", "form": "Tablet", "strength": "30mg"},
    {"name": "Domstal", "form": "Tablet", "strength": "10mg"},
    {"name": "Ondansetron", "form": "Tablet", "strength": "4mg"},
    {"name": "Emeset", "form": "Tablet", "strength": "4mg"},
    {"name": "Diclofenac", "form": "Tablet", "strength": "50mg"},
    {"name": "Voveran", "form": "Tablet", "strength": "50mg"},
    {"name": "Voltaren", "form": "Tablet", "strength": "50mg"},
    {"name": "Cefixime", "form": "Tablet", "strength": "200mg"},
    {"name": "Taxim-O", "form": "Tablet", "strength": "200mg"},
    {"name": "Suprax", "form": "Tablet", "strength": "200mg"},
    {"name": "Montelukast", "form": "Tablet", "strength": "10mg"},
    {"name": "Montair", "form": "Tablet", "strength": "10mg"},
    {"name": "Singulair", "form": "Tablet", "strength": "10mg"},
    {"name": "Levothyroxine", "form": "Tablet", "strength": "50mcg"},
    {"name": "Eltroxin", "form": "Tablet", "strength": "50mcg"},
    {"name": "Thyronorm", "form": "Tablet", "strength": "50mcg"},
    {"name": "Amlodipine", "form": "Tablet", "strength": "5mg"},
    {"name": "Amlodipine", "form": "Tablet", "strength": "10mg"},
    {"name": "Amlovas", "form": "Tablet", "strength": "5mg"},
    {"name": "Norvasc", "form": "Tablet", "strength": "5mg"},
    {"name": "Telmisartan", "form": "Tablet", "strength": "40mg"},
    {"name": "Telmisartan", "form": "Tablet", "strength": "80mg"},
    {"name": "Telma", "form": "Tablet", "strength": "40mg"},
    {"name": "Micardis", "form": "Tablet", "strength": "40mg"},
    {"name": "Losartan", "form": "Tablet", "strength": "50mg"},
    {"name": "Cozaar", "form": "Tablet", "strength": "50mg"},
    {"name": "Repace", "form": "Tablet", "strength": "50mg"},
    {"name": "Enalapril", "form": "Tablet", "strength": "5mg"},
    {"name": "Envas", "form": "Tablet", "strength": "5mg"},
    {"name": "Atenolol", "form": "Tablet", "strength": "25mg"},
    {"name": "Atenolol", "form": "Tablet", "strength": "50mg"},
    {"name": "Aten", "form": "Tablet", "strength": "25mg"},
    {"name": "Tenormin", "form": "Tablet", "strength": "25mg"},
    {"name": "Metoprolol", "form": "Tablet", "strength": "25mg"},
    {"name": "Metoprolol", "form": "Tablet", "strength": "50mg"},
    {"name": "Betaloc", "form": "Tablet", "strength": "25mg"},
    {"name": "Salbutamol", "form": "Inhaler", "strength": "100mcg"},
    {"name": "Asthalin", "form": "Inhaler", "strength": "100mcg"},
    {"name": "Ventolin", "form": "Inhaler", "strength": "100mcg"},
    {"name": "Budesonide", "form": "Inhaler", "strength": "200mcg"},
    {"name": "Budecort", "form": "Inhaler", "strength": "200mcg"},
    {"name": "Insulin Regular", "form": "Injection", "strength": "100IU/ml"},
    {"name": "Humulin R", "form": "Injection", "strength": "100IU/ml"},
    {"name": "Actrapid", "form": "Injection", "strength": "100IU/ml"},
    {"name": "Methotrexate", "form": "Tablet", "strength": "2.5mg"},
    {"name": "Folic Acid", "form": "Tablet", "strength": "5mg"},
    {"name": "Ferrous Sulphate", "form": "Tablet", "strength": "200mg"},
    {"name": "Iron Folic Acid", "form": "Tablet", "strength": "100mg"},
    {"name": "Vitamin D3", "form": "Capsule", "strength": "60000IU"},
    {"name": "Calcirol", "form": "Capsule", "strength": "60000IU"},
    {"name": "Calcium Carbonate", "form": "Tablet", "strength": "500mg"},
    {"name": "Shelcal", "form": "Tablet", "strength": "500mg"},
    {"name": "Zincovit", "form": "Tablet", "strength": "Multivitamin"},
    {"name": "Becosules", "form": "Capsule", "strength": "Multivitamin"},
    {"name": "Doxycycline", "form": "Capsule", "strength": "100mg"},
    {"name": "Doxtran", "form": "Capsule", "strength": "100mg"},
    {"name": "Tetracycline", "form": "Capsule", "strength": "250mg"},
    {"name": "Levofloxacin", "form": "Tablet", "strength": "500mg"},
    {"name": "Levaquin", "form": "Tablet", "strength": "500mg"},
    {"name": "Cephalexin", "form": "Capsule", "strength": "250mg"},
    {"name": "Cephalexin", "form": "Capsule", "strength": "500mg"},
    {"name": "Sporidex", "form": "Capsule", "strength": "250mg"},
    {"name": "Clindamycin", "form": "Capsule", "strength": "150mg"},
    {"name": "Clindamycin", "form": "Capsule", "strength": "300mg"},
    {"name": "Dalacin C", "form": "Capsule", "strength": "150mg"},
    {"name": "Ceftriaxone", "form": "Injection", "strength": "1g"},
    {"name": "Monocef", "form": "Injection", "strength": "1g"},
    {"name": "Amikacin", "form": "Injection", "strength": "250mg/ml"},
    {"name": "Gentamicin", "form": "Injection", "strength": "80mg/2ml"},
    {"name": "Vancomycin", "form": "Injection", "strength": "500mg"},
    {"name": "Clonazepam", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Rivotril", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Alprazolam", "form": "Tablet", "strength": "0.25mg"},
    {"name": "Restyl", "form": "Tablet", "strength": "0.25mg"},
    {"name": "Lorazepam", "form": "Tablet", "strength": "1mg"},
    {"name": "Ativan", "form": "Tablet", "strength": "1mg"},
    {"name": "Diazepam", "form": "Tablet", "strength": "5mg"},
    {"name": "Valium", "form": "Tablet", "strength": "5mg"},
    {"name": "Sertraline", "form": "Tablet", "strength": "50mg"},
    {"name": "Zoloft", "form": "Tablet", "strength": "50mg"},
    {"name": "Serta", "form": "Tablet", "strength": "50mg"},
    {"name": "Fluoxetine", "form": "Capsule", "strength": "20mg"},
    {"name": "Prozac", "form": "Capsule", "strength": "20mg"},
    {"name": "Fludac", "form": "Capsule", "strength": "20mg"},
    {"name": "Escitalopram", "form": "Tablet", "strength": "10mg"},
    {"name": "Nexito", "form": "Tablet", "strength": "10mg"},
    {"name": "Rosavin", "form": "Tablet", "strength": "10mg"},
    {"name": "Olanzapine", "form": "Tablet", "strength": "5mg"},
    {"name": "Oleanz", "form": "Tablet", "strength": "5mg"},
    {"name": "Zyprexa", "form": "Tablet", "strength": "5mg"},
    {"name": "Risperidone", "form": "Tablet", "strength": "1mg"},
    {"name": "Sizodon", "form": "Tablet", "strength": "1mg"},
    {"name": "Hydroxychloroquine", "form": "Tablet", "strength": "200mg"},
    {"name": "Plaquenil", "form": "Tablet", "strength": "200mg"},
    {"name": "Hcqs", "form": "Tablet", "strength": "200mg"},
    {"name": "Ivermectin", "form": "Tablet", "strength": "12mg"},
    {"name": "Ivermectin", "form": "Tablet", "strength": "6mg"},
    {"name": "Remdesivir", "form": "Injection", "strength": "100mg"},
    {"name": "Favipiravir", "form": "Tablet", "strength": "400mg"},
    {"name": "Fabiflu", "form": "Tablet", "strength": "400mg"},
    {"name": "Tocilizumab", "form": "Injection", "strength": "400mg/20ml"},
    {"name": "Sildenafil", "form": "Tablet", "strength": "50mg"},
    {"name": "Viagra", "form": "Tablet", "strength": "50mg"},
    {"name": "Manforce", "form": "Tablet", "strength": "50mg"},
    {"name": "Tadalafil", "form": "Tablet", "strength": "10mg"},
    {"name": "Cialis", "form": "Tablet", "strength": "10mg"},
    {"name": "Glipizide", "form": "Tablet", "strength": "5mg"},
    {"name": "Glimepiride", "form": "Tablet", "strength": "1mg"},
    {"name": "Amaryl", "form": "Tablet", "strength": "1mg"},
    {"name": "Glibenclamide", "form": "Tablet", "strength": "5mg"},
    {"name": "Januvia", "form": "Tablet", "strength": "100mg"},
    {"name": "Sitagliptin", "form": "Tablet", "strength": "100mg"},
    {"name": "Warfarin", "form": "Tablet", "strength": "5mg"},
    {"name": "Clopidogrel", "form": "Tablet", "strength": "75mg"},
    {"name": "Plavix", "form": "Tablet", "strength": "75mg"},
    {"name": "Deplatt", "form": "Tablet", "strength": "75mg"},
    {"name": "Digoxin", "form": "Tablet", "strength": "0.25mg"},
    {"name": "Lanoxin", "form": "Tablet", "strength": "0.25mg"},
    {"name": "Furosemide", "form": "Tablet", "strength": "40mg"},
    {"name": "Lasix", "form": "Tablet", "strength": "40mg"},
    {"name": "Spironolactone", "form": "Tablet", "strength": "25mg"},
    {"name": "Aldactone", "form": "Tablet", "strength": "25mg"},
    {"name": "Morphine", "form": "Tablet", "strength": "10mg"},
    {"name": "Tramadol", "form": "Capsule", "strength": "50mg"},
    {"name": "Ultracet", "form": "Tablet", "strength": "37.5mg/325mg"},
    {"name": "Codeine", "form": "Tablet", "strength": "30mg"},
    {"name": "Gabapentin", "form": "Capsule", "strength": "300mg"},
    {"name": "Neurontin", "form": "Capsule", "strength": "300mg"},
    {"name": "Pregabalin", "form": "Capsule", "strength": "75mg"},
    {"name": "Lyrica", "form": "Capsule", "strength": "75mg"},
    {"name": "Torvast", "form": "Tablet", "strength": "10mg"},
    {"name": "Rosuvastatin", "form": "Tablet", "strength": "10mg"},
    {"name": "Crestor", "form": "Tablet", "strength": "10mg"},
    {"name": "Rozucor", "form": "Tablet", "strength": "10mg"},
    {"name": "Simvastatin", "form": "Tablet", "strength": "20mg"},
    {"name": "Zocor", "form": "Tablet", "strength": "20mg"},
    {"name": "Carvedilol", "form": "Tablet", "strength": "6.25mg"},
    {"name": "Coreg", "form": "Tablet", "strength": "6.25mg"},
    {"name": "Bisoprolol", "form": "Tablet", "strength": "2.5mg"},
    {"name": "Concor", "form": "Tablet", "strength": "2.5mg"},
    {"name": "Ramipril", "form": "Tablet", "strength": "2.5mg"},
    {"name": "Cardace", "form": "Tablet", "strength": "2.5mg"},
    {"name": "Lisinopril", "form": "Tablet", "strength": "5mg"},
    {"name": "Perindopril", "form": "Tablet", "strength": "4mg"},
    {"name": "Nebivolol", "form": "Tablet", "strength": "5mg"},
    {"name": "Nebicard", "form": "Tablet", "strength": "5mg"},
    {"name": "Valsartan", "form": "Tablet", "strength": "80mg"},
    {"name": "Diovan", "form": "Tablet", "strength": "80mg"},
    {"name": "Nifedipine", "form": "Tablet", "strength": "10mg"},
    {"name": "Nicardia", "form": "Tablet", "strength": "10mg"},
    {"name": "Diltiazem", "form": "Tablet", "strength": "30mg"},
    {"name": "Isosorbide Mononitrate", "form": "Tablet", "strength": "20mg"},
    {"name": "Imdur", "form": "Tablet", "strength": "30mg"},
    {"name": "Nitroglycerine", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Sorbitrate", "form": "Tablet", "strength": "5mg"},
    {"name": "Aceclofenac", "form": "Tablet", "strength": "100mg"},
    {"name": "Zerodol", "form": "Tablet", "strength": "100mg"},
    {"name": "Hifenac", "form": "Tablet", "strength": "100mg"},
    {"name": "Nimesulide", "form": "Tablet", "strength": "100mg"},
    {"name": "Nise", "form": "Tablet", "strength": "100mg"},
    {"name": "Ketorolac", "form": "Tablet", "strength": "10mg"},
    {"name": "Toradol", "form": "Tablet", "strength": "10mg"},
    {"name": "Hydroxyzine", "form": "Tablet", "strength": "10mg"},
    {"name": "Atarax", "form": "Tablet", "strength": "10mg"},
    {"name": "Chlorpheniramine", "form": "Tablet", "strength": "4mg"},
    {"name": "Piriton", "form": "Tablet", "strength": "4mg"},
    {"name": "Fexofenadine", "form": "Tablet", "strength": "120mg"},
    {"name": "Allegra", "form": "Tablet", "strength": "120mg"},
    {"name": "Loratadine", "form": "Tablet", "strength": "10mg"},
    {"name": "Claritin", "form": "Tablet", "strength": "10mg"},
    {"name": "Clarithromycin", "form": "Tablet", "strength": "250mg"},
    {"name": "Klaricid", "form": "Tablet", "strength": "250mg"},
    {"name": "Roxithromycin", "form": "Tablet", "strength": "150mg"},
    {"name": "Roxid", "form": "Tablet", "strength": "150mg"},
    {"name": "Co-amoxiclav", "form": "Tablet", "strength": "625mg"},
    {"name": "Augmentin", "form": "Tablet", "strength": "625mg"},
    {"name": "Clavam", "form": "Tablet", "strength": "625mg"},
    {"name": "Piperacillin", "form": "Injection", "strength": "4.5g"},
    {"name": "Meropenem", "form": "Injection", "strength": "1g"},
    {"name": "Imipenem", "form": "Injection", "strength": "500mg"},
    {"name": "ORS", "form": "Powder", "strength": "Electrolytes"},
    {"name": "Electral", "form": "Powder", "strength": "Electrolytes"},
    {"name": "Oral Rehydration Salts", "form": "Powder", "strength": "Electrolytes"},
    {"name": "Dextrose", "form": "Injection", "strength": "5%"},
    {"name": "Normal Saline", "form": "Injection", "strength": "0.9%"},
    {"name": "Ringer Lactate", "form": "Injection", "strength": "Electrolytes"},
    {"name": "Human Albumin", "form": "Injection", "strength": "20%"},
    {"name": "Clobetasol", "form": "Cream", "strength": "0.05%"},
    {"name": "Betamethasone Cream", "form": "Cream", "strength": "0.1%"},
    {"name": "Hydrocortisone", "form": "Cream", "strength": "1%"},
    {"name": "Calamine Lotion", "form": "Lotion", "strength": "8%"},
    {"name": "Mupirocin", "form": "Ointment", "strength": "2%"},
    {"name": "Bactroban", "form": "Ointment", "strength": "2%"},
    {"name": "Clotrimazole", "form": "Cream", "strength": "1%"},
    {"name": "Canesten", "form": "Cream", "strength": "1%"},
    {"name": "Fluconazole", "form": "Capsule", "strength": "150mg"},
    {"name": "Flucos", "form": "Capsule", "strength": "150mg"},
    {"name": "Diflucan", "form": "Capsule", "strength": "150mg"},
    {"name": "Terbinafine", "form": "Tablet", "strength": "250mg"},
    {"name": "Lamisil", "form": "Tablet", "strength": "250mg"},
    {"name": "Voriconazole", "form": "Tablet", "strength": "200mg"},
    {"name": "Acyclovir", "form": "Tablet", "strength": "400mg"},
    {"name": "Zovirax", "form": "Tablet", "strength": "400mg"},
    {"name": "Valacyclovir", "form": "Tablet", "strength": "500mg"},
    {"name": "Valtrex", "form": "Tablet", "strength": "500mg"},
    {"name": "Oseltamivir", "form": "Capsule", "strength": "75mg"},
    {"name": "Tamiflu", "form": "Capsule", "strength": "75mg"},
    {"name": "Tenofovir", "form": "Tablet", "strength": "300mg"},
    {"name": "Efavirenz", "form": "Tablet", "strength": "600mg"},
    {"name": "Lamivudine", "form": "Tablet", "strength": "150mg"},
    {"name": "Allopurinol", "form": "Tablet", "strength": "100mg"},
    {"name": "Zyloric", "form": "Tablet", "strength": "100mg"},
    {"name": "Colchicine", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Phenytoin", "form": "Tablet", "strength": "100mg"},
    {"name": "Dilantin", "form": "Tablet", "strength": "100mg"},
    {"name": "Carbamazepine", "form": "Tablet", "strength": "200mg"},
    {"name": "Tegretol", "form": "Tablet", "strength": "200mg"},
    {"name": "Sodium Valproate", "form": "Tablet", "strength": "200mg"},
    {"name": "Valparin", "form": "Tablet", "strength": "200mg"},
    {"name": "Levetiracetam", "form": "Tablet", "strength": "500mg"},
    {"name": "Keppra", "form": "Tablet", "strength": "500mg"},
    {"name": "Levorag", "form": "Tablet", "strength": "500mg"},
    {"name": "Topiramate", "form": "Tablet", "strength": "50mg"},
    {"name": "Topamax", "form": "Tablet", "strength": "50mg"},
    {"name": "Propranolol", "form": "Tablet", "strength": "10mg"},
    {"name": "Inderal", "form": "Tablet", "strength": "10mg"},
    {"name": "Thyronorm", "form": "Tablet", "strength": "100mcg"},
    {"name": "Methimazole", "form": "Tablet", "strength": "10mg"},
    {"name": "Carbimazole", "form": "Tablet", "strength": "5mg"},
    {"name": "Neomercazole", "form": "Tablet", "strength": "5mg"},
    {"name": "Prednisone", "form": "Tablet", "strength": "5mg"},
    {"name": "Deflazacort", "form": "Tablet", "strength": "6mg"},
    {"name": "Betamethasone", "form": "Tablet", "strength": "0.5mg"},
    {"name": "Celecoxib", "form": "Capsule", "strength": "200mg"},
    {"name": "Celebrex", "form": "Capsule", "strength": "200mg"},
    {"name": "Etoricoxib", "form": "Tablet", "strength": "90mg"},
    {"name": "Arcoxia", "form": "Tablet", "strength": "90mg"},
    {"name": "Etodolac", "form": "Tablet", "strength": "400mg"},
    {"name": "Piroxicam", "form": "Capsule", "strength": "20mg"},
    {"name": "Dolonex", "form": "Capsule", "strength": "20mg"},
    {"name": "Naproxen", "form": "Tablet", "strength": "250mg"},
    {"name": "Naprosyn", "form": "Tablet", "strength": "250mg"},
    {"name": "Mefenamic Acid", "form": "Capsule", "strength": "250mg"},
    {"name": "Meftal", "form": "Capsule", "strength": "250mg"},
    {"name": "Pantop", "form": "Tablet", "strength": "40mg"},
    {"name": "Neksium", "form": "Tablet", "strength": "20mg"},
    {"name": "Esomeprazole", "form": "Tablet", "strength": "20mg"},
    {"name": "Rabeprazole", "form": "Tablet", "strength": "20mg"},
    {"name": "Razo", "form": "Tablet", "strength": "20mg"},
    {"name": "Lansoprazole", "form": "Capsule", "strength": "30mg"},
    {"name": "Prevacid", "form": "Capsule", "strength": "30mg"},
    {"name": "Sucralfate", "form": "Tablet", "strength": "1g"},
    {"name": "Sucral", "form": "Tablet", "strength": "1g"},
    {"name": "Famotidine", "form": "Tablet", "strength": "20mg"},
    {"name": "Pepcid", "form": "Tablet", "strength": "20mg"},
    {"name": "Lactulose", "form": "Syrup", "strength": "3.35g/5ml"},
    {"name": "Bisacodyl", "form": "Tablet", "strength": "5mg"},
    {"name": "Dulcolax", "form": "Tablet", "strength": "5mg"},
    {"name": "Sennoside", "form": "Tablet", "strength": "8.6mg"},
    {"name": "Ispaghula", "form": "Powder", "strength": "3.5g"},
    {"name": "Isabgol", "form": "Powder", "strength": "3.5g"},
    {"name": "Methyldopa", "form": "Tablet", "strength": "250mg"},
    {"name": "Aldomet", "form": "Tablet", "strength": "250mg"},
    {"name": "Labetalol", "form": "Tablet", "strength": "100mg"},
    {"name": "Hydralazine", "form": "Tablet", "strength": "25mg"},
    {"name": "Nifedipine Retard", "form": "Tablet", "strength": "20mg"},
    {"name": "Clonidine", "form": "Tablet", "strength": "0.1mg"},
    {"name": "Iron Sucrose", "form": "Injection", "strength": "100mg/5ml"},
    {"name": "Erythropoietin", "form": "Injection", "strength": "2000IU"},
    {"name": "Sodium Bicarbonate", "form": "Tablet", "strength": "650mg"},
    {"name": "Vitamin B12", "form": "Injection", "strength": "1000mcg"},
    {"name": "Mecobalamin", "form": "Tablet", "strength": "500mcg"},
    {"name": "Cobadex Forte", "form": "Capsule", "strength": "Multivitamin"},
]

KNOWN_RECALLS = [
    # Some well-known globally recalled/banned drugs 
    {"name": "Phenyl Butazone", "reason": "Banned in India - associated with aplastic anaemia and agranulocytosis", "authority": "CDSCO", "status": "recalled"},
    {"name": "Oxyphenbutazone", "reason": "Banned in India - blood disorders", "authority": "CDSCO", "status": "recalled"},
    {"name": "Furazolidone", "reason": "Banned in India - carcinogenic risk", "authority": "CDSCO", "status": "recalled"},
    {"name": "Nitrofurazone", "reason": "Banned in India - carcinogenic", "authority": "CDSCO", "status": "recalled"},
    {"name": "Metronidazole Ofloxacin", "reason": "Fixed dose combination banned - irrational", "authority": "CDSCO", "status": "recalled"},
    {"name": "Analgin", "reason": "Dipyrone/Metamizole - banned in India due to agranulocytosis risk", "authority": "CDSCO", "status": "recalled"},
    {"name": "Metamizole", "reason": "Banned in India - severe blood disorder risk", "authority": "CDSCO", "status": "recalled"},
    {"name": "Sibutramine", "reason": "Withdrawn globally - cardiovascular risks; banned in India", "authority": "CDSCO", "status": "recalled"},
    {"name": "Rimonabant", "reason": "Withdrawn globally - psychiatric side effects", "authority": "CDSCO", "status": "recalled"},
    {"name": "Rosiglitazone", "reason": "Restricted/banned - increased heart attack risk (Avandia)", "authority": "US FDA", "status": "recalled"},
    {"name": "Avandia", "reason": "Restricted/banned - increased heart attack risk", "authority": "US FDA", "status": "recalled"},
    {"name": "Vioxx", "reason": "Withdrawn - increased risk of heart attack and stroke (Rofecoxib)", "authority": "US FDA", "status": "recalled"},
    {"name": "Rofecoxib", "reason": "Withdrawn globally - increased cardiovascular events", "authority": "US FDA", "status": "recalled"},
    {"name": "Fen-phen", "reason": "Withdrawn - heart valve abnormalities (Fenfluramine)", "authority": "US FDA", "status": "recalled"},
    {"name": "Fenfluramine", "reason": "Withdrawn - pulmonary hypertension and heart valve problems", "authority": "US FDA", "status": "recalled"},
    {"name": "Dextropropoxyphene", "reason": "Withdrawn - fatal overdose risk; banned in India", "authority": "CDSCO", "status": "recalled"},
    {"name": "Propoxyphene", "reason": "Withdrawn - serious heart rhythm problems", "authority": "US FDA", "status": "recalled"},
    {"name": "Nimesulide Syrup", "reason": "Banned for paediatric use in India - liver toxicity", "authority": "CDSCO", "status": "recalled"},
    {"name": "PPA (Phenylpropanolamine)", "reason": "Withdrawn - stroke risk in young women", "authority": "US FDA", "status": "recalled"},
    {"name": "Thalidomide", "reason": "Historical - severe birth defects; restricted use only", "authority": "CDSCO", "status": "recalled"},
    {"name": "Cisapride", "reason": "Withdrawn - fatal cardiac arrhythmias", "authority": "US FDA", "status": "recalled"},
    {"name": "Prepulsid", "reason": "Withdrawn - cardiac events (Cisapride brand)", "authority": "US FDA", "status": "recalled"},
    {"name": "Troglitazone", "reason": "Withdrawn - fatal liver failure", "authority": "US FDA", "status": "recalled"},
    {"name": "Rezulin", "reason": "Withdrawn - liver failure (Troglitazone brand)", "authority": "US FDA", "status": "recalled"},
    {"name": "Baycol", "reason": "Withdrawn - fatal rhabdomyolysis (Cerivastatin)", "authority": "US FDA", "status": "recalled"},
    {"name": "Cerivastatin", "reason": "Withdrawn - risk of fatal rhabdomyolysis", "authority": "US FDA", "status": "recalled"},
    {"name": "Fluoroquinolone (systemic)", "reason": "Black box warning - disabling side effects on tendons, nerves", "authority": "US FDA", "status": "recalled"},
    {"name": "Tegaserod", "reason": "Withdrawn - increased risk of heart attacks and strokes", "authority": "US FDA", "status": "recalled"},
    {"name": "Zelnorm", "reason": "Withdrawn - cardiovascular events (Tegaserod brand)", "authority": "US FDA", "status": "recalled"},
    {"name": "Valdecoxib", "reason": "Withdrawn - cardiovascular risk and skin reactions", "authority": "US FDA", "status": "recalled"},
    {"name": "Bextra", "reason": "Withdrawn - cardiovascular and skin risks (Valdecoxib)", "authority": "US FDA", "status": "recalled"},
    {"name": "Lumiracoxib", "reason": "Withdrawn - liver failure", "authority": "WHO", "status": "recalled"},
    {"name": "Pemoline", "reason": "Withdrawn - liver failure risk", "authority": "US FDA", "status": "recalled"},
    {"name": "Cylert", "reason": "Withdrawn - liver toxicity (Pemoline brand)", "authority": "US FDA", "status": "recalled"},
    {"name": "Droperidol", "reason": "Black box warning - fatal arrhythmias (IV use)", "authority": "US FDA", "status": "recalled"},
    {"name": "Kava", "reason": "Banned in several countries - hepatotoxicity", "authority": "WHO", "status": "recalled"},
    {"name": "Aristolochic acid", "reason": "Banned - causes kidney failure and cancer", "authority": "CDSCO", "status": "recalled"},
    {"name": "Counterfeit", "reason": "Counterfeit/fake medicine - do not consume", "authority": "CDSCO", "status": "recalled"},
    {"name": "Spurious", "reason": "Spurious/substandard medicine detected by CDSCO", "authority": "CDSCO", "status": "recalled"},
    {"name": "Adulterated", "reason": "Adulterated medicine - toxic contaminants detected", "authority": "CDSCO", "status": "recalled"},
]


def upsert_medicine_simple(client, name: str, form: str = None, strength: str = None):
    """Insert a medicine into the medicines table, skip if already exists."""
    try:
        existing = client.table('medicines').select('id').ilike('name', name).limit(1).execute()
        if existing.data:
            return False  # already exists

        payload = {
            'name': name,
            'form': form,
            'strength': strength,
            'metadata': {'source': 'curated_seed', 'approved': True}
        }
        client.table('medicines').insert(payload).execute()
        return True
    except Exception as e:
        log.warning('Failed to insert medicine %s: %s', name, e)
        return False


def insert_recall_simple(client, name: str, reason: str, authority: str, status: str = 'open'):
    """Insert a recall record."""
    try:
        existing = client.table('drug_recalls').select('id').eq('reason', reason[:100]).limit(1).execute()
        if existing.data:
            return False

        payload = {
            'authority': authority,
            'recall_number': None,
            'reason': reason,
            'status': status,
            'raw_payload': {'source': 'curated_seed', 'drug_name': name}
        }
        client.table('drug_recalls').insert(payload).execute()
        return True
    except Exception as e:
        log.warning('Failed to insert recall %s: %s', name, e)
        return False


def insert_alert_simple(client, name: str, reason: str, authority: str):
    """Insert a drug alert record for a banned/recalled drug."""
    try:
        existing = client.table('drug_alerts').select('id').ilike('title', f'%{name}%').limit(1).execute()
        if existing.data:
            return False

        payload = {
            'authority': authority,
            'title': f'{name} - Banned/Recalled Drug',
            'summary': reason,
            'details': reason,
            'severity': 'high',
            'raw_payload': {'source': 'curated_seed', 'drug_name': name}
        }
        client.table('drug_alerts').insert(payload).execute()
        return True
    except Exception as e:
        log.warning('Failed to insert alert %s: %s', name, e)
        return False


def seed_openfda(client, pages: int = 10):
    """Seed from OpenFDA drug labels API."""
    log.info('=== Seeding from OpenFDA Drug Labels API ===')
    total = 0
    for page in range(pages):
        skip = page * 100
        try:
            r = requests.get(
                'https://api.fda.gov/drug/label.json',
                params={'limit': 100, 'skip': skip},
                timeout=30,
                headers={'User-Agent': 'MedVerify/Seed'}
            )
            r.raise_for_status()
            results = r.json().get('results', [])
            for item in results:
                openfda = item.get('openfda', {})
                generic_names = openfda.get('generic_name', [])
                brand_names = openfda.get('brand_name', [])
                all_names = list(set(generic_names + brand_names))
                for name in all_names[:3]:  # limit to avoid duplicates
                    if name and len(name) > 1:
                        inserted = upsert_medicine_simple(client, str(name)[:200])
                        if inserted:
                            total += 1
        except Exception as e:
            log.warning('OpenFDA page %d failed: %s', page + 1, e)
        time.sleep(0.5)
    log.info('OpenFDA seeding done: %d new medicines', total)
    return total


def main():
    log.info('========== SafeMeds AI - Database Seeder ==========')

    # Step 1: Seed common Indian & global medicines
    log.info('\n=== Step 1: Seeding curated medicines list (%d items) ===', len(COMMON_MEDICINES))
    med_count = 0
    for med in COMMON_MEDICINES:
        inserted = upsert_medicine_simple(client, med['name'], med.get('form'), med.get('strength'))
        if inserted:
            med_count += 1
    log.info('Curated medicines seeded: %d new, %d already existed', med_count, len(COMMON_MEDICINES) - med_count)

    # Step 2: Seed known recalls/banned drugs as both recall AND alert
    log.info('\n=== Step 2: Seeding known banned/recalled drugs (%d items) ===', len(KNOWN_RECALLS))
    recall_count = 0
    alert_count = 0
    for item in KNOWN_RECALLS:
        # fix typo in status field
        item_status = item.get('status', 'open')
        if isinstance(item_status, str):
            item_status = item_status.replace('=', '').strip()
        
        r = insert_recall_simple(client, item['name'], item['reason'], item['authority'], item_status)
        a = insert_alert_simple(client, item['name'], item['reason'], item['authority'])
        if r: recall_count += 1
        if a: alert_count += 1
    log.info('Banned/recalled drugs seeded: %d recalls, %d alerts', recall_count, alert_count)

    # Step 3: Seed from OpenFDA API
    log.info('\n=== Step 3: Seeding from OpenFDA API (10 pages) ===')
    fda_count = seed_openfda(client, pages=10)

    # Step 4: Final counts
    log.info('\n=== Final Table Counts ===')
    for table in ['medicines', 'drug_alerts', 'drug_recalls']:
        res = client.table(table).select('*', count='exact').limit(1).execute()
        count = res.count if hasattr(res, 'count') and res.count else '?'
        log.info('  %-20s : %s records', table, count)

    log.info('\n========== Seeding Complete ==========')
    log.info('Summary: %d curated medicines, %d recalls, %d alerts, %d from OpenFDA',
             med_count, recall_count, alert_count, fda_count)


if __name__ == '__main__':
    main()
