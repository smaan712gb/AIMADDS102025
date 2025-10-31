"""
Diagnostic script to check why Revolutionary Excel tabs show zeros
Checks actual state data for 3-Statement Model and Competitive Benchmarking tabs
"""
import json
from pathlib import Path


def diagnose_state_data(job_id: str = None):
    """
    Diagnose what data is actually in state for Excel tabs
    
    Args:
        job_id: Optional job ID to check. If None, finds latest job.
    """
    # Find latest job file
    jobs_dir = Path("data/jobs")
    
    if not jobs_dir.exists():
        print("❌ No jobs directory found at data/jobs")
        return
    
    job_files = list(jobs_dir.glob("*.json"))
    
    if not job_files:
        print("❌ No job files found in data/jobs")
        return
    
    # Get latest job
    if job_id:
        job_file = jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            print(f"❌ Job {job_id} not found")
            return
    else:
        job_file = max(job_files, key=lambda p: p.stat().st_mtime)
        job_id = job_file.stem
    
    print(f"\n{'='*80}")
    print(f"DIAGNOSING JOB: {job_id}")
    print(f"File: {job_file}")
    print(f"{'='*80}\n")
    
    # Load job data
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    # Check what data exists
    print("\n=== TOP-LEVEL STATE KEYS ===")
    print(f"Keys: {list(state.keys())}\n")
    
    # 1. Check 3-Statement Model data sources
    print("\n=== 3-STATEMENT MODEL DATA SOURCES ===")
    
    # Check normalized_financials
    normalized = state.get('normalized_financials', {})
    if normalized:
        print("✓ state['normalized_financials'] EXISTS")
        print(f"  Keys: {list(normalized.keys())}")
        
        income = normalized.get('income_statement', [])
        balance = normalized.get('balance_sheet', [])
        cashflow = normalized.get('cash_flow', [])
        
        print(f"  income_statement: {len(income)} records")
        print(f"  balance_sheet: {len(balance)} records")
        print(f"  cash_flow: {len(cashflow)} records")
        
        if income:
            latest = income[0]
            revenue = latest.get('revenue', 0)
            ebitda = latest.get('ebitda', 0)
            print(f"  Latest revenue: ${revenue:,.0f}")
            print(f"  Latest EBITDA: ${ebitda:,.0f}")
    else:
        print("❌ state['normalized_financials'] MISSING")
    
    # Check financial_data
    financial_data = state.get('financial_data', {})
    if financial_data:
        print("\n✓ state['financial_data'] EXISTS")
        print(f"  Keys: {list(financial_data.keys())}")
        
        income = financial_data.get('income_statement', [])
        print(f"  income_statement: {len(income)} records")
        
        if income:
            latest = income[0]
            revenue = latest.get('revenue', 0)
            print(f"  Latest revenue: ${revenue:,.0f}")
    else:
        print("\n❌ state['financial_data'] MISSING")
    
    # Check synthesized data
    consolidated = state.get('consolidated_insights', {})
    if consolidated:
        print("\n✓ state['consolidated_insights'] EXISTS")
        print(f"  Keys: {list(consolidated.keys())}")
    else:
        print("\n❌ state['consolidated_insights'] MISSING")
    
    # Check agent outputs
    print("\n=== AGENT OUTPUTS ===")
    agent_outputs = state.get('agent_outputs', [])
    print(f"Total agent outputs: {len(agent_outputs)}")
    
    for output in agent_outputs:
        agent_name = output.get('agent_name', 'unknown')
        data_keys = list(output.get('data', {}).keys())
        print(f"  {agent_name}: {len(data_keys)} data keys - {data_keys[:5]}")
    
    # 2. Check Competitive Benchmarking data sources
    print("\n=== COMPETITIVE BENCHMARKING DATA SOURCES ===")
    
    # Check for competitive_benchmarking agent
    comp_agent = next((o for o in agent_outputs if o.get('agent_name') == 'competitive_benchmarking'), None)
    if comp_agent:
        print("✓ competitive_benchmarking agent output EXISTS")
        comp_data = comp_agent.get('data', {})
        print(f"  Data keys: {list(comp_data.keys())}")
        
        swot = comp_data.get('swot_analysis', {})
        if swot:
            print(f"  SWOT keys: {list(swot.keys())}")
            for cat in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                items = swot.get(cat, [])
                print(f"    {cat}: {len(items) if isinstance(items, list) else 'Not a list'}")
        else:
            print("  ❌ swot_analysis MISSING")
    else:
        print("❌ competitive_benchmarking agent output MISSING")
    
    # 3. Check Anomaly Log
    print("\n=== ANOMALY LOG ===")
    anomaly_log = state.get('anomaly_log', [])
    print(f"Total anomalies logged: {len(anomaly_log)}")
    
    if anomaly_log:
        agents_with_anomalies = set(a.get('agent', 'unknown') for a in anomaly_log)
        print(f"Agents that logged anomalies: {agents_with_anomalies}")
        
        # Show first 3
        for idx, anomaly in enumerate(anomaly_log[:3], start=1):
            print(f"\n  Anomaly {idx}:")
            print(f"    Agent: {anomaly.get('agent')}")
            print(f"    Type: {anomaly.get('type')}")
            print(f"    Severity: {anomaly.get('severity')}")
            print(f"    Description: {anomaly.get('description', '')[:100]}")
    
    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    import sys
    job_id = sys.argv[1] if len(sys.argv) > 1 else None
    diagnose_state_data(job_id)
