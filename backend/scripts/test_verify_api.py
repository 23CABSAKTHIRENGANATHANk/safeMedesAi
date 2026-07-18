import sys
import requests

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'http://localhost:8000'

print('=' * 80)
print('SafeMeds AI -- Full API Test Suite')
print('=' * 80)

# 1. Health check
try:
    r = requests.get(BASE + '/', timeout=5)
    h = r.json()
    print('\n[OK] Health check:', h)
except Exception as e:
    print('\n[ERR] Backend not reachable:', e)
    print('   Make sure to start the backend: npm run backend:dev')
    sys.exit(1)

# Test cases: (medicine_name, expected_status, description)
test_cases = [
    # Safe medicines - must return 'safe'
    ('Paracetamol',        'safe',    'Very common pain reliever'),
    ('Dolo 650',           'safe',    'Indian Paracetamol brand'),
    ('Crocin',             'safe',    'Indian Paracetamol brand'),
    ('Amoxicillin',        'warning', 'Common antibiotic (has counterfeit warning alert)'),
    ('Ibuprofen',          'safe',    'Common NSAID'),
    ('Aspirin',            'safe',    'Common analgesic'),
    ('Metformin',          'safe',    'Diabetes medication'),
    ('Ciprofloxacin',      'safe',    'Antibiotic'),
    ('Pantoprazole',       'safe',    'PPI stomach med'),
    ('Cetirizine',         'safe',    'Antihistamine'),
    ('Atorvastatin',       'safe',    'Cholesterol med'),
    ('Azithromycin',       'safe',    'Antibiotic'),
    ('Omeprazole',         'safe',    'PPI stomach med'),
    ('Amlodipine',         'safe',    'Blood pressure med'),
    ('Metoprolol',         'safe',    'Beta blocker'),
    # Banned/recalled drugs - must return 'unsafe'
    ('Vioxx',              'unsafe',  'Recalled - heart attack risk'),
    ('Rofecoxib',          'unsafe',  'Withdrawn - cardiovascular'),
    ('Sibutramine',        'unsafe',  'Banned weight loss drug'),
    ('Avandia',            'unsafe',  'Restricted - heart risk'),
    ('Cisapride',          'unsafe',  'Withdrawn - cardiac arrhythmias'),
    ('Thalidomide',        'unsafe',  'Banned - birth defects'),
    # Unknown medicines - must return 'unknown'
    ('xyzfakemedicine123', 'unknown', 'Completely fake medicine'),
    ('ASDF1234NOTREAL',    'unknown', 'Non-existent drug'),
]

print('\n=== Running {} verification tests ===\n'.format(len(test_cases)))
print('{:<28} {:<10} {:<10} {:<8} {}'.format('Medicine', 'Expected', 'Got', 'Result', 'Note'))
print('-' * 100)

passed = 0
failed = 0
errors = 0

for name, expected, desc in test_cases:
    try:
        r = requests.post(BASE + '/api/verify', json={'name': name}, timeout=20)
        if r.status_code != 200:
            print('{:<28} {:<10} {:<10} {:<8} HTTP {}'.format(name, expected, 'ERR', '[ERR]', r.status_code))
            errors += 1
            continue
        data = r.json()
        got = data.get('status', 'error').lower()
        ok = got == expected.lower()
        if ok:
            passed += 1
            symbol = '[PASS]'
        else:
            failed += 1
            symbol = '[FAIL]'
        reason_short = (data.get('reason') or '')[:45]
        print('{:<28} {:<10} {:<10} {:<8} {}'.format(name, expected, got, symbol, reason_short))
    except Exception as e:
        print('{:<28} {:<10} {:<10} {:<8} {}'.format(name, expected, 'ERR', '[ERR]', str(e)[:45]))
        errors += 1

print()
print('=' * 80)
total = passed + failed + errors
print('RESULTS: {}/{} passed | {} failed | {} errors'.format(passed, total, failed, errors))

if failed == 0 and errors == 0:
    print('ALL TESTS PASSED!')
elif passed >= int(total * 0.8):
    print('Most tests passed but some failures remain.')
else:
    print('Too many failures -- check database seeding and logs.')

# 3. Test other endpoints
print('\n=== Testing Other Endpoints ===\n')
endpoints = [
    ('GET', '/api/medicines?page=1&limit=5', 'List medicines (5)'),
    ('GET', '/api/alerts?page=1&limit=5',    'List alerts (5)'),
    ('GET', '/api/recalls?page=1&limit=5',   'List recalls (5)'),
    ('GET', '/api/search?medicine=paracetamol', 'Search paracetamol'),
]
for method, path, label in endpoints:
    try:
        r = requests.request(method, BASE + path, timeout=10)
        data = r.json()
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data.get('data', data))
        else:
            count = 0
        print('  {:<30} -> HTTP {} | {} records returned'.format(label, r.status_code, count))
    except Exception as e:
        print('  {:<30} -> ERROR: {}'.format(label, str(e)[:50]))

print()
