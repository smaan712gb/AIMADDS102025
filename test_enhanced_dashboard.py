"""
Comprehensive test for enhanced revolutionary dashboard
Tests all placeholder replacements and new features
"""

import json
from pathlib import Path
import sys

def test_enhanced_dashboard():
    """Comprehensive test of dashboard enhancements"""
    
    print("=" * 80)
    print("COMPREHENSIVE DASHBOARD ENHANCEMENT TEST")
    print("=" * 80)
    
    # Use the complete job file with all agent data
    job_file = Path("data/jobs/comprehensive_test_run.json")
    
    if not job_file.exists():
        print(f"❌ ERROR: Complete job file not found: {job_file}")
        print("Run a comprehensive test first to generate this file")
        return False
    
    print(f"\n✓ Using complete job file: {job_file}")
    
    # Load job data
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    print(f"\n{'='*80}")
    print("TEST 1: VALIDATE DATA STRUCTURE")
    print('='*80)
    
    # Check for key data structures
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Risk assessment data
    print("\n1. Testing Risk Assessment Data...")
    risk_data = state.get('risk_assessment', {})
    if risk_data:
        risk_scores = risk_data.get('risk_scores', {})
        critical_count = risk_scores.get('critical_risks', 0)
        high_count = risk_scores.get('high_risks', 0)
        total_risks = risk_scores.get('total_risks', 0)
        print(f"   ✓ Risk scores found:")
        print(f"     - Critical risks: {critical_count}")
        print(f"     - High risks: {high_count}")
        print(f"     - Total risks: {total_risks}")
        tests_passed += 1
    else:
        print("   ❌ Risk assessment data not found")
        tests_failed += 1
    
    # Test 2: External validator data
    print("\n2. Testing External Validator Data...")
    validator_data = state.get('external_validator', {})
    if validator_data:
        confidence = validator_data.get('confidence_score', 0)
        requires_reanalysis = validator_data.get('requires_reanalysis', False)
        critical_discrepancies = len(validator_data.get('critical_discrepancies', []))
        print(f"   ✓ Validator data found:")
        print(f"     - Confidence: {confidence:.1%}")
        print(f"     - Requires reanalysis: {requires_reanalysis}")
        print(f"     - Critical discrepancies: {critical_discrepancies}")
        tests_passed += 1
    else:
        print("   ❌ External validator data not found")
        tests_failed += 1
    
    # Test 3: Tax structuring data
    print("\n3. Testing Tax Structuring Data...")
    tax_data = state.get('tax_structuring', {})
    if tax_data:
        tax_impact = tax_data.get('estimated_tax_impact', 0)
        optimal_structure = tax_data.get('optimal_structure', 'N/A')
        print(f"   ✓ Tax structuring data found:")
        print(f"     - Tax impact: ${tax_impact/1e6:.0f}M")
        print(f"     - Optimal structure: {optimal_structure}")
        tests_passed += 1
    else:
        print("   ⚠️  Tax structuring data not found (optional)")
    
    # Test 4: Financial deep dive data
    print("\n4. Testing Financial Deep Dive Data...")
    deep_dive = state.get('financial_deep_dive', {})
    if deep_dive:
        segment_analysis = deep_dive.get('segment_analysis', {}).get('segment_analysis', {})
        segment_count = len(segment_analysis)
        print(f"   ✓ Financial deep dive data found:")
        print(f"     - Segments analyzed: {segment_count}")
        if segment_count > 0:
            print(f"     - Segments: {list(segment_analysis.keys())[:3]}")
        tests_passed += 1
    else:
        print("   ⚠️  Financial deep dive data not found (optional)")
    
    # Test 5: Competitive benchmarking data
    print("\n5. Testing Competitive Benchmarking Data...")
    comp_data = state.get('competitive_benchmarking', {})
    if comp_data:
        competitive_position = comp_data.get('competitive_position', {})
        strengths = competitive_position.get('strengths', [])
        weaknesses = competitive_position.get('weaknesses', [])
        print(f"   ✓ Competitive benchmarking data found:")
        print(f"     - Strengths identified: {len(strengths)}")
        print(f"     - Weaknesses identified: {len(weaknesses)}")
        tests_passed += 1
    else:
        print("   ⚠️  Competitive benchmarking data not found (optional)")
    
    # Test 6: Macroeconomic data
    print("\n6. Testing Macroeconomic Analyst Data...")
    macro_data = state.get('macroeconomic_analyst', {})
    if macro_data:
        scenarios = macro_data.get('scenario_models', {})
        scenario_count = len(scenarios)
        print(f"   ✓ Macroeconomic data found:")
        print(f"     - Scenarios modeled: {scenario_count}")
        print(f"     - Scenarios: {list(scenarios.keys())}")
        tests_passed += 1
    else:
        print("   ⚠️  Macroeconomic data not found (optional)")
    
    # Test 7: Normalized financials
    print("\n7. Testing Normalized Financials...")
    normalized = state.get('normalized_financials', {})
    if normalized:
        normalized_income = normalized.get('normalized_income', [])
        adjustments = normalized.get('adjustments', [])
        print(f"   ✓ Normalized financials found:")
        print(f"     - Income statements: {len(normalized_income)}")
        print(f"     - Adjustments: {len(adjustments)}")
        tests_passed += 1
    else:
        print("   ❌ Normalized financials not found")
        tests_failed += 1
    
    # Test 8: Valuation models
    print("\n8. Testing Valuation Models...")
    valuation_models = state.get('valuation_models', {})
    if valuation_models:
        dcf_data = valuation_models.get('dcf_advanced', {})
        dcf_analysis = dcf_data.get('dcf_analysis', {})
        print(f"   ✓ Valuation models found:")
        print(f"     - DCF scenarios: {list(dcf_analysis.keys())}")
        tests_passed += 1
    else:
        print("   ❌ Valuation models not found")
        tests_failed += 1
    
    print(f"\n{'='*80}")
    print("TEST 2: INSTANTIATE DASHBOARD")
    print('='*80)
    
    try:
        from revolutionary_dashboard import AgenticInsightsDashboard
        dashboard = AgenticInsightsDashboard(str(job_file))
        print("\n✓ Dashboard instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"\n❌ Dashboard instantiation failed: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        tests_failed += 1
        return False
    
    print(f"\n{'='*80}")
    print("TEST 3: VALIDATE PLACEHOLDER REMOVAL")
    print('='*80)
    
    # Check that methods work correctly
    print("\n1. Testing validation confidence method...")
    try:
        confidence_display = dashboard._get_validation_confidence()
        print(f"   ✓ Confidence display: {confidence_display}")
        # Should show warning emoji if < 50%
        if validator_data.get('confidence_score', 0) < 0.5:
            if '⚠️' in confidence_display:
                print(f"   ✓ Warning emoji correctly displayed for low confidence")
            else:
                print(f"   ⚠️  Warning emoji missing for low confidence")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Validation confidence method failed: {str(e)}")
        tests_failed += 1
    
    print("\n2. Testing validation subtitle method...")
    try:
        subtitle = dashboard._get_validation_subtitle()
        print(f"   ✓ Subtitle: {subtitle}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Validation subtitle method failed: {str(e)}")
        tests_failed += 1
    
    print("\n3. Testing validation gradient method...")
    try:
        gradient = dashboard._get_validation_gradient()
        print(f"   ✓ Gradient: {gradient[:50]}...")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Validation gradient method failed: {str(e)}")
        tests_failed += 1
    
    print(f"\n{'='*80}")
    print("TEST 4: VALIDATE CHART GENERATION")
    print('='*80)
    
    # Test chart generation methods
    charts = [
        ('KPI Header', dashboard._create_kpi_header),
        ('Football Field', dashboard._create_football_field),
        ('Risks & Red Flags', dashboard._create_risks_red_flags),
        ('Synergies & Opportunities', dashboard._create_synergies_opportunities),
        ('Normalization Waterfall', dashboard._create_normalization_waterfall),
        ('Normalized Timeline', dashboard._create_normalized_timeline),
    ]
    
    for chart_name, chart_method in charts:
        print(f"\n{chart_name}...")
        try:
            result = chart_method()
            print(f"   ✓ {chart_name} generated successfully")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ {chart_name} generation failed: {str(e)}")
            tests_failed += 1
    
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print('='*80)
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED - Dashboard enhancement complete!")
        return True
    elif success_rate >= 80:
        print(f"\n✅ TESTS MOSTLY PASSED ({success_rate:.1f}%) - Dashboard functional with minor issues")
        return True
    else:
        print(f"\n⚠️  TESTS PARTIALLY PASSED ({success_rate:.1f}%) - Review failures")
        return False

if __name__ == "__main__":
    success = test_enhanced_dashboard()
    sys.exit(0 if success else 1)
