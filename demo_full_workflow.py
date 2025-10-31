"""
Demo: Full M&A Due Diligence Workflow
Shows Project Manager orchestration and Data Ingestion
"""
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

from src.core.state import create_initial_state, Document
from src.agents.project_manager import ProjectManagerAgent
from src.agents.data_ingestion import DataIngestionAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.outputs.excel_generator import ExcelGenerator


async def run_full_workflow():
    """Run complete M&A analysis workflow"""
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Full M&A Due Diligence Workflow")
    logger.info("=" * 60)
    
    # Step 1: Create initial state
    logger.info("\n📋 Step 1: Creating project state...")
    state = create_initial_state(
        deal_id="DEMO-2025-001",
        target_company="Microsoft Corporation",
        target_ticker="MSFT",
        acquirer_company="Hypothetical Acquirer",
        investment_thesis="Strategic acquisition to expand cloud computing capabilities and enterprise software portfolio",
        strategic_rationale="Gain access to Azure cloud platform, Office 365 ecosystem, and enterprise customer base",
        deal_type="acquisition",
        deal_value=500_000_000_000,  # $500B
        deal_structure="cash_and_stock",
        expected_close_date="2025-12-31"
    )
    
    logger.info(f"✅ Created project: {state['deal_id']}")
    logger.info(f"   Target: {state['target_company']}")
    logger.info(f"   Value: ${state['deal_value']:,.0f}")
    
    # Step 2: Initialize Project Manager
    logger.info("\n🎯 Step 2: Initializing Project Manager...")
    pm_agent = ProjectManagerAgent()
    state = await pm_agent.execute(state)
    
    # Show project plan
    workflow = state['metadata'].get("agent_workflow", [])
    logger.info(f"\n📋 Project Workflow:")
    for i, agent in enumerate(workflow, 1):
        logger.info(f"   {i}. {agent}")
    
    # Step 3: Add sample documents (if you have any)
    logger.info("\n📚 Step 3: Preparing documents...")
    
    # Check if sample documents exist
    sample_docs_dir = Path("data/raw")
    sample_docs = []
    
    if sample_docs_dir.exists():
        for file_path in sample_docs_dir.glob("*.*"):
            if file_path.suffix.lower() in ['.pdf', '.docx', '.txt']:
                doc = Document(
                    document_id=f"doc_{len(sample_docs)+1}",
                    filename=file_path.name,
                    filepath=str(file_path),
                    document_type="financial"  # You could auto-detect this
                )
                sample_docs.append(doc)
                logger.info(f"   Found: {file_path.name}")
    
    if sample_docs:
        state['documents'] = sample_docs
        logger.info(f"✅ Added {len(sample_docs)} documents for processing")
        
        # Step 4: Run Data Ingestion
        logger.info("\n📖 Step 4: Running Data Ingestion Agent...")
        ingestion_agent = DataIngestionAgent()
        state = await ingestion_agent.execute(state)
        
        # Show document catalog
        catalog = state['metadata'].get("document_catalog", {})
        logger.info(f"\n📊 Document Catalog:")
        logger.info(f"   Total Documents: {catalog.get('total_documents', 0)}")
        logger.info(f"   Total Words: {catalog.get('total_words', 0):,}")
        
        # Mark agent complete
        pm_agent.mark_agent_complete(state, "data_ingestion")
    else:
        logger.info("   No sample documents found in data/raw/")
        logger.info("   Skipping data ingestion step")
    
    # Step 5: Run Financial Analysis
    logger.info("\n💰 Step 5: Running Financial Analyst Agent...")
    financial_agent = FinancialAnalystAgent()
    state = await financial_agent.execute(state)
    
    # Mark agent complete
    pm_agent.mark_agent_complete(state, "financial_analyst")
    
    # Show key findings
    if state['financial_data']:
        logger.info(f"\n📈 Financial Analysis Complete:")
        logger.info(f"   Revenue: ${state['financial_data'].get('revenue', 0):,.0f}")
        logger.info(f"   Net Income: ${state['financial_data'].get('net_income', 0):,.0f}")
        logger.info(f"   Total Assets: ${state['financial_data'].get('total_assets', 0):,.0f}")
    
    # Step 6: Show Project Progress
    logger.info("\n📊 Step 6: Project Progress Summary...")
    progress = pm_agent.get_progress_summary(state)
    logger.info(f"   Overall Progress: {progress['overall_progress']}")
    logger.info(f"   Status: {progress['status']}")
    logger.info(f"   Completed Agents: {', '.join(progress['completed_agents'])}")
    
    # Step 7: Generate Reports
    logger.info("\n📄 Step 7: Generating Reports...")
    generator = ExcelGenerator()
    
    try:
        report_path = generator.generate_full_report(state)
        logger.info(f"✅ Excel report generated: {report_path}")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
    
    # Final Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ WORKFLOW COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nDeal ID: {state['deal_id']}")
    logger.info(f"Target: {state['target_company']}")
    logger.info(f"Status: {progress['status']}")
    logger.info(f"\nNext Steps:")
    logger.info("  1. Review generated Excel report in outputs/")
    logger.info("  2. Complete remaining agent analyses")
    logger.info("  3. Generate final synthesis report")
    
    if state['errors']:
        logger.warning(f"\n⚠️  {len(state['errors'])} errors encountered during workflow")
        for error in state['errors']:
            logger.warning(f"   - {error.get('agent')}: {error.get('error')}")
    
    return state


def main():
    """Main entry point"""
    logger.info("\n🔍 Full M&A Due Diligence System Demo\n")
    
    try:
        # Run async workflow
        state = asyncio.run(run_full_workflow())
        
        logger.info("\n✅ Demo completed successfully!")
        logger.info("\nCheck the 'outputs' directory for generated reports.")
        logger.info("Check the 'data/gcs_local' directory for stored documents.")
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
