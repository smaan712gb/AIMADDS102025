"""
Demonstration script for M&A Diligence Swarm
This script shows how to run a complete financial analysis
"""
import asyncio
from src.core.state import create_initial_state
from src.agents.financial_analyst import FinancialAnalystAgent
from src.outputs.excel_generator import ExcelGenerator
from loguru import logger


async def run_demo_analysis():
    """Run a demonstration analysis on a public company"""
    
    logger.info("🚀 Starting M&A Diligence Swarm Demo")
    logger.info("=" * 60)
    
    # Create initial state for the analysis
    logger.info("📋 Creating deal state...")
    state = create_initial_state(
        deal_id="DEMO-2025-001",
        target_company="Apple Inc.",
        target_ticker="AAPL",
        investment_thesis="Strategic acquisition to expand into consumer electronics and services",
        strategic_rationale="Market leader with strong brand, ecosystem lock-in, and recurring revenue streams",
        deal_type="acquisition",
        deal_value=3_000_000_000_000,  # $3T valuation
        currency="USD"
    )
    
    logger.info(f"✓ Deal ID: {state['deal_id']}")
    logger.info(f"✓ Target: {state['target_company']} ({state['target_ticker']})")
    logger.info(f"✓ Deal Value: ${state['deal_value']:,.0f}")
    logger.info("")
    
    # Run Financial Analyst Agent
    logger.info("💰 Running Financial Analyst Agent...")
    logger.info("   Using Claude Sonnet 4.5 for financial modeling")
    logger.info("   Fetching data from FMP API in parallel...")
    
    analyst = FinancialAnalystAgent()
    state = await analyst.execute(state)
    
    # Check results
    if state['agent_statuses']['financial_analyst'] == 'completed':
        logger.success("✓ Financial analysis completed successfully!")
        
        # Get financial metrics
        metrics = state.get('financial_metrics')
        if metrics:
            logger.info("")
            logger.info("📊 Key Financial Metrics:")
            logger.info(f"   Revenue: ${metrics.get('revenue', 0):,.0f}")
            logger.info(f"   EBITDA: ${metrics.get('ebitda', 0):,.0f}")
            logger.info(f"   Net Income: ${metrics.get('net_income', 0):,.0f}")
            logger.info(f"   ROE: {metrics.get('roe', 0):.2%}")
            logger.info(f"   ROA: {metrics.get('roa', 0):.2%}")
        
        # Get DCF valuation
        dcf = state.get('valuation_models', {}).get('dcf', {})
        if dcf and 'enterprise_value' in dcf:
            logger.info("")
            logger.info("💵 DCF Valuation:")
            logger.info(f"   Enterprise Value: ${dcf['enterprise_value']:,.0f}")
        
        # Get agent output for insights
        agent_outputs = state.get('agent_outputs', [])
        financial_output = next((o for o in agent_outputs if o['agent_name'] == 'financial_analyst'), None)
        
        if financial_output:
            data = financial_output.get('data', {})
            
            # Financial health
            health = data.get('financial_health', {})
            if health:
                logger.info("")
                logger.info("🏥 Financial Health:")
                logger.info(f"   Score: {health.get('health_score', 0)}/100")
                logger.info(f"   Rating: {health.get('rating', 'Unknown')}")
            
            # Red flags
            red_flags = data.get('red_flags', [])
            if red_flags:
                logger.warning("")
                logger.warning("⚠️  Red Flags Identified:")
                for i, flag in enumerate(red_flags, 1):
                    logger.warning(f"   {i}. {flag}")
            
            # Recommendations
            recommendations = financial_output.get('recommendations', [])
            if recommendations:
                logger.info("")
                logger.info("💡 Recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    logger.info(f"   {i}. {rec}")
    else:
        logger.error("✗ Financial analysis failed")
        errors = state.get('errors', [])
        for error in errors:
            logger.error(f"   Error: {error}")
        return None
    
    # Generate Excel Report
    logger.info("")
    logger.info("📄 Generating Excel Report...")
    logger.info("   Creating worksheets:")
    logger.info("   - Executive Summary")
    logger.info("   - Financial Overview")
    logger.info("   - DCF Valuation Model")
    logger.info("   - Ratio Analysis")
    logger.info("   - Risk Assessment")
    logger.info("   - Assumptions & Methodology")
    
    try:
        generator = ExcelGenerator()
        report_path = generator.generate_full_report(state)
        
        logger.success(f"✓ Excel report generated!")
        logger.success(f"📊 Report location: {report_path}")
        logger.info("")
        logger.info("📂 Report includes:")
        logger.info("   ✓ Professional formatting with corporate colors")
        logger.info("   ✓ Transparent formulas (all calculations visible)")
        logger.info("   ✓ Charts and visualizations")
        logger.info("   ✓ Color-coded assessments")
        logger.info("   ✓ Risk identification")
        
    except Exception as e:
        logger.error(f"✗ Failed to generate report: {e}")
        return None
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.success("🎉 Demo Complete!")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("1. Open the Excel report to review the analysis")
    logger.info("2. Check the DCF model with transparent formulas")
    logger.info("3. Review the risk assessment and recommendations")
    logger.info("4. Customize the configuration in config/settings.yaml")
    logger.info("5. Add your own API keys in .env file")
    logger.info("")
    logger.info("For production use:")
    logger.info("- Implement remaining 6 agents")
    logger.info("- Add PDF report generation")
    logger.info("- Create interactive dashboard")
    logger.info("- Integrate document processing")
    logger.info("")
    
    return state


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("  M&A DILIGENCE SWARM - DEMO")
    print("  Autonomous AI-Powered Due Diligence System")
    print("="*60 + "\n")
    
    try:
        # Run the async demo
        state = asyncio.run(run_demo_analysis())
        
        if state:
            print("\n✅ Demo completed successfully!")
            print("Check the 'outputs' directory for the generated Excel report.")
        else:
            print("\n❌ Demo failed. Check the logs above for details.")
            print("\nCommon issues:")
            print("- Missing API keys in .env file")
            print("- Invalid ticker symbol")
            print("- API rate limits exceeded")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error in demo")


if __name__ == "__main__":
    main()
