"""Check which job files have complete agent data"""
import json
from pathlib import Path

jobs_dir = Path("data/jobs")
job_files = list(jobs_dir.glob("*.json"))

print(f"Checking {len(job_files)} job files...\n")

for job_file in job_files:
    with open(job_file, 'r') as f:
        data = json.load(f)
    
    # Check for key agent data
    has_risk = 'risk_assessment' in data
    has_validator = 'external_validator' in data
    has_tax = 'tax_structuring' in data
    has_comp = 'competitive_benchmarking' in data
    has_macro = 'macroeconomic_analyst' in data
    has_deep_dive = 'financial_deep_dive' in data
    
    completeness = sum([has_risk, has_validator, has_tax, has_comp, has_macro, has_deep_dive])
    
    print(f"{job_file.name}:")
    print(f"  Completeness: {completeness}/6")
    print(f"  risk={has_risk}, validator={has_validator}, tax={has_tax}")
    print(f"  comp={has_comp}, macro={has_macro}, deep_dive={has_deep_dive}")
    print()
    
    if completeness == 6:
        print(f"✓ COMPLETE FILE FOUND: {job_file.name}\n")
        break
