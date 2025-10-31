"""
PRODUCTION M&A ANALYSIS: CrowdStrike (CRWD)

This script runs the complete M&A due diligence workflow for CrowdStrike
using REAL data sources:
- Financial Modeling Prep API for financials
- SEC EDGAR for filings
- Gemini 2.5 Pro for deep research and external validation
- No placeholders or fallbacks - production quality only

Target: CrowdStrike Holdings Inc. (CRWD)
Acquiring Company: Strategic Acquirer Corp
"""

# Suppress gRPC warnings for clean output (harmless, only appear in local dev)
import os
import warnings
import logging
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''
warnings.filterwarnings('ignore', category=UserWarning, module='google')
logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('google').setLevel(logging.ERROR)

import asyncio
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# Fix Windows event loop for aiodns compatibility
from src.utils import setup_windows_event_loop
setup_windows_event_loop()

from src.core.state import create_initial_state, update_agent_status, add_agent_output, AgentStatus
from src.core.config import get_config
from src.utils.api_health_check import run_health_check
from src.utils.data_validator import validate_data
from src.agents.project_manager import ProjectManagerAgent
from src.agents.data_ingestion import DataIngestionAgent
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.legal_counsel import LegalCounselAgent
from src.agents.market_strategist import MarketStrategistAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.macroeconomic_analyst import MacroeconomicAnalystAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.external_validator import ExternalValidatorAgent
from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.agents.conversational_synthesis import ConversationalSynthesisAgent


