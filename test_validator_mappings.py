"""
Simple test to validate all validator-synthesis mappings are correct
"""
import sys
from datetime import datetime
from src.outputs.report_consistency_validator import ReportConsistencyValidator

def create_mock_synthesized_data():
    """Create mock synthesized data with all required fields"""
    return {
        'synthesized_data': {
            # Required top-level fields
            'metadata': {
                'deal_id': 'TEST-001',
                'target_company': 'Test Company',
                'target_ticker': 'TEST',
                'agent_coverage': 11,  # Number of agents
            },
            'executive_summary': {
                'key_recommendation': 'Proceed with confidence',
                'overall_confidence': 0.85,
            },
            'detailed_financials': {
                # CRITICAL: DCF with flattened structure
                'dcf_outputs': {
                    # Root level values (for validator)
                    'enterprise_value': 1000000000,  # $1B
                    'equity_value': 950000000,
                    'equity_value_per_share': 25.50,
                    'wacc': 0.08,
                    'terminal_growth_rate': 0.025,
                    'valuation_date': '2025-10-24',
                    # Nested structure (for reports)
                    'base': {
                        'enterprise_value': 1000000000,
                        'equity_value': 950000000,
                    },
                    'optimistic': {
                        'enterprise_value': 1200000000,
                        'equity_value': 1150000000,
                    },
                    'pessimistic': {
                        'enterprise_value': 800000000,
                        'equity_value': 750000000,
                    },
                },
                # CRITICAL: Normalized EBITDA
                'normalized_ebitda': 150000000,  # $150M
                # Other financial data
                'normalized_income_statement': [],
                'financial_health': {'health_score': 75},
            },
            'legal_diligence': {
                'risk_register': [],
                'compliance_status': 'No Issues Identified',
            },
            'market_analysis': {
                'swot_analysis': {},
                'competitive_landscape': {},
            },
            'validation_summary': {
                'overall_confidence_score': 0.85,
                'component_confidences': {},
            },
            # Required metadata fields
            'synthesis_metadata': {
                'processing_time_seconds': 30.0,
                'conflicts_resolved': 2,
            },
            'consolidated_timestamp': datetime.utcnow().isoformat(),
            'data_version': '1.0',
            'source': 'synthesis_reporting_agent',
        }
    }

def test_validator_mappings():
    """Test that validator accepts the synthesized data structure"""
    print("=" * 80)
    print("VALIDATOR MAPPING TEST")
    print("=" * 80)
    print()
    
    # Create mock state with synthesized data
    state = create_mock_synthesized_data()
    
    print("✓ Created mock synthesized data with:")
    print(f"  - metadata: {bool(state['synthesized_data'].get('metadata'))}")
    print(f"  - executive_summary: {bool(state['synthesized_data'].get('executive_summary'))}")
    print(f"  - detailed_financials: {bool(state['synthesized_data'].get('detailed_financials'))}")
    print(f"  - dcf_outputs: {bool(state['synthesized_data']['detailed_financials'].get('dcf_outputs'))}")
    print(f"  - enterprise_value: {state['synthesized_data']['detailed_financials']['dcf_outputs'].get('enterprise_value')}")
    print(f"  - normalized_ebitda: {state['synthesized_data']['detailed_financials'].get('normalized_ebitda')}")
    print(f"  - legal_diligence: {bool(state['synthesized_data'].get('legal_diligence'))}")
    print(f"  - market_analysis: {bool(state['synthesized_data'].get('market_analysis'))}")
    print(f"  - validation_summary: {bool(state['synthesized_data'].get('validation_summary'))}")
    print()
    
    # Run validator
    print("Running validator...")
    print()
    validator = ReportConsistencyValidator()
    result = validator.validate_pre_report_generation(state)
    
    # Display results
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    print(f"Valid: {'✅ YES' if result['valid'] else '❌ NO'}")
    print(f"Total Issues: {result['summary']['total_issues']}")
    print(f"Critical Issues: {result['summary']['critical_issues']}")
    print(f"Blocking Issues: {result['summary']['blocking_issues']}")
    print()
    
    if result['issues']:
        print("ISSUES FOUND:")
        print("-" * 80)
        for i, issue in enumerate(result['issues'], 1):
            severity = issue['severity']
            blocker = " [BLOCKER]" if issue.get('blocker', False) else ""
            print(f"{i}. [{severity}]{blocker} {issue['issue']}")
            print(f"   Fix: {issue['fix']}")
            print()
    else:
        print("✅ NO ISSUES FOUND - ALL VALIDATION CHECKS PASSED!")
        print()
    
    # Test specific critical checks
    print("=" * 80)
    print("CRITICAL CHECKS")
    print("=" * 80)
    print()
    
    synth_data = state['synthesized_data']
    financials = synth_data.get('detailed_financials', {})
    dcf = financials.get('dcf_outputs', {})
    
    checks = [
        ("synthesized_data exists", 'synthesized_data' in state),
        ("metadata exists", 'metadata' in synth_data),
        ("detailed_financials exists", 'detailed_financials' in synth_data),
        ("dcf_outputs exists", 'dcf_outputs' in financials),
        ("enterprise_value exists", 'enterprise_value' in dcf),
        ("enterprise_value > 0", dcf.get('enterprise_value', 0) > 0),
        ("normalized_ebitda exists", 'normalized_ebitda' in financials),
        ("normalized_ebitda is number", isinstance(financials.get('normalized_ebitda'), (int, float))),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False
    
    print()
    print("=" * 80)
    if result['valid'] and all_passed:
        print("✅ ALL TESTS PASSED - MAPPINGS ARE CORRECT!")
        print("=" * 80)
        return 0
    else:
        print("❌ TESTS FAILED - MAPPINGS NEED FIXING")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = test_validator_mappings()
    sys.exit(exit_code)
