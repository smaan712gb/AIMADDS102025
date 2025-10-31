"""
Unit test for Deal Structuring Agent
"""
import asyncio
from src.agents.deal_structuring import DealStructuringAgent
from src.core.state import create_initial_state


async def test_deal_structuring():
    """Test deal structuring agent"""
    print("Testing Deal Structuring Agent...")
    
    try:
        # Create agent
        print("1. Creating agent...")
        agent = DealStructuringAgent()
        print("✓ Agent created successfully")
        
        # Create test state
        print("2. Creating test state...")
        state = create_initial_state(
            deal_id="TEST-001",
            target_company="Test Company",
            target_ticker="TEST",
            investment_thesis="Test deal",
            strategic_rationale="Test rationale",
            deal_type="acquisition",
            deal_value=1_000_000_000
        )
        print("✓ State created successfully")
        
        # Add minimal financial data
        state['financial_data'] = {
            'balance_sheet': [{
                'totalCurrentAssets': 100000,
                'totalCurrentLiabilities': 50000,
                'cashAndCashEquivalents': 20000,
                'totalAssets': 500000,
                'intangibleAssets': 100000,
                'totalLiabilities': 200000
            }]
        }
        print("✓ Financial data added")
        
        # Execute agent
        print("3. Executing agent...")
        result = await agent.execute(state)
        print("✓ Agent executed successfully")
        
        # Check result
        print("\n4. Result:")
        print(f"   Errors: {len(result.get('errors', []))}")
        print(f"   Warnings: {len(result.get('warnings', []))}")
        
        if result.get('errors'):
            print("\n   ERRORS:")
            for error in result['errors']:
                print(f"   - {error}")
        
        agent_outputs = state.get('agent_outputs', [])
        deal_output = next((o for o in agent_outputs if o.get('agent_name') == 'deal_structuring'), None)
        
        if deal_output:
            print(f"\n   Agent output found:")
            print(f"   Status: {deal_output.get('status')}")
            data = deal_output.get('data', {})
            print(f"   Data keys: {list(data.keys())}")
        
        print("\n✅ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_deal_structuring())
    exit(0 if result else 1)