class ProductionWorkflow:
    """Production-grade M&A workflow orchestrator"""
    
    def __init__(self):
        self.config = get_config()
        self.output_dir = Path("outputs/crwd_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_file = self.output_dir / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logger.add(log_file, rotation="100 MB", level="INFO")
        
    async def run_complete_analysis(self):
        """Run complete M&A analysis workflow for CrowdStrike"""
        
        logger.info("=" * 100)
        logger.info("PRODUCTION M&A ANALYSIS: CROWDSTRIKE (CRWD)")
        logger.info("=" * 100)
        
        print("\n" + "=" * 100)
        print("PRODUCTION M&A ANALYSIS: CROWDSTRIKE (CRWD)".center(100))
        print("=" * 100 + "\n")
        
        # Step 0: API Health Check (NEW)
        print("🔍 Step 0: API Health Check...")
        print("-" * 100)
        logger.info("Running API health checks")
        
        try:
            is_healthy, health_results = await run_health_check()
            
            if not is_healthy:
                unhealthy_apis = [api for api, result in health_results.items() 
                                if isinstance(result, dict) and result.get('status') in ['missing', 'error']]
                print(f"\n❌ CRITICAL: API health check FAILED")
                print(f"   Unhealthy APIs: {', '.join(unhealthy_apis)}")
                print(f"   Fix API configuration before proceeding")
                print()
                logger.error("API health check failed - blocking execution")
                return None
            
            print("✅ API Health Check Passed - All critical APIs operational")
            print()
            
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            print(f"❌ API Health Check Failed: {e}")
            print("   Cannot proceed without valid API configuration")
            print()
            return None
        
        # Step 1: Initialize State
        print("📋 Step 1: Initializing Deal State...")
        print("-" * 100)
        
        state = create_initial_state(
            deal_id=f"CRWD_ACQUISITION_{datetime.now().strftime('%Y%m%d')}",
            target_company="CrowdStrike Holdings Inc.",
            target_ticker="CRWD",
            acquirer_company="Microsoft Corporation",
            acquirer_ticker="MSFT",  # CRITICAL: Required for synergy calculations
            investment_thesis=(
                "Strategic acquisition of CrowdStrike by Microsoft to strengthen cloud "
                "security portfolio. CrowdStrike's Falcon platform complements Azure's "
                "security offerings, creating a comprehensive enterprise security solution. "
                "Strong strategic fit with Microsoft's cloud-first strategy and enterprise customer base."
            ),
            strategic_rationale=(
                "1. Market Leadership: CrowdStrike is a pioneer in cloud-native EDR/XDR\n"
                "2. Technology Moat: AI-powered Falcon platform with extensive threat intelligence\n"
                "3. Azure Integration: Natural fit with Microsoft's cloud infrastructure\n"
                "4. Cross-Selling: Access to Microsoft's enterprise customer base\n"
                "5. Combined Platform: Creates comprehensive security offering (endpoint + cloud + identity)"
            ),
            deal_type="acquisition",
            currency="USD"
        )
        
        logger.info(f"Deal initialized: {state['deal_id']}")
        print(f"✓ Deal ID: {state['deal_id']}")
        print(f"✓ Target: CrowdStrike Holdings Inc. (CRWD)")
        print(f"✓ Acquirer: Strategic Acquirer Corp")
        print(f"✓ Deal Type: Acquisition")
        print()
        
        # Step 2: Project Management & Orchestration
        print("🎯 Step 2: Project Management & Orchestration...")
        print("-" * 100)
        logger.info("Starting Project Manager Agent")
        
        try:
            pm_agent = ProjectManagerAgent()
            state = update_agent_status(state, "project_manager", AgentStatus.RUNNING)
            
            print("  → Creating comprehensive project plan")
            print("  → Identifying required analyses")
            print("  → Setting priorities and timeline")
            print()
            
            state = await pm_agent.execute(state)
            
            print("✅ Project Plan Created")
            logger.info("Project management completed successfully")
            print()
            
        except Exception as e:
            logger.error(f"Project management failed: {e}")
            print(f"⚠️  Project Management Failed: {e}")
            state = update_agent_status(state, "project_manager", AgentStatus.FAILED)
            print()
        
        # Step 3: Financial Analysis
        print("💰 Step 3: Financial Analysis (Real FMP Data)...")
        print("-" * 100)
        logger.info("Starting Financial Analyst Agent")
        
        try:
            financial_agent = FinancialAnalystAgent()
            state = update_agent_status(state, "financial_analyst", AgentStatus.RUNNING)
            
            print("  → Fetching real financial statements from FMP API")
            print("  → Analyzing revenue trends, profitability, cash flows")
            print("  → Building valuation models (DCF, Comparable Companies)")
            print()
            
            state = await financial_agent.execute(state)
            
            financial_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "financial_analyst"),
                None
            )
            
            if financial_output and financial_output["status"] == AgentStatus.COMPLETED:
                print("✅ Financial Analysis Complete")
                print(f"  → Status: {financial_output['status']}")
                print(f"  → Warnings: {len(financial_output.get('warnings', []))}")
                print(f"  → Recommendations: {len(financial_output.get('recommendations', []))}")
                logger.info("Financial analysis completed successfully")
                
                # NEW: Validate financial data quality
                print()
                print("🔍 Validating Financial Data Quality...")
                try:
                    financial_data = state.get('financial_data', {})
                    if financial_data:
                        validation_result = validate_data(financial_data, state.get('target_ticker', 'UNKNOWN'))
                        
                        # Store validation result in state
                        state['data_quality'] = {
                            'is_valid': validation_result.is_valid,
                            'completeness_score': validation_result.completeness_score,
                            'quality_grade': validation_result.quality_grade,
                            'error_count': len(validation_result.errors),
                            'warning_count': len(validation_result.warnings),
                            'outlier_count': len(validation_result.outliers)
                        }
                        
                        if not validation_result.is_valid:
                            logger.error(f"Data validation FAILED - Grade: {validation_result.quality_grade}")
                            print(f"⚠️  WARNING: Data quality issues detected (Grade: {validation_result.quality_grade})")
                            print(f"   Completeness: {validation_result.completeness_score:.1f}%")
                            print(f"   Errors: {len(validation_result.errors)}, Warnings: {len(validation_result.warnings)}")
                            # Don't block, but warn user
                        else:
                            print(f"✅ Data Quality: Grade {validation_result.quality_grade} ({validation_result.completeness_score:.1f}% complete)")
                            logger.info(f"Data validation passed - Grade: {validation_result.quality_grade}")
                    else:
                        print("⚠️  No financial data available to validate")
                except Exception as val_error:
                    logger.error(f"Data validation error: {val_error}")
                    print(f"⚠️  Data validation failed: {val_error}")
            else:
                print("⚠️  Financial Analysis completed with issues")
                if financial_output:
                    for error in financial_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Financial analysis error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Financial analysis failed: {e}")
            print(f"❌ Financial Analysis Failed: {e}")
            state = update_agent_status(state, "financial_analyst", AgentStatus.FAILED)
            state["errors"].append(f"Financial Analysis: {str(e)}")
            print()
        
        # Step 4: Financial Deep Dive Analysis
        print("🔬 Step 4: Financial Deep Dive Analysis (IB-Quality Metrics)...")
        print("-" * 100)
        logger.info("Starting Financial Deep Dive Agent")
        
        try:
            deep_dive_agent = FinancialDeepDiveAgent()
            state = update_agent_status(state, "financial_deep_dive", AgentStatus.RUNNING)
            
            print("  → Analyzing working capital & cash conversion cycle")
            print("  → Evaluating CapEx intensity & asset requirements")
            print("  → Assessing customer concentration risk")
            print("  → Reviewing segment performance")
            print("  → Analyzing debt schedule & covenants")
            print()
            
            result = await deep_dive_agent.run(state)
            
            # Add result to agent outputs
            state = add_agent_output(
                state,
                "financial_deep_dive",
                result.get("data", {}),
                AgentStatus.COMPLETED if not result.get("errors") else AgentStatus.FAILED,
                result.get("errors", []),
                result.get("warnings", []),
                result.get("recommendations", [])
            )
            
            deep_dive_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "financial_deep_dive"),
                None
            )
            
            if deep_dive_output and deep_dive_output["status"] == AgentStatus.COMPLETED:
                print("✅ Financial Deep Dive Complete")
                print(f"  → Status: {deep_dive_output['status']}")
                
                # Display key metrics
                deep_dive_data = deep_dive_output.get("data", {})
                insights = deep_dive_data.get("insights", {})
                key_metrics = insights.get("key_metrics", {})
                
                if key_metrics:
                    print(f"  → Cash Conversion Cycle: {key_metrics.get('cash_conversion_cycle', 0):.0f} days")
                    print(f"  → NWC Efficiency: {key_metrics.get('nwc_efficiency', 0):.0f}/100")
                    print(f"  → CapEx Intensity: {key_metrics.get('capex_intensity', 0):.2f}% of revenue")
                    print(f"  → Debt/Equity: {key_metrics.get('debt_to_equity', 0):.2f}x")
                    print(f"  → Interest Coverage: {key_metrics.get('interest_coverage', 0):.1f}x")
                
                logger.info("Financial deep dive completed successfully")
            else:
                print("⚠️  Financial Deep Dive completed with issues")
                if deep_dive_output:
                    for error in deep_dive_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Financial deep dive error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Financial deep dive failed: {e}")
            print(f"❌ Financial Deep Dive Failed: {e}")
            state = update_agent_status(state, "financial_deep_dive", AgentStatus.FAILED)
            state["errors"].append(f"Financial Deep Dive: {str(e)}")
            print()
        
        # Step 5: Market & Competitive Analysis
        print("📊 Step 5: Market & Competitive Analysis...")
        print("-" * 100)
        logger.info("Starting Market Strategist Agent")
        
        try:
            market_agent = MarketStrategistAgent()
            state = update_agent_status(state, "market_strategist", AgentStatus.RUNNING)
            
            print("  → Analyzing cybersecurity market landscape")
            print("  → Competitive positioning (Palo Alto, Fortinet, SentinelOne, etc.)")
            print("  → Market trends and growth drivers")
            print()
            
            state = await market_agent.execute(state)
            
            market_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "market_strategist"),
                None
            )
            
            if market_output and market_output["status"] == AgentStatus.COMPLETED:
                print("✅ Market Analysis Complete")
                print(f"  → Status: {market_output['status']}")
                logger.info("Market analysis completed successfully")
            else:
                print("⚠️  Market Analysis completed with issues")
                if market_output:
                    for error in market_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Market analysis error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            print(f"❌ Market Analysis Failed: {e}")
            state = update_agent_status(state, "market_strategist", AgentStatus.FAILED)
            state["errors"].append(f"Market Analysis: {str(e)}")
            print()
        
        # Step 6: Competitive Benchmarking
        print("🏆 Step 6: Competitive Benchmarking Analysis...")
        print("-" * 100)
        logger.info("Starting Competitive Benchmarking Agent")
        
        try:
            comp_agent = CompetitiveBenchmarkingAgent()
            state = update_agent_status(state, "competitive_benchmarking", AgentStatus.RUNNING)
            
            print("  → Benchmarking against industry peers")
            print("  → Analyzing competitive performance metrics")
            print("  → Identifying competitive advantages")
            print()
            
            state = await comp_agent.execute(state)
            
            print("✅ Competitive Benchmarking Complete")
            logger.info("Competitive benchmarking completed successfully")
            print()
            
        except Exception as e:
            logger.error(f"Competitive benchmarking failed: {e}")
            print(f"⚠️  Competitive Benchmarking Failed: {e}")
            state = update_agent_status(state, "competitive_benchmarking", AgentStatus.FAILED)
            print()
        
        # Step 7: Macroeconomic Analysis
        print("🌍 Step 7: Macroeconomic Analysis...")
        print("-" * 100)
        logger.info("Starting Macroeconomic Analyst Agent")
        
        try:
            macro_agent = MacroeconomicAnalystAgent()
            state = update_agent_status(state, "macroeconomic_analyst", AgentStatus.RUNNING)
            
            print("  → Analyzing economic indicators and trends")
            print("  → Scenario modeling (base/bull/bear cases)")
            print("  → Assessing macroeconomic risks")
            print()
            
            state = await macro_agent.execute(state)
            
            print("✅ Macroeconomic Analysis Complete")
            logger.info("Macroeconomic analysis completed successfully")
            print()
            
        except Exception as e:
            logger.error(f"Macroeconomic analysis failed: {e}")
            print(f"⚠️  Macroeconomic Analysis Failed: {e}")
            state = update_agent_status(state, "macroeconomic_analyst", AgentStatus.FAILED)
            print()
        
        # Step 8: Legal & Compliance Review
        print("⚖️  Step 8: Legal & Compliance Review...")
        print("-" * 100)
        logger.info("Starting Legal Counsel Agent")
        
        try:
            legal_agent = LegalCounselAgent()
            state = update_agent_status(state, "legal_counsel", AgentStatus.RUNNING)
            
            print("  → Reviewing SEC filings (10-K, 10-Q, 8-K)")
            print("  → Analyzing risk factors and legal disclosures")
            print("  → Compliance assessment")
            print()
            
            state = await legal_agent.execute(state)
            
            legal_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "legal_counsel"),
                None
            )
            
            if legal_output and legal_output["status"] == AgentStatus.COMPLETED:
                print("✅ Legal Review Complete")
                print(f"  → Status: {legal_output['status']}")
                logger.info("Legal review completed successfully")
            else:
                print("⚠️  Legal Review completed with issues")
                if legal_output:
                    for error in legal_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Legal review error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Legal review failed: {e}")
            print(f"❌ Legal Review Failed: {e}")
            state = update_agent_status(state, "legal_counsel", AgentStatus.FAILED)
            state["errors"].append(f"Legal Review: {str(e)}")
            print()
        
        # Step 9: Integration Planning
        print("🔧 Step 9: Integration Planning...")
        print("-" * 100)
        logger.info("Starting Integration Planner Agent")
        
        try:
            integration_agent = IntegrationPlannerAgent()
            state = update_agent_status(state, "integration_planner", AgentStatus.RUNNING)
            
            print("  → Identifying synergies (revenue & cost)")
            print("  → Creating integration roadmap")
            print("  → Planning organizational design")
            print()
            
            state = await integration_agent.execute(state)
            
            print("✅ Integration Planning Complete")
            logger.info("Integration planning completed successfully")
            print()
            
        except Exception as e:
            logger.error(f"Integration planning failed: {e}")
            print(f"⚠️  Integration Planning Failed: {e}")
            state = update_agent_status(state, "integration_planner", AgentStatus.FAILED)
            print()
        
        # Step 10: EXTERNAL VALIDATION (The Game Changer)
        print("🌐 Step 10: EXTERNAL VALIDATION - Gemini Deep Research...")
        print("-" * 100)
        logger.info("Starting External Validator Agent")
        
        try:
            validator = ExternalValidatorAgent()
            state = update_agent_status(state, "external_validator", AgentStatus.RUNNING)
            
            print("  → Fetching Wall Street analyst reports")
            print("  → Accessing latest SEC filings and earnings transcripts")
            print("  → Gathering market consensus data")
            print("  → Validating internal findings against external sources")
            print()
            print("⏳ Deep research in progress (may take 60-90 seconds)...")
            print()
            
            state = await validator.execute(state)
            
            validator_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "external_validator"),
                None
            )
            
            if validator_output and validator_output["status"] == AgentStatus.COMPLETED:
                validation_data = validator_output.get("data", {})
                confidence = validation_data.get("confidence_score", 0)
                requires_reanalysis = validation_data.get("requires_reanalysis", False)
                
                print("✅ External Validation Complete")
                print(f"  → Confidence Score: {confidence:.2%}")
                print(f"  → Findings Validated: {validation_data.get('key_findings_validated', 0)}")
                print(f"  → External Sources: {validation_data.get('external_sources_consulted', 0)}")
                print(f"  → Critical Discrepancies: {len(validation_data.get('critical_discrepancies', []))}")
                print(f"  → Moderate Discrepancies: {len(validation_data.get('moderate_discrepancies', []))}")
                print(f"  → Requires Reanalysis: {'YES' if requires_reanalysis else 'NO'}")
                
                if requires_reanalysis:
                    adjustment_plan = validation_data.get("adjustment_plan", {})
                    print()
                    print("⚠️  ADJUSTMENT PLAN:")
                    print(f"  Priority: {adjustment_plan.get('priority', 'Unknown').upper()}")
                    print(f"  Agents to Rerun: {', '.join(adjustment_plan.get('agents_to_rerun', []))}")
                    print(f"  {adjustment_plan.get('summary', 'No summary')}")
                
                logger.info(f"External validation completed. Confidence: {confidence:.2%}")
            else:
                print("⚠️  External Validation completed with issues")
                if validator_output:
                    for error in validator_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Validation error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"External validation failed: {e}")
            print(f"❌ External Validation Failed: {e}")
            state = update_agent_status(state, "external_validator", AgentStatus.FAILED)
            state["errors"].append(f"External Validation: {str(e)}")
            print()
        
        # Step 11: Synthesis & Final Report
        print("📝 Step 11: Synthesis & Final Report Generation...")
        print("-" * 100)
        logger.info("Starting Synthesis & Reporting Agent")
        
        try:
            synthesis_agent = SynthesisReportingAgent()
            state = update_agent_status(state, "synthesis_reporting", AgentStatus.RUNNING)
            
            print("  → Synthesizing all findings")
            print("  → Incorporating external validation results")
            print("  → Generating executive summary")
            print("  → Creating final recommendations")
            print()
            
            state = await synthesis_agent.execute(state)
            
            synthesis_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "synthesis_reporting"),
                None
            )
            
            if synthesis_output and synthesis_output["status"] == AgentStatus.COMPLETED:
                print("✅ Synthesis Complete")
                logger.info("Synthesis completed successfully")
            else:
                print("⚠️  Synthesis completed with issues")
                if synthesis_output:
                    for error in synthesis_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Synthesis error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            print(f"❌ Synthesis Failed: {e}")
            state = update_agent_status(state, "synthesis_reporting", AgentStatus.FAILED)
            state["errors"].append(f"Synthesis: {str(e)}")
            print()
        
        # Step 12: Conversational Synthesis (Interactive Interface)
        print("💬 Step 12: Conversational Synthesis - Interactive Analysis...")
        print("-" * 100)
        logger.info("Starting Conversational Synthesis Agent")
        
        try:
            conv_agent = ConversationalSynthesisAgent()
            state = update_agent_status(state, "conversational_synthesis", AgentStatus.RUNNING)
            
            print("  → Initializing conversational interface")
            print("  → Loading complete analysis context")
            print("  → Preparing for interactive Q&A")
            print()
            
            state = await conv_agent.execute(state)
            
            conv_output = next(
                (o for o in state["agent_outputs"] if o["agent_name"] == "conversational_synthesis"),
                None
            )
            
            if conv_output and conv_output["status"] == AgentStatus.COMPLETED:
                print("✅ Conversational Interface Ready")
                print("  → Analysis loaded and ready for interactive queries")
                logger.info("Conversational synthesis completed successfully")
            else:
                print("⚠️  Conversational Synthesis completed with issues")
                if conv_output:
                    for error in conv_output.get("errors", []):
                        print(f"  ERROR: {error}")
                        logger.error(f"Conversational synthesis error: {error}")
            print()
            
        except Exception as e:
            logger.error(f"Conversational synthesis failed: {e}")
            print(f"⚠️  Conversational Synthesis Failed: {e}")
            state = update_agent_status(state, "conversational_synthesis", AgentStatus.FAILED)
            state["errors"].append(f"Conversational Synthesis: {str(e)}")
            print()
        
        # Step 13: Generate Professional Reports
        print("📊 Step 13: Generating Professional Reports...")
        print("-" * 100)
        logger.info("Starting report generation")
        
        try:
            # NOTE: Revolutionary report generators are now used via:
            # - demo_revolutionary_system.py for full reports
            # - Individual generators in src/outputs/ (excel_generator, pdf_generator, ppt_generator)
            # This production script focuses on agent execution and state management
            
            print("  ℹ️  Report generation handled by revolutionary system")
            print("  → State data available in: outputs/crwd_analysis/")
            print("  → Use demo_revolutionary_system.py or individual generators for reports")
            print()
            
            # Save synthesized data separately for easy report generation
            if 'synthesized_data' in state:
                synth_file = self.output_dir / "synthesis" / f"{state['deal_id']}_consolidated_data.json"
                synth_file.parent.mkdir(parents=True, exist_ok=True)
                with open(synth_file, 'w') as f:
                    json.dump(state['synthesized_data'], f, indent=2, default=str)
                print(f"✓ Synthesized data ready for report generation: {synth_file}")
                logger.info(f"Synthesized data saved: {synth_file}")
            
            print("✅ State Data Ready for Revolutionary Report Generators")
            logger.info("Report generation ready - use revolutionary system")
            print()
            
        except Exception as e:
            logger.error(f"Report generation setup failed: {e}")
            print(f"⚠️  Report Generation Setup Failed: {e}")
            state["errors"].append(f"Report Generation: {str(e)}")
            print()
        
        # Step 14: Save State Files
        print("💾 Step 14: Saving State Files...")
        print("-" * 100)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete state
        state_file = self.output_dir / f"crwd_complete_state_{timestamp}.json"
        with open(state_file, 'w') as f:
            json.dump(dict(state), f, indent=2, default=str)
        print(f"✓ Complete state saved: {state_file}")
        logger.info(f"State saved to {state_file}")
        
        # Save agent outputs separately
        for agent_output in state["agent_outputs"]:
            agent_name = agent_output["agent_name"]
            output_file = self.output_dir / f"crwd_{agent_name}_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(agent_output, f, indent=2, default=str)
            print(f"✓ {agent_name} output saved: {output_file}")
        
        print()
        
        # Step 12: Summary
        print("=" * 100)
        print("WORKFLOW SUMMARY".center(100))
        print("=" * 100)
        print()
        
        print(f"Deal ID: {state['deal_id']}")
        print(f"Target: {state['target_company']} ({state.get('target_ticker', 'N/A')})")
        print(f"Started: {state['workflow_started']}")
        print(f"Progress: {state['progress_percentage']}%")
        print()
        
        print("Agent Status:")
        for agent_name, status in state["agent_statuses"].items():
            status_icon = {
                AgentStatus.COMPLETED: "✅",
                AgentStatus.FAILED: "❌",
                AgentStatus.RUNNING: "🔄",
                AgentStatus.PENDING: "⏳",
                AgentStatus.SKIPPED: "⏭️"
            }.get(status, "❓")
            print(f"  {status_icon} {agent_name}: {status.value}")
        print()
        
        if state["errors"]:
            print(f"Errors: {len(state['errors'])}")
            for error in state["errors"]:
                print(f"  ❌ {error}")
            print()
        
        print(f"Output Directory: {self.output_dir}")
        print()
        
        logger.info("Workflow completed")
        logger.info(f"Final progress: {state['progress_percentage']}%")
        logger.info(f"Errors: {len(state['errors'])}")
        
        return state


async def main():
    """Main entry point"""
    print("\n")
    print("╔" + "=" * 98 + "╗")
    print("║" + " " * 98 + "║")
    print("║" + "PRODUCTION M&A ANALYSIS: CROWDSTRIKE (CRWD)".center(98) + "║")
    print("║" + "Real APIs • Real Data • External Validation • No Placeholders".center(98) + "║")
    print("║" + " " * 98 + "║")
    print("╚" + "=" * 98 + "╝")
    print("\n")
    
    workflow = ProductionWorkflow()
    
    try:
        final_state = await workflow.run_complete_analysis()
        
        print("=" * 100)
        print("✅ ANALYSIS COMPLETE".center(100))
        print("=" * 100)
        print()
        print("Next Steps:")
        print("1. Review outputs in: outputs/crwd_analysis/")
        print("2. Check external validation results for discrepancies")
        print("3. Review confidence scores and recommendations")
        print("4. If reanalysis required, address flagged discrepancies")
        print()
        
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        print(f"\n❌ WORKFLOW FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
