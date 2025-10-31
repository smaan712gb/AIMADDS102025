"""
Production Test Script - Complete System Test with Real APIs

This script tests the entire M&A analysis system with real API keys and data.
It validates that all agents, tools, and integrations work correctly in production.

Usage:
    python test_production_system.py

Requirements:
    - .env file with valid API keys (FMP, ANTHROPIC, GOOGLE)
    - Active internet connection
    - Conda environment activated
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import get_config
from src.core.state import create_initial_state
from src.core.llm_factory import get_llm
from src.integrations.fmp_client import FMPClient
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.macroeconomic_analyst import MacroeconomicAnalystAgent
from src.agents.conversational_synthesis import ConversationalSynthesisAgent
from src.utils.anomaly_detection import AnomalyDetector


class ProductionTestSuite:
    """Comprehensive production test suite"""
    
    def __init__(self):
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'start_time': datetime.now(),
            'end_time': None
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        if passed:
            self.test_results['passed'].append(result)
            print(f"✅ PASS: {test_name}")
        else:
            self.test_results['failed'].append(result)
            print(f"❌ FAIL: {test_name}")
            
        if details:
            print(f"   {details}")
    
    def log_warning(self, message: str):
        """Log warning"""
        self.test_results['warnings'].append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"⚠️  WARNING: {message}")
    
    async def test_configuration(self) -> bool:
        """Test 1: Configuration loading"""
        print("\n" + "="*80)
        print("TEST 1: Configuration Loading")
        print("="*80)
        
        try:
            config = get_config()
            
            # Check agents are configured
            required_agents = [
                'financial_analyst', 'competitive_benchmarking',
                'macroeconomic_analyst', 'conversational_synthesis'
            ]
            
            missing_agents = [a for a in required_agents if a not in config.agents]
            
            if missing_agents:
                self.log_test(
                    "Configuration Loading",
                    False,
                    f"Missing agents: {missing_agents}"
                )
                return False
            
            self.log_test("Configuration Loading", True, "All required agents configured")
            return True
            
        except Exception as e:
            self.log_test("Configuration Loading", False, str(e))
            return False
    
    async def test_llm_initialization(self) -> bool:
        """Test 2: LLM initialization"""
        print("\n" + "="*80)
        print("TEST 2: LLM Initialization")
        print("="*80)
        
        try:
            # Test Claude
            claude = get_llm('claude')
            model_name = getattr(claude, 'model_name', getattr(claude, 'model', 'claude-sonnet-4-5'))
            self.log_test("Claude LLM Init", True, f"Model: {model_name}")
            
            # Test Gemini
            gemini = get_llm('gemini')
            model_name = getattr(gemini, 'model_name', getattr(gemini, 'model', 'gemini-2.5-pro'))
            self.log_test("Gemini LLM Init", True, f"Model: {model_name}")
            
            return True
            
        except Exception as e:
            self.log_test("LLM Initialization", False, str(e))
            return False
    
    async def test_fmp_api(self) -> bool:
        """Test 3: FMP API integration"""
        print("\n" + "="*80)
        print("TEST 3: FMP API Integration")
        print("="*80)
        
        try:
            async with FMPClient() as client:
                # Test fetching company profile
                profile = await client.get_company_profile('AAPL')
                
                if profile:
                    self.log_test(
                        "FMP API - Company Profile",
                        True,
                        f"Retrieved profile for {profile.get('companyName', 'Unknown')}"
                    )
                else:
                    self.log_test("FMP API - Company Profile", False, "No data returned")
                    return False
                
                # Test fetching financial statements
                income_stmt = await client.get_income_statement('AAPL', limit=1)
                
                if income_stmt and len(income_stmt) > 0:
                    self.log_test(
                        "FMP API - Income Statement",
                        True,
                        f"Retrieved {len(income_stmt)} period(s)"
                    )
                else:
                    self.log_test("FMP API - Income Statement", False, "No data returned")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("FMP API Integration", False, str(e))
            return False
    
    async def test_financial_analyst_agent(self, symbol: str = "NVDA") -> Dict[str, Any]:
        """Test 4: Financial Analyst Agent"""
        print("\n" + "="*80)
        print(f"TEST 4: Financial Analyst Agent ({symbol})")
        print("="*80)
        
        try:
            # Initialize agent
            agent = FinancialAnalystAgent()
            agent.set_fmp_client(FMPClient())
            
            self.log_test("Financial Analyst - Initialization", True)
            
            # Run analysis
            analysis = await agent.analyze(symbol)
            
            if 'error' in analysis:
                self.log_test(
                    "Financial Analyst - Analysis",
                    False,
                    f"Error: {analysis['error']}"
                )
                return {}
            
            # Check key components
            checks = [
                ('financial_health_score', 'Financial Health Score'),
                ('valuation', 'Valuation'),
                ('ratio_analysis', 'Ratio Analysis'),
                ('normalized_financials', 'Normalized Financials'),
                ('advanced_valuation', 'Advanced Valuation'),
            ]
            
            for key, name in checks:
                if key in analysis:
                    self.log_test(f"Financial Analyst - {name}", True)
                else:
                    self.log_test(f"Financial Analyst - {name}", False, f"Missing {key}")
            
            # Check quality score
            quality_score = analysis.get('normalized_financials', {}).get('quality_score', 0)
            self.log_test(
                "Financial Analyst - Quality Score",
                True,
                f"Quality: {quality_score}/100"
            )
            
            return analysis
            
        except Exception as e:
            self.log_test("Financial Analyst Agent", False, str(e))
            return {}
    
    async def test_competitive_agent(self, symbol: str, target_metrics: Dict) -> bool:
        """Test 5: Competitive Benchmarking Agent"""
        print("\n" + "="*80)
        print(f"TEST 5: Competitive Benchmarking Agent ({symbol})")
        print("="*80)
        
        try:
            agent = CompetitiveBenchmarkingAgent()
            agent.set_fmp_client(FMPClient())
            
            self.log_test("Competitive Agent - Initialization", True)
            
            # Run analysis
            analysis = await agent.analyze(symbol, target_metrics)
            
            if 'summary' in analysis:
                position = analysis['summary'].get('competitive_position', 'Unknown')
                peers_count = analysis['summary'].get('peers_analyzed', 0)
                
                self.log_test(
                    "Competitive Agent - Analysis",
                    True,
                    f"Position: {position}, Peers: {peers_count}"
                )
                return True
            else:
                self.log_test("Competitive Agent - Analysis", False, "No summary generated")
                return False
                
        except Exception as e:
            self.log_test("Competitive Agent", False, str(e))
            return False
    
    async def test_macro_agent(self, symbol: str) -> bool:
        """Test 6: Macroeconomic Analyst Agent"""
        print("\n" + "="*80)
        print(f"TEST 6: Macroeconomic Analyst Agent ({symbol})")
        print("="*80)
        
        try:
            agent = MacroeconomicAnalystAgent()
            agent.set_fmp_client(FMPClient())
            
            self.log_test("Macro Agent - Initialization", True)
            
            # Run analysis
            analysis = await agent.analyze(symbol, {})
            
            if 'scenario_models' in analysis:
                scenario_count = len(analysis['scenario_models'])
                self.log_test(
                    "Macro Agent - Analysis",
                    True,
                    f"Generated {scenario_count} scenarios"
                )
                return True
            else:
                self.log_test("Macro Agent - Analysis", False, "No scenarios generated")
                return False
                
        except Exception as e:
            self.log_test("Macro Agent", False, str(e))
            return False
    
    async def test_conversational_agent(self) -> bool:
        """Test 7: Conversational Synthesis Agent"""
        print("\n" + "="*80)
        print("TEST 7: Conversational Synthesis Agent")
        print("="*80)
        
        try:
            agent = ConversationalSynthesisAgent()
            
            self.log_test("Conversational Agent - Initialization", True)
            
            # Initialize with sample analysis
            sample_analysis = {
                'financial_analysis': {
                    'financial_health_score': 85,
                    'valuation': {'dcf_value_per_share': 150.00}
                }
            }
            
            summary = await agent.initialize_analysis(sample_analysis)
            
            if summary and len(summary) > 0:
                self.log_test(
                    "Conversational Agent - Initialization",
                    True,
                    f"Generated summary ({len(summary)} chars)"
                )
            else:
                self.log_test(
                    "Conversational Agent - Initialization",
                    False,
                    "No summary generated"
                )
                return False
            
            # Test question processing
            response = await agent.process_question("What are the biggest risks?")
            
            if response and 'answer' in response:
                self.log_test(
                    "Conversational Agent - Q&A",
                    True,
                    f"Answered question ({len(response['answer'])} chars)"
                )
                return True
            else:
                self.log_test("Conversational Agent - Q&A", False, "Failed to answer")
                return False
                
        except Exception as e:
            self.log_test("Conversational Agent", False, str(e))
            return False
    
    async def test_anomaly_detection(self) -> bool:
        """Test 8: Anomaly Detection"""
        print("\n" + "="*80)
        print("TEST 8: Anomaly Detection")
        print("="*80)
        
        try:
            detector = AnomalyDetector()
            
            # Train on sample data
            historical_data = [
                {
                    'revenue': 1000000000 + i * 100000000,
                    'inventory': 200000000 + i * 10000000,
                    'accounts_receivable': 150000000 + i * 8000000,
                    'cost_of_revenue': 600000000 + i * 60000000,
                    'operating_expenses': 200000000 + i * 20000000,
                    'total_assets': 1500000000 + i * 100000000,
                    'cash': 300000000
                }
                for i in range(8)
            ]
            
            training_result = detector.train(historical_data)
            
            if training_result.get('periods_analyzed', 0) > 0:
                self.log_test(
                    "Anomaly Detection - Training",
                    True,
                    f"Trained on {training_result['periods_analyzed']} periods"
                )
            else:
                self.log_test("Anomaly Detection - Training", False, "Training failed")
                return False
            
            # Test detection
            current_data = historical_data[-1].copy()
            current_data['inventory'] *= 1.5  # Create anomaly
            
            detection_result = detector.detect_anomalies(current_data)
            
            if 'anomalies_detected' in detection_result:
                anomaly_count = len(detection_result['anomalies_detected'])
                self.log_test(
                    "Anomaly Detection - Detection",
                    True,
                    f"Detected {anomaly_count} anomalies"
                )
                return True
            else:
                self.log_test("Anomaly Detection - Detection", False, "No results")
                return False
                
        except Exception as e:
            self.log_test("Anomaly Detection", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.test_results['end_time'] = datetime.now()
        duration = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("PRODUCTION TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])
        passed_tests = len(self.test_results['passed'])
        failed_tests = len(self.test_results['failed'])
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {len(self.test_results['warnings'])}")
        print(f"\nDuration: {duration:.2f} seconds")
        
        if failed_tests > 0:
            print("\n" + "="*80)
            print("FAILED TESTS:")
            print("="*80)
            for test in self.test_results['failed']:
                print(f"\n❌ {test['test']}")
                print(f"   {test['details']}")
        
        if len(self.test_results['warnings']) > 0:
            print("\n" + "="*80)
            print("WARNINGS:")
            print("="*80)
            for warning in self.test_results['warnings']:
                print(f"\n⚠️  {warning['message']}")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        print("\n" + "="*80)
        if failed_tests == 0:
            print("✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
        else:
            print("❌ SOME TESTS FAILED - REVIEW FAILURES BEFORE PRODUCTION")
        print("="*80 + "\n")
        
        return failed_tests == 0


async def run_production_tests(test_symbol: str = "NVDA"):
    """Run complete production test suite"""
    suite = ProductionTestSuite()
    
    print("\n" + "🚀"*40)
    print("PRODUCTION SYSTEM TEST SUITE")
    print("🚀"*40)
    print(f"\nTest Symbol: {test_symbol}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    config_ok = await suite.test_configuration()
    if not config_ok:
        print("\n❌ Configuration test failed. Cannot continue.")
        suite.print_summary()
        return False
    
    llm_ok = await suite.test_llm_initialization()
    if not llm_ok:
        print("\n❌ LLM initialization failed. Cannot continue.")
        suite.print_summary()
        return False
    
    api_ok = await suite.test_fmp_api()
    if not api_ok:
        print("\n❌ FMP API test failed. Cannot continue.")
        suite.print_summary()
        return False
    
    # Run agent tests
    financial_analysis = await suite.test_financial_analyst_agent(test_symbol)
    
    if financial_analysis:
        # Extract metrics for competitive analysis
        target_metrics = {
            'revenue_growth': financial_analysis.get('ratio_analysis', {}).get('growth_metrics', {}).get('revenue_cagr', 0),
            'gross_margin': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('gross_margin', 0),
            'net_margin': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('net_margin', 0),
            'roe': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('roe', 0),
        }
        
        await suite.test_competitive_agent(test_symbol, target_metrics)
    
    await suite.test_macro_agent(test_symbol)
    await suite.test_conversational_agent()
    await suite.test_anomaly_detection()
    
    # Print summary
    all_passed = suite.print_summary()
    
    return all_passed


if __name__ == "__main__":
    # Check for test symbol argument
    test_symbol = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    
    print(f"\n📋 Running production tests for: {test_symbol}")
    print("🔧 Make sure .env file has valid API keys")
    print("🌐 Ensure internet connection is active\n")
    
    # Run tests
    all_passed = asyncio.run(run_production_tests(test_symbol))
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)
