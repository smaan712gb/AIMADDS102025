"""
Test Complete Report Regeneration - Excel + PDF with All Agent Data
"""
import json
from pathlib import Path
from src.outputs.revolutionary_excel_generator import RevolutionaryExcelGenerator
from src.outputs.revolutionary_pdf_generator import RevolutionaryPDFGenerator

# Load CRWV job data
job_file = Path("data/jobs/360181db-a8a9-4885-87f7-b56b767bd952.json")
with open(job_file, 'r') as f:
    state = json.load(f)

print(f"="*80)
print(f"TESTING COMPLETE REPORT GENERATION FOR {state.get('target_company', 'Unknown')}")
print(f"="*80)

# Count agent outputs
agent_outputs = state.get('agent_outputs', [])
print(f"\nAgent Outputs: {len(agent_outputs)}")

# Check for critical data
print("\n" + "="*80)
print("CRITICAL AGENT DATA AVAILABILITY")
print("="*80)

critical_agents = [
    ('financial_analyst', ['normalized_financials', 'anomaly_detection', 'advanced_valuation']),
    ('financial_deep_dive', ['working_capital', 'capex_analysis', 'debt_schedule']),
    ('risk_assessment', ['risk_matrix', 'risk_scores', 'risk_scenarios']),
    ('tax_structuring', ['tax_position', 'structure_comparison', 'optimal_structure']),
    ('legal_counsel', None),  # Uses state.legal_risks[]
    ('external_validator', ['validation_results', 'confidence_score'])
]

for agent_name, expected_keys in critical_agents:
    agent = next((o for o in agent_outputs if o.get('agent_name') == agent_name), None)
    if agent and 'data' in agent:
        if expected_keys:
            available = [k for k in expected_keys if k in agent['data']]
            print(f"✓ {agent_name}: {len(available)}/{len(expected_keys)} keys available")
        else:
            print(f"✓ {agent_name}: Data present")
    else:
        print(f"✗ {agent_name}: NO DATA")

# Check legal_risks array
legal_risks = state.get('legal_risks', [])
print(f"✓ legal_risks: {len(legal_risks)} risks found")

# Check LBO data
lbo_data = state.get('valuation_models', {}).get('dcf_advanced', {}).get('lbo_analysis', {})
if lbo_data:
    returns = lbo_data.get('returns_analysis', {})
    print(f"✓ LBO Analysis: IRR {returns.get('irr_percent', 0):.1f}%, MoM {returns.get('multiple_of_money', 0):.2f}x")
else:
    print("✗ LBO Analysis: NOT FOUND")

print("\n" + "="*80)
print("REGENERATING EXCEL REPORT")
print("="*80)

try:
    excel_gen = RevolutionaryExcelGenerator()
    excel_path = excel_gen.generate_revolutionary_workbook(state)
    print(f"✓ Excel generated: {excel_path}")
    
    # Check file size
    excel_file = Path(excel_path)
    if excel_file.exists():
        size_kb = excel_file.stat().st_size / 1024
        print(f"  File size: {size_kb:.1f} KB")
except Exception as e:
    print(f"✗ Excel generation failed: {e}")

print("\n" + "="*80)
print("REGENERATING PDF REPORT")
print("="*80)

try:
    pdf_gen = RevolutionaryPDFGenerator()
    pdf_path = pdf_gen.generate_revolutionary_report(state)
    print(f"✓ PDF generated: {pdf_path}")
    
    # Check file size
    pdf_file = Path(pdf_path)
    if pdf_file.exists():
        size_kb = pdf_file.stat().st_size / 1024
        print(f"  File size: {size_kb:.1f} KB")
except Exception as e:
    print(f"✗ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("REPORT GENERATION TEST COMPLETE")
print("="*80)
