"""
Test Excel Report Regeneration with Real CRWV Data
"""
import json
from pathlib import Path
from src.outputs.revolutionary_excel_generator import RevolutionaryExcelGenerator

# Load CRWV job data
job_file = Path("data/jobs/360181db-a8a9-4885-87f7-b56b767bd952.json")
with open(job_file, 'r') as f:
    state = json.load(f)

print(f"Loaded job data for {state.get('target_company', 'Unknown')}")
print(f"Agent outputs count: {len(state.get('agent_outputs', []))}")

# Print agent output keys to understand data structure
print("\n=== AGENT OUTPUT ANALYSIS ===")
for agent_output in state.get('agent_outputs', []):
    agent_name = agent_output.get('agent_name', agent_output.get('agent_key', 'unknown'))
    has_data = agent_output.get('has_data', False)
    data_keys = []
    
    if 'data' in agent_output and isinstance(agent_output['data'], dict):
        data_keys = list(agent_output['data'].keys())
    
    print(f"\nAgent: {agent_name}")
    print(f"  Has Data: {has_data}")
    print(f"  Data Keys: {data_keys[:5] if data_keys else 'None'}")  # First 5 keys

# Check specific critical data for Excel tabs
print("\n=== CRITICAL DATA FOR EXCEL TABS ===")

# 1. Normalization Ledger (Financial Analyst)
financial_analyst = next((o for o in state.get('agent_outputs', []) 
                         if o.get('agent_name') == 'financial_analyst'), None)
if financial_analyst and 'data' in financial_analyst:
    print(f"\n1. Financial Analyst Data Available:")
    print(f"   - normalized_financials: {'normalized_financials' in financial_analyst.get('data', {})}")
    print(f"   - anomaly_detection: {'anomaly_detection' in financial_analyst.get('data', {})}")
    adjustments = state.get('normalized_financials', {}).get('adjustments', [])
    print(f"   - Adjustments count: {len(adjustments)}")

# 2. Working Capital (Financial Deep Dive)
deep_dive = next((o for o in state.get('agent_outputs', []) 
                 if o.get('agent_name') == 'financial_deep_dive'), None)
if deep_dive and 'data' in deep_dive:
    print(f"\n2. Financial Deep Dive Data Available:")
    dd_data = deep_dive.get('data', {})
    print(f"   - working_capital: {'working_capital' in dd_data}")
    print(f"   - capex_analysis: {'capex_analysis' in dd_data}")
    print(f"   - debt_schedule: {'debt_schedule' in dd_data}")

# 3. Legal Risks
legal = next((o for o in state.get('agent_outputs', []) 
             if 'legal' in o.get('agent_name', '').lower()), None)
if legal and 'data' in legal:
    print(f"\n3. Legal Counsel Data Available:")
    print(f"   Data keys: {list(legal.get('data', {}).keys())}")

# 4. Risk Assessment
risk = next((o for o in state.get('agent_outputs', []) 
            if 'risk' in o.get('agent_name', '').lower()), None)
if risk and 'data' in risk:
    print(f"\n4. Risk Assessment Data Available:")
    risk_data = risk.get('data', {})
    print(f"   - risk_matrix: {'risk_matrix' in risk_data}")
    print(f"   - risk_scores: {'risk_scores' in risk_data}")
    print(f"   - risk_scenarios: {'risk_scenarios' in risk_data}")

# 5. Tax Structuring
tax = next((o for o in state.get('agent_outputs', []) 
           if 'tax' in o.get('agent_name', '').lower()), None)
if tax and 'data' in tax:
    print(f"\n5. Tax Structuring Data Available:")
    tax_data = tax.get('data', {})
    print(f"   - tax_position: {'tax_position' in tax_data}")
    print(f"   - structure_comparison: {'structure_comparison' in tax_data}")

print("\n=== GENERATING EXCEL REPORT ===")

# Generate Excel
generator = RevolutionaryExcelGenerator()
try:
    excel_path = generator.generate_revolutionary_workbook(state)
    print(f"✓ Excel generated: {excel_path}")
except Exception as e:
    print(f"✗ Excel generation failed: {e}")
    import traceback
    traceback.print_exc()
