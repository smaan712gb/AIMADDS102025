"""
Test script to validate normalized financials fixes across all agents

This test validates that:
1. Smart data accessor works correctly
2. Agents prioritize normalized data when available
3. Fallback to raw data works properly
4. Quality gates are enforced
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

# Import agents with fixes
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent


class NormalizedFinancialsFixValidator:
    """Validates that normalized financials fixes are working correctly"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
    
    def log_test(self, test_name: str, passed: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")
        
        self.test_results['test_details'].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1
    
    async def run_all_tests(self):
        """Run all validation tests"""
        logger.info("=" * 80)
        logger.info("NORMALIZED FINANCIALS FIXES VALIDATION TEST SUITE")
        logger.info("=" * 80)
        
        # Test 1: Smart Data Accessor Basic Functionality
        await self.test_smart_accessor_basic()
        
        # Test 2: Financial Analyst Creates Normalized Data
        await self.test_financial_analyst_creates_normalized()
        
        # Test 3: Financial Deep Dive Uses Normalized Data
        await self.test_financial_deep_dive_uses_normalized()
        
        # Test 4: Integration Planner Uses Normalized Data
        await self.test_integration_planner_uses_normalized()
        
        # Test 5: Competitive Benchmarking Uses Normalized Data
        await self.test_competitive_benchmarking_uses_normalized()
        
        # Test 6: Fallback to Raw Data Works
        await self.test_fallback_to_raw_data()
        
        # Test 7: Quality Gate Enforcement
        await self.test_quality_gate_enforcement()
        
        # Print summary
        self.print_summary()
        
        return self.test_results
    
    async def test_smart_accessor_basic(self):
        """Test that smart data accessor method exists and works"""
        test_name = "Smart Data Accessor - Basic Functionality"
        
        try:
            # Create a test agent
            agent = FinancialDeepDiveAgent()
            
            # Verify method exists
            if not hasattr(agent, '_get_financial_data_smart'):
                self.log_test(test_name, False, "Method _get_financial_data_smart not found on agent")
                return
            
            # Create mock state with normalized data
            test_state = {
                'normalized_financials': {
                    'quality_score': 85,
                    'normalized_income': [{'revenue': 1000000, 'ebitda': 250000}],
                    'normalized_balance': [{'totalAssets': 5000000}],
                    'normalized_cash_flow': [{'freeCashFlow': 200000}],
                    'ebitda': 250000
                },
                'financial_data': {
                    'income_statement': [{'revenue': 950000, 'ebitda': 230000}]
                }
            }
            
            # Call smart accessor
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            # Verify it returned normalized data
            if result.get('source') == 'normalized':
                self.log_test(test_name, True, f"Correctly returned normalized data (quality: {result.get('quality_score')})")
            else:
                self.log_test(test_name, False, f"Expected normalized source, got: {result.get('source')}")
            
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_financial_analyst_creates_normalized(self):
        """Test that Financial Analyst creates normalized financials"""
        test_name = "Financial Analyst - Creates Normalized Financials"
        
        try:
            agent = FinancialAnalystAgent()
            
            # Create minimal state
            test_state = {
                'target_company': 'Test Company',
                'target_ticker': 'AAPL',  # Use AAPL for testing
                'errors': [],
                'warnings': []
            }
            
            # Run financial analyst
            logger.info("Running Financial Analyst on AAPL...")
            result = await agent.run(test_state)
            
            # Check if normalized_financials was created
            if 'normalized_financials' in test_state:
                normalized = test_state['normalized_financials']
                quality_score = normalized.get('quality_score', 0)
                
                if quality_score > 0:
                    self.log_test(test_name, True, 
                                f"Created normalized financials with quality score: {quality_score}/100")
                else:
                    self.log_test(test_name, False, "Normalized financials created but quality score is 0")
            else:
                self.log_test(test_name, False, "normalized_financials not found in state")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_financial_deep_dive_uses_normalized(self):
        """Test that Financial Deep Dive uses normalized data"""
        test_name = "Financial Deep Dive - Uses Normalized Data"
        
        try:
            agent = FinancialDeepDiveAgent()
            
            # Create state with both normalized and raw data
            test_state = {
                'target_company': 'Test Company',
                'target_ticker': 'TEST',
                'normalized_financials': {
                    'quality_score': 87,
                    'normalized_income': [{'revenue': 1000000, 'ebitda': 250000}],
                    'normalized_balance': [{'totalAssets': 5000000, 'totalCurrentAssets': 2000000, 'totalCurrentLiabilities': 1000000, 'cashAndCashEquivalents': 500000}],
                    'normalized_cash_flow': [{'freeCashFlow': 200000, 'capitalExpenditure': -50000, 'depreciationAndAmortization': 40000}],
                    'ebitda': 250000
                },
                'financial_data': {
                    'income_statement': [{'revenue': 950000, 'ebitda': 230000}],
                    'balance_sheet': [{'totalAssets': 4800000}],
                    'cash_flow': [{'freeCashFlow': 190000}]
                },
                'errors': [],
                'warnings': []
            }
            
            # Call smart accessor to verify it uses normalized
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            if result.get('source') == 'normalized' and result.get('quality_score') == 87:
                self.log_test(test_name, True, 
                            "Correctly uses normalized data with quality score 87/100")
            else:
                self.log_test(test_name, False, 
                            f"Expected normalized source, got: {result.get('source')}, quality: {result.get('quality_score')}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_integration_planner_uses_normalized(self):
        """Test that Integration Planner uses normalized data for synergies"""
        test_name = "Integration Planner - Uses Normalized for Synergies"
        
        try:
            agent = IntegrationPlannerAgent()
            
            # Create test state
            test_state = {
                'target_company': 'Target Corp',
                'acquirer_company': 'Acquirer Inc',
                'deal_type': 'Acquisition',
                'target_ticker': 'TGT',
                'normalized_financials': {
                    'quality_score': 92,
                    'normalized_income': [{'revenue': 2000000, 'ebitda': 400000}],
                    'ebitda': 400000
                },
                'financial_data': {
                    'income_statement': [{'revenue': 1900000, 'ebitda': 350000}]
                },
                'errors': [],
                'warnings': [],
                'metadata': {}
            }
            
            # Test smart accessor
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            if result.get('source') == 'normalized' and result.get('ebitda') == 400000:
                self.log_test(test_name, True, 
                            f"Uses normalized EBITDA ($400K) instead of raw ($350K) for synergy baseline")
            else:
                self.log_test(test_name, False, 
                            f"Expected normalized EBITDA 400000, got: {result.get('ebitda')}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_competitive_benchmarking_uses_normalized(self):
        """Test that Competitive Benchmarking uses normalized data"""
        test_name = "Competitive Benchmarking - Uses Normalized Metrics"
        
        try:
            agent = CompetitiveBenchmarkingAgent()
            
            # Create test state
            test_state = {
                'target_ticker': 'COMP',
                'normalized_financials': {
                    'quality_score': 78,
                    'normalized_income': [{'revenue': 5000000, 'grossProfitMargin': 0.45, 'ebitda': 1000000}],
                    'ebitda': 1000000
                },
                'financial_data': {
                    'income_statement': [{'revenue': 4800000, 'grossProfitMargin': 0.40}]
                },
                'errors': [],
                'warnings': []
            }
            
            # Test smart accessor
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            if result.get('source') == 'normalized':
                income = result.get('income_statement', [{}])[0]
                revenue = income.get('revenue', 0)
                
                if revenue == 5000000:  # Normalized revenue, not raw
                    self.log_test(test_name, True, 
                                "Uses normalized revenue ($5M) instead of raw ($4.8M) for peer comparisons")
                else:
                    self.log_test(test_name, False, 
                                f"Expected normalized revenue 5000000, got: {revenue}")
            else:
                self.log_test(test_name, False, 
                            f"Expected normalized source, got: {result.get('source')}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_fallback_to_raw_data(self):
        """Test that agents fall back to raw data when normalized unavailable"""
        test_name = "Fallback Mechanism - Uses Raw When Normalized Unavailable"
        
        try:
            agent = FinancialDeepDiveAgent()
            
            # Create state with NO normalized data
            test_state = {
                'financial_data': {
                    'income_statement': [{'revenue': 3000000, 'ebitda': 600000}],
                    'balance_sheet': [{'totalAssets': 10000000}],
                    'cash_flow': [{'freeCashFlow': 500000}]
                }
                # No normalized_financials key
            }
            
            # Call smart accessor - should fall back to raw
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            if result.get('source') == 'raw':
                income = result.get('income_statement', [{}])[0]
                if income.get('revenue') == 3000000:
                    self.log_test(test_name, True, 
                                "Correctly falls back to raw data when normalized unavailable")
                else:
                    self.log_test(test_name, False, "Fallback worked but data incorrect")
            else:
                self.log_test(test_name, False, 
                            f"Expected raw source on fallback, got: {result.get('source')}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    async def test_quality_gate_enforcement(self):
        """Test that low-quality normalized data is rejected"""
        test_name = "Quality Gate - Rejects Low Quality Normalized Data"
        
        try:
            agent = FinancialDeepDiveAgent()
            
            # Create state with LOW quality normalized data (below 60 threshold)
            test_state = {
                'normalized_financials': {
                    'quality_score': 45,  # Below 60 threshold
                    'normalized_income': [{'revenue': 8000000}],
                    'ebitda': 1500000
                },
                'financial_data': {
                    'income_statement': [{'revenue': 7500000, 'ebitda': 1400000}]
                }
            }
            
            # Call smart accessor - should reject low quality and use raw
            result = agent._get_financial_data_smart(test_state, prefer_normalized=True)
            
            if result.get('source') == 'raw':
                self.log_test(test_name, True, 
                            "Correctly rejects low-quality normalized data (score: 45) and uses raw")
            else:
                self.log_test(test_name, False, 
                            f"Expected to reject quality=45 and use raw, but got source: {result.get('source')}")
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']}")
        
        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        pass_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        logger.info("=" * 80)
        
        if self.test_results['tests_failed'] == 0:
            logger.info("🎉 ALL TESTS PASSED - Normalized Financials Fixes Validated!")
        else:
            logger.warning(f"⚠️ {self.test_results['tests_failed']} test(s) failed - review details above")
        
        # Save results to file
        output_file = f"test_results_normalized_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"Test results saved to: {output_file}")


async def main():
    """Main test execution"""
    validator = NormalizedFinancialsFixValidator()
    results = await validator.run_all_tests()
    return results


if __name__ == "__main__":
    # Run tests
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if results['tests_failed'] == 0 else 1
    exit(exit_code)
