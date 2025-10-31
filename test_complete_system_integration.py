"""
Comprehensive System Integration Diagnostic
Tests all agents, synthesis, and report generation end-to-end
"""
import json
from pathlib import Path
from loguru import logger

def load_latest_job():
    """Load most recent job data"""
    data_dir = Path("data/jobs")
    if not data_dir.exists():
        return None
    
    job_files = sorted(data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not job_files:
        return None
    
    with open(job_files[0], 'r') as f:
        return json.load(f)

def test_agent_outputs(state):
    """Test all agents produced output"""
    print("\n" + "="*80)
    print("1. AGENT OUTPUT VALIDATION")
    print("="*80)
    
    expected_agents = [
        'project_manager',
        'financial_analyst',
        'financial_deep_dive',
        'legal_counsel',
        'market_strategist',
        'competitive_benchmarking',
        'macroeconomic_analyst',
        'risk_assessment',
        'tax_structuring',
        'deal_structuring',
        'accretion_dilution',  # NEW
        'integration_planner',
        'external_validator',
        'synthesis_reporting'
    ]
    
    agent_outputs = state.get('agent_outputs', [])
    output_map = {o.get('agent_name'): o for o in agent_outputs}
    
    passed = 0
    failed = 0
    
    for agent_name in expected_agents:
        if agent_name in output_map:
            output = output_map[agent_name]
            data = output.get('data', {})
            
            if data and len(data) > 0:
                print(f"✅ {agent_name}: {len(data)} keys")
                passed += 1
            else:
                print(f"⚠️  {agent_name}: NO DATA")
                failed += 1
        else:
            print(f"❌ {agent_name}: NOT IN agent_outputs")
            failed += 1
    
    print(f"\nAgent Output Summary: {passed}/{len(expected_agents)} passed")
    return passed == len(expected_agents)

def test_synthesis_collection(state):
    """Test synthesis agent collected from all agents"""
    print("\n" + "="*80)
    print("2. SYNTHESIS DATA COLLECTION")
    print("="*80)
    
    # Find synthesis output
    synthesis_output = None
    for output in state.get('agent_outputs', []):
        if output.get('agent_name') == 'synthesis_reporting':
            synthesis_output = output.get('data', {})
            break
    
    if not synthesis_output:
        print("❌ NO SYNTHESIS OUTPUT FOUND")
        return False
    
    print(f"✅ Synthesis output found with {len(synthesis_output)} top-level keys")
    
    # Check expected sections
    expected_sections = [
        'metadata',
        'executive_summary',
        'detailed_financials',
        'legal_diligence',
        'market_analysis',
        'risk_macro',
        'integration_tax',
        'validation_summary'
    ]
    
    passed = 0
    for section in expected_sections:
        if section in synthesis_output:
            data = synthesis_output[section]
            if isinstance(data, dict):
                print(f"  ✅ {section}: {len(data)} keys")
            else:
                print(f"  ✅ {section}: {type(data).__name__}")
            passed += 1
        else:
            print(f"  ❌ {section}: MISSING")
    
    print(f"\nSynthesis Collection: {passed}/{len(expected_sections)} sections")
    return passed >= len(expected_sections) * 0.8  # 80% threshold

def test_report_mappings(state):
    """Test reports can access all required data"""
    print("\n" + "="*80)
    print("3. REPORT DATA MAPPING VALIDATION")
    print("="*80)
    
    # CRITICAL FIX: Check synthesis agent output (where data actually lives)
    synthesis_output = None
    for output in state.get('agent_outputs', []):
        if output.get('agent_name') == 'synthesis_reporting':
            synthesis_output = output.get('data', {})
            break
    
    # PDF requirements mapped to CORRECT locations
    pdf_requirements = {
        'Executive Summary': {'source': 'synthesis', 'keys': ['executive_summary', 'detailed_financials']},
        'Financial Deep Dive': {'source': 'synthesis', 'keys': ['detailed_financials']},
        'Competitive': {'source': 'synthesis', 'keys': ['market_analysis']},
        'Macro': {'source': 'synthesis', 'keys': ['risk_macro']},
        'External Validation': {'source': 'synthesis', 'keys': ['validation_summary']},
        'Legal Risk Register': {'source': 'state', 'keys': ['legal_risks']},
        'Tax Structuring': {'source': 'agents', 'keys': ['tax_structuring']},
        'LBO Analysis': {'source': 'state', 'keys': ['valuation_models']},
        'EPS Accretion/Dilution': {'source': 'agents', 'keys': ['accretion_dilution']},
        'Normalized Financials': {'source': 'state', 'keys': ['normalized_financials']}
    }
    
    passed = 0
    failed = 0
    
    for section_name, requirement in pdf_requirements.items():
        source = requirement['source']
        keys = requirement['keys']
        
        if source == 'synthesis':
            # Check in synthesis output
            if synthesis_output:
                has_all = all(key in synthesis_output for key in keys)
                if has_all:
                    print(f"✅ {section_name}: Data in synthesis")
                    passed += 1
                else:
                    missing = [k for k in keys if k not in synthesis_output]
                    print(f"⚠️  {section_name}: Missing from synthesis: {missing}")
                    failed += 1
            else:
                print(f"❌ {section_name}: No synthesis data")
                failed += 1
        
        elif source == 'state':
            # Check in state top-level
            has_all = all(key in state and state[key] for key in keys)
            if has_all:
                print(f"✅ {section_name}: Data in state")
                passed += 1
            else:
                missing = [k for k in keys if k not in state or not state[k]]
                print(f"⚠️  {section_name}: Missing from state: {missing}")
                failed += 1
        
        elif source == 'agents':
            # Check specific agent exists in agent_outputs
            agent_outputs = state.get('agent_outputs', [])
            agent_name = keys[0]
            agent_exists = any(o.get('agent_name') == agent_name for o in agent_outputs)
            
            if agent_exists:
                print(f"✅ {section_name}: Agent output available")
                passed += 1
            else:
                print(f"⚠️  {section_name}: Agent {agent_name} not run")
                failed += 1
    
    print(f"\nReport Mapping: {passed}/{len(pdf_requirements)} sections")
    return passed >= len(pdf_requirements) * 0.7  # 70% threshold

def test_excel_tabs(state):
    """Test Excel can generate all revolutionary tabs"""
    print("\n" + "="*80)
    print("4. EXCEL TAB DATA VALIDATION")
    print("="*80)
    
    excel_tabs = {
        'CONTROL PANEL': ['metadata', 'detailed_financials'],
        'Normalization Ledger': ['normalized_financials'],
        'Anomaly Log': ['anomaly_log'],
        'Legal Risk Register': ['legal_risks'],
        'Risk Assessment': ['agent_outputs'],  # risk_assessment agent
        'Tax Structuring': ['agent_outputs'],  # tax_structuring agent
        'LBO Model': ['valuation_models'],
        'EPS Accretion/Dilution': ['agent_outputs'],  # NEW: accretion_dilution agent
        'Validation Tear Sheet': ['validation_summary', 'valuation_models'],
        'Agent Collaboration': ['agent_outputs']
    }
    
    passed = 0
    failed = 0
    
    for tab_name, required_keys in excel_tabs.items():
        has_all = all(key in state and state[key] for key in required_keys)
        
        if has_all:
            print(f"✅ {tab_name}: Data available")
            passed += 1
        else:
            missing = [k for k in required_keys if k not in state or not state[k]]
            print(f"⚠️  {tab_name}: Missing {missing}")
            failed += 1
    
    print(f"\nExcel Tab Validation: {passed}/{len(excel_tabs)} tabs")
    return passed >= len(excel_tabs) * 0.7

def test_accretion_dilution_integration(state):
    """Specifically test accretion/dilution integration"""
    print("\n" + "="*80)
    print("5. ACCRETION/DILUTION INTEGRATION CHECK")
    print("="*80)
    
    # Check agent output
    agent_output = next(
        (o for o in state.get('agent_outputs', []) 
         if o.get('agent_name') == 'accretion_dilution'),
        None
    )
    
    if not agent_output:
        print("❌ Accretion/dilution agent did NOT run")
        return False
    
    print("✅ Accretion/dilution agent ran")
    
    data = agent_output.get('data', {})
    if data:
        print(f"  ✅ Agent produced {len(data)} keys of data")
        
        # Check for expected keys
        expected = ['accretion_dilution', 'pro_forma_combined', 'deal_recommendation']
        for key in expected:
            if key in data:
                print(f"    ✅ {key}")
            else:
                print(f"    ❌ {key}: MISSING")
    else:
        print("  ❌ Agent data is EMPTY")
        return False
    
    # Check if synthesis collected it
    synthesis_output = next(
        (o for o in state.get('agent_outputs', []) 
         if o.get('agent_name') == 'synthesis_reporting'),
        None
    )
    
    if synthesis_output:
        synth_data = synthesis_output.get('data', {})
        # Check if accretion data is in synthesis somewhere
        has_eps_data = any('eps' in str(v).lower() or 'accretion' in str(v).lower() 
                          for v in str(synth_data)[:1000].split())
        
        if has_eps_data:
            print("  ✅ Synthesis collected accretion/dilution data")
        else:
            print("  ⚠️  Synthesis may not have EPS data (check manually)")
    
    return True

def run_full_diagnostic():
    """Run complete diagnostic"""
    print("\n" + "="*80)
    print("COMPLETE SYSTEM INTEGRATION DIAGNOSTIC")
    print("="*80)
    
    state = load_latest_job()
    if not state:
        print("❌ ERROR: No job data found")
        return
    
    print(f"\nLoaded job: {state.get('job_id', 'Unknown')}")
    print(f"Target: {state.get('target_company', 'Unknown')} ({state.get('target_ticker', 'N/A')})")
    print(f"Acquirer: {state.get('acquirer_company', 'N/A')}")
    
    # Run all tests
    results = {
        'agent_outputs': test_agent_outputs(state),
        'synthesis_collection': test_synthesis_collection(state),
        'report_mappings': test_report_mappings(state),
        'excel_tabs': test_excel_tabs(state),
        'accretion_dilution': test_accretion_dilution_integration(state)
    }
    
    # Final summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    passed_tests = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL SYSTEMS OPERATIONAL - Ready for production!")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ SYSTEM HEALTHY - Minor issues detected")
    else:
        print("\n⚠️  ISSUES DETECTED - Review failures above")
    
    print("="*80)

if __name__ == "__main__":
    run_full_diagnostic()
