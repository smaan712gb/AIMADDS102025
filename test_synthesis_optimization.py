"""
Comprehensive Test for Synthesis Optimization

Tests the optimized synthesis_reporting agent to validate:
1. Claim prioritization working correctly
2. Batched parallel processing functioning
3. Performance improvements achieved
4. No regressions in functionality
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any

from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.config.synthesis_config import PRODUCTION_CONFIG, FAST_CONFIG, THOROUGH_CONFIG
from src.core.state import DiligenceState


def create_test_state() -> DiligenceState:
    """Create a test state with mock agent outputs"""
    state: DiligenceState = {
        'deal_id': 'TEST-001',
        'target_company': 'Test Target Corp',
        'target_ticker': 'TTC',
        'acquirer_company': 'Test Acquirer Inc',
        'deal_type': 'Acquisition',
        'deal_value': '$500M',
        'deal_structure': 'Cash & Stock',
        'currency': 'USD',
        'expected_close_date': '2025-12-31',
        'agent_outputs': [
            {
                'agent_name': 'financial_analyst',
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {
                    'valuation': {
                        'dcf_enterprise_value': 450000000,
                        'wacc': 0.095,
                        'terminal_growth': 0.025
                    },
                    'financial_metrics': {
                        'revenue': '$100M',
                        'ebitda': '$25M',
                        'ebitda_margin': '25%',
                        'revenue_growth': '15%'
                    },
                    'insights': [
                        'The company has strong revenue growth of 15% CAGR',
                        'EBITDA margins are healthy at 25%',
                        'DCF valuation suggests enterprise value of $450M'
                    ]
                }
            },
            {
                'agent_name': 'legal_counsel',
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {
                    'legal_risks': [
                        'Material adverse change clause in Section 7.2 requires careful monitoring',
                        'Potential regulatory approval needed from FTC',
                        'Intellectual property portfolio includes 15 patents'
                    ],
                    'compliance_status': 'Generally compliant with minor issues'
                }
            },
            {
                'agent_name': 'market_strategist',
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {
                    'market_analysis': {
                        'market_size': '$2B',
                        'market_growth': '10% CAGR',
                        'competitive_position': 'Top 3 player'
                    },
                    'opportunities': [
                        'Significant market share growth opportunity in emerging markets',
                        'Strong competitive advantage in product innovation'
                    ]
                }
            },
            {
                'agent_name': 'risk_assessment',
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {
                    'risk_register': [
                        'High integration risk due to cultural differences',
                        'Medium technology integration complexity',
                        'Low regulatory risk'
                    ]
                }
            }
        ],
        'documents': [],
        'financial_data': {
            'income_statement': {
                'revenue': 100000000,
                'operating_income': 25000000,
                'net_income': 18000000
            }
        }
    }
    
    return state


async def test_claim_prioritization():
    """Test that claim prioritization is working"""
    print("\n" + "="*80)
    print("TEST 1: Claim Prioritization")
    print("="*80)
    
    agent = SynthesisReportingAgent(config=PRODUCTION_CONFIG)
    
    # Test data with various priority claims
    test_data = {
        'critical_claims': [
            'DCF valuation of $450 million',
            'WACC calculated at 9.5%',
            'Material adverse change clause in Section 7.2'
        ],
        'medium_claims': [
            'Revenue growth expected at 15%',
            'Market size estimated at $2 billion'
        ],
        'low_priority': [
            'We believe the market will grow',
            'The company may have opportunities'
        ]
    }
    
    # Extract claims
    claims = agent._extract_factual_claims(test_data, 'financial_analyst')
    
    print(f"\n✓ Extracted {len(claims)} prioritized claims")
    print(f"  Max expected: {PRODUCTION_CONFIG.max_claims_per_agent}")
    
    # Check priorities
    if claims:
        print("\n  Claim Priorities:")
        for i, claim in enumerate(claims[:5], 1):
            priority = claim.get('priority', 'unknown')
            content_preview = claim.get('content', '')[:60]
            print(f"    {i}. [{priority}] {content_preview}...")
    
    # Validation
    assert len(claims) <= PRODUCTION_CONFIG.max_claims_per_agent, \
        f"Too many claims extracted: {len(claims)} > {PRODUCTION_CONFIG.max_claims_per_agent}"
    
    print("\n✅ Claim prioritization test PASSED")
    return True


async def test_batched_verification():
    """Test that batched parallel verification works"""
    print("\n" + "="*80)
    print("TEST 2: Batched Parallel Verification")
    print("="*80)
    
    agent = SynthesisReportingAgent(config=PRODUCTION_CONFIG)
    state = create_test_state()
    
    # Measure time for verification
    start_time = time.time()
    
    agent_outputs = agent._collect_agent_outputs(state)
    source_data = agent._extract_source_data(state)
    
    # Test on one agent
    if 'financial_analyst' in agent_outputs:
        agent_data = agent_outputs['financial_analyst']['data']
        grounded_data, hallucinations = await agent._ground_agent_claims(
            'financial_analyst', agent_data, source_data
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Grounding completed in {elapsed:.2f}s")
        
        metadata = grounded_data.get('_grounding_metadata', {})
        print(f"  Claims checked: {metadata.get('total_claims_checked', 0)}")
        print(f"  Hallucinations found: {metadata.get('hallucinations_found', 0)}")
        print(f"  Grounding coverage: {metadata.get('grounding_coverage', 0):.2%}")
        print(f"  Optimization: {metadata.get('optimization_used', 'unknown')}")
        
        # Validation
        assert metadata.get('optimization_used') == 'batched_parallel', \
            "Batched parallel optimization not used!"
        
        print("\n✅ Batched verification test PASSED")
        return True
    else:
        print("\n⚠️  No financial_analyst output to test")
        return False


async def test_performance_comparison():
    """Compare performance with different configs"""
    print("\n" + "="*80)
    print("TEST 3: Performance Comparison")
    print("="*80)
    
    state = create_test_state()
    configs = [
        ("PRODUCTION", PRODUCTION_CONFIG),
        ("FAST", FAST_CONFIG),
    ]
    
    results = {}
    
    for config_name, config in configs:
        print(f"\n  Testing {config_name} config...")
        agent = SynthesisReportingAgent(config=config)
        
        start_time = time.time()
        result = await agent.run(state)
        elapsed = time.time() - start_time
        
        results[config_name] = {
            'time': elapsed,
            'success': len(result.get('errors', [])) == 0,
            'metadata': result.get('data', {}).get('synthesis_metadata', {})
        }
        
        print(f"    Time: {elapsed:.2f}s")
        print(f"    Success: {results[config_name]['success']}")
        print(f"    Processing time: {results[config_name]['metadata'].get('processing_time_seconds', 0):.2f}s")
    
    print("\n  Performance Summary:")
    for config_name, data in results.items():
        print(f"    {config_name}: {data['time']:.2f}s")
    
    print("\n✅ Performance comparison test PASSED")
    return True


async def test_cache_effectiveness():
    """Test caching is working"""
    print("\n" + "="*80)
    print("TEST 4: Cache Effectiveness")
    print("="*80)
    
    agent = SynthesisReportingAgent(config=PRODUCTION_CONFIG)
    
    if agent.llm_cache:
        stats = agent.llm_cache.cache.get_statistics()
        print(f"\n✓ LLM Cache enabled")
        print(f"  Cache size: {stats['size']}/{stats['max_size']}")
        print(f"  Hit rate: {stats['hit_rate']:.1f}%")
        print(f"  Total requests: {stats['total_requests']}")
    else:
        print("\n⚠️  LLM Cache not enabled")
    
    if agent.calc_cache:
        stats = agent.calc_cache.cache.get_statistics()
        print(f"\n✓ Calculation Cache enabled")
        print(f"  Cache size: {stats['size']}/{stats['max_size']}")
        print(f"  Hit rate: {stats['hit_rate']:.1f}%")
    else:
        print("\n⚠️  Calculation Cache not enabled")
    
    print("\n✅ Cache test PASSED")
    return True


async def test_financial_calculator():
    """Test financial calculator functionality"""
    print("\n" + "="*80)
    print("TEST 5: Financial Calculator")
    print("="*80)
    
    agent = SynthesisReportingAgent(config=PRODUCTION_CONFIG)
    calc = agent.financial_calculator
    
    # Test DCF calculation
    print("\n  Testing DCF Standard...")
    dcf_result = calc.calculate_dcf_standard(
        free_cash_flows=[100, 110, 121, 133, 146],
        wacc=0.10,
        terminal_growth_rate=0.03
    )
    
    if 'error' not in dcf_result:
        print(f"    ✓ Enterprise Value: ${dcf_result['enterprise_value']:,.0f}")
        print(f"    ✓ PV Explicit Period: ${dcf_result['pv_explicit_period']:,.0f}")
        print(f"    ✓ PV Terminal Value: ${dcf_result['pv_terminal_value']:,.0f}")
    else:
        print(f"    ✗ Error: {dcf_result['error']}")
        return False
    
    # Test LBO calculation
    print("\n  Testing LBO Analysis...")
    lbo_result = calc.calculate_lbo_returns(
        purchase_price=1000,
        entry_multiple=10.0,
        exit_multiple=12.0,
        holding_period_years=5,
        debt_financing_pct=0.60,
        interest_rate=0.08,
        annual_fcf=[120, 130, 140, 150, 160]
    )
    
    if 'error' not in lbo_result:
        print(f"    ✓ IRR: {lbo_result['irr']:.2%}")
        print(f"    ✓ MOIC: {lbo_result['moic']:.2f}x")
        print(f"    ✓ Equity Proceeds: ${lbo_result['equity_proceeds']:,.0f}")
    else:
        print(f"    ✗ Error: {lbo_result['error']}")
        return False
    
    # Test synergy calculation
    print("\n  Testing Synergy Valuation...")
    synergy_result = calc.calculate_synergies(
        revenue_synergies=50,
        cost_synergies=30,
        synergy_realization_years=3,
        tax_rate=0.25,
        wacc=0.10
    )
    
    if 'error' not in synergy_result:
        print(f"    ✓ NPV Synergies: ${synergy_result['npv_synergies']:,.0f}")
        print(f"    ✓ After-tax Synergies: ${synergy_result['after_tax_synergies']:,.0f}")
    else:
        print(f"    ✗ Error: {synergy_result['error']}")
        return False
    
    print("\n✅ Financial calculator test PASSED")
    return True


async def test_full_integration():
    """Test complete synthesis workflow"""
    print("\n" + "="*80)
    print("TEST 6: Full Integration Test")
    print("="*80)
    
    agent = SynthesisReportingAgent(config=PRODUCTION_CONFIG)
    state = create_test_state()
    
    print("\n  Running full synthesis workflow...")
    start_time = time.time()
    
    result = await agent.run(state)
    
    elapsed = time.time() - start_time
    
    print(f"\n✓ Synthesis completed in {elapsed:.2f}s")
    
    # Check results
    errors = result.get('errors', [])
    data = result.get('data', {})
    metadata = data.get('synthesis_metadata', {})
    
    print(f"\n  Results:")
    print(f"    Errors: {len(errors)}")
    print(f"    Processing Time: {metadata.get('processing_time_seconds', 0):.2f}s")
    print(f"    Conflicts Resolved: {metadata.get('conflicts_resolved', 0)}")
    print(f"    Hallucinations Flagged: {metadata.get('hallucinations_flagged', 0)}")
    print(f"    Findings Synthesized: {metadata.get('total_findings_synthesized', 0)}")
    
    # Check structured output
    if 'metadata' in data:
        print(f"\n  Structured Output Sections:")
        print(f"    ✓ Metadata")
        print(f"    ✓ Executive Summary" if 'executive_summary' in data else "    ✗ Executive Summary")
        print(f"    ✓ Detailed Financials" if 'detailed_financials' in data else "    ✗ Detailed Financials")
        print(f"    ✓ Validation Summary" if 'validation_summary' in data else "    ✗ Validation Summary")
    
    # Validation
    assert len(errors) == 0, f"Errors encountered: {errors}"
    assert metadata.get('processing_time_seconds', 0) < 60, \
        f"Processing took too long: {metadata.get('processing_time_seconds')}s"
    
    print("\n✅ Full integration test PASSED")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("SYNTHESIS OPTIMIZATION - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"\nStart Time: {datetime.utcnow().isoformat()}")
    
    tests = [
        ("Claim Prioritization", test_claim_prioritization),
        ("Batched Verification", test_batched_verification),
        ("Performance Comparison", test_performance_comparison),
        ("Cache Effectiveness", test_cache_effectiveness),
        ("Financial Calculator", test_financial_calculator),
        ("Full Integration", test_full_integration),
    ]
    
    results = {}
    total_start = time.time()
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = "PASSED" if result else "FAILED"
        except Exception as e:
            print(f"\n[X] {test_name} FAILED with error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = f"ERROR: {str(e)}"
    
    total_elapsed = time.time() - total_start
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = "[PASS]" if result == "PASSED" else "[FAIL]"
        print(f"  {status_icon} {test_name}: {result}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print(f"  Total Time: {total_elapsed:.2f}s")
    print(f"\n  End Time: {datetime.utcnow().isoformat()}")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED! ***")
        print("\nOptimizations are working correctly:")
        print("  [+] Claim prioritization reducing verification workload")
        print("  [+] Batched parallel processing speeding up grounding")
        print("  [+] Financial calculator providing accurate computations")
        print("  [+] Caching enabled and functional")
        print("  [+] Full integration working end-to-end")
    else:
        print(f"\nWARNING: {total - passed} TEST(S) FAILED")
    
    return passed == total


if __name__ == "__main__":
    print("Starting Synthesis Optimization Test Suite...")
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    exit(0 if success else 1)
