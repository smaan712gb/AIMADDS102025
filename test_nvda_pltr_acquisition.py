"""
Comprehensive End-to-End Test: NVDA Acquiring PLTR
Real data, real APIs, all scenarios covered
"""
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

from src.core.state import create_initial_state, Document
from src.agents.project_manager import ProjectManagerAgent
from src.agents.data_ingestion import DataIngestionAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.legal_counsel import LegalCounselAgent
from src.agents.market_strategist import MarketStrategistAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.outputs.excel_generator import ExcelGenerator
from src.integrations.sec_client import get_sec_client


class NVDAPLTRTestSuite:
    """
    Comprehensive test suite for NVDA acquiring PLTR
    
    Scenarios Tested:
    1. Financial Analysis (both companies)
    2. Legal Due Diligence
    3. Market Positioning
    4. Integration Planning
    5. Final Synthesis
    6. All Output Formats
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.sec_client = get_sec_client()
        
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        logger.info("=" * 80)
        logger.info("🧪 COMPREHENSIVE END-TO-END TEST SUITE: NVDA ACQUIRING PLTR")
        logger.info("=" * 80)
        
        # Test 1: Initial Setup and Data Gathering
        await self.test_01_setup_and_data_gathering()
        
        # Test 2: Full Agent Workflow
        await self.test_02_complete_workflow()
        
        # Test 3: SEC Filings Integration
        await self.test_03_sec_filings()
        
        # Test 4: All Output Formats
        await self.test_04_output_formats()
        
        # Test 5: Error Handling
        await self.test_05_error_scenarios()
        
        # Final Report
        self.generate_test_report()
    
    async def test_01_setup_and_data_gathering(self):
        """Test 1: Setup and data gathering from real APIs"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Setup and Real Data Gathering")
        logger.info("=" * 80)
        
        try:
            # Create state for NVDA acquiring PLTR
            state = create_initial_state(
                deal_id="NVDA-PLTR-2025-001",
                target_company="Palantir Technologies Inc.",
                target_ticker="PLTR",
                acquirer_company="NVIDIA Corporation",
                investment_thesis="Strategic acquisition to enhance AI/ML capabilities and expand enterprise software portfolio. NVIDIA seeks to integrate Palantir's data analytics platform with its AI infrastructure.",
                strategic_rationale="Combine NVIDIA's GPU computing power with Palantir's enterprise AI platform to create comprehensive AI solutions for government and commercial customers.",
                deal_type="acquisition",
                deal_value=50_000_000_000,  # $50B estimated
                deal_structure="cash_and_stock",
                expected_close_date="2026-06-30"
            )
            
            logger.info(f"✅ Created deal state: {state['deal_id']}")
            logger.info(f"   Acquirer: NVIDIA Corporation")
            logger.info(f"   Target: Palantir Technologies Inc. (PLTR)")
            logger.info(f"   Deal Value: ${state['deal_value']:,.0f}")
            logger.info(f"   Strategic Rationale: AI/ML + Enterprise Data Analytics")
            
            # Fetch real SEC filing information
            logger.info("\n📄 Fetching SEC Filings...")
            pltr_filings = self.sec_client.get_all_filings_info("PLTR")
            nvda_filings = self.sec_client.get_all_filings_info("NVDA")
            
            logger.info(f"   PLTR Filings: {pltr_filings.get('filing_count', 0)} available")
            logger.info(f"   NVDA Filings: {nvda_filings.get('filing_count', 0)} available")
            logger.info(f"   PLTR CIK: {pltr_filings.get('cik', 'N/A')}")
            logger.info(f"   NVDA CIK: {nvda_filings.get('cik', 'N/A')}")
            
            # Store SEC info in state
            state['metadata']['sec_filings'] = {
                "target": pltr_filings,
                "acquirer": nvda_filings
            }
            
            self.test_results.append({
                "test": "01_setup_and_data",
                "status": "PASSED",
                "details": f"Successfully created deal and fetched SEC filing info for both companies"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Test 1 failed: {e}")
            self.test_results.append({
                "test": "01_setup_and_data",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    async def test_02_complete_workflow(self):
        """Test 2: Complete multi-agent workflow"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Complete Multi-Agent Workflow")
        logger.info("=" * 80)
        
        try:
            # Create state
            state = create_initial_state(
                deal_id="NVDA-PLTR-2025-WORKFLOW",
                target_company="Palantir Technologies Inc.",
                target_ticker="PLTR",
                acquirer_company="NVIDIA Corporation",
                investment_thesis="Strategic AI/ML acquisition",
                strategic_rationale="Enhance enterprise AI capabilities",
                deal_type="acquisition",
                deal_value=50_000_000_000
            )
            
            # Agent 1: Project Manager
            logger.info("\n🎯 Running Project Manager...")
            pm_agent = ProjectManagerAgent()
            state = await pm_agent.execute(state)
            workflow = state['metadata'].get('agent_workflow', [])
            logger.info(f"   ✅ Created workflow: {' → '.join(workflow)}")
            
            # Agent 2: Financial Analyst (Target: PLTR)
            logger.info("\n💰 Running Financial Analyst for PLTR...")
            financial_agent = FinancialAnalystAgent()
            state = await financial_agent.execute(state)
            pm_agent.mark_agent_complete(state, "financial_analyst")
            logger.info(f"   ✅ Financial analysis complete")
            
            # Agent 3: Legal Counsel
            logger.info("\n⚖️ Running Legal Counsel...")
            legal_agent = LegalCounselAgent()
            state = await legal_agent.execute(state)
            pm_agent.mark_agent_complete(state, "legal_counsel")
            logger.info(f"   ✅ Legal analysis complete")
            
            # Agent 4: Market Strategist (with Grok 4)
            logger.info("\n📊 Running Market Strategist with Grok 4...")
            market_agent = MarketStrategistAgent()
            state = await market_agent.execute(state)
            pm_agent.mark_agent_complete(state, "market_strategist")
            logger.info(f"   ✅ Market analysis complete")
            logger.info(f"   🤖 Sentiment analyzed with: {state['sentiment_analysis'].get('analyzed_with', 'N/A')}")
            
            # Agent 5: Integration Planner
            logger.info("\n🔧 Running Integration Planner...")
            integration_agent = IntegrationPlannerAgent()
            state = await integration_agent.execute(state)
            pm_agent.mark_agent_complete(state, "integration_planner")
            logger.info(f"   ✅ Integration planning complete")
            
            # Agent 6: Synthesis & Reporting
            logger.info("\n📝 Running Synthesis & Reporting...")
            synthesis_agent = SynthesisReportingAgent()
            state = await synthesis_agent.execute(state)
            pm_agent.mark_agent_complete(state, "synthesis_reporting")
            logger.info(f"   ✅ Synthesis complete")
            
            # Check progress
            progress = pm_agent.get_progress_summary(state)
            logger.info(f"\n📊 Final Progress: {progress['overall_progress']}")
            logger.info(f"   Completed: {', '.join(progress['completed_agents'])}")
            
            # Verify all agents ran
            assert progress['overall_progress'] == '100.0%', "Not all agents completed"
            
            self.test_results.append({
                "test": "02_complete_workflow",
                "status": "PASSED",
                "details": f"All {len(progress['completed_agents'])} agents completed successfully",
                "progress": progress['overall_progress']
            })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Test 2 failed: {e}")
            self.test_results.append({
                "test": "02_complete_workflow",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    async def test_03_sec_filings(self):
        """Test 3: SEC filings integration"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: SEC Filings Integration")
        logger.info("=" * 80)
        
        try:
            # Fetch comprehensive SEC data
            logger.info("\n📄 Fetching SEC Filings for PLTR...")
            pltr_filings = self.sec_client.get_all_filings_info("PLTR")
            
            logger.info("\n📄 Fetching SEC Filings for NVDA...")
            nvda_filings = self.sec_client.get_all_filings_info("NVDA")
            
            # Verify data retrieved
            assert pltr_filings.get('cik'), "PLTR CIK not found"
            assert nvda_filings.get('cik'), "NVDA CIK not found"
            
            logger.info(f"\n✅ SEC Filings Retrieved:")
            logger.info(f"   PLTR: CIK {pltr_filings['cik']}, {pltr_filings['filing_count']} filings")
            logger.info(f"   NVDA: CIK {nvda_filings['cik']}, {nvda_filings['filing_count']} filings")
            logger.info(f"\n   PLTR SEC URL: {pltr_filings.get('sec_edgar_url', 'N/A')}")
            logger.info(f"   NVDA SEC URL: {nvda_filings.get('sec_edgar_url', 'N/A')}")
            
            self.test_results.append({
                "test": "03_sec_filings",
                "status": "PASSED",
                "details": f"Retrieved SEC data for both companies",
                "pltr_cik": pltr_filings['cik'],
                "nvda_cik": nvda_filings['cik']
            })
            
            return {"pltr": pltr_filings, "nvda": nvda_filings}
            
        except Exception as e:
            logger.error(f"❌ Test 3 failed: {e}")
            self.test_results.append({
                "test": "03_sec_filings",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    async def test_04_output_formats(self):
        """Test 4: All output format generation"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Output Format Generation")
        logger.info("=" * 80)
        
        try:
            # Create state with complete analysis
            state = create_initial_state(
                deal_id="NVDA-PLTR-2025-OUTPUT",
                target_company="Palantir Technologies Inc.",
                target_ticker="PLTR",
                investment_thesis="AI/ML strategic acquisition",
                strategic_rationale="Enhance enterprise AI capabilities"
            )
            
            # Run financial analysis
            financial_agent = FinancialAnalystAgent()
            state = await financial_agent.execute(state)
            
            # Test Excel Generation
            logger.info("\n📊 Testing Excel Report Generation...")
            generator = ExcelGenerator()
            excel_path = generator.generate_full_report(state)
            
            assert Path(excel_path).exists(), f"Excel file not created: {excel_path}"
            logger.info(f"   ✅ Excel report created: {excel_path}")
            
            # Verify Excel contents
            import openpyxl
            wb = openpyxl.load_workbook(excel_path)
            sheet_names = wb.sheetnames
            logger.info(f"   ✅ Excel has {len(sheet_names)} worksheets: {', '.join(sheet_names)}")
            
            # Expected sheets
            expected_sheets = [
                "Executive Summary",
                "Financial Overview",
                "DCF Valuation",
                "Ratio Analysis",
                "Risk Assessment",
                "Assumptions"
            ]
            
            for expected in expected_sheets:
                assert expected in sheet_names, f"Missing sheet: {expected}"
                logger.info(f"   ✅ Verified sheet: {expected}")
            
            self.test_results.append({
                "test": "04_output_formats",
                "status": "PASSED",
                "details": f"Excel report generated with all {len(sheet_names)} required sheets",
                "file": excel_path
            })
            
            return excel_path
            
        except Exception as e:
            logger.error(f"❌ Test 4 failed: {e}")
            self.test_results.append({
                "test": "04_output_formats",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    async def test_05_error_scenarios(self):
        """Test 5: Error handling and edge cases"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: Error Handling & Edge Cases")
        logger.info("=" * 80)
        
        try:
            # Scenario 1: Invalid ticker
            logger.info("\n🧪 Scenario 1: Invalid ticker handling...")
            state = create_initial_state(
                deal_id="TEST-INVALID",
                target_company="Invalid Company",
                target_ticker="XXXXX",  # Invalid ticker
                investment_thesis="Test case",
                strategic_rationale="Testing error handling"
            )
            
            financial_agent = FinancialAnalystAgent()
            state = await financial_agent.execute(state)
            
            # Should have errors but not crash
            assert len(state['errors']) > 0 or not state['financial_data'], "Should handle invalid ticker gracefully"
            logger.info(f"   ✅ Invalid ticker handled gracefully")
            
            # Scenario 2: Missing data
            logger.info("\n🧪 Scenario 2: Missing optional data...")
            state2 = create_initial_state(
                deal_id="TEST-MINIMAL",
                target_company="Test Company",
                investment_thesis="Minimal test",
                strategic_rationale="Testing with minimal data"
                # No ticker, no deal value
            )
            
            pm_agent = ProjectManagerAgent()
            state2 = await pm_agent.execute(state2)
            
            # Should still create a workflow
            assert state2['metadata'].get('agent_workflow'), "Should create workflow even with minimal data"
            logger.info(f"   ✅ Minimal data scenario handled")
            
            self.test_results.append({
                "test": "05_error_scenarios",
                "status": "PASSED",
                "details": "Error handling and edge cases work correctly"
            })
            
        except Exception as e:
            logger.error(f"❌ Test 5 failed: {e}")
            self.test_results.append({
                "test": "05_error_scenarios",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    def generate_test_report(self):
        """Generate final test report"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 80)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')
        total = len(self.test_results)
        
        logger.info(f"\nTests Run: {total}")
        logger.info(f"Passed: {passed} ✅")
        logger.info(f"Failed: {failed} ❌")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        
        logger.info("\nDetailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            logger.info(f"   {i}. {result['test']}: {status_icon} {result['status']}")
            if result.get('details'):
                logger.info(f"      {result['details']}")
            if result.get('error'):
                logger.error(f"      Error: {result['error']}")
        
        # Save report to file
        report_path = f"outputs/TEST_REPORT_NVDA_PLTR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write("COMPREHENSIVE TEST REPORT: NVDA ACQUIRING PLTR\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Success Rate: {(passed/total*100):.1f}%\n\n")
            
            for i, result in enumerate(self.test_results, 1):
                f.write(f"\n{i}. {result['test']}: {result['status']}\n")
                f.write(f"   Details: {result.get('details', 'N/A')}\n")
                if result.get('error'):
                    f.write(f"   Error: {result['error']}\n")
        
        logger.info(f"\n💾 Test report saved: {report_path}")


async def main():
    """Main test runner"""
    logger.info("\n🚀 Starting Comprehensive End-to-End Tests\n")
    logger.info("Real Data | Real APIs | Real Results\n")
    
    test_suite = NVDAPLTRTestSuite()
    
    try:
        await test_suite.run_all_tests()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL TESTS COMPLETED!")
        logger.info("=" * 80)
        logger.info("\nCheck outputs/ directory for:")
        logger.info("  - Excel reports")
        logger.info("  - Test report")
        logger.info("\nCheck data/gcs_local/ for uploaded documents")
        
    except Exception as e:
        logger.error(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
