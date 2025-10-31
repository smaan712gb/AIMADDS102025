"""
Diagnostic script to identify which agents are producing empty outputs
"""
import asyncio
import json
from datetime import datetime
from loguru import logger
from pathlib import Path

from src.core.state import DiligenceState
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


async def diagnose_agent_outputs():
    """
    Run all agents and check which produce empty outputs
    """
    logger.info("=" * 80)
    logger.info("AGENT OUTPUT DIAGNOSTIC")
    logger.info("=" * 80)
    
    # Initialize state
    state = DiligenceState()
    state['target_company'] = 'Microsoft Corporation'
    state['target_ticker'] = 'MSFT'
    state['acquirer_company'] = 'Acquirer Inc.'
    state['deal_type'] = 'acquisition'
    state['deal_value'] = 75000000000  # $75B
    
    # Track agent outputs
    agent_results = {}
    agents_to_test = [
        ("project_manager", ProjectManagerAgent()),
        ("financial_analyst", FinancialAnalystAgent()),
        ("financial_deep_dive", FinancialDeepDiveAgent()),
        ("legal_counsel", LegalCounselAgent()),
        ("market_strategist", MarketStrategistAgent()),
        ("competitive_benchmarking", CompetitiveBenchmarkingAgent()),
        ("macroeconomic_analyst", MacroeconomicAnalystAgent()),
        ("risk_assessment", RiskAssessmentAgent()),
        ("tax_structuring", TaxStructuringAgent()),
        ("integration_planner", IntegrationPlannerAgent()),
        ("external_validator", ExternalValidatorAgent()),
        ("synthesis_reporting", SynthesisReportingAgent())
    ]
    
    logger.info(f"Testing {len(agents_to_test)} agents...")
    logger.info("")
    
    for idx, (agent_key, agent) in enumerate(agents_to_test, 1):
        logger.info(f"[{idx}/{len(agents_to_test)}] Testing {agent_key}...")
        
        try:
            result = await agent.run(state)
            
            # Analyze output
            data = result.get('data', {})
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            
            has_data = bool(data and len(data) > 0)
            has_errors = len(errors) > 0
            has_warnings = len(warnings) > 0
            
            # Calculate data size
            data_keys = list(data.keys()) if data else []
            data_size = len(json.dumps(data)) if data else 0
            
            agent_results[agent_key] = {
                'has_data': has_data,
                'data_keys': data_keys,
                'data_size_bytes': data_size,
                'num_errors': len(errors),
                'num_warnings': len(warnings),
                'errors': errors[:3] if errors else [],  # First 3 errors
                'status': 'HAS_OUTPUT' if has_data else 'EMPTY_OUTPUT'
            }
            
            # Log status
            if has_data:
                logger.success(f"✅ {agent_key}: HAS OUTPUT ({len(data_keys)} keys, {data_size} bytes)")
            else:
                logger.warning(f"⚠️ {agent_key}: EMPTY OUTPUT")
                if errors:
                    logger.error(f"   Errors: {errors[0]}")
            
            # Update state with agent output
            if has_data:
                # Store agent output in state
                state[agent_key] = data
                
        except Exception as e:
            logger.error(f"❌ {agent_key}: EXCEPTION - {e}")
            agent_results[agent_key] = {
                'has_data': False,
                'data_keys': [],
                'data_size_bytes': 0,
                'num_errors': 1,
                'errors': [str(e)],
                'status': 'EXCEPTION'
            }
        
        logger.info("")
    
    # Summary
    logger.info("=" * 80)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    logger.info("=" * 80)
    
    agents_with_output = [k for k, v in agent_results.items() if v['has_data']]
    agents_without_output = [k for k, v in agent_results.items() if not v['has_data']]
    
    logger.info(f"Total agents tested: {len(agents_to_test)}")
    logger.info(f"Agents with output: {len(agents_with_output)}")
    logger.info(f"Agents without output: {len(agents_without_output)}")
    logger.info("")
    
    if agents_with_output:
        logger.success("✅ Agents WITH output:")
        for agent in agents_with_output:
            result = agent_results[agent]
            logger.success(f"   • {agent}: {len(result['data_keys'])} keys, {result['data_size_bytes']} bytes")
    
    logger.info("")
    
    if agents_without_output:
        logger.warning("⚠️ Agents WITHOUT output:")
        for agent in agents_without_output:
            result = agent_results[agent]
            logger.warning(f"   • {agent}: {result['status']}")
            if result['errors']:
                logger.error(f"     Error: {result['errors'][0]}")
    
    # Check state keys
    logger.info("")
    logger.info("=" * 80)
    logger.info("📋 STATE ANALYSIS")
    logger.info("=" * 80)
    
    state_keys = list(state.keys())
    logger.info(f"Total state keys: {len(state_keys)}")
    logger.info(f"State keys: {', '.join(state_keys)}")
    
    # Save diagnostic report
    report = {
        'timestamp': datetime.now().isoformat(),
        'agents_tested': len(agents_to_test),
        'agents_with_output': len(agents_with_output),
        'agents_without_output': len(agents_without_output),
        'agent_results': agent_results,
        'state_keys': state_keys
    }
    
    output_path = Path('agent_output_diagnostic.json')
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.success(f"💾 Diagnostic report saved to: {output_path}")
    
    # Identify the specific 5 agents with missing outputs
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔍 ROOT CAUSE ANALYSIS")
    logger.info("=" * 80)
    
    if len(agents_without_output) == 5:
        logger.warning("CONFIRMED: 5 agents producing empty outputs (7/12 pattern)")
        logger.warning("Missing agents:")
        for agent in agents_without_output:
            result = agent_results[agent]
            logger.warning(f"  • {agent}")
            if result['errors']:
                logger.error(f"    Reason: {result['errors'][0]}")
    elif len(agents_without_output) > 0:
        logger.warning(f"Found {len(agents_without_output)} agents with empty outputs")
    else:
        logger.success("✅ ALL AGENTS PRODUCING OUTPUT!")
    
    return agent_results


if __name__ == "__main__":
    asyncio.run(diagnose_agent_outputs())
