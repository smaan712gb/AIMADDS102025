import asyncio
from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.core.state import DiligenceState

async def test_synthesis():
    # Create a state with a simple test
    state = DiligenceState()
    state['target_company'] = 'TEST_COMPANY'
    state['target_ticker'] = 'TSLA'

    # Test synthesis agent directly
    agent = SynthesisReportingAgent()

    # Mock some agent outputs
    state['project_manager'] = {'status': 'completed', 'test': 'data'}
    state['financial_analyst'] = {
        'normalized_financials': {'test': 'data'},
        'advanced_valuation': {'test': 'valuation'},
        'financial_metrics': {},
        'trend_analysis': {},
        'seasonality': {},
        'financial_health': {},
        'ratio_analysis': {},
        'red_flags': [],
        'insights': {},
        'raw_data': {}
    }

    result = await agent.run(state)
    print('Synthesis test completed successfully!')
    print(f'Data keys: {list(result.get("data", {}).keys())}')
    return result

if __name__ == "__main__":
    asyncio.run(test_synthesis())
