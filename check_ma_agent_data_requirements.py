"""
Check why M&A agents are returning default values instead of actual calculations
"""
import json
from pathlib import Path
from loguru import logger

def check_ma_agent_outputs(job_id: str = "81a10a3d-5935-43f0-a5cf-811ad7cdd310"):
    """Check what M&A agents actually returned vs what PDF expects"""
    
    job_file = Path(f"data/jobs/{job_id}.json")
    
    with open(job_file, 'r') as f:
        state = json.load(f)
    
    logger.info("\n" + "="*80)
    logger.info("M&A AGENT OUTPUT INSPECTION")
    logger.info("="*80)
    
    # Define what each agent SHOULD return
    expected_outputs = {
        'accretion_dilution': {
            'expected_keys': ['accretion_dilution', 'deal_recommendation', 'board_summary'],
            'required_inputs': ['acquirer_data', 'deal_terms']
        },
        'sources_uses': {
            'expected_keys': ['uses_of_funds', 'sources_of_funds', 'balance_check'],
            'required_inputs': ['deal_value', 'deal_terms']
        },
        'contribution_analysis': {
            'expected_keys': ['financial_contribution', 'ownership_split', 'fairness_analysis'],
            'required_inputs': ['acquirer_data', 'financial_data', 'synergy_analysis']
        },
        'exchange_ratio_analysis': {
            'expected_keys': ['market_based_ratio', 'proposed_ratio', 'fairness_assessment'],
            'required_inputs': ['acquirer_data', 'financial_data', 'valuation_models']
        },
        'deal_structuring': {
            'expected_keys': ['consideration_structure', 'purchase_structure', 'recommended_structure'],
            'required_inputs': ['deal_value', 'deal_terms']
        }
    }
    
    # Check each M&A agent
    agent_outputs = state.get('agent_outputs', [])
    
    for agent_name, specs in expected_outputs.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"AGENT: {agent_name}")
        logger.info(f"{'='*80}")
        
        # Find this agent's output
        agent_output = next(
            (o for o in agent_outputs if o.get('agent_name') == agent_name),
            None
        )
        
        if not agent_output:
            logger.error(f"❌ {agent_name} DID NOT RUN or has no output!")
            continue
        
        # Check data structure
        data = agent_output.get('data', {})
        logger.info(f"Data type: {type(data)}")
        
        if isinstance(data, list):
            logger.error(f"❌ Data is a LIST (should be dict)!")
            logger.error(f"   Data: {data}")
            continue
        
        if not isinstance(data, dict):
            logger.error(f"❌ Data is {type(data)} (should be dict)!")
            continue
        
        # Check expected keys
        logger.info(f"\nExpected keys: {specs['expected_keys']}")
        logger.info(f"Actual keys: {list(data.keys())}")
        
        missing_keys = [k for k in specs['expected_keys'] if k not in data]
        if missing_keys:
            logger.warning(f"⚠️  Missing expected keys: {missing_keys}")
        else:
            logger.success(f"✅ All expected keys present")
        
        # Show actual key-value pairs for first few keys
        for key in list(data.keys())[:5]:
            value = data[key]
            logger.info(f"  {key}: {type(value).__name__}")
            if isinstance(value, dict) and value:
                logger.info(f"    Sample keys: {list(value.keys())[:3]}")
        
        # Check required inputs in state
        logger.info(f"\nRequired inputs: {specs['required_inputs']}")
        for req_input in specs['required_inputs']:
            if req_input in state:
                value = state[req_input]
                logger.success(f"  ✅ {req_input}: {type(value).__name__}")
                if isinstance(value, dict):
                    logger.info(f"     Keys: {list(value.keys())[:5]}")
                elif isinstance(value, list):
                    logger.info(f"     Length: {len(value)}")
            else:
                logger.error(f"  ❌ {req_input}: MISSING!")
    
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    # Overall check
    ma_agents_found = [
        agent_name for agent_name in expected_outputs.keys()
        if any(o.get('agent_name') == agent_name for o in agent_outputs)
    ]
    
    logger.info(f"\nM&A agents that ran: {len(ma_agents_found)}/5")
    for agent in ma_agents_found:
        logger.info(f"  ✅ {agent}")
    
    missing_agents = set(expected_outputs.keys()) - set(ma_agents_found)
    if missing_agents:
        logger.error(f"\nM&A agents that DID NOT RUN: {missing_agents}")
    
    # Check critical inputs
    logger.info("\nCritical inputs for M&A analysis:")
    critical_inputs = ['acquirer_data', 'deal_terms', 'deal_value', 'synergy_analysis']
    for inp in critical_inputs:
        if inp in state:
            logger.success(f"  ✅ {inp}: Present")
        else:
            logger.error(f"  ❌ {inp}: MISSING - M&A agents cannot run without this!")

if __name__ == "__main__":
    logger.info("Checking M&A Agent Data Requirements")
    check_ma_agent_outputs()
