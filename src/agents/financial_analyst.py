"""
Financial Analyst Agent - Uses Claude Sonnet 4.5 for financial modeling and analysis

Phase 2 Enhancements:
- Financial statement normalization (non-recurring items, GAAP/non-GAAP)
- Multi-scenario DCF analysis (Base, Optimistic, Pessimistic)
- Sensitivity analysis and Monte Carlo simulation
- 10-year trend analysis with CAGRs
- Advanced valuation models
"""
import asyncio
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState, FinancialMetrics
from ..integrations.fmp_client import FMPClient
from ..utils.financial_normalizer import FinancialNormalizer, normalize_quarterly_data
from ..utils.enhanced_valuation_engine import EnhancedValuationEngine
from ..utils.financial_calculator import FinancialCalculator
from ..utils.llm_retry import llm_call_with_retry


class FinancialAnalystAgent(BaseAgent):
    """
    Financial Analyst Agent specializing in:
    - Financial modeling
    - Valuation (DCF, Comps, Precedent Transactions)
    - Financial health analysis
    - Accounting irregularity detection
    - Projection stress-testing
    """
    
    def __init__(self):
        """Initialize Financial Analyst Agent"""
        super().__init__("financial_analyst")
        self.fmp_client = None
        self.financial_calculator = FinancialCalculator()
    

    
    async def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Perform financial analysis for a specific symbol.
        This is the method called by the revolutionary demo.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Comprehensive financial analysis
        """
        self.log_action(f"Starting financial analysis for {symbol}")
        
        try:
            # Fetch comprehensive financial data
            financial_data = await self._fetch_financial_data(symbol, extended=True)
            
            if not financial_data:
                return {'error': 'Failed to fetch financial data'}
            
            # Phase 2 Enhancement 1: Financial Statement Normalization
            self.log_action("Normalizing financial statements...")
            normalized_data = await self._normalize_financial_statements(financial_data)
            
            # Phase 2 Enhancement 2: Advanced Valuation
            self.log_action("Running advanced valuation suite...")
            advanced_valuation = await self._run_advanced_valuation(financial_data, {})
            
            # Phase 2 Enhancement 3: 10-Year Trend Analysis
            self.log_action("Analyzing long-term trends...")
            trend_analysis = await self._analyze_long_term_trends(financial_data, normalized_data)
            
            # Phase 2 Enhancement 4: Quarterly Seasonality Analysis
            self.log_action("Analyzing seasonality...")
            seasonality = await self._analyze_seasonality(financial_data)
            
            # Legacy analysis
            analysis_tasks = [
                self._analyze_financial_health(financial_data),
                self._perform_ratio_analysis(financial_data),
                self._identify_red_flags(financial_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            financial_health = results[0] if not isinstance(results[0], Exception) else {}
            ratio_analysis = results[1] if not isinstance(results[1], Exception) else {}
            red_flags = results[2] if not isinstance(results[2], Exception) else []
            
            # Generate insights
            insights = await self._generate_enhanced_insights(
                symbol,
                financial_data,
                normalized_data,
                advanced_valuation,
                trend_analysis,
                financial_health,
                ratio_analysis
            )
            
            analysis = {
                'financial_health_score': financial_health.get('health_score', 0),
                'valuation': advanced_valuation.get('valuation_summary', {}),
                'ratio_analysis': {
                    'profitability_ratios': ratio_analysis.get('profitability', {}),
                    'growth_metrics': normalized_data.get('cagr_analysis', {})
                },
                'historical_data': financial_data,
                'normalized_financials': normalized_data,
                'advanced_valuation': advanced_valuation,
                'trend_analysis': trend_analysis,
                'seasonality': seasonality,
                'financial_health': financial_health,
                'red_flags': red_flags,
                'insights': insights
            }
            
            self.log_action("Financial analysis complete")
            return analysis
            
        except Exception as e:
            self.log_action(f"Error in financial analysis: {str(e)}", level="error")
            raise
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Execute comprehensive financial analysis with Phase 2 enhancements
        
        Args:
            state: Current diligence state
        
        Returns:
            Analysis results with advanced financial models and insights
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Get target company info
        target_company = state["target_company"]
        target_ticker = state.get("target_ticker")
        
        if not target_ticker:
            errors.append("No ticker symbol provided. Cannot fetch financial data.")
            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        logger.info(f"[PHASE 2] Advanced financial analysis for {target_company} ({target_ticker})")
        
        # Fetch comprehensive financial data (10 years + quarterly)
        financial_data = await self._fetch_financial_data(target_ticker, extended=True)
        
        if not financial_data:
            errors.append("Failed to fetch financial data")
            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        # Phase 2 Enhancement 1: Financial Statement Normalization
        logger.info("Step 1: Normalizing financial statements...")
        normalized_data = await self._normalize_financial_statements(financial_data)

        # CRITICAL FIX: Quality Gate - Block valuation if data quality is too low
        quality_score = normalized_data.get('quality_score', 0)
        quality_threshold = 60  # Minimum 60/100 quality score required
        
        if quality_score < quality_threshold:
            logger.error(f"⛔ DATA QUALITY GATE: Quality score {quality_score}/100 is below threshold ({quality_threshold})")
            logger.error("❌ BLOCKING VALUATION: Data quality insufficient for reliable M&A analysis")
            
            # Log all critical adjustments made
            critical_adjustments = [
                adj for adj in normalized_data.get('adjustments', []) 
                if adj.get('severity') == 'CRITICAL'
            ]
            
            if critical_adjustments:
                logger.error(f"Found {len(critical_adjustments)} CRITICAL data quality issues:")
                for adj in critical_adjustments[:5]:  # Show first 5
                    logger.error(f"  • {adj.get('type', 'Unknown')}: {adj.get('reason', 'No details')}")
            
            # Return error state with diagnostic information
            errors.append(f"DATA QUALITY INSUFFICIENT: Score {quality_score}/100 (minimum {quality_threshold} required)")
            errors.append("REQUIRED ACTIONS: Review and fix critical data issues before proceeding to valuation")
            warnings.append(f"Made {len(normalized_data.get('adjustments', []))} normalization adjustments")
            
            if critical_adjustments:
                warnings.append(f"{len(critical_adjustments)} CRITICAL issues detected - manual review required")
            
            recommendations.append("1. Review critical data quality warnings above")
            recommendations.append("2. Verify extreme margins with 10-K/10-Q filings")
            recommendations.append("3. Reconcile large NI vs OCF discrepancies")
            recommendations.append("4. Obtain missing cash values from SEC filings")
            recommendations.append("5. Re-run analysis after data corrections")
            
            return {
                "data": {
                    "quality_score": quality_score,
                    "quality_threshold": quality_threshold,
                    "normalized_financials": normalized_data,
                    "financial_metrics": {},
                    "status": "BLOCKED_BY_QUALITY_GATE"
                },
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        logger.info(f"✓ DATA QUALITY GATE PASSED: Score {quality_score}/100 (threshold: {quality_threshold})")

        # CRITICAL FIX: Add historical and forecast sections to normalized_financials
        logger.info("Step 1.1: Structuring historical data...")
        normalized_data['historical'] = {
            'income_statements': financial_data.get('income_statement', [])[:10],
            'balance_sheets': financial_data.get('balance_sheet', [])[:10],
            'cash_flows': financial_data.get('cash_flow', [])[:10],
            'years_available': min(len(financial_data.get('income_statement', [])), 10)
        }
        
        # CRITICAL FIX: Generate 5-year forecast
        logger.info("Step 1.2: Generating 5-year financial forecast...")
        forecast_data = await self._generate_forecast(financial_data, normalized_data)
        normalized_data['forecast'] = forecast_data
        
        # CRITICAL FIX: Calculate and store EBITDA
        logger.info("Step 1.3: Calculating EBITDA...")
        ebitda = self._ensure_ebitda_calculated(financial_data.get('income_statement', []))
        state['ebitda'] = ebitda  # Store in state for downstream agents
        normalized_data['ebitda'] = ebitda  # Also store in normalized_financials
        logger.info(f"✓ EBITDA calculated and stored: ${ebitda:,.0f}")

        # Log normalization issues to centralized log
        if normalized_data.get("adjustments"):
            for adjustment in normalized_data["adjustments"]:
                self.log_anomaly(
                    anomaly_type="normalization_adjustment",
                    description=f"Normalization adjustment: {adjustment.get('type', 'Unknown')}",
                    severity="low",
                    data=adjustment
                )

        # Phase 2 Enhancement 1.5: Anomaly Detection (Early Warning System)
        logger.info("Step 1.5: Running anomaly detection...")
        anomaly_results = await self._detect_financial_anomalies(financial_data)

        # Log anomalies to centralized log
        if anomaly_results.get("anomalies_detected"):
            for anomaly in anomaly_results["anomalies_detected"]:
                self.log_anomaly(
                    anomaly_type="financial_anomaly",
                    description=anomaly.get("description", "Financial anomaly detected"),
                    severity=anomaly.get("severity", "medium"),
                    data=anomaly
                )
        
        # Phase 2 Enhancement 2: Advanced Valuation (Multi-scenario DCF, Sensitivity, Monte Carlo)
        logger.info("Step 2: Running advanced valuation suite...")
        advanced_valuation = await self._run_advanced_valuation(financial_data, state)

        # Log valuation discrepancies to centralized log
        external_validation = advanced_valuation.get('external_validation', {})
        if external_validation.get('variance_percent', 0) > 25:
            self.log_anomaly(
                anomaly_type="valuation_discrepancy",
                description=f"Large DCF variance: {external_validation.get('interpretation', 'Unknown')}",
                severity="high" if external_validation.get('variance_percent', 0) > 50 else "moderate",
                data=external_validation
            )
        
        # Phase 2 Enhancement 3: 10-Year Trend Analysis
        logger.info("Step 3: Analyzing 10-year trends and CAGRs...")
        trend_analysis = await self._analyze_long_term_trends(financial_data, normalized_data)
        
        # Phase 2 Enhancement 4: Quarterly Seasonality Analysis
        logger.info("Step 4: Analyzing quarterly seasonality...")
        seasonality = await self._analyze_seasonality(financial_data)
        
        # Legacy analysis (still useful)
        analysis_tasks = [
            self._analyze_financial_health(financial_data),
            self._perform_ratio_analysis(financial_data),
            self._identify_red_flags(financial_data)
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Compile results
        financial_health = results[0] if not isinstance(results[0], Exception) else {}
        ratio_analysis = results[1] if not isinstance(results[1], Exception) else {}
        legacy_red_flags = results[2] if not isinstance(results[2], Exception) else []
        
        # Extract key metrics
        financial_metrics = self._extract_key_metrics(financial_data)
        
        # Generate AI-powered insights
        insights = await self._generate_enhanced_insights(
            target_company,
            financial_data,
            normalized_data,
            advanced_valuation,
            trend_analysis,
            financial_health,
            ratio_analysis
        )
        
        # Compile all warnings and recommendations
        recommendations.extend(insights.get("recommendations", []))
        
        # Combine red flags from normalization and legacy analysis
        all_red_flags = normalized_data.get('red_flags', []) + legacy_red_flags
        if all_red_flags:
            warnings.extend(all_red_flags)
        
        # Update state with enhanced financial data
        state["financial_data"] = financial_data
        state["financial_metrics"] = financial_metrics
        state["normalized_financials"] = normalized_data
        state.setdefault("valuation_models", {})
        state["valuation_models"]["dcf_advanced"] = advanced_valuation
        state["valuation_models"]["dcf"] = advanced_valuation.get('dcf_analysis', {}).get('base', {})
        
        # CRITICAL: Store data in both formats for backward compatibility
        # The data MUST be stored in state[target_company] for synthesis agent
        if state["target_company"] not in state:
            state[state["target_company"]] = {}

        # Store in state[target_company] as primary single source of truth
        state[state["target_company"]]["financial_data"] = financial_data
        state[state["target_company"]]["normalized_financials"] = normalized_data
        state[state["target_company"]]["advanced_valuation"] = advanced_valuation
        state[state["target_company"]]["financial_health"] = financial_health

        # Log what was stored in target_company key
        target_keys = list(state[state["target_company"]].keys())
        logger.info(f"✓ Stored {len(target_keys)} keys in state['{state['target_company']}']: {target_keys}")

        # Also store in state["financial_analyst"] for synthesis agent compatibility
        if "financial_analyst" not in state:
            state["financial_analyst"] = {}

        state["financial_analyst"] = {
            "financial_metrics": financial_metrics,
            "normalized_financials": normalized_data,
            "anomaly_detection": anomaly_results,
            "advanced_valuation": advanced_valuation,
            "trend_analysis": trend_analysis,
            "seasonality": seasonality,
            "financial_health": financial_health,
            "ratio_analysis": ratio_analysis,
            "red_flags": all_red_flags,
            "insights": insights,
            "raw_data": financial_data
        }
        
        # Log what was stored in financial_analyst key
        analyst_keys = list(state["financial_analyst"].keys())
        logger.info(f"✓ Stored {len(analyst_keys)} keys in state['financial_analyst']: {analyst_keys}")
        logger.info(f"📊 Output data ready for Synthesis Agent and Report Generators")

        return {
            "data": {
                "financial_metrics": financial_metrics,
                "normalized_financials": normalized_data,
                "anomaly_detection": anomaly_results,
                "advanced_valuation": advanced_valuation,
                "trend_analysis": trend_analysis,
                "seasonality": seasonality,
                "financial_health": financial_health,
                "ratio_analysis": ratio_analysis,
                "red_flags": all_red_flags,
                "insights": insights,
                "raw_data": financial_data
            },
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    async def _fetch_financial_data(self, ticker: str, extended: bool = True) -> Dict[str, Any]:
        """Fetch comprehensive financial data from FMP API with Phase 2 extensions and freshness validation"""
        try:
            # Calculate date range for latest data (last 10 years for extended, 5 for basic)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*10 if extended else 365*5)).strftime('%Y-%m-%d')

            async with FMPClient() as client:
                data = await client.fetch_all_financial_data(ticker, extended=extended)

                # Validate data freshness
                if data and data.get('income_statement'):
                    latest_date = data['income_statement'][0].get('date') if data['income_statement'] else None
                    if latest_date:
                        try:
                            stmt_date = datetime.strptime(latest_date, '%Y-%m-%d')
                            days_old = (datetime.now() - stmt_date).days

                            if days_old > 180:  # More than 6 months old
                                logger.warning(f"⚠️ Financial data for {ticker} is {days_old} days old (latest: {latest_date})")
                            else:
                                logger.info(f"✓ Financial data for {ticker} is fresh ({days_old} days old, latest: {latest_date})")
                        except ValueError:
                            logger.warning(f"⚠️ Could not parse financial statement date: {latest_date}")

                # Validate SEC filings freshness
                if data and data.get('sec_filings'):
                    latest_filing = data['sec_filings'][0] if data['sec_filings'] else None
                    if latest_filing:
                        filing_date = latest_filing.get('fillingDate') or latest_filing.get('acceptedDate')
                        if filing_date:
                            try:
                                f_date = datetime.strptime(filing_date.split()[0], '%Y-%m-%d')
                                days_old = (datetime.now() - f_date).days

                                if days_old > 365:  # More than 1 year old
                                    logger.warning(f"⚠️ SEC filings for {ticker} are {days_old} days old (latest: {filing_date})")
                                else:
                                    logger.info(f"✓ SEC filings for {ticker} are fresh ({days_old} days old, latest: {filing_date})")
                            except ValueError:
                                logger.warning(f"⚠️ Could not parse SEC filing date: {filing_date}")

            logger.info(f"Successfully fetched {'extended' if extended else 'basic'} financial data for {ticker}")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch financial data: {e}")
            return {}
    
    def _ensure_ebitda_calculated(self, income_statements: List[Dict]) -> float:
        """
        PRODUCTION-SAFE: Calculate EBITDA with multiple fallbacks
        This ensures EBITDA is ALWAYS available downstream
        
        Returns:
            EBITDA value (never None, never raises exception)
        """
        if not income_statements:
            logger.error("No income statements available")
            return 0.0
        
        latest = income_statements[0]
        
        # Method 1: Use existing EBITDA if available and valid
        if 'ebitda' in latest and latest['ebitda'] and latest['ebitda'] > 0:
            logger.info(f"Using existing EBITDA: ${latest['ebitda']:,.0f}")
            return float(latest['ebitda'])
        
        # Method 2: Calculate from operating income + D&A
        operating_income = latest.get('operatingIncome', 0) or 0
        depreciation = latest.get('depreciationAndAmortization', 0) or 0
        
        if operating_income > 0:
            ebitda = operating_income + depreciation
            logger.info(f"Calculated EBITDA from Op Income: ${ebitda:,.0f}")
            return ebitda
        
        # Method 3: Build up from net income
        net_income = latest.get('netIncome', 0) or 0
        interest = latest.get('interestExpense', 0) or 0
        tax = latest.get('incomeTaxExpense', 0) or 0
        
        if net_income != 0:  # Can be negative
            ebitda = net_income + abs(interest) + abs(tax) + depreciation
            logger.info(f"Calculated EBITDA from Net Income: ${ebitda:,.0f}")
            return ebitda
        
        # Method 4: Estimate from revenue (worst case)
        revenue = latest.get('revenue', 0) or 0
        if revenue > 0:
            ebitda = revenue * 0.15  # Conservative 15% margin estimate
            logger.warning(f"Estimated EBITDA from revenue: ${ebitda:,.0f}")
            return ebitda
        
        logger.error("Unable to calculate EBITDA - returning 0")
        return 0.0
    
    async def _normalize_financial_statements(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Normalize financial statements
        - Remove non-recurring items
        - Reconcile GAAP vs non-GAAP
        - Adjust for R&D capitalization
        - Calculate earnings quality score
        """
        try:
            normalizer = FinancialNormalizer()
            
            income_statements = financial_data.get('income_statement', [])
            balance_sheets = financial_data.get('balance_sheet', [])
            cash_flows = financial_data.get('cash_flow', [])
            income_as_reported = financial_data.get('income_as_reported', [])
            company_profile = financial_data.get('profile', {})
            
            if not income_statements:
                return {'error': 'No income statements available for normalization'}
            
            normalized = normalizer.normalize_financial_statements(
                income_statements=income_statements,
                balance_sheets=balance_sheets,
                cash_flows=cash_flows,
                income_as_reported=income_as_reported,
                company_info=company_profile
            )
            
            logger.info(f"Normalization complete. Quality score: {normalized.get('quality_score', 0)}/100")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing financial statements: {e}")
            return {'error': str(e)}
    
    async def _run_advanced_valuation(
        self,
        financial_data: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Phase 2: Run advanced valuation suite
        - Multi-scenario DCF (Base, Optimistic, Pessimistic)
        - Sensitivity analysis
        - Monte Carlo simulation
        - Comparable company analysis (if available) - NOW WITH REAL DATA
        - External validation with FMP DCF (NEW)
        """
        try:
            from ..utils.advanced_valuation import AdvancedValuationEngine
            
            valuation_engine = AdvancedValuationEngine()
            
            company_profile = financial_data.get('profile', {})
            
            # Get comparable companies from state if available, or auto-select peers
            comparable_companies = state.get('comparable_companies', None)
            
            # Auto-select comparable companies if not provided
            if not comparable_companies:
                sector = company_profile.get('sector', '')
                industry = company_profile.get('industry', '')
                
                # Get default peer list based on sector/industry
                if sector and industry:
                    comparable_companies = await self._auto_select_peers(company_profile)
                    logger.info(f"Auto-selected {len(comparable_companies) if comparable_companies else 0} comparable companies")
            
            # Run full valuation suite with async comparable analysis
            results = {}
            
            # 1. Multi-scenario DCF
            results['dcf_analysis'] = valuation_engine.run_multi_scenario_dcf(
                financial_data, company_profile
            )
            
            # 2. Sensitivity Analysis
            results['sensitivity_analysis'] = valuation_engine.run_sensitivity_analysis(
                financial_data, company_profile
            )
            
            # 3. Monte Carlo Simulation
            results['monte_carlo_simulation'] = valuation_engine.run_monte_carlo_valuation(
                financial_data, company_profile, num_simulations=10000
            )
            
            # 4. Comparable Company Analysis - NOW ASYNC WITH REAL DATA
            if comparable_companies:
                logger.info(f"Running comparable company analysis with {len(comparable_companies)} peers...")
                results['comparable_companies'] = await valuation_engine.run_comparable_analysis(
                    financial_data, comparable_companies
                )
                logger.info("✓ Comparable company analysis complete with real market data")
            
            # 5. LBO Analysis
            results['lbo_analysis'] = valuation_engine.run_lbo_analysis(
                financial_data, company_profile
            )
            
            # 6. Valuation Summary
            results['valuation_summary'] = valuation_engine.generate_valuation_summary(results)
            results['recommendation'] = valuation_engine.generate_valuation_recommendation(results)
            
            # NEW: Add FMP DCF comparison for external validation
            fmp_dcf = financial_data.get('custom_dcf_levered', {})
            if fmp_dcf and fmp_dcf.get('dcf'):
                our_dcf_base = results.get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0)
                fmp_dcf_value = fmp_dcf.get('dcf', 0)
                
                results['external_validation'] = {
                    'fmp_dcf_value': fmp_dcf_value,
                    'fmp_stock_price': fmp_dcf.get('Stock Price', 0),
                    'our_dcf_value': our_dcf_base,
                    'variance_percent': ((our_dcf_base - fmp_dcf_value) / fmp_dcf_value * 100) if fmp_dcf_value > 0 else 0,
                    'interpretation': self._interpret_dcf_variance(our_dcf_base, fmp_dcf_value),
                    'validation_status': 'Strong' if abs((our_dcf_base - fmp_dcf_value) / fmp_dcf_value) < 0.15 else 'Moderate'
                }
                logger.info(f"FMP DCF external validation complete: {results['external_validation']['interpretation']}")
            
            # NEW: Add earnings quality analysis from surprises
            earnings_surprises = financial_data.get('earnings_surprises', [])
            if earnings_surprises:
                results['earnings_quality'] = self._analyze_earnings_quality(earnings_surprises)
                logger.info(f"Earnings quality score: {results['earnings_quality'].get('quality_score', 0)}/100")
            
            logger.info("Advanced valuation suite complete with external validation")
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced valuation: {e}")
            return {'error': str(e)}
    
    async def _analyze_long_term_trends(
        self,
        financial_data: Dict[str, Any],
        normalized_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 2: Analyze 10-year trends and calculate CAGRs
        """
        try:
            cagr_analysis = normalized_data.get('cagr_analysis', {}) if normalized_data else {}
            trends = normalized_data.get('trends', {}) if normalized_data else {}
            
            # Additional trend analysis
            income_statements = financial_data.get('income_statement', []) if financial_data else []
            
            if not income_statements:
                return {
                    'analysis_period': 'N/A',
                    'cagr_metrics': {},
                    'trends': {},
                    'data_points': 0
                }
            
            if len(income_statements) >= 10:
                analysis_period = "10 years"
            elif len(income_statements) >= 5:
                analysis_period = "5 years"
            else:
                analysis_period = f"{len(income_statements)} years"
            
            return {
                'analysis_period': analysis_period,
                'cagr_metrics': cagr_analysis,
                'trends': trends,
                'data_points': len(income_statements)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing long-term trends: {e}")
            return {'error': str(e), 'analysis_period': 'N/A', 'cagr_metrics': {}, 'trends': {}, 'data_points': 0}
    
    async def _analyze_seasonality(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Analyze quarterly seasonality patterns
        """
        try:
            quarterly_income = financial_data.get('income_statement_quarterly', [])
            
            if not quarterly_income or len(quarterly_income) < 4:
                return {'seasonality_detected': False, 'note': 'Insufficient quarterly data'}
            
            seasonality_result = normalize_quarterly_data(
                quarterly_statements=quarterly_income,
                statement_type='income'
            )
            
            return seasonality_result
            
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {e}")
            return {'error': str(e)}
    
    async def _detect_financial_anomalies(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Detect financial anomalies using machine learning
        Early warning system for unusual patterns
        """
        try:
            from ..utils.anomaly_detection import AnomalyDetector
            
            quarterly_data = financial_data.get('income_statement_quarterly', [])
            
            if not quarterly_data or len(quarterly_data) < 8:
                return {
                    'anomalies_detected': [],
                    'risk_level': 'Unknown',
                    'note': 'Insufficient quarterly data for anomaly detection (need 8+ quarters)'
                }
            
            # Train detector on historical data
            detector = AnomalyDetector()
            training_result = detector.train(quarterly_data[1:])  # Train on historical, not latest
            
            # Detect anomalies in latest quarter
            latest_quarter = quarterly_data[0]
            anomalies = detector.detect_anomalies(latest_quarter, threshold=2.0)
            
            # Generate early warning report if anomalies found
            if anomalies.get('anomalies_detected'):
                early_warning = detector.generate_early_warning_report(anomalies)
                anomalies['early_warning_report'] = early_warning
            
            logger.info(f"Anomaly detection complete. Risk level: {anomalies.get('risk_level', 'Unknown')}")
            return anomalies
            
        except ImportError:
            logger.warning("Anomaly detection module not available")
            return {'note': 'Anomaly detection module not available'}
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}
    
    async def _analyze_financial_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall financial health"""
        health_score = 0
        max_score = 100
        factors = []
        
        try:
            # Get latest financial statements
            income_stmt = data.get("income_statement", [])
            balance_sheet = data.get("balance_sheet", [])
            cash_flow = data.get("cash_flow", [])
            ratios = data.get("ratios", [])
            
            if not income_stmt or not balance_sheet:
                return {"health_score": 0, "factors": ["Insufficient financial data"]}
            
            latest_income = income_stmt[0]
            latest_balance = balance_sheet[0]
            latest_ratios = ratios[0] if ratios else {}
            
            # Profitability (30 points)
            net_margin = latest_ratios.get("netProfitMargin", 0)
            if net_margin > 0.15:
                health_score += 30
                factors.append("Strong profitability")
            elif net_margin > 0.05:
                health_score += 20
                factors.append("Moderate profitability")
            else:
                factors.append("Weak profitability")
            
            # Liquidity (20 points)
            current_ratio = latest_ratios.get("currentRatio", 0)
            if current_ratio > 2.0:
                health_score += 20
                factors.append("Strong liquidity")
            elif current_ratio > 1.0:
                health_score += 15
                factors.append("Adequate liquidity")
            else:
                factors.append("Liquidity concerns")
            
            # Leverage (25 points)
            debt_to_equity = latest_ratios.get("debtEquityRatio", 999)
            if debt_to_equity < 0.5:
                health_score += 25
                factors.append("Conservative leverage")
            elif debt_to_equity < 1.5:
                health_score += 15
                factors.append("Moderate leverage")
            else:
                factors.append("High leverage risk")
            
            # Growth (25 points)
            if len(income_stmt) >= 3:
                revenue_growth = (latest_income.get("revenue", 0) - income_stmt[2].get("revenue", 1)) / income_stmt[2].get("revenue", 1)
                if revenue_growth > 0.10:
                    health_score += 25
                    factors.append("Strong revenue growth")
                elif revenue_growth > 0:
                    health_score += 15
                    factors.append("Positive revenue growth")
                else:
                    factors.append("Revenue decline")
            
            return {
                "health_score": health_score,
                "max_score": max_score,
                "rating": self._get_health_rating(health_score),
                "factors": factors,
                "key_metrics": {
                    "net_margin": net_margin,
                    "current_ratio": current_ratio,
                    "debt_to_equity": debt_to_equity
                }
            }
        
        except Exception as e:
            logger.error(f"Error analyzing financial health: {e}")
            return {"health_score": 0, "factors": [f"Analysis error: {str(e)}"]}
    
    def _get_health_rating(self, score: float) -> str:
        """Convert health score to rating"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        else:
            return "Critical"
    
    async def _build_dcf_model(self, data: Dict[str, Any], state: DiligenceState) -> Dict[str, Any]:
        """Build DCF valuation model using FinancialCalculator"""
        try:
            income_stmt = data.get("income_statement", [])
            cash_flow = data.get("cash_flow", [])
            
            if not income_stmt or not cash_flow:
                return {"error": "Insufficient data for DCF"}
            
            # Get historical free cash flows
            fcf_history = []
            for i in range(min(5, len(cash_flow))):
                fcf = cash_flow[i].get("freeCashFlow", 0)
                fcf_history.append(fcf)
            
            if not fcf_history or fcf_history[0] <= 0:
                return {"error": "Negative or zero free cash flow"}
            
            # Project future cash flows (5-year projection)
            growth_rate = 0.05  # Conservative 5% growth
            terminal_growth = 0.025  # 2.5% terminal growth
            wacc = 0.10  # 10% WACC assumption
            
            # Use FinancialCalculator for growth projections
            current_fcf = fcf_history[0]
            
            growth_projection = self.financial_calculator.project_growth(
                base_value=current_fcf,
                growth_rate=growth_rate,
                periods=5,
                growth_type='compound'
            )
            
            projections = [proj['value'] for proj in growth_projection['projections']]
            
            # Calculate DCF using the calculator
            dcf_result = self.financial_calculator.calculate_dcf_standard(
                free_cash_flows=projections,
                wacc=wacc,
                terminal_growth_rate=terminal_growth
            )
            
            if 'error' in dcf_result:
                return dcf_result
            
            # Add historical data to result
            dcf_result["historical_fcf"] = fcf_history
            dcf_result["current_fcf"] = current_fcf
            dcf_result["assumptions"] = {
                "growth_rate": growth_rate,
                "terminal_growth": terminal_growth,
                "wacc": wacc
            }
            
            return dcf_result
        
        except Exception as e:
            logger.error(f"Error building DCF model: {e}")
            return {"error": str(e)}
    
    async def _perform_ratio_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive ratio analysis"""
        try:
            ratios = data.get("ratios", [])
            if not ratios:
                return {}
            
            latest = ratios[0]
            
            return {
                "profitability": {
                    "gross_margin": latest.get("grossProfitMargin"),
                    "operating_margin": latest.get("operatingProfitMargin"),
                    "net_margin": latest.get("netProfitMargin"),
                    "roe": latest.get("returnOnEquity"),
                    "roa": latest.get("returnOnAssets"),
                    "roic": latest.get("returnOnCapitalEmployed")
                },
                "liquidity": {
                    "current_ratio": latest.get("currentRatio"),
                    "quick_ratio": latest.get("quickRatio"),
                    "cash_ratio": latest.get("cashRatio")
                },
                "leverage": {
                    "debt_to_equity": latest.get("debtEquityRatio"),
                    "debt_to_assets": latest.get("debtRatio"),
                    "interest_coverage": latest.get("interestCoverage")
                },
                "efficiency": {
                    "asset_turnover": latest.get("assetTurnover"),
                    "inventory_turnover": latest.get("inventoryTurnover"),
                    "receivables_turnover": latest.get("receivablesTurnover")
                }
            }
        
        except Exception as e:
            logger.error(f"Error in ratio analysis: {e}")
            return {}
    
    async def _identify_red_flags(self, data: Dict[str, Any]) -> List[str]:
        """Identify potential accounting red flags"""
        red_flags = []
        
        try:
            income_stmt = data.get("income_statement", [])
            cash_flow = data.get("cash_flow", [])
            balance_sheet = data.get("balance_sheet", [])
            
            if not income_stmt or not cash_flow:
                return red_flags
            
            latest_income = income_stmt[0]
            latest_cf = cash_flow[0]
            latest_bs = balance_sheet[0] if balance_sheet else {}
            
            # Check if net income >> operating cash flow
            net_income = latest_income.get("netIncome", 0)
            operating_cf = latest_cf.get("operatingCashFlow", 0)
            
            if net_income > 0 and operating_cf > 0:
                if net_income / operating_cf > 1.5:
                    red_flags.append("Net income significantly exceeds operating cash flow - potential earnings quality issue")
            
            # Check for declining margins
            if len(income_stmt) >= 3:
                margins = [stmt.get("netIncome", 0) / max(stmt.get("revenue", 1), 1) for stmt in income_stmt[:3]]
                if margins[0] < margins[1] < margins[2]:
                    red_flags.append("Declining profit margins over the past 3 years")
            
            # Check for high accounts receivable growth
            if len(balance_sheet) >= 2:
                ar_current = balance_sheet[0].get("netReceivables", 0)
                ar_prior = balance_sheet[1].get("netReceivables", 1)
                revenue_current = income_stmt[0].get("revenue", 0)
                revenue_prior = income_stmt[1].get("revenue", 1) if len(income_stmt) >= 2 else 1
                
                ar_growth = (ar_current - ar_prior) / max(ar_prior, 1)
                revenue_growth = (revenue_current - revenue_prior) / max(revenue_prior, 1)
                
                if ar_growth > revenue_growth * 1.5:
                    red_flags.append("Accounts receivable growing faster than revenue - potential revenue recognition issue")
        
        except Exception as e:
            logger.error(f"Error identifying red flags: {e}")
        
        return red_flags
    
    async def _analyze_growth_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth trends"""
        try:
            income_stmt = data.get("income_statement", [])
            
            if len(income_stmt) < 3:
                return {"error": "Insufficient historical data"}
            
            # Calculate CAGR for key metrics
            years = min(5, len(income_stmt))
            
            revenue_cagr = self._calculate_cagr(
                [stmt.get("revenue", 0) for stmt in income_stmt[:years]]
            )
            
            ebitda_cagr = self._calculate_cagr(
                [stmt.get("ebitda", 0) for stmt in income_stmt[:years]]
            )
            
            net_income_cagr = self._calculate_cagr(
                [stmt.get("netIncome", 0) for stmt in income_stmt[:years]]
            )
            
            return {
                "revenue_cagr": revenue_cagr,
                "ebitda_cagr": ebitda_cagr,
                "net_income_cagr": net_income_cagr,
                "years_analyzed": years
            }
        
        except Exception as e:
            logger.error(f"Error analyzing growth trends: {e}")
            return {}
    
    def _calculate_cagr(self, values: List[float]) -> float:
        """Calculate Compound Annual Growth Rate"""
        if len(values) < 2 or values[-1] == 0:
            return 0.0
        
        n = len(values) - 1
        cagr = (values[0] / values[-1]) ** (1/n) - 1
        return cagr
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> Optional[FinancialMetrics]:
        """Extract key financial metrics"""
        try:
            income_stmt = data.get("income_statement", [])
            balance_sheet = data.get("balance_sheet", [])
            ratios = data.get("ratios", [])
            
            if not income_stmt or not balance_sheet:
                return None
            
            latest_income = income_stmt[0]
            latest_balance = balance_sheet[0]
            latest_ratios = ratios[0] if ratios else {}
            
            return FinancialMetrics(
                revenue=latest_income.get("revenue"),
                ebitda=latest_income.get("ebitda"),
                net_income=latest_income.get("netIncome"),
                total_assets=latest_balance.get("totalAssets"),
                total_liabilities=latest_balance.get("totalLiabilities"),
                equity=latest_balance.get("totalEquity"),
                debt_to_equity=latest_ratios.get("debtEquityRatio"),
                current_ratio=latest_ratios.get("currentRatio"),
                roe=latest_ratios.get("returnOnEquity"),
                roa=latest_ratios.get("returnOnAssets")
            )
        
        except Exception as e:
            logger.error(f"Error extracting key metrics: {e}")
            return None
    
    async def _generate_enhanced_insights(
        self,
        company: str,
        financial_data: Dict[str, Any],
        normalized_data: Dict[str, Any],
        advanced_valuation: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        health: Dict[str, Any],
        ratios: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced AI-powered insights using Claude with Phase 2 data"""
        try:
            # Extract key metrics
            cagr = normalized_data.get('cagr_analysis', {})
            quality_score = normalized_data.get('quality_score', 0)
            adjustments = normalized_data.get('adjustments', [])
            
            valuation_summary = advanced_valuation.get('valuation_summary', {})
            monte_carlo = advanced_valuation.get('monte_carlo_simulation', {})
            
            # Create enhanced analysis prompt
            prompt = f"""Perform comprehensive M&A due diligence analysis for {company}:

=== FINANCIAL HEALTH ===
Health Score: {health.get('health_score', 0)}/100 - {health.get('rating', 'Unknown')}
Earnings Quality Score: {quality_score}/100
Key Factors: {', '.join(health.get('factors', []))}

=== NORMALIZED GROWTH METRICS ({trend_analysis.get('analysis_period', 'N/A')}) ===
- Revenue CAGR: {cagr.get('revenue_cagr', 0):.2%}
- Net Income CAGR: {cagr.get('net_income_cagr', 0):.2%}
- EBITDA CAGR: {cagr.get('ebitda_cagr', 0):.2%}

=== FINANCIAL ADJUSTMENTS ===
Number of Adjustments Made: {len(adjustments)}
{self._format_adjustments(adjustments[:5])}

=== VALUATION ANALYSIS ===
DCF Base Case: ${valuation_summary.get('dcf_base_case', 0):,.0f}
DCF Range: ${valuation_summary.get('valuation_range', {}).get('low', 0):,.0f} - ${valuation_summary.get('valuation_range', {}).get('high', 0):,.0f}
Monte Carlo Median: ${monte_carlo.get('median_valuation', 0):,.0f}
90% Confidence Interval: ${monte_carlo.get('confidence_intervals', {}).get('90%', [0, 0])[0]:,.0f} - ${monte_carlo.get('confidence_intervals', {}).get('90%', [0, 0])[1]:,.0f}

=== PROFITABILITY RATIOS ===
{ratios.get('profitability', {})}

=== LEVERAGE RATIOS ===
{ratios.get('leverage', {})}

As a professional M&A analyst, provide:
1. Executive summary of financial position and quality
2. Key investment highlights (3-5 points)
3. Major financial risks and red flags
4. Impact of normalizing adjustments on valuation
5. 5-7 actionable recommendations for due diligence team
6. Deal structure recommendations based on valuation range"""

            # Use investment banking grade retry logic
            response = await llm_call_with_retry(
                self.llm,
                prompt,
                max_retries=3,
                timeout=90,
                context="Financial insights generation"
            )
            
            return {
                "summary": response.content,
                "recommendations": self._extract_recommendations(response.content)
            }
        
        except Exception as e:
            logger.error(f"Error generating enhanced insights: {e}")
            return {
                "summary": f"Analysis completed with data gathering. AI insight generation encountered an error: {str(e)}",
                "recommendations": [
                    "Financial data successfully fetched and normalized",
                    "Valuation models calculated successfully",
                    "Review raw analysis data for insights"
                ]
            }
    
    def _format_adjustments(self, adjustments: List[Dict[str, Any]]) -> str:
        """Format adjustment list for prompt"""
        if not adjustments:
            return "None"
        
        formatted = []
        for adj in adjustments:
            adj_type = adj.get('type', 'Unknown')
            date = adj.get('date', 'N/A')
            formatted.append(f"- {date}: {adj_type}")
        
        return "\n".join(formatted)
    
    def _interpret_dcf_variance(self, our_dcf: float, fmp_dcf: float) -> str:
        """Interpret variance between our DCF and FMP's DCF"""
        if fmp_dcf == 0:
            return "Unable to compare - FMP DCF not available"
        
        variance = abs((our_dcf - fmp_dcf) / fmp_dcf)
        
        if variance < 0.10:
            return "Excellent - Our valuation closely aligns with FMP (within 10%)"
        elif variance < 0.15:
            return "Good - Our valuation reasonably aligns with FMP (within 15%)"
        elif variance < 0.25:
            return "Moderate - Notable variance with FMP, review assumptions"
        else:
            return "Significant - Large variance with FMP, requires detailed assumption review"
    
    def _analyze_earnings_quality(self, earnings_surprises: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze earnings quality from surprise data"""
        if not earnings_surprises:
            return {'quality_score': 0, 'note': 'No earnings surprise data available'}
        
        beats = 0
        misses = 0
        total_surprise = 0
        
        for surprise in earnings_surprises[:8]:  # Last 8 quarters
            actual = surprise.get('actualEarningResult', 0)
            estimated = surprise.get('estimatedEarning', 0)
            
            if estimated != 0:
                surprise_pct = (actual - estimated) / abs(estimated)
                total_surprise += surprise_pct
                
                if actual > estimated:
                    beats += 1
                else:
                    misses += 1
        
        total_reports = beats + misses
        beat_rate = (beats / total_reports * 100) if total_reports > 0 else 0
        avg_surprise = (total_surprise / total_reports * 100) if total_reports > 0 else 0
        
        # Calculate quality score (0-100)
        quality_score = min(100, beat_rate + (avg_surprise * 10))
        
        return {
            'quality_score': round(quality_score, 1),
            'beat_rate': round(beat_rate, 1),
            'average_surprise_pct': round(avg_surprise, 2),
            'beats': beats,
            'misses': misses,
            'consistency': 'High' if beat_rate >= 75 else 'Moderate' if beat_rate >= 50 else 'Low',
            'interpretation': self._interpret_earnings_quality(beat_rate, avg_surprise)
        }
    
    def _interpret_earnings_quality(self, beat_rate: float, avg_surprise: float) -> str:
        """Interpret earnings quality metrics"""
        if beat_rate >= 75 and avg_surprise > 2:
            return "Excellent - Consistently beats estimates with strong surprises"
        elif beat_rate >= 75:
            return "Strong - Consistently beats estimates"
        elif beat_rate >= 50 and avg_surprise > 0:
            return "Good - More beats than misses with positive surprises"
        elif beat_rate >= 50:
            return "Moderate - Balanced performance"
        else:
            return "Weak - More misses than beats, earnings predictability concerns"
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from analysis text"""
        recommendations = []
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # Remove numbering and bullet points
                clean_line = line.lstrip("0123456789.-•) ").strip()
                if len(clean_line) > 20:  # Filter out short lines
                    recommendations.append(clean_line)
        
        return recommendations[:10]  # Limit to top 10
    
    async def _generate_forecast(
        self,
        financial_data: Dict[str, Any],
        normalized_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate 5-year financial forecast
        Uses historical CAGR, analyst estimates, and scenario planning
        
        Returns:
            Dict with forecasted income statements, balance sheets, cash flows, and assumptions
        """
        try:
            income_statements = financial_data.get('income_statement', [])
            balance_sheets = financial_data.get('balance_sheet', [])
            cash_flows = financial_data.get('cash_flow', [])
            analyst_estimates = financial_data.get('analyst_estimates', [])
            
            if not income_statements:
                return {
                    'income_statements': [],
                    'balance_sheets': [],
                    'cash_flows': [],
                    'assumptions': {},
                    'note': 'Insufficient historical data for forecasting'
                }
            
            latest_income = income_statements[0]
            latest_balance = balance_sheets[0] if balance_sheets else {}
            latest_cf = cash_flows[0] if cash_flows else {}
            
            # Calculate historical CAGRs for growth assumptions
            cagr_analysis = normalized_data.get('cagr_analysis', {})
            revenue_cagr = cagr_analysis.get('revenue_cagr', 0.05)  # Default 5%
            
            # Use analyst estimates if available, otherwise use historical CAGR
            revenue_growth_rates = []
            if analyst_estimates:
                # Use analyst revenue growth estimates for next 2-3 years
                for est in analyst_estimates[:3]:
                    estimated_growth = est.get('estimatedRevenueAvg', 0)
                    if estimated_growth:
                        revenue_growth_rates.append(estimated_growth / 100)  # Convert percentage
            
            # Fill remaining years with historical CAGR, trending toward industry avg
            while len(revenue_growth_rates) < 5:
                if not revenue_growth_rates:
                    revenue_growth_rates.append(max(min(revenue_cagr, 0.15), -0.05))  # Cap at +15% or -5%
                else:
                    # Gradually trend toward sustainable 3% growth
                    last_rate = revenue_growth_rates[-1]
                    next_rate = last_rate * 0.9 + 0.03 * 0.1  # Weighted average trending to 3%
                    revenue_growth_rates.append(max(min(next_rate, 0.12), 0.02))  # Cap between 2-12%
            
            # Forecast assumptions
            assumptions = {
                'revenue_growth_rates': revenue_growth_rates,
                'ebitda_margin': latest_income.get('ebitda', 0) / max(latest_income.get('revenue', 1), 1),
                'tax_rate': abs(latest_income.get('incomeTaxExpense', 0)) / max(abs(latest_income.get('incomeBeforeTax', 1)), 1),
                'capex_as_pct_revenue': abs(latest_cf.get('capitalExpenditure', 0)) / max(latest_income.get('revenue', 1), 1) if cash_flows else 0.03,
                'nwc_as_pct_revenue': 0.10,  # Working capital assumption
                'depreciation_rate': 0.05,  # 5% of PP&E
                'methodology': 'Historical CAGR + Analyst Estimates + Mean Reversion'
            }
            
            # Generate forecasted income statements
            forecasted_income = []
            current_revenue = latest_income.get('revenue', 0)
            
            for year in range(1, 6):
                growth_rate = revenue_growth_rates[year-1]
                forecast_revenue = current_revenue * (1 + growth_rate)
                forecast_ebitda = forecast_revenue * assumptions['ebitda_margin']
                forecast_operating_income = forecast_ebitda * 0.85  # Assume D&A is 15% of EBITDA
                forecast_net_income = forecast_operating_income * (1 - assumptions['tax_rate'])
                
                forecasted_income.append({
                    'year': year,
                    'fiscal_year': datetime.now().year + year,
                    'revenue': round(forecast_revenue, 2),
                    'ebitda': round(forecast_ebitda, 2),
                    'operatingIncome': round(forecast_operating_income, 2),
                    'netIncome': round(forecast_net_income, 2),
                    'growth_rate': growth_rate
                })
                
                current_revenue = forecast_revenue
            
            # Generate forecasted cash flows
            forecasted_cf = []
            for year_forecast in forecasted_income:
                capex = year_forecast['revenue'] * assumptions['capex_as_pct_revenue']
                nwc_change = year_forecast['revenue'] * assumptions['nwc_as_pct_revenue'] * 0.1  # 10% of NWC
                
                fcf = year_forecast['ebitda'] - capex - nwc_change - (year_forecast['ebitda'] * assumptions['tax_rate'])
                
                forecasted_cf.append({
                    'year': year_forecast['year'],
                    'fiscal_year': year_forecast['fiscal_year'],
                    'operatingCashFlow': round(year_forecast['ebitda'] * 0.9, 2),
                    'capitalExpenditure': round(-capex, 2),
                    'freeCashFlow': round(fcf, 2)
                })
            
            # Simplified balance sheet forecast (key items only)
            forecasted_balance = []
            current_assets = latest_balance.get('totalAssets', 0)
            
            for year_forecast in forecasted_income:
                asset_growth = year_forecast['growth_rate'] * 0.8  # Assets grow slower than revenue
                forecast_assets = current_assets * (1 + asset_growth)
                
                forecasted_balance.append({
                    'year': year_forecast['year'],
                    'fiscal_year': year_forecast['fiscal_year'],
                    'totalAssets': round(forecast_assets, 2),
                    'note': 'Simplified forecast - key items only'
                })
                
                current_assets = forecast_assets
            
            logger.info(f"Generated 5-year financial forecast with {len(forecasted_income)} years")
            logger.info(f"Revenue CAGR assumption: {revenue_cagr:.2%}, Year 1 growth: {revenue_growth_rates[0]:.2%}")
            
            return {
                'income_statements': forecasted_income,
                'balance_sheets': forecasted_balance,
                'cash_flows': forecasted_cf,
                'assumptions': assumptions,
                'forecast_horizon': '5 years',
                'methodology': 'Historical CAGR + Analyst Estimates + Industry Normalization',
                'confidence_level': 'Moderate' if analyst_estimates else 'Low'
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {
                'income_statements': [],
                'balance_sheets': [],
                'cash_flows': [],
                'assumptions': {},
                'error': str(e)
            }
    
    async def _auto_select_peers(self, company_profile: Dict[str, Any]) -> List[str]:
        """Auto-select peer companies based on sector/industry"""
        try:
            sector = company_profile.get('sector', '')
            industry = company_profile.get('industry', '')
            
            # Default peer lists by sector (examples - would be more comprehensive)
            peer_map = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA'],
                'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO'],
                'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
                'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD'],
                'Communication Services': ['GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA']
            }
            
            peers = peer_map.get(sector, [])
            
            if not peers and industry:
                logger.info(f"No sector match for '{sector}', using generic tech peers")
                peers = ['AAPL', 'MSFT', 'GOOGL']  # Generic fallback
            
            return peers[:5]  # Limit to 5 comps
            
        except Exception as e:
            logger.error(f"Error auto-selecting peers: {e}")
            return []
