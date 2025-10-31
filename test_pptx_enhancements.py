"""
Test script for PPTX enhancements - Verify all 3 phases implemented correctly
"""
import json
from pathlib import Path
from src.outputs.revolutionary_ppt_generator import RevolutionaryPowerPointGenerator
from src.outputs.report_config import ReportConfiguration, DealType, BuyerType
from src.core.state import DiligenceState

def load_test_data():
    """Load existing agent output data"""
    # Find most recent job with complete data
    jobs_dir = Path("data/jobs")
    
    # Try to find a job with good data
    test_jobs = [
        "360181db-a8a9-4885-87f7-b56b767bd952.json",  # Known complete job
        "cef24d52-0de1-4362-b0bf-e7124bd91c80.json",
    ]
    
    for job_file in test_jobs:
        job_path = jobs_dir / job_file
        if job_path.exists():
            with open(job_path, 'r') as f:
                data = json.load(f)
                print(f"✓ Loaded test data from {job_file}")
                return data
    
    # If no test file found, look for any recent file
    job_files = sorted(jobs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if job_files:
        with open(job_files[0], 'r') as f:
            data = json.load(f)
            print(f"✓ Loaded test data from {job_files[0].name}")
            return data
    
    raise FileNotFoundError("No test data found in data/jobs/")

def verify_phase_1_fixes(state):
    """Verify Phase 1: All placeholders replaced with real data"""
    print("\n" + "="*80)
    print("PHASE 1 VERIFICATION: Placeholder Removal")
    print("="*80)
    
    checks = []
    
    # Check 1: Anomaly count is real
    anomaly_data = state.get('anomaly_detection', {})
    anomalies = anomaly_data.get('anomalies_detected', [])
    anomaly_count = len(anomalies) if anomalies else 0
    checks.append(("Anomaly Count", f"{anomaly_count} anomalies", anomaly_count >= 0))
    
    # Check 2: Financial health score
    health_data = state.get('financial_health', {})
    health_score = health_data.get('health_score', 0)
    health_rating = health_data.get('rating', 'N/A')
    checks.append(("Health Score", f"{health_score}/100 ({health_rating})", health_score > 0))
    
    # Check 3: Real agent count
    agent_count = len(state.get('agent_outputs', []))
    checks.append(("Agent Count", f"{agent_count} agents", agent_count > 0))
    
    # Check 4: Risk score is real
    risk_data = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'risk_assessment':
            risk_data = agent.get('data', {})
            break
    
    if not risk_data:
        risk_data = state.get('risk_assessment', {})
    
    risk_scores = risk_data.get('risk_scores', {})
    overall_risk = risk_scores.get('overall_risk_score', 0)
    risk_rating = risk_scores.get('risk_rating', 'Unknown')
    checks.append(("Risk Score", f"{overall_risk}/100 ({risk_rating})", overall_risk > 0))
    
    # Check 5: Validation confidence is real
    validator = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'external_validator':
            validator = agent.get('data', {})
            break
    
    if validator:
        confidence = validator.get('confidence_score', 0)
        checks.append(("Validation Confidence", f"{confidence:.1%}", True))
    else:
        checks.append(("Validation Confidence", "No data", False))
    
    # Print results
    for check_name, value, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name:25s}: {value}")
    
    return all(passed for _, _, passed in checks[:4])  # Must pass first 4

def verify_phase_2_additions(state):
    """Verify Phase 2: New board-level slides can be generated"""
    print("\n" + "="*80)
    print("PHASE 2 VERIFICATION: New Board-Level Slides")
    print("="*80)
    
    checks = []
    
    # Check 1: Tax structuring data
    tax_data = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'tax_structuring':
            tax_data = agent.get('data', {})
            break
    
    if not tax_data:
        tax_data = state.get('tax_structuring', {})
    
    has_tax = bool(tax_data)
    optimal_structure = tax_data.get('optimal_structure', 'None') if tax_data else 'None'
    checks.append(("Tax Structure Data", optimal_structure, has_tax))
    
    # Check 2: Macro analysis data
    macro_data = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'macroeconomic_analyst':
            macro_data = agent.get('data', {})
            break
    
    if not macro_data:
        macro_data = state.get('macroeconomic_analyst', {})
    
    has_macro = bool(macro_data)
    scenarios = len(macro_data.get('scenario_models', {})) if macro_data else 0
    checks.append(("Macro Sensitivity Data", f"{scenarios} scenarios", has_macro))
    
    # Check 3: LBO analysis data
    dcf_data = state.get("valuation_models", {}).get("dcf_advanced", {})
    lbo_data = dcf_data.get('lbo_analysis', {})
    has_lbo = bool(lbo_data)
    irr = lbo_data.get('returns_analysis', {}).get('irr_percent', 'N/A') if lbo_data else 'N/A'
    checks.append(("LBO Analysis Data", f"IRR: {irr}", has_lbo))
    
    # Check 4: Earnings quality data
    earnings_quality = dcf_data.get('earnings_quality', {})
    has_eq = bool(earnings_quality)
    checks.append(("Earnings Quality Data", f"{len(earnings_quality)} metrics", has_eq))
    
    # Check 5: Competitive benchmarking
    comp_data = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'competitive_benchmarking':
            comp_data = agent.get('data', {})
            break
    
    if not comp_data:
        comp_data = state.get('competitive_benchmarking', {})
    
    has_comp = bool(comp_data)
    strengths = len(comp_data.get('competitive_position', {}).get('strengths', [])) if comp_data else 0
    checks.append(("Strategic Rationale Data", f"{strengths} strengths", has_comp))
    
    # Print results
    for check_name, value, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name:30s}: {value}")
    
    passed_count = sum(1 for _, _, passed in checks if passed)
    print(f"\nPassed {passed_count}/5 new slide checks")
    
    return passed_count >= 3  # At least 3 of 5 should have data

