"""
Test script to verify the quality_score attribute fix in FinancialNormalizer
"""
import sys
sys.path.insert(0, 'src')

from utils.financial_normalizer import FinancialNormalizer

def test_quality_score_initialization():
    """Test that quality_score is properly initialized"""
    print("Testing FinancialNormalizer quality_score initialization...")
    
    # Test 1: Create instance and check attribute
    normalizer = FinancialNormalizer()
    assert hasattr(normalizer, 'quality_score'), "❌ FinancialNormalizer missing quality_score attribute"
    assert normalizer.quality_score == 100, f"❌ quality_score not initialized to 100, got {normalizer.quality_score}"
    print("✓ Test 1 passed: quality_score attribute exists and initialized to 100")
    
    # Test 2: Create instance with LLM disabled
    normalizer_no_llm = FinancialNormalizer(use_llm_intelligence=False)
    assert hasattr(normalizer_no_llm, 'quality_score'), "❌ FinancialNormalizer (no LLM) missing quality_score attribute"
    assert normalizer_no_llm.quality_score == 100, f"❌ quality_score not initialized to 100, got {normalizer_no_llm.quality_score}"
    print("✓ Test 2 passed: quality_score attribute exists with LLM disabled")
    
    # Test 3: Simulate the normalization flow
    mock_income = [
        {'date': '2024-12-31', 'revenue': 1000000, 'netIncome': 100000, 'operatingIncome': 120000}
    ]
    mock_balance = [
        {'date': '2024-12-31', 'totalAssets': 5000000, 'totalLiabilities': 2000000}
    ]
    mock_cash_flow = [
        {'date': '2024-12-31', 'operatingCashFlow': 90000, 'freeCashFlow': 80000}
    ]
    
    result = normalizer.normalize_financial_statements(
        income_statements=mock_income,
        balance_sheets=mock_balance,
        cash_flows=mock_cash_flow
    )
    
    assert 'quality_score' in result, "❌ quality_score not in returned result dictionary"
    assert isinstance(result['quality_score'], (int, float)), f"❌ quality_score not numeric, got {type(result['quality_score'])}"
    print(f"✓ Test 3 passed: quality_score in result = {result['quality_score']}")
    
    print("\n✅ All tests passed! quality_score attribute is properly initialized")
    return True

if __name__ == '__main__':
    try:
        test_quality_score_initialization()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
