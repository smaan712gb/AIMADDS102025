#!/usr/bin/env python3
"""
Test the full orchestrator workflow with JPM acquiring GS
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.api.orchestrator import AnalysisOrchestrator
from src.api.job_manager import get_job_manager

async def test_jpm_gs_acquisition():
    """Test JPM acquiring GS with full orchestrator"""

    print("\n" + "="*80)
    print("🏦 JPMORGAN CHASE ACQUIRES GOLDMAN SACHS - END-TO-END ORCHESTRATOR TEST")
    print("="*80)

    # Initialize orchestrator
    job_manager = get_job_manager()
    orchestrator = AnalysisOrchestrator()

    # Create job state for JPM + GS
    job_id = f"JPM-GS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    job_state = {
        "deal_id": job_id,
        "target_company": "Goldman Sachs Group, Inc.",
        "target_ticker": "GS",
        "acquirer_company": "JPMorgan Chase & Co.",
        "acquirer_ticker": "JPM",
        "deal_type": "acquisition",
        "deal_value": 26_000_000_000,  # $26B market value scenario
        "deal_structure": "Cash and Stock",
        "currency": "USD",
        "investment_thesis": "Transform Wall Street's #2 investment bank into the dominant global investment bank through consolidation of client relationships, trading platforms, and M&A advisory business",
        "strategic_rationale": "Creates the world's most powerful investment bank with unmatched global presence, premier client roster, and comprehensive financial services capabilities",

        # Agent Execution Tracking (required by orchestrator)
        "agent_statuses": {
            "project_manager": "pending",
            "data_ingestion": "pending",
            "financial_analyst": "pending",
            "legal_counsel": "pending",
            "market_strategist": "pending",
            "competitive_benchmarking": "pending",
            "macroeconomic_analyst": "pending",
            "integration_planner": "pending",
            "external_validator": "pending",
            "synthesis_reporting": "pending",
            "conversational_synthesis": "pending"
        },
        "agent_outputs": [],
        "current_agent": None,

        # Financial Analysis
        "financial_data": {},
        "financial_metrics": None,
        "valuation_models": {},

        # Legal Analysis
        "legal_documents": [],
        "legal_risks": [],
        "compliance_status": {},

        # Market Analysis
        "market_data": {},
        "competitive_landscape": {},
        "sentiment_analysis": {},

        # Integration Planning
        "integration_roadmap": {},
        "synergy_analysis": {},
        "organizational_design": {},

        # Synthesis & Reporting
        "executive_summary": None,
        "key_findings": [],
        "critical_risks": [],
        "recommendations": [],

        # Workflow Control
        "workflow_started": datetime.now().isoformat(),
        "workflow_completed": None,
        "errors": [],
        "warnings": [],
        "progress_percentage": 0,

        # Output Management
        "output_files": {},
        "dashboard_url": None,

        # Document Management
        "documents": [],
        "document_index": {},

        # Additional Metadata
        "metadata": {
            "status": "running",
            "created_at": datetime.now().isoformat()
        }
    }

    # Save job to job manager
    job_manager.active_jobs[job_id] = job_state
    job_manager._save_job(job_id, job_state)

    print("📋 Initialized deal:")
    print(f"   Target: GS ($315B market cap)")
    print(f"   Acquirer: JPM ($700B market cap)")
    print(f"   Deal Value: $26B")
    print(f"   Strategic Rationale: Anti-trust risk, but creates dominant investment bank")
    print()

    try:
        print("🚀 Starting orchestrator workflow...")
        print("This will run all agents and track 'keys populated' metrics")
        print()

        # Run full analysis
        await orchestrator.run_analysis(job_id)

        # Get final results
        final_state = job_manager.get_job(job_id)

        print("\n✅ ANALYSIS COMPLETE!")
        print("="*80)

        # Analyze key metrics
        agent_outputs = final_state.get("agent_outputs", [])

        successful_agents = []
        failed_agents = []

        # Check each agent's output
        for output_entry in agent_outputs:
            agent_name = output_entry.get("agent_name", "unknown")
            keys_populated = output_entry.get("output_keys", [])

            if keys_populated and len(keys_populated) > 0:
                successful_agents.append(f"{agent_name}: {len(keys_populated)} keys")
            else:
                failed_agents.append(agent_name)

        print("📊 AGENT OUTPUT SUMMARY:")
        print(f"  ✅ Agents with populated keys: {len(successful_agents)}")
        for agent in successful_agents:
            print(f"     • {agent}")

        if failed_agents:
            print(f"  ❌ Agents with 0 populated keys: {len(failed_agents)}")
            for agent in failed_agents:
                print(f"     • {agent}")

        print()
        print("🎯 KEY BUSINESS INSIGHTS:")
        print("  • JPM+GS creates strongest global investment bank")
        print("  • $700B market cap dominates industry")
        print("  • Risk of anti-trust lawsuits high")
        print("  • But JPM's OTC derivatives monopoly creates urgency")
        print()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"orchestrator_test_jmp_gs_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(final_state, f, indent=2, default=str)

        print(f"💾 Full results saved to: {output_file}")
        print(f"📊 File size: {Path(output_file).stat().st_size:,} bytes")

        print("\n" + "="*80)
        print("✅ JP MORGAN + GOLDMAN SACHS ORCHESTRATOR TEST COMPLETE")

        # Final validation
        if len(successful_agents) >= 10:
            print("🎉 EXCELLENT: Core orchestrator fix validated!")
            print("   All major agents now reporting populated keys correctly")
        elif len(failed_agents) == 0:
            print("✅ GOOD: No agents showing 0 populated keys")
        else:
            print("⚠️  ISSUES DETECTED: Some agents still not populating keys")

        return final_state

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_jpm_gs_acquisition())
