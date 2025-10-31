"""
Test Deal Structuring Agent Fix for NoneType Error
Tests that the agent handles None deal_value properly
"""
import asyncio
from src.agents.deal_structuring import DealStructuringAgent
from src.core.state import DiligenceState


async def test_deal_structuring_with_none():
    """Test that agent handles None deal_value without crashing"""
    
    agent = DealStructuringAgent()
    
    # Test Case 1: None deal_value
    print("\n=== TEST 1: None deal_value ===")
    state = DiligenceState(
        target_company="Palantir Technologies Inc.",
        target_ticker="PLTR",
        deal_value=None,  # This was causing the crash
        financial_data={
            'balance_sheet': [
                {
                    'totalCurrentAssets': 5000000000,
                    'totalCurrentLiabilities': 2000000000,
                    'cashAndCashEquivalents': 1000000000,
                    'totalAssets': 10000000000,
                    'intangibleAssets': 500000000,
                    'totalLiabilities': 3000000000
                }
            ]
        }
    )
    
    try:
        result = await agent.run(state)
        print(f"✓ Agent completed without error")
        print(f"  Data keys: {list(result.get('data', {}).keys())}")
        print(f"  Errors: {result.get('errors', [])}")
        print(f"  Warnings: {result.get('warnings', [])}")
    except Exception as e:
        print(f"✗ Agent failed with error: {e}")
        return False
    
    # Test Case 2: Valid deal_value
    print("\n=== TEST 2: Valid deal_value ($50B) ===")
    state['deal_value'] = 50000000000
    
    try:
        result = await agent.run(state)
        print(f"✓ Agent completed without error")
        print(f"  Deal value: ${result['data']['deal_value']:,.0f}")
        print(f"  Recommended structure: {result['data']['recommended_structure'].get('recommended_consideration', 'N/A')}")
    except Exception as e:
        print(f"✗ Agent failed with error: {e}")
        return False
    
    # Test Case 3: Zero deal_value
    print("\n=== TEST 3: Zero deal_value ===")
    state['deal_value'] = 0
    
    try:
        result = await agent.run(state)
        print(f"✓ Agent completed without error")
        print(f"  Deal value: ${result['data']['deal_value']:,.0f}")
    except Exception as e:
        print(f"✗ Agent failed with error: {e}")
        return False
    
    # Test Case 4: String deal_value (invalid)
    print("\n=== TEST 4: Invalid string deal_value ===")
    state['deal_value'] = "invalid"
    
    try:
        result = await agent.run(state)
        print(f"✓ Agent handled invalid input gracefully")
        print(f"  Warnings: {result.get('warnings', [])}")
    except Exception as e:
        print(f"✗ Agent failed with error: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_deal_structuring_with_none())
    exit(0 if success else 1)