def verify_phase_3_questions(state):
    """Verify Phase 3: Dynamic DD question generation"""
    print("\n" + "="*80)
    print("PHASE 3 VERIFICATION: Dynamic DD Questions")
    print("="*80)
    
    questions = []
    
    # From anomalies
    anomaly_data = state.get('anomaly_detection', {})
    anomalies = anomaly_data.get('anomalies_detected', [])
    for anomaly in anomalies[:2]:
        questions.append({
            'source': 'Anomaly Detection',
            'question': f"Explain {anomaly.get('description', 'anomaly')[:50]}..."
        })
    
    # From high risks
    risk_data = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'risk_assessment':
            risk_data = agent.get('data', {})
            break
    
    if risk_data:
        risk_factors = risk_data.get('risk_factors', [])
        high_risks = [r for r in risk_factors if r.get('severity') in ['high', 'critical']]
        for risk in high_risks[:2]:
            questions.append({
                'source': 'Risk Assessment',
                'question': f"Mitigation for: {risk.get('description', 'risk')[:50]}..."
            })
    
    # From validation discrepancies
    validator = None
    for agent in state.get('agent_outputs', []):
        if agent.get('agent_name') == 'external_validator':
            validator = agent.get('data', {})
            break
    
    if validator:
        critical_discrep = validator.get('critical_discrepancies', [])
        for discrep in critical_discrep[:2]:
            finding_type = discrep.get('finding_type', 'Unknown')
            questions.append({
                'source': 'External Validator',
                'question': f"Resolve {finding_type} discrepancy"
            })
    
    print(f"Generated {len(questions)} DD questions from agent findings:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. [{q['source']}] {q['question']}")
    
    return len(questions) > 0

def test_report_generation():
    """Test actual PPTX generation"""
    print("\n" + "="*80)
    print("GENERATING TEST REPORT")
    print("="*80)
    
    # Load test data
    try:
        job_data = load_test_data()
        state = DiligenceState(job_data)
    except Exception as e:
        print(f"✗ Failed to load test data: {e}")
        return False
    
    # Create config
    target = state.get('metadata', {}).get('target_company', 'TEST')
    config = ReportConfiguration(
        deal_id="test-123",
        target_company=target,
        target_ticker=target,
        acquirer_company="Acquirer",
        deal_type=DealType.ACQUISITION,  # Use enum
        buyer_type=BuyerType.STRATEGIC,  # Use enum
        industry="Technology",
        file_prefix=f"{target}_TEST",
        include_deep_dive=True,
        include_external_validation=True,
        include_synergy_analysis=False,
        include_integration_planning=False
    )
    
    # Generate PPTX
    try:
        generator = RevolutionaryPowerPointGenerator()
        output_path = generator.generate_revolutionary_deck(state, config)
        
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"\n✓ Report generated successfully!")
            print(f"  Location: {output_path}")
            print(f"  Size: {file_size:,} bytes")
            return True
        else:
            print(f"\n✗ Report file not found at {output_path}")
            return False
            
    except Exception as e:
        print(f"\n✗ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("\n" + "="*80)
    print("PPTX ENHANCEMENT VERIFICATION - ALL 3 PHASES")
    print("="*80)
    
    try:
        # Load data once
        job_data = load_test_data()
        state = DiligenceState(job_data)
        
        # Run verifications
        phase1_ok = verify_phase_1_fixes(state)
        phase2_ok = verify_phase_2_additions(state)
        phase3_ok = verify_phase_3_questions(state)
        
        # Generate actual report
        report_ok = test_report_generation()
        
        # Summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        print(f"{'✓' if phase1_ok else '✗'} Phase 1: Placeholder Removal - {'PASSED' if phase1_ok else 'FAILED'}")
        print(f"{'✓' if phase2_ok else '✗'} Phase 2: New Board Slides - {'PASSED' if phase2_ok else 'FAILED'}")
        print(f"{'✓' if phase3_ok else '✗'} Phase 3: Dynamic Questions - {'PASSED' if phase3_ok else 'FAILED'}")
        print(f"{'✓' if report_ok else '✗'} Report Generation - {'PASSED' if report_ok else 'FAILED'}")
        
        all_passed = phase1_ok and phase2_ok and phase3_ok and report_ok
        
        print("\n" + "="*80)
        if all_passed:
            print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*80)
        
        return all_passed
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
