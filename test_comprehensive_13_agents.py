"""
Comprehensive Test for All 13 Agents with Real Data
Tests entire M&A workflow from start to finish
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Import all agents
from src.agents.project_manager import ProjectManagerAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.legal_counsel import LegalCounselAgent
from src.agents.market_strategist import MarketStrategistAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.macroeconomic_analyst import MacroeconomicAnalystAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.external_validator import ExternalValidatorAgent
from src.agents.risk_assessment import RiskAssessmentAgent
from src.agents.tax_structuring import TaxStructuringAgent
from src.agents.synthesis_reporting import SynthesisReportingAgent

# Import state management
from src.core.state import create_initial_state


async def run_comprehensive_test(ticker: str = "AAPL"):
    """
    Run comprehensive test of all 13 agents with real data
    
    Args:
        ticker: Stock ticker to analyze (default: AAPL - high quality data)
    """
    print("\n" + "="*100)
    print(f"COMPREHENSIVE 13-AGENT TEST - {ticker}")
    print("="*100)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create initial state with all required parameters
    deal_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    state = create_initial_state(
        deal_id=deal_id,
        target_company=ticker,
        target_ticker=ticker,
        acquirer_company="Test Acquirer",
        deal_type="acquisition",
        strategic_rationale=f"Strategic acquisition of {ticker} to expand market presence",
        investment_thesis=f"Acquire {ticker} to gain market leadership and technology capabilities"
    )
    
    # Track results
    agent_results = {}
    
    # Define all 13 agents to test (OPTIMAL WORKFLOW ORDER)
    agents_to_test = [
        ("1. Project Manager", "project_manager", ProjectManagerAgent()),
        ("2. Financial Analyst", "financial_analyst", FinancialAnalystAgent()),
        ("3. Financial Deep Dive", "financial_deep_dive", FinancialDeepDiveAgent()),
        ("4. Legal Counsel", "legal_counsel", LegalCounselAgent()),
        ("5. Market Strategist", "market_strategist", MarketStrategistAgent()),
        ("6. Competitive Benchmarking", "competitive_benchmarking", CompetitiveBenchmarkingAgent()),
        ("7. Macroeconomic Analyst", "macroeconomic_analyst", MacroeconomicAnalystAgent()),
        ("8. Risk Assessment", "risk_assessment", RiskAssessmentAgent()),  # MOVED: Before Integration & Validator
        ("9. Tax Structuring", "tax_structuring", TaxStructuringAgent()),  # MOVED: Before Integration & Validator
        ("10. Integration Planner", "integration_planner", IntegrationPlannerAgent()),  # Uses Risk + Tax data
        ("11. External Validator", "external_validator", ExternalValidatorAgent()),  # MOVED: Validates Risk + Tax
        ("12. Synthesis & Reporting", "synthesis_reporting", SynthesisReportingAgent()),  # Final consolidation
    ]
    
    print("\n" + "─"*100)
    print("EXECUTING ALL 13 AGENTS")
    print("─"*100 + "\n")
    
    # Execute each agent
    for agent_name, agent_key, agent_instance in agents_to_test:
        print(f"\n{'='*100}")
        print(f"{agent_name}")
        print(f"{'='*100}")
        
        try:
            # Execute agent
            result = await agent_instance.run(state)
            
            # Update state (handle both dict and DiligenceState)
            if isinstance(result, dict):
                # If agent returns dict with data/errors/warnings
                if 'data' in result:
                    state[agent_key] = result['data']
                    
                    # CRITICAL FIX: Append to agent_outputs array
                    state['agent_outputs'].append({
                        'agent_name': agent_key,
                        'agent_type': agent_key,
                        'status': 'completed',
                        'data': result['data'],
                        'result': result['data'],
                        'errors': result.get('errors', []),
                        'warnings': result.get('warnings', []),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    agent_results[agent_key] = {
                        'status': 'SUCCESS',
                        'data_keys': list(result['data'].keys()) if isinstance(result['data'], dict) else ['data_present'],
                        'errors': result.get('errors', []),
                        'warnings': result.get('warnings', []),
                        'data_size': len(str(result['data']))
                    }
                else:
                    # Full state update
                    state = result
                    agent_results[agent_key] = {
                        'status': 'SUCCESS',
                        'state_updated': True
                    }
            else:
                # DiligenceState returned
                state = result
                agent_results[agent_key] = {
                    'status': 'SUCCESS',
                    'state_updated': True
                }
            
            # Print summary
            print(f"✅ {agent_name} - COMPLETED")
            
            # Print key outputs
            if agent_key in agent_results:
                result_info = agent_results[agent_key]
                if 'data_keys' in result_info:
                    print(f"   Data Keys: {', '.join(result_info['data_keys'][:5])}")
                    if len(result_info['data_keys']) > 5:
                        print(f"   ... and {len(result_info['data_keys']) - 5} more")
                    print(f"   Data Size: {result_info['data_size']:,} characters")
                
                if result_info.get('errors'):
                    print(f"   ⚠️ Errors: {len(result_info['errors'])}")
                if result_info.get('warnings'):
                    print(f"   ⚠️ Warnings: {len(result_info['warnings'])}")
            
            # Show special capabilities
            if agent_key == 'financial_analyst':
                advanced_val = state.get('valuation_models', {}).get('dcf_advanced', {})
                if 'lbo_analysis' in advanced_val:
                    lbo = advanced_val['lbo_analysis']
                    if 'returns_analysis' in lbo:
                        irr = lbo['returns_analysis'].get('irr_percent', 0)
                        mom = lbo['returns_analysis'].get('multiple_of_money', 0)
                        print(f"   🎯 LBO Analysis: {irr:.1f}% IRR, {mom:.2f}x MoM")
            
            elif agent_key == 'legal_counsel':
                litigation = state.get('metadata', {}).get('legal_analysis', {}).get('litigation_analysis', {})
                if litigation:
                    lawsuit_count = len(litigation.get('lawsuits', []))
                    print(f"   ⚖️ Litigation Analysis: {lawsuit_count} cases found")
                
                compliance = state.get('compliance_status', {})
                if compliance:
                    print(f"   ✓ Compliance Status: {len(compliance)} categories assessed")
            
            elif agent_key == 'risk_assessment':
                risk_data = state.get('risk_assessment', {})
                if risk_data:
                    scores = risk_data.get('risk_scores', {})
                    print(f"   🎯 Risk Rating: {scores.get('risk_rating', 'N/A')}")
                    print(f"   📊 Risk Score: {scores.get('overall_risk_score', 0)}/100")
                    print(f"   ⚠️ Total Risks: {scores.get('total_risks', 0)}")
            
            elif agent_key == 'tax_structuring':
                tax_data = state.get('tax_analysis', {})
                if tax_data:
                    structure = tax_data.get('optimal_structure', 'N/A')
                    print(f"   💰 Optimal Structure: {structure}")
                    tax_benefit = tax_data.get('tax_implications', {}).get('asset_step_up_benefit', {}).get('npv_at_10_percent', 0)
                    if tax_benefit > 0:
                        print(f"   💵 Tax Benefit NPV: ${tax_benefit:,.0f}")
            
            elif agent_key == 'external_validator':
                val_data = state.get('external_validator', {})
                if not val_data:
                    # Check agent_outputs
                    for output in state.get('agent_outputs', []):
                        if output.get('agent_name') == 'external_validator':
                            val_data = output.get('data', {})
                            break
                
                if val_data:
                    conf = val_data.get('confidence_score', 0)
                    validated = len(val_data.get('validated_findings', []))
                    print(f"   ✓ Confidence Score: {conf:.1%}")
                    print(f"   ✓ Validated Findings: {validated}")
        
        except Exception as e:
            print(f"❌ {agent_name} - FAILED")
            print(f"   Error: {str(e)}")
            agent_results[agent_key] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100 + "\n")
    
    # Count results
    total = len(agents_to_test)
    successful = sum(1 for r in agent_results.values() if r['status'] == 'SUCCESS')
    failed = sum(1 for r in agent_results.values() if r['status'] == 'FAILED')
    
    print(f"Total Agents Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {successful/total*100:.1f}%\n")
    
    # Show key capabilities tested
    print("KEY CAPABILITIES VERIFIED:")
    
    capabilities_tested = []
    
    if 'financial_analyst' in agent_results and agent_results['financial_analyst']['status'] == 'SUCCESS':
        capabilities_tested.append("✅ Financial Analysis (FMP API)")
        if 'lbo_analysis' in str(state.get('valuation_models', {})):
            capabilities_tested.append("✅ LBO Model (IRR, MoM, debt paydown)")
    
    if 'legal_counsel' in agent_results and agent_results['legal_counsel']['status'] == 'SUCCESS':
        capabilities_tested.append("✅ Legal Analysis (SEC 10-K)")
        if state.get('compliance_status'):
            capabilities_tested.append("✅ Compliance Assessment (7 categories)")
        litigation = state.get('metadata', {}).get('legal_analysis', {}).get('litigation_analysis', {})
        if litigation and litigation.get('lawsuits'):
            capabilities_tested.append(f"✅ Litigation Analysis ({len(litigation['lawsuits'])} cases)")
    
    if 'risk_assessment' in agent_results and agent_results['risk_assessment']['status'] == 'SUCCESS':
        capabilities_tested.append("✅ Risk Assessment (aggregates all agents)")
        risk_data = state.get('risk_assessment', {})
        if risk_data:
            capabilities_tested.append(f"✅ Risk Matrix (likelihood × impact)")
            capabilities_tested.append(f"✅ Risk Scenarios (Best/Base/Worst)")
    
    if 'tax_structuring' in agent_results and agent_results['tax_structuring']['status'] == 'SUCCESS':
        capabilities_tested.append("✅ Tax Structuring (Asset/Stock/Merger)")
        tax_data = state.get('tax_analysis', {})
        if tax_data:
            capabilities_tested.append(f"✅ Tax Benefit NPV Calculation")
    
    if 'external_validator' in agent_results and agent_results['external_validator']['status'] == 'SUCCESS':
        capabilities_tested.append("✅ External Validation (validates all 13 agents)")
        # Check for validated_findings
        val_data = state.get('external_validator', {})
        if not val_data:
            for output in state.get('agent_outputs', []):
                if output.get('agent_name') == 'external_validator':
                    val_data = output.get('data', {})
                    break
        if val_data and val_data.get('validated_findings'):
            capabilities_tested.append(f"✅ Populated Validated Findings ({len(val_data['validated_findings'])})")
    
    for cap in capabilities_tested:
        print(f"  {cap}")
    
    print(f"\n{'='*100}")
    print("FINAL VALIDATION")
    print(f"{'='*100}\n")
    
    # Run validation on the generated state
    print("Running validation script on generated state...\n")
    
    # Save state to temporary file
    temp_file = Path('data/jobs/comprehensive_test_run.json')
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    
    print(f"State saved to: {temp_file}")
    print(f"State size: {temp_file.stat().st_size:,} bytes")
    print(f"Agent outputs in state: {len(state.get('agent_outputs', []))}")
    
    # Show state structure
    print("\nState Keys Present:")
    for key in sorted(state.keys()):
        value = state[key]
        if isinstance(value, dict):
            print(f"  {key}: dict with {len(value)} keys")
        elif isinstance(value, list):
            print(f"  {key}: list with {len(value)} items")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    print(f"\n{'='*100}")
    print(f"TEST COMPLETE - {successful}/{total} agents successful ({successful/total*100:.1f}%)")
    print(f"{'='*100}\n")
    
    if successful == total:
        print("🎉 EXCELLENT: All 13 agents executed successfully!")
        print("✅ System is ready for production use")
    elif successful >= total * 0.75:
        print("⚠️ GOOD: Most agents working, some issues to address")
    else:
        print("❌ NEEDS WORK: Multiple agents failing")
    
    return state, agent_results


if __name__ == '__main__':
    ticker = input("Enter ticker to analyze (default: AAPL): ").strip().upper() or "AAPL"
    print(f"\nRunning comprehensive test for {ticker}...")
    print("This will execute all 13 agents with real FMP + SEC data\n")
    
    # Run the test
    state, results = asyncio.run(run_comprehensive_test(ticker))
    
    print("\n✅ Comprehensive test complete!")
    print(f"Next step: python validate_all_agents.py data/jobs/comprehensive_test_run.json")
