"""
Analysis orchestrator - coordinates agents and sends real-time updates
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Set, List
import copy
from loguru import logger

from src.api.job_manager import get_job_manager
from src.api.models import AgentStatusEnum
from src.core.state import update_agent_status, AgentStatus

# Import quality control systems
from src.utils.api_health_check import run_health_check
from src.utils.data_validator import validate_data

# Import all agents
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
from src.agents.risk_assessment import RiskAssessmentAgent
from src.agents.tax_structuring import TaxStructuringAgent
from src.agents.deal_structuring import DealStructuringAgent
from src.agents.accretion_dilution import AccretionDilutionAgent
from src.agents.sources_uses import SourcesUsesGenerator
from src.agents.contribution_analysis import ContributionAnalyzer
from src.agents.exchange_ratio_analysis import ExchangeRatioAnalyzer
from src.agents.synthesis_reporting import SynthesisReportingAgent
# Import FMP client for agents that need it
from src.integrations.fmp_client import FMPClient
# Import symbol validator
from src.utils.symbol_validator import SymbolValidator
# Import report generators (using revolutionary generators)
try:
    from src.outputs.report_generator import ReportGenerator
    REPORT_AVAILABLE = True
except ImportError as e:
    ReportGenerator = None
    REPORT_AVAILABLE = False

# Import M&A report generator
try:
    from src.outputs.ma_report_generator import MAReportGenerator
    MA_REPORTS_AVAILABLE = True
except ImportError as e:
    MAReportGenerator = None
    MA_REPORTS_AVAILABLE = False
    logger.warning("M&A Report Generator not available")


class AnalysisOrchestrator:
    """Orchestrates the complete analysis workflow"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.job_manager = get_job_manager()
        self.report_generator = ReportGenerator() if REPORT_AVAILABLE else None
        
        # Agent status messages for UI
        self.agent_messages = {}  # Will be populated dynamically or use defaults
    
    def _validate_agent_prerequisites(self, state: Dict[str, Any], agent_key: str) -> tuple[bool, List[str]]:
        """
        Check if agent has required data to run
        
        Args:
            state: Current diligence state
            agent_key: Agent identifier
            
        Returns:
            Tuple of (can_run: bool, missing_fields: list)
        """
        # Define prerequisites for each agent
        prerequisites = {
            'sources_uses': {
                'required': ['deal_value'],
                'optional': ['deal_terms', 'financial_data']
            },
            'accretion_dilution': {
                'required': ['acquirer_data', 'deal_value'],
                'optional': ['deal_terms']
            },
            'exchange_ratio_analysis': {
                'required': ['acquirer_data', 'valuation_models'],
                'optional': ['deal_terms']
            },
            'contribution_analysis': {
                'required': ['acquirer_data', 'valuation_models'],
                'optional': ['deal_terms']
            }
        }
        
        # If agent doesn't have prerequisites defined, it can always run
        if agent_key not in prerequisites:
            return True, []
        
        reqs = prerequisites[agent_key]['required']
        missing = []
        
        for field in reqs:
            value = state.get(field)
            # Check if field exists and has meaningful data
            if not value or (isinstance(value, dict) and not value) or (isinstance(value, list) and not value):
                missing.append(field)
        
        if missing:
            logger.error(f"❌ {agent_key} missing required data: {missing}")
            return False, missing
        
        logger.info(f"✓ {agent_key} prerequisites validated")
        return True, []
    
    async def run_analysis(self, job_id: str):
        """Run complete analysis workflow
        
        Args:
            job_id: Job ID to run
        """
        try:
            logger.info(f"Starting analysis for job {job_id}")
            
            # Get job state
            state = self.job_manager.get_job(job_id)
            if not state:
                logger.error(f"Job {job_id} not found")
                return
            
            # STEP 0: API Health Check - Validate all API credentials BEFORE starting
            logger.info("Running API health check...")
            try:
                is_healthy, health_results = await run_health_check()
                
                if not is_healthy:
                    unhealthy_apis = []
                    for api, result in health_results.items():
                        if isinstance(result, dict) and result.get('status') in ['missing', 'error']:
                            unhealthy_apis.append(api)
                    
                    error_msg = f"API health check failed: {', '.join(unhealthy_apis)} unavailable"
                    logger.error(error_msg)
                    
                    # Abort analysis
                    state['metadata']['status'] = 'failed'
                    state['errors'].append(error_msg)
                    self.job_manager._save_job(job_id, state)
                    
                    await self.job_manager.broadcast_update(job_id, {
                        "type": "validation_error",
                        "job_id": job_id,
                        "data": {
                            "message": "API Configuration Error",
                            "error": error_msg,
                            "details": [
                                "One or more critical APIs are unavailable.",
                                "Please verify API key configuration in .env file.",
                                f"Unhealthy APIs: {', '.join(unhealthy_apis)}"
                            ]
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    logger.error(f"Analysis aborted for job {job_id} due to API health check failure")
                    return
                
                logger.info("✓ API health check passed - all critical APIs operational")
                
            except Exception as health_error:
                logger.error(f"API health check error: {health_error}")
                # Non-blocking - log warning but proceed
                logger.warning("Proceeding with analysis despite health check error")
            
            # CRITICAL: Validate ticker symbol BEFORE starting analysis using async context manager
            target_ticker = state.get('target_ticker', '')
            logger.info(f"Validating ticker symbol: {target_ticker}")
            
            # Use FMP client with async context manager for validation
            async with FMPClient() as fmp_client:
                is_valid, validation_message, company_info = await SymbolValidator.validate_symbol(
                    target_ticker, 
                    fmp_client
                )
                
                # Try to suggest corrections if invalid
                suggestions = []
                if not is_valid:
                    suggestions = await SymbolValidator.suggest_corrections(target_ticker, fmp_client)
            
            # Process validation result (outside context manager)
            if not is_valid:
                # Symbol validation failed - abort analysis
                error_msg = f"❌ Symbol validation failed: {validation_message}"
                logger.error(error_msg)
                
                if suggestions:
                    suggestion_text = f"\n\nDid you mean: {', '.join(suggestions)}?"
                    error_msg += suggestion_text
                    logger.info(f"Suggested corrections: {suggestions}")
                
                # Update state with error
                state['metadata']['status'] = 'failed'
                state['errors'].append(error_msg)
                self.job_manager._save_job(job_id, state)
                
                # Send error notification
                await self.job_manager.broadcast_update(job_id, {
                    "type": "validation_error",
                    "job_id": job_id,
                    "data": {
                        "message": "Invalid Ticker Symbol",
                        "error": validation_message,
                        "suggestions": suggestions,
                        "details": [
                            f"The ticker '{target_ticker}' could not be found or validated.",
                            "Please verify the ticker symbol and try again.",
                            "Suggestions are provided if similar tickers were found."
                        ]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.error(f"Analysis aborted for job {job_id} due to invalid ticker: {target_ticker}")
                return
            
            # Symbol is valid - log company info and proceed
            logger.info(f"✓ Symbol validation passed: {validation_message}")
            logger.info(f"  Company: {company_info.get('name')}")
            logger.info(f"  Market Cap: ${company_info.get('market_cap', 0)/1e9:.1f}B")
            logger.info(f"  Sector: {company_info.get('sector')}")
            logger.info(f"  Exchange: {company_info.get('exchange')}")
            
            # Store validated company info in state
            state['validated_company_info'] = company_info
            state['target_company'] = company_info.get('name', state.get('target_company'))
            
            # Note: FMP client will be initialized by each agent individually using async context manager
            
            # Update status to running
            state['metadata']['status'] = 'running'
            self.job_manager._save_job(job_id, state)
            
            # Initialize agent_outputs array for structured collection
            if 'agent_outputs' not in state:
                state['agent_outputs'] = []

            # Run agents sequentially with updates (OPTIMAL WORKFLOW ORDER)
            agents_to_run = [
                ("project_manager", ProjectManagerAgent()),
                ("data_ingestion", None),  # Not implemented yet, skip
                ("financial_analyst", FinancialAnalystAgent()),
                ("financial_deep_dive", FinancialDeepDiveAgent()),
                ("deal_structuring", DealStructuringAgent()),  # Deal structure optimization
                ("sources_uses", SourcesUsesGenerator()),  # NEW: Sources & uses of funds
                ("legal_counsel", LegalCounselAgent()),
                ("market_strategist", MarketStrategistAgent()),
                ("competitive_benchmarking", CompetitiveBenchmarkingAgent()),
                ("macroeconomic_analyst", MacroeconomicAnalystAgent()),
                ("risk_assessment", RiskAssessmentAgent()),  # Aggregates all risks
                ("tax_structuring", TaxStructuringAgent()),  # Tax analysis
                ("accretion_dilution", AccretionDilutionAgent()),  # EPS accretion/dilution analysis
                ("contribution_analysis", ContributionAnalyzer()),  # NEW: Value contribution analysis
                ("exchange_ratio_analysis", ExchangeRatioAnalyzer()),  # NEW: Exchange ratio fairness
                ("integration_planner", IntegrationPlannerAgent()),  # Uses all prior data + synergies
                ("external_validator", ExternalValidatorAgent()),  # Validates everything
                ("synthesis_reporting", SynthesisReportingAgent())  # Final consolidation
            ]
            
            for agent_key, agent_instance in agents_to_run:
                # CRITICAL FIX: Validate prerequisites before running agent
                can_run, missing_fields = self._validate_agent_prerequisites(state, agent_key)
                
                if not can_run:
                    logger.warning(f"⚠️  Skipping {agent_key} - missing required data: {', '.join(missing_fields)}")
                    state = update_agent_status(state, agent_key, AgentStatus.SKIPPED)
                    state['warnings'].append(f"{agent_key} skipped - missing data: {', '.join(missing_fields)}")
                    
                    # Notify user about skipped agent
                    await self.job_manager.broadcast_update(job_id, {
                        "type": "agent_skipped",
                        "job_id": job_id,
                        "data": {
                            "agent_name": agent_key.replace('_', ' ').title(),
                            "reason": f"Missing required data: {', '.join(missing_fields)}",
                            "message": f"Agent skipped - requires: {', '.join(missing_fields)}"
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Save state and continue to next agent
                    self.job_manager.active_jobs[job_id] = state
                    self.job_manager._save_job(job_id, state)
                    continue
                # Send "running" status
                await self._send_agent_update(
                    job_id,
                    agent_key,
                    AgentStatusEnum.RUNNING
                )
                
                if agent_instance:
                    # Update state
                    state = update_agent_status(state, agent_key, AgentStatus.RUNNING)
                    self.job_manager.active_jobs[job_id] = state
                    self.job_manager._save_job(job_id, state)
                    
                    try:
                        # Run agent
                        state = await agent_instance.execute(state)
                        
                        # CRITICAL FIX: Auto-calculate deal_value from DCF if not provided by user
                        if agent_key == "financial_analyst":
                            # Check if user provided deal_value
                            user_provided_value = state.get('deal_value')
                            
                            if not user_provided_value:
                                logger.info("deal_value not provided by user - calculating from DCF valuation...")
                                
                                # Extract all DCF scenarios for transparency
                                dcf_base = state.get('valuation_models', {}).get('dcf', {}).get('enterprise_value', 0)
                                
                                # Fallback to advanced DCF with all scenarios
                                advanced_val = state.get('valuation_models', {}).get('dcf_advanced', {})
                                dcf_analysis = advanced_val.get('dcf_analysis', {})
                                
                                dcf_scenarios = {
                                    'base': dcf_analysis.get('base', {}).get('enterprise_value', 0),
                                    'optimistic': dcf_analysis.get('optimistic', {}).get('enterprise_value', 0),
                                    'pessimistic': dcf_analysis.get('pessimistic', {}).get('enterprise_value', 0)
                                }
                                
                                # Use base case as primary valuation
                                dcf_valuation = dcf_base or dcf_scenarios['base']
                                
                                # Set deal_value to DCF base case with full metadata
                                if dcf_valuation and dcf_valuation > 0:
                                    state['deal_value'] = dcf_valuation
                                    
                                    # CRITICAL: Store metadata about deal_value source
                                    state['deal_value_metadata'] = {
                                        'source': 'auto_calculated',
                                        'method': 'DCF Base Case Valuation',
                                        'calculation_basis': 'Financial Analyst Agent - Multi-scenario DCF Analysis',
                                        'user_provided': False,
                                        'dcf_base_case': dcf_scenarios['base'],
                                        'dcf_optimistic': dcf_scenarios['optimistic'],
                                        'dcf_pessimistic': dcf_scenarios['pessimistic'],
                                        'valuation_range': {
                                            'low': dcf_scenarios['pessimistic'] or dcf_valuation * 0.8,
                                            'mid': dcf_valuation,
                                            'high': dcf_scenarios['optimistic'] or dcf_valuation * 1.2
                                        },
                                        'note': 'User did not provide deal value. System automatically calculated from DCF base case scenario.',
                                        'report_annotation': f"Deal value auto-calculated from DCF analysis. Base case: ${dcf_valuation:,.0f}. Range: ${(dcf_scenarios['pessimistic'] or dcf_valuation * 0.8):,.0f} - ${(dcf_scenarios['optimistic'] or dcf_valuation * 1.2):,.0f}",
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                                    
                                    logger.info(f"✓ Auto-calculated deal_value from DCF: ${dcf_valuation:,.0f}")
                                    logger.info(f"  DCF Scenarios - Base: ${dcf_scenarios['base']:,.0f}, Optimistic: ${dcf_scenarios['optimistic']:,.0f}, Pessimistic: ${dcf_scenarios['pessimistic']:,.0f}")
                                    
                                    await self.job_manager.broadcast_update(job_id, {
                                        "type": "deal_value_calculated",
                                        "job_id": job_id,
                                        "data": {
                                            "message": f"💰 Deal Value Calculated: ${dcf_valuation:,.0f}",
                                            "details": [
                                                "User did not specify deal value",
                                                f"Calculated from DCF Base Case: ${dcf_valuation:,.0f}",
                                                f"DCF Valuation Range: ${dcf_scenarios['pessimistic'] or dcf_valuation * 0.8:,.0f} - ${dcf_scenarios['optimistic'] or dcf_valuation * 1.2:,.0f}",
                                                "Deal structuring will use base case valuation"
                                            ]
                                        },
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                                else:
                                    logger.warning("Unable to calculate deal_value - DCF valuation not available")
                                    state['deal_value'] = 0
                                    state['deal_value_metadata'] = {
                                        'source': 'default',
                                        'method': 'Default Value',
                                        'user_provided': False,
                                        'note': 'User did not provide deal value and DCF calculation was unavailable. Using $0 as placeholder.',
                                        'report_annotation': 'Deal value not specified and could not be calculated from DCF.',
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                            else:
                                # User provided deal_value - store metadata
                                logger.info(f"Using user-provided deal_value: ${user_provided_value:,.0f}")
                                
                                # Get DCF for comparison
                                dcf_base = state.get('valuation_models', {}).get('dcf', {}).get('enterprise_value', 0)
                                advanced_val = state.get('valuation_models', {}).get('dcf_advanced', {})
                                dcf_analysis = advanced_val.get('dcf_analysis', {})
                                dcf_scenarios = {
                                    'base': dcf_analysis.get('base', {}).get('enterprise_value', 0),
                                    'optimistic': dcf_analysis.get('optimistic', {}).get('enterprise_value', 0),
                                    'pessimistic': dcf_analysis.get('pessimistic', {}).get('enterprise_value', 0)
                                }
                                
                                dcf_valuation = dcf_base or dcf_scenarios['base']
                                
                                # Calculate variance if DCF available
                                variance_pct = 0
                                if dcf_valuation > 0:
                                    variance_pct = ((user_provided_value - dcf_valuation) / dcf_valuation) * 100
                                
                                state['deal_value_metadata'] = {
                                    'source': 'user_provided',
                                    'method': 'User Specified',
                                    'user_provided': True,
                                    'dcf_comparison': {
                                        'dcf_base_case': dcf_valuation,
                                        'user_value': user_provided_value,
                                        'variance_amount': user_provided_value - dcf_valuation,
                                        'variance_percent': variance_pct
                                    },
                                    'note': f'Deal value provided by user: ${user_provided_value:,.0f}',
                                    'report_annotation': f"Deal value specified by user: ${user_provided_value:,.0f}" + 
                                                       (f" (DCF base case: ${dcf_valuation:,.0f}, variance: {variance_pct:+.1f}%)" if dcf_valuation > 0 else ""),
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                
                                logger.info(f"  Deal value metadata stored: User-provided value with DCF comparison")
                            
                            # Fetch acquirer data after target's financial analysis completes
                            acquirer_ticker = state.get('acquirer_ticker')
                            if acquirer_ticker:
                                logger.info(f"Acquirer ticker detected: {acquirer_ticker} - Fetching acquirer financial data...")
                                
                                await self.job_manager.broadcast_update(job_id, {
                                    "type": "acquirer_analysis",
                                    "job_id": job_id,
                                    "data": {
                                        "message": f"💼 Fetching Acquirer Data: {acquirer_ticker}",
                                        "details": [
                                            f"Downloading {acquirer_ticker} financial statements...",
                                            "Analyzing acquirer's financial capacity...",
                                            "Calculating combined pro forma metrics..."
                                        ]
                                    },
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                                
                                try:
                                    # Fetch acquirer's financial data using the same financial analyst agent
                                    acquirer_analyst = FinancialAnalystAgent()
                                    acquirer_result = await acquirer_analyst.analyze(acquirer_ticker)
                                    
                                    # CRITICAL FIX: Store in format that accretion_dilution agent expects
                                    historical_data = acquirer_result.get('historical_data', {})
                                    state['acquirer_data'] = {
                                        'income_statement': historical_data.get('income_statement', []),
                                        'balance_sheet': historical_data.get('balance_sheet', []),
                                        'cash_flow': historical_data.get('cash_flow', []),
                                        'current_stock_price': acquirer_result.get('price_data', {}).get('current_price', 100)
                                    }
                                    
                                    # Also store in original locations for backward compatibility
                                    state['acquirer_financial_data'] = historical_data
                                    state['acquirer_metrics'] = acquirer_result.get('financial_health', {})
                                    state['acquirer_analysis'] = {
                                        'ticker': acquirer_ticker,
                                        'financial_data': acquirer_result,
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                                    
                                    logger.info(f"✓ Acquirer data fetched and stored in state['acquirer_data'] for {acquirer_ticker}")
                                    logger.info(f"  Income statements: {len(state['acquirer_data']['income_statement'])} periods")
                                    logger.info(f"  Balance sheets: {len(state['acquirer_data']['balance_sheet'])} periods")
                                    
                                except Exception as acq_error:
                                    logger.error(f"Failed to fetch acquirer data: {acq_error}")
                                    state['warnings'].append(f"Could not fetch acquirer data for {acquirer_ticker}: {str(acq_error)}")

                        # NEW: Data Validation after Financial Analyst
                        if agent_key == "financial_analyst":
                            # CRITICAL FIX: Auto-generate deal_terms if not provided (required for M&A agents)
                            if not state.get('deal_terms'):
                                logger.info("deal_terms not provided - auto-generating from valuation for M&A agents...")
                                
                                # Get DCF valuation
                                dcf_value = state.get('valuation_models', {}).get('dcf_advanced', {})
                                dcf_analysis = dcf_value.get('dcf_analysis', {})
                                base_case = dcf_analysis.get('base', {})
                                base_ev = base_case.get('enterprise_value', 0)
                                
                                # Get acquirer stock price
                                acquirer_price = state.get('acquirer_data', {}).get('current_stock_price', 100)
                                
                                # Auto-generate reasonable defaults based on industry norms
                                state['deal_terms'] = {
                                    'purchase_price': base_ev,
                                    'cash_percentage': 0.5,  # 50/50 cash/stock mix (common structure)
                                    'debt_interest_rate': 0.05,  # 5% interest rate
                                    'tax_rate': 0.21,  # Federal corporate tax rate
                                    'acquirer_stock_price': acquirer_price,
                                    'synergies_year1': base_ev * 0.05,  # 5% synergies (industry standard)
                                    'acquirer_cash_available': 0,  # Conservative assumption
                                    'proposed_exchange_ratio': 0.50,  # Will be recalculated by exchange ratio agent
                                    'auto_generated': True,
                                    'generation_source': 'DCF Base Case Valuation',
                                    'note': 'Auto-generated deal terms using industry-standard assumptions. User should provide actual negotiated terms for precise analysis.',
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                
                                logger.info(f"✓ Auto-generated deal_terms:")
                                logger.info(f"  Purchase Price: ${base_ev/1e9:.1f}B (from DCF)")
                                logger.info(f"  Cash/Stock Mix: 50%/50% (industry standard)")
                                logger.info(f"  Year 1 Synergies: ${base_ev * 0.05/1e9:.1f}B (5% of deal value)")
                                logger.info(f"  Acquirer Stock Price: ${acquirer_price:.2f}")
                                
                                await self.job_manager.broadcast_update(job_id, {
                                    "type": "deal_terms_generated",
                                    "job_id": job_id,
                                    "data": {
                                        "message": "💼 Deal Terms Auto-Generated for M&A Analysis",
                                        "details": [
                                            f"Purchase Price: ${base_ev/1e9:.1f}B (from DCF valuation)",
                                            "Cash/Stock Mix: 50%/50% (industry standard)",
                                            f"Year 1 Synergies: ${base_ev * 0.05/1e9:.1f}B (5% assumption)",
                                            "Note: Provide actual deal terms for precise analysis"
                                        ]
                                    },
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            
                            logger.info("Running data quality validation on financial data...")
                            try:
                                financial_data = state.get('financial_data', {})
                                if financial_data:
                                    validation_result = validate_data(financial_data, target_ticker)
                                    
                                    # Store in state
                                    state['data_quality'] = {
                                        'is_valid': validation_result.is_valid,
                                        'completeness_score': validation_result.completeness_score,
                                        'quality_grade': validation_result.quality_grade,
                                        'error_count': len(validation_result.errors),
                                        'warning_count': len(validation_result.warnings),
                                        'outlier_count': len(validation_result.outliers),
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                                    
                                    # Broadcast data quality results
                                    await self.job_manager.broadcast_update(job_id, {
                                        "type": "data_quality",
                                        "job_id": job_id,
                                        "data": {
                                            "message": f"Data Quality: Grade {validation_result.quality_grade}",
                                            "completeness": float(validation_result.completeness_score),
                                            "grade": str(validation_result.quality_grade),
                                            "is_valid": bool(validation_result.is_valid),
                                            "error_count": len(validation_result.errors),
                                            "warning_count": len(validation_result.warnings),
                                            "outlier_count": len(validation_result.outliers),
                                            "details": [
                                                f"Completeness: {validation_result.completeness_score:.1f}%",
                                                f"Errors: {len(validation_result.errors)}",
                                                f"Warnings: {len(validation_result.warnings)}",
                                                f"Outliers: {len(validation_result.outliers)}"
                                            ]
                                        },
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                                    
                                    if not validation_result.is_valid:
                                        logger.warning(f"Data quality issues detected - Grade: {validation_result.quality_grade}")
                                    else:
                                        logger.info(f"Data quality validated - Grade: {validation_result.quality_grade}")
                            except Exception as val_error:
                                logger.error(f"Data validation error: {val_error}")

                        # Mark as completed
                        state = update_agent_status(state, agent_key, AgentStatus.COMPLETED)

                        # The agent's data is already in state['agent_outputs'] via add_agent_output() in base_agent.py
                        # Let's find and log it
                        output_keys = []
                        agent_data = {}

                        # Look for agent's data in agent_outputs array that was just added by base_agent.execute()
                        for output_entry in state.get('agent_outputs', []):
                            if output_entry.get('agent_name') == agent_key:
                                agent_data = output_entry.get('data', {})
                                # Count all non-empty data keys as populated
                                if agent_data and isinstance(agent_data, dict):
                                    for key, value in agent_data.items():
                                        if self._is_meaningful_data(value):
                                            output_keys.append(key)
                                # Take the last entry for this agent (most recent)
                                break

                        # If no meaningful data in agent_outputs, check direct state fields (fallback)
                        if not output_keys:
                            direct_keys = self._check_agent_direct_state_fields(state, agent_key)
                            output_keys.extend(direct_keys)

                        # SAVE output_keys to the agent_output entry for test script to find
                        for output_entry in state.get('agent_outputs', []):
                            if output_entry.get('agent_name') == agent_key:
                                output_entry['output_keys'] = output_keys
                                break

                        logger.info(f"Collected output for {agent_key}: {len(output_keys)} keys populated from {len(agent_data)} total data keys")

                        await self._send_agent_update(
                            job_id,
                            agent_key,
                            AgentStatusEnum.COMPLETED
                        )
                    except Exception as e:
                        logger.error(f"Error in {agent_key}: {e}")
                        state = update_agent_status(state, agent_key, AgentStatus.FAILED)
                        state['errors'].append(f"{agent_key}: {str(e)}")
                        await self._send_agent_update(
                            job_id,
                            agent_key,
                            AgentStatusEnum.FAILED
                        )
                else:
                    # Skip this agent (not implemented)
                    state = update_agent_status(state, agent_key, AgentStatus.SKIPPED)
                    await self._send_agent_update(
                        job_id,
                        agent_key,
                        AgentStatusEnum.COMPLETED
                    )
                
                # Save updated state
                self.job_manager.active_jobs[job_id] = state
                self.job_manager._save_job(job_id, state)
            
            # Generate reports
            await self._generate_reports(job_id, state)
            
            # Mark as completed
            state['metadata']['status'] = 'completed'
            state['workflow_completed'] = datetime.utcnow().isoformat()
            self.job_manager.active_jobs[job_id] = state
            self.job_manager._save_job(job_id, state)
            
            # Send completion message
            await self._send_completion(job_id)
            
            logger.info(f"Analysis completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error running analysis for job {job_id}: {e}")
            # Mark as failed
            state = self.job_manager.get_job(job_id)
            if state:
                state['metadata']['status'] = 'failed'
                state['errors'].append(f"Orchestration error: {str(e)}")
                self.job_manager._save_job(job_id, state)
    
    async def _send_agent_update(self, job_id: str, agent_key: str, status: AgentStatusEnum):
        """Send agent status update via WebSocket with detailed execution info
        
        Args:
            job_id: Job ID
            agent_key: Agent key
            status: Agent status
        """
        agent_info = self.agent_messages.get(agent_key, {
            "name": agent_key.replace('_', ' ').title(),
            "running": f"Processing {agent_key}...",
            "details": []
        })
        
        # CRITICAL FIX: Include detailed agent activities for frontend display
        message = {
            "type": "agent_status",
            "job_id": job_id,
            "data": {
                "agent_name": agent_info["name"],
                "status": status.value,
                "message": agent_info["running"] if status == AgentStatusEnum.RUNNING else f"{agent_info['name']} {status.value}",
                "details": agent_info["details"] if status == AgentStatusEnum.RUNNING else [],
                "timestamp": datetime.utcnow().isoformat(),
                # Add capabilities metadata for frontend to display
                "capabilities": self._get_agent_capabilities(agent_key) if status == AgentStatusEnum.RUNNING else []
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📤 Sending {status.value} update for {agent_info['name']} with {len(agent_info.get('details', []))} detail items")
        
        await self.job_manager.broadcast_update(job_id, message)
        
        # Small delay for UX (so user can see the update)
        await asyncio.sleep(0.5)
    
    def _get_agent_capabilities(self, agent_key: str) -> List[str]:
        """Get agent capabilities for frontend display
        
        Args:
            agent_key: Agent identifier
            
        Returns:
            List of capability descriptions
        """
        capabilities_map = {
            "project_manager": [
                "Multi-agent orchestration & sequencing",
                "Real-time workflow optimization",
                "Error handling & retry logic",
                "Status monitoring & dependency management"
            ],
            "financial_analyst": [
                "Financial statement normalization & adjustments",
                "Earnings quality scoring (100-point scale)",
                "DCF valuation with Monte Carlo simulation",
                "R&D capitalization & one-time expense identification"
            ],
            "financial_deep_dive": [
                "Working capital efficiency analysis & optimization",
                "Cash conversion cycle & days payable optimization",
                "CapEx intensity analysis & capital recommendations",
                "Customer concentration risk assessment"
            ],
            "legal_counsel": [
                "SEC EDGAR analysis (10-K, 10-Q, 8-K, DEF 14A)",
                "Change-of-control clause detection & quantification",
                "Debt covenant analysis & waiver requirements",
                "Founder compensation risk review"
            ],
            "market_strategist": [
                "Industry growth projections & trend analysis",
                "Market sentiment analysis with proprietary algorithms",
                "Competitive positioning assessment & fit evaluation",
                "Economic cycle impact modeling"
            ],
            "competitive_benchmarking": [
                "Automated peer company selection & analysis",
                "Financial multiples & valuation benchmarking",
                "Competitive advantage quantification",
                "Market share trends & growth analysis"
            ],
            "macroeconomic_analyst": [
                "Interest rate sensitivity analysis & forecasting",
                "Inflation impact modeling & hedge recommendations",
                "GDP growth & economic cycle assessment",
                "Currency exposure analysis & FX risk quantification"
            ],
            "risk_assessment": [
                "65-point operational risk scoring methodology",
                "Critical/high/medium/low risk categorization",
                "Industry-standard risk frameworks (COSO, ISO 31000)",
                "Mitigation strategy recommendations & cost-benefit analysis"
            ],
            "tax_structuring": [
                "Asset vs. stock purchase structural analysis",
                "Section 338(h)(10) election optimization modeling",
                "Tax-efficient restructuring alternatives",
                "Big 4-caliber tax benefit quantification"
            ],
            "deal_structuring": [
                "Stock vs. cash consideration optimization analysis",
                "Asset purchase vs. stock purchase structure comparison",
                "Tax implications modeling (338(h)(10), 338(g) elections)",
                "Earnout provisions and contingent payment structuring"
            ],
            "accretion_dilution": [
                "Pro forma EPS impact analysis post-transaction",
                "Share dilution calculations from new equity issuance",
                "Accretion quantification from synergies and earnings",
                "Breakeven analysis and sensitivity scenarios"
            ],
            "sources_uses": [
                "Complete sources and uses of funds table creation",
                "Equity vs. debt financing mix optimization",
                "Transaction costs and financing fees calculation",
                "Credit impact assessment and debt capacity analysis"
            ],
            "contribution_analysis": [
                "Standalone value contribution calculations for both parties",
                "Synergy value creation and attribution analysis",
                "Fair ownership percentage determination",
                "Relative bargaining position and deal fairness evaluation"
            ],
            "exchange_ratio_analysis": [
                "Market valuation-based exchange ratio calculation",
                "DCF, P/E, and P/B methodology-based ratio analysis",
                "Dilution impact modeling for existing shareholders",
                "Fairness assessment from acquirer and target perspectives"
            ],
            "integration_planner": [
                "Integration roadmap development (12-month timeline)",
                "Revenue & cost synergy quantification",
                "Day 1 readiness assessment & planning",
                "Cultural integration risk evaluation"
            ],
            "external_validator": [
                "Cross-referencing with external data sources",
                "Confidence scoring across all findings",
                "Data accuracy verification & hallucination detection",
                "External valuation consensus comparison"
            ],
            "synthesis_reporting": [
                "Multi-agent data consolidation & conflict resolution",
                "Quality control & hallucination detection",
                "Executive summary synthesis & key insight extraction",
                "Report-ready data structure creation for all outputs"
            ]
        }
        
        return capabilities_map.get(agent_key, [])
    
    async def _generate_reports(self, job_id: str, state: Dict[str, Any]):
        """Generate all reports with data consistency validation
        
        Args:
            job_id: Job ID
            state: Analysis state
        """
        logger.info(f"Generating reports for job {job_id}")
        
        try:
            # CRITICAL: Validate data consistency BEFORE generating ANY reports
            from src.outputs.report_consistency_validator import ReportConsistencyValidator
            
            logger.info("Running pre-report data consistency validation...")
            validation = ReportConsistencyValidator.validate_pre_report_generation(state)
            
            if not validation['valid']:
                # Validation failed - block report generation
                critical_issues = [i for i in validation['issues'] if i.get('blocker', False)]
                error_msg = f"Cannot generate reports: {len(critical_issues)} blocking issues found"
                logger.error(error_msg)
                
                # Log each blocking issue
                for issue in critical_issues:
                    logger.error(f"  - [{issue['severity']}] {issue['issue']}")
                    logger.error(f"    Fix: {issue['fix']}")
                
                # Send error notification
                await self.job_manager.broadcast_update(job_id, {
                    "type": "report_generation_blocked",
                    "job_id": job_id,
                    "data": {
                        "message": "Report generation blocked due to data consistency issues",
                        "issues": critical_issues,
                        "validation_report": ReportConsistencyValidator.format_validation_report(validation)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                state['errors'].append(error_msg)
                return
            
            # Log validation summary
            summary = validation.get('summary', {})
            logger.info(f"✓ Validation PASSED - Safe to generate reports")
            logger.info(f"  Issues found: {summary.get('total_issues', 0)} (non-blocking)")
            
            # Log non-blocking warnings
            warnings = [i for i in validation['issues'] if not i.get('blocker', False)]
            if warnings:
                logger.warning(f"Found {len(warnings)} non-blocking issues:")
                for warning in warnings[:5]:  # Log first 5
                    logger.warning(f"  - [{warning['severity']}] {warning['issue']}")
            
            # Send status update
            await self.job_manager.broadcast_update(job_id, {
                "type": "report_generation",
                "job_id": job_id,
                "data": {
                    "message": "✓ Data validated - Generating revolutionary reports...",
                    "details": [
                        "Data consistency validated successfully",
                        "Creating Glass Box Excel with 6 revolutionary tabs...",
                        "Building C-Suite PowerPoint with agent attribution...",
                        "Generating Diligence Bible PDF with embedded evidence..."
                    ]
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # ARCHITECTURE FIX: Generate ONLY revolutionary reports (removed redundant standard reports)
            logger.info(f"Generating REVOLUTIONARY 'Glass Box' reports for job {job_id}")
            
            try:
                report_paths = self.report_generator.generate_all_revolutionary_reports(state)
                logger.info(f"✓ Revolutionary reports generated: {list(report_paths.keys())}")
            except Exception as rev_error:
                logger.error(f"Revolutionary reports failed: {rev_error}")
                report_paths = {}
                state['errors'].append(f"Report generation error: {str(rev_error)}")
            
            # Generate M&A reports if deal terms are provided
            deal_terms = state.get('deal_terms', {})
            acquirer_ticker = state.get('acquirer_ticker')
            
            if MA_REPORTS_AVAILABLE and deal_terms and acquirer_ticker:
                logger.info(f"Deal terms detected - Generating M&A transaction reports...")
                await self.job_manager.broadcast_update(job_id, {
                    "type": "ma_reports",
                    "job_id": job_id,
                    "data": {
                        "message": "💼 Generating M&A Transaction Reports...",
                        "details": [
                            "Creating Investment Committee Memorandum...",
                            "Building M&A Financial Model (Excel)...",
                            "Generating Board Presentation Deck..."
                        ]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                try:
                    ma_generator = MAReportGenerator()
                    
                    # Extract target ticker
                    target_ticker = state.get('target_ticker', '')
                    
                    # Generate M&A reports
                    ma_results = await ma_generator.generate_complete_ma_report(
                        acquirer_symbol=acquirer_ticker,
                        target_symbol=target_ticker,
                        deal_terms=deal_terms,
                        output_dir=None  # Auto-generate path
                    )
                    
                    # Add M&A reports to output files
                    report_paths.update({
                        'ma_ic_memo': ma_results.get('ic_memo'),
                        'ma_financial_model': ma_results.get('financial_model'),
                        'ma_board_deck': ma_results.get('board_deck')
                    })
                    
                    # Store M&A analysis summary in state
                    state['ma_analysis'] = ma_results.get('summary', {})
                    
                    logger.info(f"M&A reports generated successfully")
                    
                except Exception as ma_error:
                    logger.warning(f"M&A reports failed (non-critical): {ma_error}")
                    # Don't fail workflow if M&A reports fail
            
            # Update state with all report paths
            state['output_files'] = report_paths
            
            logger.info(f"Reports generated for job {job_id}: {list(report_paths.keys())}")
            
        except Exception as e:
            logger.error(f"Error generating reports for job {job_id}: {e}")
            state['errors'].append(f"Report generation error: {str(e)}")
    
    async def _send_completion(self, job_id: str):
        """Send completion message
        
        Args:
            job_id: Job ID
        """
        result = self.job_manager.get_job_result(job_id)
        if not result:
            return
        
        message = {
            "type": "completion",
            "job_id": job_id,
            "data": {
                "message": "Analysis Complete!",
                "valuation_range": result.get('valuation_range'),
                "top_risks": result.get('top_risks', []),
                "top_opportunities": result.get('top_opportunities', []),
                "reports": result.get('reports', {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.job_manager.broadcast_update(job_id, message)



    def _deep_copy_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of state for comparison"""
        try:
            return copy.deepcopy(state)
        except Exception as e:
            logger.warning(f"Deep copy failed, using shallow copy: {e}")
            return state.copy() if hasattr(state, 'copy') else dict(state)

    def _find_populated_keys(self, state_before: Dict[str, Any], state_after: Dict[str, Any]) -> List[str]:
        """Dynamically detect which keys an agent populated by comparing state before/after"""
        populated_keys = []

        def recursive_compare(before: Any, after: Any, path: str = "") -> Set[str]:
            """Recursively compare all nested structures to find populated keys"""
            keys_populated = set()

            try:
                if isinstance(before, dict) and isinstance(after, dict):
                    # Compare dictionaries
                    for key in after.keys():
                        current_path = f"{path}.{key}" if path else key

                        if key not in before:
                            # Key was added
                            if after[key] is not None and after[key] != {} and after[key] != []:
                                # Check if it's actually meaningful data
                                if self._is_meaningful_data(after[key]):
                                    keys_populated.add(current_path.split('.')[0] if '.' not in current_path else current_path)

                        elif before.get(key) != after[key]:
                            # Key was modified
                            if after[key] is not None:
                                if self._is_meaningful_data(after[key]):
                                    keys_populated.add(current_path.split('.')[0] if '.' not in current_path else current_path)

                        else:
                            # Key exists in both, check deeper
                            sub_keys = recursive_compare(before.get(key), after[key], current_path)
                            keys_populated.update(sub_keys)

                elif isinstance(before, list) and isinstance(after, list):
                    # One common change: lists growing
                    if len(after) > len(before) and len(after) > 0:
                        # Something was added to list
                        current_key = path.split('.')[0] if '.' in path else path
                        if current_key and self._is_meaningful_data(after):
                            keys_populated.add(current_key)

                elif before != after:
                    # Value changed
                    current_key = path.split('.')[0] if '.' in path else path
                    if current_key and self._is_meaningful_data(after):
                        keys_populated.add(current_key)

            except Exception as e:
                logger.warning(f"Error in recursive compare at {path}: {e}")

            return keys_populated

        try:
            if state_before and state_after:
                # Find all keys that were populated/modified
                all_populated = recursive_compare(state_before, state_after)

                # Filter out system/metadata keys that agents shouldn't count as "populated"
                exclude_keys = {'errors', 'warnings', 'status', 'timestamp', 'agent_outputs', 'output_files'}

                populated_keys = [key for key in all_populated if key not in exclude_keys and key]

                # Log for debugging
                logger.debug(f"Detected populated keys: {populated_keys}")

                return populated_keys

        except Exception as e:
            logger.warning(f"Error detecting populated keys: {e}")
            return []

        return populated_keys

    def _check_agent_direct_state_fields(self, state: Dict[str, Any], agent_key: str) -> List[str]:
        """Check for agent data stored directly in state fields (fallback for agents that don't use add_agent_output)

        Args:
            state: Current state
            agent_key: Agent identifier (e.g., 'legal_counsel')

        Returns:
            List of meaningful data key names that were populated
        """
        populated_keys = []

        try:
            # Agent-specific state field mappings - COMPREHENSIVE LISTING
            agent_fields = {
                'project_manager': ['deal_structure', 'strategic_rationale', 'metadata'],
                'financial_analyst': ['financial_data', 'valuation_models', 'financial_metrics', 'metadata.financial_analysis'],
                'financial_deep_dive': ['financial_data', 'valuation_models', 'financial_metrics', 'metadata.financial_deep_dive'],
                'legal_counsel': ['legal_risks', 'compliance_status', 'legal_documents', 'metadata.legal_analysis'],
                'market_strategist': ['market_data', 'competitive_landscape', 'sentiment_analysis', 'market_analysis', 'metadata.market_analysis'],
                'competitive_benchmarking': ['competitive_landscape', 'peer_analysis', 'metadata.competitive_benchmarking'],
                'macroeconomic_analyst': ['macroeconomic_analysis', 'market_data', 'economic_indicators', 'metadata.macroeconomic_analysis'],
                'risk_assessment': ['critical_risks', 'legal_risks', 'risk_matrix', 'metadata.risk_assessment'],
                'tax_structuring': ['tax_analysis', 'tax_position', 'tax_recommendations', 'metadata.tax_structuring'],
                'deal_structuring': ['deal_structure_analysis', 'consideration_structure', 'purchase_structure', 'earnout_provisions', 'metadata.deal_structuring'],
                'accretion_dilution': ['eps_impact_analysis', 'pro_forma_combined', 'accretion_dilution_summary', 'breakeven_analysis', 'metadata.accretion_dilution'],
                'integration_planner': ['integration_roadmap', 'synergy_analysis', 'organizational_design', 'cultural_assessment', 'operational_plan', 'metadata.integration_planning'],
                'external_validator': ['validation_results', 'external_research', 'wall_street_reports', 'metadata.external_validation'],
                'synthesis_reporting': ['executive_summary', 'key_findings', 'recommendations', 'critical_risks', 'report_sections', 'metadata.synthesis_reporting']
            }

            agent_field_list = agent_fields.get(agent_key, [])

            for field_path in agent_field_list:
                # Handle nested fields like 'metadata.legal_analysis'
                if '.' in field_path:
                    parts = field_path.split('.')
                    current = state
                    found_value = True

                    for part in parts:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            found_value = False
                            break

                    if found_value and self._is_meaningful_data(current):
                        populated_keys.append(field_path)
                else:
                    # Direct field check
                    if field_path in state and self._is_meaningful_data(state[field_path]):
                        populated_keys.append(field_path)

        except Exception as e:
            logger.warning(f"Error checking direct state fields for {agent_key}: {e}")

        return populated_keys

    def _is_meaningful_data(self, data: Any) -> bool:
        """Check if data represents meaningful content (not empty/null)"""
        if data is None:
            return False
        if isinstance(data, (list, dict, str)):
            if data == [] or data == {} or data == "":
                return False
            if isinstance(data, str) and len(data.strip()) == 0:
                return False
        return True
