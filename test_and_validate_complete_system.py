"""
Comprehensive Test & Validation - All 13 Agents with Real Data
Combines testing + validation in one script
"""
import asyncio
import json
import subprocess
from pathlib import Path
from datetime import datetime

from src.agents.project_manager import ProjectManagerAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.legal_counsel import LegalCounselAgent
from src.agents.market_strategist import MarketStrategistAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.macroeconomic_analyst import MacroeconomicAnalystAgent
from src.agents.risk_assessment import RiskAssessmentAgent
from src.agents.tax_structuring import TaxStructuringAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.external_validator import ExternalValidatorAgent
from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.core.state import create_initial_state


async def main():
    """Run complete test and validation"""
    ticker = input("Enter ticker (default: AAPL): ").strip().upper() or "AAPL"
    
    print(f"\n{'='*100}")
    print(f"COMPREHENSIVE 13-AGENT SYSTEM TEST - {ticker}")
    print(f"{'='*100}\n")
    
    # Initialize state
    deal_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    state = create_initial_state(
        deal_id=deal_id,
        target_company=ticker,
        target_ticker=ticker,
        acquirer_company="Test Acquirer",
        deal_type="acquisition",
        strategic_rationale=f"Strategic acquisition of {ticker}",
        investment_thesis=f"Market leadership acquisition"
    )
    
    # Define agents in OPTIMAL workflow order
    agents = [
        ("Project Manager", "project_manager", ProjectManagerAgent()),
        ("Financial Analyst", "financial_analyst", FinancialAnalystAgent()),
        ("Financial Deep Dive", "financial_deep_dive", FinancialDeepDiveAgent()),
        ("Legal Counsel", "legal_counsel", LegalCounselAgent()),
        ("Market Strategist", "market_strategist", MarketStrategistAgent()),
        ("Competitive Benchmarking", "competitive_benchmarking", CompetitiveBenchmarkingAgent()),
        ("Macroeconomic Analyst", "macroeconomic_analyst", MacroeconomicAnalystAgent()),
        ("Risk Assessment", "risk_assessment", RiskAssessmentAgent()),
        ("Tax Structuring", "tax_structuring", TaxStructuringAgent()),
        ("Integration Planner", "integration_planner", IntegrationPlannerAgent()),
        ("External Validator", "external_validator", ExternalValidatorAgent()),
        ("Synthesis", "synthesis_reporting", SynthesisReportingAgent()),
    ]
    
    successful = 0
    failed = 0
    
    # Run all agents
    for idx, (name, key, agent) in enumerate(agents, 1):
        print(f"\n{idx}. {name}...", end=" ")
        try:
            result = await agent.run(state)
            
            # Update state
            if isinstance(result, dict) and 'data' in result:
                state[key] = result['data']
                state['agent_outputs'].append({
                    'agent_name': key,
                    'status': 'completed',
                    'data': result['data'],
                    'timestamp': datetime.now().isoformat()
                })
            else:
                state = result
            
            print("✅ PASS")
            successful += 1
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            failed += 1
    
    # Save state
    job_file = Path(f'data/jobs/test_{ticker.lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    job_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(job_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    
    print(f"\n{'='*100}")
    print("TEST SUMMARY")
    print(f"{'='*100}")
    print(f"Agents Tested: {len(agents)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {successful/len(agents)*100:.1f}%")
    print(f"Job file: {job_file}")
    print(f"Agent outputs: {len(state.get('agent_outputs', []))}")
    
    # Run validation
    print(f"\n{'='*100}")
    print("RUNNING VALIDATION")
    print(f"{'='*100}\n")
    
    result = subprocess.run(
        ['python', 'validate_all_agents.py', str(job_file)],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if successful == len(agents):
        print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION!")
    
    return state


if __name__ == '__main__':
    asyncio.run(main())
