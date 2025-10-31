"""
Diagnostic script for ORCL acquisition reporting issues
Checks for data completeness and report generation failures
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def find_orcl_jobs():
    """Find all ORCL-related job files"""
    jobs_dir = Path("data/jobs")
    orcl_jobs = []
    
    for job_file in jobs_dir.glob("*.json"):
        try:
            with open(job_file, 'r') as f:
                # Read only first 1000 chars to check target
                content = f.read(1000)
                if 'ORCL' in content or 'Oracle' in content:
                    orcl_jobs.append(job_file)
        except:
            pass
    
    return orcl_jobs

def check_job_data(job_file):
    """Check job data for completeness and issues"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {job_file.name}")
    print(f"{'='*80}")
    
    try:
        with open(job_file, 'r') as f:
            data = json.load(f)
        
        # Basic info
        target = data.get('target_company', 'Unknown')
        ticker = data.get('target_ticker', 'Unknown')
        timestamp = data.get('timestamp', 'Unknown')
        print(f"Target: {target} ({ticker})")
        print(f"Timestamp: {timestamp}")
        
        # Check synthesis data
        has_synthesis = 'consolidated_insights' in data
        print(f"\n✓ Synthesized Data: {'YES' if has_synthesis else '❌ NO - MISSING'}")
        
        if not has_synthesis:
            print("  ⚠️ CRITICAL: Report generation requires synthesized data!")
            print("  → Synthesis agent must complete successfully before reports")
        
        # Check agent outputs
        agent_outputs = data.get('agent_outputs', [])
        print(f"\n✓ Agent Outputs: {len(agent_outputs)} agents completed")
        
        if agent_outputs:
            for output in agent_outputs:
                agent_name = output.get('agent_name', 'unknown')
                success = output.get('success', False)
                has_data = bool(output.get('data'))
                status = '✓' if success and has_data else '❌'
                print(f"  {status} {agent_name}: success={success}, has_data={has_data}")
        
        # Check for anomalies
        anomaly_count = 0
        agents_with_anomalies = []
        
        for agent_key in ['financial_analyst', 'legal_counsel', 'risk_assessment', 
                         'integration_planner', 'market_strategist', 'financial_deep_dive',
                         'external_validator', 'tax_structuring', 'macroeconomic_analyst',
                         'competitive_benchmarking']:
            agent_data = data.get(agent_key, {})
            if isinstance(agent_data, dict):
                anomalies = agent_data.get('anomalies', {})
                if isinstance(anomalies, dict):
                    count = len(anomalies.get('anomalies_detected', []))
                    if count > 0:
                        anomaly_count += count
                        agents_with_anomalies.append(f"{agent_key}: {count}")
        
        print(f"\n✓ Anomalies Detected: {anomaly_count} total")
        if agents_with_anomalies:
            for agent_info in agents_with_anomalies:
                print(f"  • {agent_info}")
        
        # Check valuation data
        valuation = data.get('valuation_models', {})
        has_dcf = 'dcf_advanced' in valuation if isinstance(valuation, dict) else False
        print(f"\n✓ Valuation Data: {'YES' if has_dcf else '❌ NO - MISSING'}")
        
        # Check financial data
        financial_data = data.get('financial_data', {})
        has_financials = bool(financial_data)
        print(f"✓ Financial Data: {'YES' if has_financials else '❌ NO - MISSING'}")
        
        # Diagnosis
        print(f"\n{'='*80}")
        print("DIAGNOSIS:")
        print(f"{'='*80}")
        
        issues = []
        if not has_synthesis:
            issues.append("❌ CRITICAL: Missing synthesized data - reports cannot generate")
            issues.append("   → Run synthesis_reporting agent to completion")
        
        if not has_dcf:
            issues.append("❌ Missing DCF valuation data - dashboard will fail")
            issues.append("   → Check financial_analyst agent completion")
        
        if not has_financials:
            issues.append("❌ Missing financial data - analysis incomplete")
            issues.append("   → Check data_ingestion agent")
        
        if len(agent_outputs) < 10:
            issues.append(f"⚠️ Only {len(agent_outputs)}/13 agents completed")
            issues.append("   → Full analysis requires all agents")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✓ All checks passed - data should be complete")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ ERROR analyzing job: {e}")
        return False

def main():
    print("="*80)
    print("ORCL ACQUISITION REPORT GENERATION DIAGNOSTIC")
    print("="*80)
    
    orcl_jobs = find_orcl_jobs()
    
    if not orcl_jobs:
        print("\n❌ No ORCL jobs found in data/jobs/")
        print("\nSearching for MSFT jobs (MSFT acquiring ORCL)...")
        
        # Check for MSFT jobs that might have ORCL as target
        jobs_dir = Path("data/jobs")
        for job_file in jobs_dir.glob("test_msft*.json"):
            print(f"\n→ Found: {job_file.name}")
            orcl_jobs.append(job_file)
    
    if not orcl_jobs:
        print("❌ No ORCL-related jobs found")
        return
    
    print(f"\n✓ Found {len(orcl_jobs)} ORCL-related job(s)")
    
    all_good = True
    for job_file in orcl_jobs:
        is_good = check_job_data(job_file)
        all_good = all_good and is_good
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if all_good:
        print("✓ All jobs appear complete and ready for reporting")
    else:
        print("❌ One or more jobs have issues that prevent report generation")
        print("\nRECOMMENDED ACTIONS:")
        print("1. Re-run the analysis to ensure all agents complete")
        print("2. Ensure synthesis_reporting agent runs successfully")
        print("3. Check logs for agent errors during execution")
        print("4. Verify API keys and network connectivity")

if __name__ == "__main__":
    main()
