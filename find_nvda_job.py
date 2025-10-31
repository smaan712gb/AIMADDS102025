"""Find NVDA job data file"""
import json
from pathlib import Path

job_files = list(Path("data/jobs").glob("*.json"))

for job_file in job_files:
    try:
        with open(job_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            ticker = data.get('target_ticker', '')
            if ticker == 'NVDA':
                print(f"✅ Found NVDA job: {job_file.name}")
                print(f"   Acquirer: {data.get('acquirer_company', 'N/A')}")
                print(f"   Deal Type: {data.get('deal_type', 'N/A')}")
                break
    except Exception as e:
        continue
else:
    print("❌ No NVDA job found in data/jobs/")
    print("\nSearching for NVDA in file names...")
    nvda_files = list(Path("data/jobs").glob("*nvda*.json"))
    if nvda_files:
        print(f"Found: {nvda_files}")
