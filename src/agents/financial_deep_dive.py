"""
Financial Deep Dive Agent - Specialized financial analysis using Gemini 2.5 Pro

Focuses on the 13% gap in Investment Banking M&A coverage:
- Working Capital Analysis
- CapEx & Depreciation Deep Dive  
- Customer Concentration Analysis
- Segment Analysis
- Debt Schedule & Covenant Tracking

This agent complements the Financial Analyst to achieve 100% IB coverage.
"""
import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..core.llm_factory import get_llm
from ..utils.enhanced_valuation_engine import EnhancedValuationEngine
from ..utils.financial_calculator import FinancialCalculator
from ..utils.llm_retry import llm_call_with_retry

# CRITICAL FIX: Feature flags for cloud deployment optimization
ENABLE_SEC_DOCUMENTS = os.getenv('ENABLE_SEC_DOCUMENTS', 'false').lower() == 'true'
SEC_FETCH_TIMEOUT = int(os.getenv('SEC_FETCH_TIMEOUT', '120'))  # 2 minutes default


class FinancialDeepDiveAgent(BaseAgent):
    """
    Financial Deep Dive Agent - Specialized analysis for IB coverage gaps
    
    Uses Gemini 2.5 Pro for:
    - Pattern recognition in financial data
    - Structured data extraction from SEC filings
    - Long context analysis of footnotes
    - Detailed working capital and segment analysis
    """
    
    def __init__(self):
        """Initialize Financial Deep Dive Agent with Gemini 2.5 Pro"""
        super().__init__("financial_deep_dive")
        # Gemini 2.5 Pro is used by default (set in config via 'gemini' key)
        self.financial_calculator = FinancialCalculator()
        
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Execute deep dive financial analysis
        
        Args:
            state: Current diligence state with financial_data populated
            
        Returns:
            Deep dive analysis results
        """
        errors = []
        warnings = []
        recommendations = []
        
        target_company = state.get("target_company", "Unknown")
        target_ticker = state.get("target_ticker")
        
        if not target_ticker:
            errors.append("No ticker symbol provided")
            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        logger.info(f"[DEEP DIVE] Starting specialized financial analysis for {target_company} ({target_ticker})")
        
        # Get financial data from state using smart accessor (prioritizes normalized)
        financial_data_smart = self._get_financial_data_smart(state, prefer_normalized=True)
        financial_data = state.get('financial_data', {})  # Keep for SEC filing access
        normalized_financials = state.get('normalized_financials', {})  # Keep for quality metadata
        
        if not financial_data and not normalized_financials:
            errors.append("No financial data available. Financial Analyst must run first.")
            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        # Log data source being used
        data_source = financial_data_smart.get('source', 'unknown')
        quality_score = financial_data_smart.get('quality_score', 'N/A')
        logger.info(f"[DEEP DIVE] Using {data_source} financial data (quality: {quality_score})")
        
        # CRITICAL FIX: Conditional SEC document fetching with timeout controls
        sec_cache = {}
        
        if ENABLE_SEC_DOCUMENTS and target_ticker:
            logger.info(f"[DEEP DIVE] Pre-fetching SEC documents with {SEC_FETCH_TIMEOUT}s timeout...")
            try:
                from ..integrations.sec_client import get_sec_client
                sec_client = get_sec_client()
                
                # Fetch 10-K with timeout
                logger.info(f"[DEEP DIVE] Fetching 10-K for {target_ticker}...")
                try:
                    filing_10k = await asyncio.wait_for(
                        sec_client.get_filing_full_text(target_ticker, '10-K'),
                        timeout=SEC_FETCH_TIMEOUT
                    )
                    if 'full_text' in filing_10k:
                        sec_cache['10k_text'] = filing_10k['full_text']
                        logger.info(f"✓ 10-K cached ({len(sec_cache['10k_text'])//1000}KB)")
                    else:
                        warnings.append("Could not fetch 10-K filing")
                except asyncio.TimeoutError:
                    logger.warning(f"10-K fetch timed out after {SEC_FETCH_TIMEOUT}s - skipping SEC data")
                    warnings.append(f"SEC 10-K fetch timed out - using FMP data only")
                    sec_cache['10k_text'] = ''
                
                # Fetch DEF 14A with timeout
                logger.info(f"[DEEP DIVE] Fetching DEF 14A proxy for {target_ticker}...")
                try:
                    proxy_data = await asyncio.wait_for(
                        sec_client.extract_proxy_data(target_ticker),
                        timeout=SEC_FETCH_TIMEOUT
                    )
                    if 'error' not in proxy_data:
                        sec_cache['proxy_data'] = proxy_data
                        logger.info(f"✓ Proxy data extracted: {proxy_data.get('executive_compensation', {}).get('count', 0)} items")
                        state['proxy_compensation'] = proxy_data
                    else:
                        warnings.append(f"Proxy data extraction: {proxy_data.get('error')}")
                        sec_cache['proxy_data'] = {}
                except asyncio.TimeoutError:
                    logger.warning(f"Proxy fetch timed out after {SEC_FETCH_TIMEOUT}s")
                    warnings.append(f"SEC proxy fetch timed out")
                    sec_cache['proxy_data'] = {}
                    
            except Exception as e:
                logger.error(f"Error pre-fetching SEC documents: {e}")
                warnings.append(f"SEC document fetch error: {str(e)}")
        else:
            logger.info(f"[DEEP DIVE] SEC document fetching disabled (ENABLE_SEC_DOCUMENTS={ENABLE_SEC_DOCUMENTS})")
            logger.info(f"[DEEP DIVE] Using FMP API data only for faster cloud performance")
            warnings.append("SEC document analysis disabled - using FMP data only (faster performance)")
        
        # Run all 6 specialized analyses in parallel with cached SEC data
        logger.info("[DEEP DIVE] Running 6 specialized analyses in parallel (using cached SEC filings)...")
        
        analyses = await asyncio.gather(
            self._analyze_working_capital(financial_data, target_ticker, normalized_financials),
            self._analyze_capex_depreciation(financial_data, target_ticker, normalized_financials),
            self._analyze_customer_concentration(financial_data, target_ticker, state, normalized_financials, sec_cache),
            self._analyze_segments(financial_data, target_ticker, normalized_financials, sec_cache),
            self._analyze_debt_schedule(financial_data, target_ticker, state),
            self._analyze_compensation_impact(sec_cache.get('proxy_data', {}), financial_data, target_ticker),
            return_exceptions=True
        )
        
        # Process results and collect errors/warnings
        working_capital = analyses[0]
        capex_analysis = analyses[1]
        customer_concentration = analyses[2]
        segment_analysis = analyses[3]
        debt_schedule = analyses[4]
        compensation_analysis = analyses[5]
        
        # Handle exceptions and error dictionaries
        if isinstance(working_capital, Exception):
            warnings.append(f"Working capital analysis failed: {str(working_capital)}")
            working_capital = {}
        elif isinstance(working_capital, dict) and 'error' in working_capital:
            warnings.append(f"Working capital analysis: {working_capital['error']}")
            working_capital = {}
            
        if isinstance(capex_analysis, Exception):
            warnings.append(f"CapEx analysis failed: {str(capex_analysis)}")
            capex_analysis = {}
        elif isinstance(capex_analysis, dict) and 'error' in capex_analysis:
            warnings.append(f"CapEx analysis: {capex_analysis['error']}")
            capex_analysis = {}
            
        if isinstance(customer_concentration, Exception):
            warnings.append(f"Customer concentration analysis failed: {str(customer_concentration)}")
            customer_concentration = {}
        elif isinstance(customer_concentration, dict) and 'error' in customer_concentration:
            warnings.append(f"Customer concentration analysis: {customer_concentration['error']}")
            customer_concentration = {}
            
        if isinstance(segment_analysis, Exception):
            warnings.append(f"Segment analysis failed: {str(segment_analysis)}")
            segment_analysis = {}
        elif isinstance(segment_analysis, dict) and 'error' in segment_analysis:
            warnings.append(f"Segment analysis: {segment_analysis['error']}")
            segment_analysis = {}
            
        if isinstance(debt_schedule, Exception):
            warnings.append(f"Debt schedule analysis failed: {str(debt_schedule)}")
            debt_schedule = {}
        elif isinstance(debt_schedule, dict) and 'error' in debt_schedule:
            warnings.append(f"Debt schedule analysis: {debt_schedule['error']}")
            debt_schedule = {}
        
        if isinstance(compensation_analysis, Exception):
            warnings.append(f"Compensation analysis failed: {str(compensation_analysis)}")
            compensation_analysis = {}
        elif isinstance(compensation_analysis, dict) and 'error' in compensation_analysis:
            warnings.append(f"Compensation analysis: {compensation_analysis['error']}")
            compensation_analysis = {}
        
        # NEW: Detect financial deep dive anomalies
        logger.info("[DEEP DIVE] Detecting financial operational anomalies...")
        deep_dive_anomalies = await self._detect_deep_dive_anomalies(
            working_capital, capex_analysis, customer_concentration, 
            segment_analysis, debt_schedule, state
        )
        
        # Log deep dive anomalies to centralized log
        if deep_dive_anomalies.get('anomalies_detected'):
            for anomaly in deep_dive_anomalies['anomalies_detected']:
                self.log_anomaly(
                    anomaly_type=anomaly.get('type', 'operational_anomaly'),
                    description=anomaly.get('description', 'Financial operational anomaly detected'),
                    severity=anomaly.get('severity', 'medium'),
                    data=anomaly
                )
        
        # Generate overall insights
        insights = await self._generate_deep_dive_insights(
            target_company,
            working_capital,
            capex_analysis,
            customer_concentration,
            segment_analysis,
            debt_schedule
        )
        
        # Handle insights generation errors
        if isinstance(insights, dict) and 'error' in insights:
            warnings.append(f"Insights generation: {insights['error']}")
            insights = {}
        
        # Compile recommendations
        if working_capital.get('recommendations'):
            recommendations.extend(working_capital['recommendations'])
        if capex_analysis.get('recommendations'):
            recommendations.extend(capex_analysis['recommendations'])
        if customer_concentration.get('risk_level') == 'High':
            warnings.append("High customer concentration detected")
        
        # Update state
        state['financial_deep_dive'] = {
            'working_capital': working_capital,
            'capex_analysis': capex_analysis,
            'customer_concentration': customer_concentration,
            'segment_analysis': segment_analysis,
            'debt_schedule': debt_schedule,
            'compensation_analysis': compensation_analysis,
            'insights': insights
        }
        
        # Log what was stored (matching financial_analyst pattern)
        deep_dive_keys = list(state['financial_deep_dive'].keys())
        logger.info(f"✓ Stored {len(deep_dive_keys)} keys in state['financial_deep_dive']: {deep_dive_keys}")
        logger.info(f"📊 Deep dive output ready for Synthesis Agent and Report Generators")
        
        logger.info("[DEEP DIVE] Specialized financial analysis complete")
        
        return {
            "data": {
                'working_capital': working_capital,
                'capex_analysis': capex_analysis,
                'customer_concentration': customer_concentration,
                'segment_analysis': segment_analysis,
                'debt_schedule': debt_schedule,
                'compensation_analysis': compensation_analysis,
                'insights': insights
            },
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    async def _analyze_working_capital(self, financial_data: Dict[str, Any], ticker: str, normalized_financials: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        MODULE 1: Working Capital Analysis
        Detailed NWC trends, cash conversion cycle, efficiency metrics
        """
        logger.info(f"[DEEP DIVE] Module 1: Working Capital Analysis for {ticker}")
        
        try:
            balance_sheets = financial_data.get('balance_sheet', [])
            income_statements = financial_data.get('income_statement', [])
            
            if not balance_sheets or not income_statements:
                return {'error': 'Insufficient data for working capital analysis'}
            
            # Calculate NWC for last 5 years
            nwc_trend = []
            for i, bs in enumerate(balance_sheets[:5]):
                current_assets = bs.get('totalCurrentAssets', 0)
                current_liabilities = bs.get('totalCurrentLiabilities', 0)
                cash = bs.get('cashAndCashEquivalents', 0)
                
                # NWC = Current Assets - Current Liabilities - Cash
                nwc = current_assets - current_liabilities - cash
                
                # Calculate as % of revenue
                if i < len(income_statements):
                    revenue = income_statements[i].get('revenue', 1)
                    nwc_pct_revenue = (nwc / revenue * 100) if revenue > 0 else 0
                else:
                    nwc_pct_revenue = 0
                
                nwc_trend.append({
                    'year': bs.get('date', 'Unknown'),
                    'nwc': nwc,
                    'current_assets': current_assets,
                    'current_liabilities': current_liabilities,
                    'cash': cash,
                    'nwc_pct_revenue': round(nwc_pct_revenue, 2),
                    'revenue': income_statements[i].get('revenue', 0) if i < len(income_statements) else 0
                })
            
            # Calculate Cash Conversion Cycle using FinancialCalculator
            latest_bs = balance_sheets[0]
            latest_is = income_statements[0] if income_statements else {}
            
            inventory = latest_bs.get('inventory', 0)
            receivables = latest_bs.get('netReceivables', 0)
            payables = latest_bs.get('accountPayables', 0)
            revenue = latest_is.get('revenue', 1)
            cogs = latest_is.get('costOfRevenue', None)
            
            # Use FinancialCalculator for deterministic working capital calculations
            wc_calc = self.financial_calculator.calculate_working_capital(
                accounts_receivable=receivables,
                inventory=inventory,
                accounts_payable=payables,
                revenue=revenue,
                cost_of_goods_sold=cogs
            )
            
            # Extract calculated values
            dio = wc_calc.get('dio', 0)
            dso = wc_calc.get('dso', 0)
            dpo = wc_calc.get('dpo', 0)
            ccc = wc_calc.get('cash_conversion_cycle', 0)
            
            # Calculate volatility using FinancialCalculator
            nwc_values = [item['nwc'] for item in nwc_trend]
            volatility_calc = self.financial_calculator.calculate_volatility(nwc_values)
            volatility = volatility_calc.get('volatility', 0)
            volatility_assessment = volatility_calc.get('assessment', 'Moderate')
            
            # Calculate statistics using FinancialCalculator
            nwc_pct_values = [item['nwc_pct_revenue'] for item in nwc_trend]
            stats = self.financial_calculator.calculate_statistics(nwc_pct_values)
            avg_nwc_pct = stats.get('mean', 0)
            
            # Efficiency score using FinancialCalculator (CCC component)
            # Benchmark: 60 days is good, 0 days is excellent
            ccc_efficiency = self.financial_calculator.calculate_efficiency_score(
                actual_value=ccc,
                benchmark_value=60,
                score_type='lower_is_better'
            )
            ccc_score = ccc_efficiency.get('score', 50)
            
            # NWC efficiency (lower % of revenue is better)
            # CRITICAL FIX: Don't use abs() - negative NWC can be efficient for financial services
            nwc_efficiency_calc = self.financial_calculator.calculate_efficiency_score(
                actual_value=avg_nwc_pct,  # Allow negative values - efficient for brokerages
                benchmark_value=15,
                score_type='lower_is_better'
            )
            nwc_score = nwc_efficiency_calc.get('score', 50)
            
            efficiency_score = (ccc_score + nwc_score) / 2
            
            result = {
                'nwc_analysis': {
                    'historical_trend': nwc_trend,
                    'average_nwc_pct_revenue': round(avg_nwc_pct, 2),
                    'latest_nwc': nwc_trend[0]['nwc'] if nwc_trend else 0,
                    'cash_conversion_cycle': {
                        'days_inventory_outstanding': round(dio, 1),
                        'days_sales_outstanding': round(dso, 1),
                        'days_payables_outstanding': round(dpo, 1),
                        'ccc_days': round(ccc, 1)
                    },
                    'efficiency_score': round(efficiency_score, 1),
                    'volatility': round(volatility, 3),
                    'volatility_assessment': volatility_assessment
                },
                'interpretation': self._interpret_working_capital(ccc, avg_nwc_pct, efficiency_score),
                'recommendations': self._generate_nwc_recommendations(ccc, avg_nwc_pct, volatility_assessment)
            }
            
            logger.info(f"[DEEP DIVE] Working Capital: CCC={ccc:.1f} days, Efficiency={efficiency_score:.1f}/100")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in working capital analysis: {e}")
            return {'error': str(e)}
    
    async def _analyze_capex_depreciation(self, financial_data: Dict[str, Any], ticker: str, normalized_financials: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        MODULE 2: CapEx & Depreciation Deep Dive
        Maintenance vs growth CapEx, intensity analysis, future requirements
        """
        logger.info(f"[DEEP DIVE] Module 2: CapEx & Depreciation Analysis for {ticker}")
        
        try:
            cash_flows = financial_data.get('cash_flow', [])
            income_statements = financial_data.get('income_statement', [])
            
            if not cash_flows or not income_statements:
                return {'error': 'Insufficient data for CapEx analysis'}
            
            # Analyze last 5 years
            capex_trend = []
            for i, cf in enumerate(cash_flows[:5]):
                capex = abs(cf.get('capitalExpenditure', 0))
                da = abs(cf.get('depreciationAndAmortization', 0))
                
                if i < len(income_statements):
                    revenue = income_statements[i].get('revenue', 1)
                    capex_pct_revenue = (capex / revenue * 100) if revenue > 0 else 0
                    rd_expense = income_statements[i].get('researchAndDevelopmentExpenses', 0)
                else:
                    capex_pct_revenue = 0
                    rd_expense = 0
                
                capex_to_da = (capex / da) if da > 0 else 0
                
                capex_trend.append({
                    'year': cf.get('date', 'Unknown'),
                    'capex': capex,
                    'depreciation_amortization': da,
                    'capex_pct_revenue': round(capex_pct_revenue, 2),
                    'capex_to_da_ratio': round(capex_to_da, 2),
                    'rd_expense': rd_expense
                })
            
            # Estimate maintenance vs growth CapEx
            # Rule of thumb: Maintenance CapEx ≈ D&A
            latest = capex_trend[0] if capex_trend else {}
            total_capex = latest.get('capex', 0)
            da = latest.get('depreciation_amortization', 0)
            
            # Maintenance CapEx = min(CapEx, D&A)
            maintenance_capex = min(total_capex, da)
            growth_capex = max(0, total_capex - maintenance_capex)
            
            maintenance_pct = (maintenance_capex / total_capex * 100) if total_capex > 0 else 0
            growth_pct = (growth_capex / total_capex * 100) if total_capex > 0 else 0
            
            # Asset intensity using FinancialCalculator
            capex_pct_values = [item['capex_pct_revenue'] for item in capex_trend]
            capex_stats = self.financial_calculator.calculate_statistics(capex_pct_values)
            avg_capex_pct = capex_stats.get('mean', 0)
            
            # Classify intensity using FinancialCalculator
            intensity_calc = self.financial_calculator.classify_intensity(
                percentage=avg_capex_pct,
                low_threshold=7.0,
                high_threshold=15.0
            )
            asset_intensity = intensity_calc.get('classification', 'Medium')
            
            # R&D capitalization potential
            rd_current = latest.get('rd_expense', 0)
            estimated_capitalizable = rd_current * 0.3  # Estimate 30% capitalizable
            
            result = {
                'capex_analysis': {
                    'total_capex': total_capex,
                    'maintenance_capex': round(maintenance_capex, 0),
                    'growth_capex': round(growth_capex, 0),
                    'maintenance_capex_pct': round(maintenance_pct, 1),
                    'growth_capex_pct': round(growth_pct, 1),
                    'capex_to_revenue_trend': capex_trend,
                    'avg_capex_pct_revenue': round(avg_capex_pct, 2),
                    'avg_capex_to_da_ratio': round(np.mean([item['capex_to_da_ratio'] for item in capex_trend]), 2),
                    'asset_intensity': asset_intensity,
                    'rd_capitalization': {
                        'current_rd_expense': rd_current,
                        'estimated_capitalizable': round(estimated_capitalizable, 0),
                        'capitalization_pct': 30
                    }
                },
                'interpretation': self._interpret_capex(maintenance_pct, avg_capex_pct, asset_intensity),
                'recommendations': self._generate_capex_recommendations(growth_capex, total_capex, asset_intensity)
            }
            
            logger.info(f"[DEEP DIVE] CapEx: {maintenance_pct:.1f}% maintenance, {growth_pct:.1f}% growth")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in CapEx analysis: {e}")
            return {'error': str(e)}
    
    async def _analyze_customer_concentration(
        self,
        financial_data: Dict[str, Any],
        ticker: str,
        state: DiligenceState,
        normalized_financials: Dict[str, Any] = None,
        sec_cache: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        MODULE 3: Customer Concentration Analysis - REAL DATA from SEC filings
        Uses cached 10-K text to avoid redundant API calls
        """
        logger.info(f"[DEEP DIVE] Module 3: Customer Concentration Analysis for {ticker}")
        
        try:
            import re
            
            profile = financial_data.get('profile', {})
            
            # Use cached 10-K text
            logger.info(f"[DEEP DIVE] Using cached 10-K for customer concentration...")
            
            customer_disclosures = []
            geographic_revenue_data = {}
            concentration_risk = 'Low'  # Default
            
            try:
                # CRITICAL FIX: Use cached 10-K text instead of re-fetching
                text = sec_cache.get('10k_text', '') if sec_cache else ''
                
                if text:
                    
                    # Search for customer concentration disclosures
                    customer_patterns = [
                        r'(?:no\s+(?:single|individual)\s+customer.*?(?:represents|accounts\s+for|comprised).*?(\d+)%)',
                        r'(?:largest|significant)\s+customer.*?(\d+)%',
                        r'(\d+)%\s+of.*?(?:revenue|sales).*?(?:single|one)\s+customer',
                        r'customer.*?concentration.*?(\d+)%'
                    ]
                    
                    for pattern in customer_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            for match in matches[:3]:  # Top 3 findings
                                try:
                                    pct = float(match) if isinstance(match, str) else float(match[0]) if isinstance(match, tuple) else 0
                                    if 5 <= pct <= 100:  # Reasonable percentage
                                        customer_disclosures.append({
                                            'percentage': pct,
                                            'note': 'Extracted from 10-K disclosure'
                                        })
                                except:
                                    pass
                    
                    # Determine concentration risk
                    if customer_disclosures:
                        max_customer_pct = max([d['percentage'] for d in customer_disclosures])
                        if max_customer_pct > 20:
                            concentration_risk = 'High'
                        elif max_customer_pct > 10:
                            concentration_risk = 'Moderate'
                        else:
                            concentration_risk = 'Low'
                    
                    # Search for geographic revenue disclosures
                    geo_patterns = [
                        r'(?:united\s+states|domestic|americas?).*?(\d+)%',
                        r'(?:europe|emea).*?(\d+)%',
                        r'(?:asia|apac|china).*?(\d+)%'
                    ]
                    
                    for pattern in geo_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            for match in matches[:2]:
                                try:
                                    pct = float(match) if isinstance(match, str) else float(match[0]) if isinstance(match, tuple) else 0
                                    if 10 <= pct <= 100:
                                        region = 'extracted_from_10K'
                                        if 'united states' in pattern.lower() or 'domestic' in pattern.lower():
                                            region = 'north_america'
                                        elif 'europe' in pattern.lower():
                                            region = 'europe'
                                        elif 'asia' in pattern.lower():
                                            region = 'asia_pacific'
                                        geographic_revenue_data[region] = pct
                                except:
                                    pass
                
            except Exception as parse_error:
                logger.warning(f"Error parsing cached 10-K: {parse_error}")
                # Fall back to profile-based estimates if parsing fails
                country = profile.get('country', 'US')
                if country == 'US':
                    geographic_revenue_data = {
                        'north_america': 65,
                        'europe': 20,
                        'asia_pacific': 10,
                        'other': 5,
                        'note': 'Estimated from company profile (cached 10-K parsing failed)'
                    }
            
            # Build result
            result = {
                'customer_analysis': {
                    'customer_disclosures': customer_disclosures if customer_disclosures else [],
                    'has_customer_data': len(customer_disclosures) > 0,
                    'max_customer_concentration': max([d['percentage'] for d in customer_disclosures]) if customer_disclosures else None,
                    'concentration_risk': concentration_risk,
                    'geographic_breakdown': geographic_revenue_data if geographic_revenue_data else {'note': 'Not disclosed in 10-K'},
                    'data_source': '10-K Filing' if customer_disclosures or geographic_revenue_data else 'Profile Estimates'
                },
                'interpretation': f"Customer concentration risk: {concentration_risk}. " + 
                                (f"Largest customer: {max([d['percentage'] for d in customer_disclosures]):.0f}% of revenue" if customer_disclosures else "No specific customer disclosures found."),
                'recommendations': [
                    "Monitor customer concentration for M&A risk" if concentration_risk in ['High', 'Moderate'] else "Customer base appears diversified",
                    "Review 10-K footnotes for additional customer details",
                    "Assess customer retention and churn metrics"
                ],
                'risk_level': concentration_risk
            }
            
            logger.info(f"[DEEP DIVE] Customer Concentration: Risk={concentration_risk}, Disclosures={len(customer_disclosures)}")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in customer concentration analysis: {e}")
            return {'error': str(e)}
    
    async def _analyze_segments(self, financial_data: Dict[str, Any], ticker: str, normalized_financials: Dict[str, Any] = None, sec_cache: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        MODULE 4: Segment Analysis - REAL DATA from SEC 10-K
        Uses cached 10-K text to avoid redundant API calls
        """
        logger.info(f"[DEEP DIVE] Module 4: Segment Analysis for {ticker}")
        
        try:
            import re
            
            income_statements = financial_data.get('income_statement', [])
            
            if not income_statements:
                return {'error': 'Insufficient data for segment analysis'}
            
            latest_is = income_statements[0]
            total_revenue = latest_is.get('revenue', 0)
            
            # Use cached 10-K text
            logger.info(f"[DEEP DIVE] Using cached 10-K for segment reporting...")
            
            segments_found = []
            
            try:
                # CRITICAL FIX: Use cached 10-K text instead of re-fetching
                text = sec_cache.get('10k_text', '') if sec_cache else ''
                
                if text:
                    
                    # Search for segment revenue patterns
                    segment_patterns = [
                        r'(\w+(?:\s+\w+)*)\s+segment.*?revenue.*?\$?([\d,]+)\s*(?:million|billion)?',
                        r'revenue.*?(\w+(?:\s+\w+)*)\s+segment.*?\$?([\d,]+)',
                        r'(\w+(?:\s+\w+)*)\s+business.*?revenue.*?\$?([\d,]+)'
                    ]
                    
                    for pattern in segment_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches and len(matches) >= 2:  # At least 2 segments
                            for match in matches[:5]:  # Top 5 segments
                                try:
                                    if isinstance(match, tuple) and len(match) >= 2:
                                        segment_name = match[0].strip()
                                        revenue_str = match[1].replace(',', '')
                                        
                                        # Skip if segment name is too short or generic
                                        if len(segment_name) > 2 and segment_name.lower() not in ['the', 'and', 'for', 'our']:
                                            segments_found.append({
                                                'name': segment_name,
                                                'revenue': revenue_str,
                                                'source': '10-K Filing'
                                            })
                                except:
                                    pass
                            if segments_found:
                                break  # Found segments, stop searching
                    
                    # Calculate segment percentages if we have data
                    if segments_found and total_revenue > 0:
                        for segment in segments_found:
                            try:
                                seg_rev = float(segment['revenue'])
                                segment['revenue_pct'] = round((seg_rev / total_revenue) * 100, 1) if total_revenue > 0 else 0
                            except:
                                segment['revenue_pct'] = None
                
            except Exception as parse_error:
                logger.warning(f"Error parsing 10-K for segments: {parse_error}")
            
            # Build result
            if segments_found:
                result = {
                    'segment_analysis': {
                        'segments_identified': len(segments_found),
                        'segments': segments_found,
                        'total_revenue': total_revenue,
                        'data_source': '10-K Filing',
                        'has_real_data': True
                    },
                    'interpretation': f"Identified {len(segments_found)} business segments from 10-K disclosures.",
                    'recommendations': [
                        "Deep dive into segment profitability and margins",
                        "Analyze YoY growth rates by segment",
                        "Identify strategic vs. non-core segments for divestiture opportunities"
                    ]
                }
            else:
                # No segments found - may be single-segment company
                result = {
                    'segment_analysis': {
                        'segments_identified': 0,
                        'total_revenue': total_revenue,
                        'note': 'No segment disclosures found in 10-K. Company may operate as single segment.',
                        'data_source': '10-K Filing (no segments disclosed)',
                        'has_real_data': False
                    },
                    'interpretation': "Company appears to operate as single integrated business or segment disclosures not found.",
                    'recommendations': [
                        "Verify if company reports segments in 10-K footnotes",
                        "Analyze by product line or geography if disclosed elsewhere",
                        "Assess business model as single integrated operation"
                    ]
                }
            
            logger.info(f"[DEEP DIVE] Segment Analysis: {len(segments_found)} segments identified")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in segment analysis: {e}")
            return {'error': str(e)}
    
    async def _analyze_debt_schedule(
        self,
        financial_data: Dict[str, Any],
        ticker: str,
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        MODULE 5: Debt Schedule & Covenant Analysis
        Maturity schedule, covenant compliance, refinancing risk
        """
        logger.info(f"[DEEP DIVE] Module 5: Debt Schedule Analysis for {ticker}")
        
        try:
            balance_sheets = financial_data.get('balance_sheet', [])
            ratios = financial_data.get('ratios', [])
            
            if not balance_sheets:
                return {'error': 'Insufficient data for debt analysis'}
            
            latest_bs = balance_sheets[0]
            latest_ratios = ratios[0] if ratios else {}
            
            # Debt components
            total_debt = latest_bs.get('totalDebt', 0)
            short_term_debt = latest_bs.get('shortTermDebt', 0)
            long_term_debt = latest_bs.get('longTermDebt', 0)
            
            # Calculate debt metrics
            total_equity = latest_bs.get('totalEquity', 1)
            debt_to_equity = total_debt / total_equity if total_equity > 0 else 0
            
            # CRITICAL FIX: Calculate interest coverage properly for cash-rich companies
            # Try to get from ratios first, then calculate manually
            interest_coverage = latest_ratios.get('interestCoverage', 0)
            
            # If not available or zero, calculate manually from income statement
            if interest_coverage == 0:
                income_statements = financial_data.get('income_statement', [])
                if income_statements:
                    latest_is = income_statements[0]
                    ebit = latest_is.get('operatingIncome', 0)
                    interest_expense = latest_is.get('interestExpense', 0)
                    
                    # Handle cash-rich companies with minimal/no debt
                    if interest_expense == 0:
                        # No meaningful debt service - set to very high value
                        interest_coverage = 999.0
                        logger.info(f"[DEEP DIVE] No interest expense detected - setting coverage to {interest_coverage}x (cash-rich company)")
                    elif interest_expense > 0 and ebit > 0:
                        interest_coverage = ebit / interest_expense
                        logger.info(f"[DEEP DIVE] Calculated interest coverage: {interest_coverage:.2f}x")
                    elif interest_expense < 0:  # Interest income
                        interest_coverage = 999.0
                        logger.info(f"[DEEP DIVE] Company has interest income - setting coverage to {interest_coverage}x")
            
            # Maturity profile (would parse from 10-K debt footnotes)
            # Placeholder structure
            maturity_schedule = [
                {
                    'year': '2025',
                    'amount': short_term_debt,
                    'type': 'Short-term debt',
                    'note': 'Due within 1 year'
                },
                {
                    'year': '2026-2030',
                    'amount': long_term_debt,
                    'type': 'Long-term debt',
                    'note': 'Parse 10-K for detailed maturity schedule'
                }
            ]
            
            # Covenant compliance (would parse from credit agreements)
            covenant_compliance = {
                'leverage_ratio': {
                    'actual': round(debt_to_equity, 2),
                    'covenant': 'Parse from credit agreement',
                    'headroom': 'To be determined'
                },
                'interest_coverage': {
                    'actual': round(interest_coverage, 2),
                    'covenant': 'Typically 3.0x minimum',
                    'headroom': 'Good' if interest_coverage > 4.0 else 'Moderate' if interest_coverage > 2.5 else 'Tight'
                }
            }
            
            # Refinancing risk
            refinancing_risk = 'Low' if short_term_debt / total_debt < 0.3 else 'Moderate' if short_term_debt / total_debt < 0.5 else 'High'
            
            result = {
                'debt_analysis': {
                    'total_debt': total_debt,
                    'short_term_debt': short_term_debt,
                    'long_term_debt': long_term_debt,
                    'debt_to_equity': round(debt_to_equity, 2),
                    'maturity_schedule': maturity_schedule,
                    'covenant_compliance': covenant_compliance,
                    'interest_rate_exposure': {
                        'note': 'Parse from 10-K debt footnotes for fixed vs floating breakdown'
                    },
                    'refinancing_risk': refinancing_risk
                },
                'interpretation': self._interpret_debt(debt_to_equity, interest_coverage, refinancing_risk),
                'recommendations': [
                    "Review credit agreements for covenant details",
                    "Parse 10-K debt footnotes for maturity schedule",
                    "Assess refinancing timing and market conditions",
                    "Evaluate interest rate hedge positions"
                ]
            }
            
            logger.info(f"[DEEP DIVE] Debt Analysis: D/E={debt_to_equity:.2f}, Coverage={interest_coverage:.2f}x")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in debt analysis: {e}")
            return {'error': str(e)}
    
    async def _analyze_compensation_impact(
        self,
        proxy_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        ticker: str
    ) -> Dict[str, Any]:
        """
        MODULE 6: Executive Compensation Impact Analysis (from DEF 14A)
        Analyzes compensation structure, SBC impact, golden parachutes
        """
        logger.info(f"[DEEP DIVE] Module 6: Compensation Analysis for {ticker}")
        
        try:
            if not proxy_data or 'error' in proxy_data:
                return {'note': 'Proxy data not available for compensation analysis'}
            
            exec_comp = proxy_data.get('executive_compensation', {})
            related_parties = proxy_data.get('related_party_transactions', {})
            
            # Extract key compensation findings
            comp_findings = exec_comp.get('excerpts', [])[:3]
            rpt_findings = related_parties.get('excerpts', [])[:3]
            
            # Get financial context
            income_statements = financial_data.get('income_statement', [])
            if income_statements:
                latest_is = income_statements[0]
                revenue = latest_is.get('revenue', 1)
                operating_income = latest_is.get('operatingIncome', 0)
            else:
                revenue = 1
                operating_income = 0
            
            # Analyze impact
            result = {
                'compensation_structure': {
                    'executive_compensation_disclosed': exec_comp.get('found', False),
                    'count': exec_comp.get('count', 0),
                    'key_findings': [f['context'][:200] for f in comp_findings] if comp_findings else [],
                    'analysis_note': 'Review DEF 14A Summary Compensation Table for detailed breakdown'
                },
                'related_party_transactions': {
                    'found': related_parties.get('found', False),
                    'count': related_parties.get('count', 0),
                    'key_findings': [f['context'][:200] for f in rpt_findings] if rpt_findings else [],
                    'financial_impact': 'Assess materiality relative to financial statements'
                },
                'ma_considerations': {
                    'change_of_control': 'Review proxy for golden parachute provisions',
                    'retention_risk': 'High' if exec_comp.get('count', 0) > 10 else 'Moderate',
                    'sbc_impact': 'Evaluate stock-based compensation acceleration upon change of control'
                }
            }
            
            logger.info(f"[DEEP DIVE] Compensation: {exec_comp.get('count', 0)} items found")
            return result
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error in compensation analysis: {e}")
            return {'error': str(e)}
    
    async def _generate_deep_dive_insights(
        self,
        company: str,
        working_capital: Dict,
        capex: Dict,
        customer: Dict,
        segment: Dict,
        debt: Dict
    ) -> Dict[str, Any]:
        """Generate AI-powered insights from deep dive analysis"""
        try:
            # Extract key findings
            ccc = working_capital.get('nwc_analysis', {}).get('cash_conversion_cycle', {}).get('ccc_days', 0)
            nwc_efficiency = working_capital.get('nwc_analysis', {}).get('efficiency_score', 0)
            
            capex_intensity = capex.get('capex_analysis', {}).get('avg_capex_pct_revenue', 0)
            maintenance_pct = capex.get('capex_analysis', {}).get('maintenance_capex_pct', 0)
            
            debt_ratio = debt.get('debt_analysis', {}).get('debt_to_equity', 0)
            interest_coverage = debt.get('debt_analysis', {}).get('covenant_compliance', {}).get('interest_coverage', {}).get('actual', 0)
            
            # Create summary prompt
            prompt = f"""As a specialized financial analyst, provide executive-level insights on {company}'s financial operations:

WORKING CAPITAL:
- Cash Conversion Cycle: {ccc:.1f} days
- NWC Efficiency Score: {nwc_efficiency:.1f}/100

CAPITAL INTENSITY:
- CapEx as % Revenue: {capex_intensity:.2f}%
- Maintenance CapEx: {maintenance_pct:.1f}% of total

LEVERAGE:
- Debt/Equity: {debt_ratio:.2f}x
- Interest Coverage: {interest_coverage:.2f}x

Provide:
1. Executive summary of operational efficiency (2-3 sentences)
2. Key strengths (2-3 points)
3. Areas of concern (1-2 points)
4. Impact on valuation and deal structure (2-3 sentences)"""

            response = await llm_call_with_retry(
                self.llm,
                prompt,
                max_retries=3,
                timeout=60,
                context="Deep dive insights generation"
            )
            
            return {
                'summary': response.content,
                'key_metrics': {
                    'cash_conversion_cycle': round(ccc, 1),
                    'nwc_efficiency': round(nwc_efficiency, 1),
                    'capex_intensity': round(capex_intensity, 2),
                    'debt_to_equity': round(debt_ratio, 2),
                    'interest_coverage': round(interest_coverage, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"[DEEP DIVE] Error generating insights: {e}")
            return {'error': str(e)}
    
    # Helper methods for interpretation
    
    def _interpret_working_capital(self, ccc: float, avg_nwc_pct: float, efficiency: float) -> str:
        """Interpret working capital metrics"""
        if efficiency >= 80:
            return f"Excellent working capital management. CCC of {ccc:.0f} days indicates efficient operations."
        elif efficiency >= 60:
            return f"Good working capital efficiency. CCC of {ccc:.0f} days is within acceptable range."
        else:
            return f"Working capital efficiency needs improvement. CCC of {ccc:.0f} days suggests operational friction."
    
    def _interpret_capex(self, maint_pct: float, avg_intensity: float, intensity_class: str) -> str:
        """Interpret CapEx metrics"""
        return f"{intensity_class} capital intensity ({avg_intensity:.1f}% of revenue). Maintenance CapEx represents {maint_pct:.0f}% of total, indicating {'growth-focused' if maint_pct < 70 else 'maintenance-heavy'} capital allocation."
    
    def _interpret_debt(self, de_ratio: float, coverage: float, refi_risk: str) -> str:
        """Interpret debt metrics"""
        leverage = 'Conservative' if de_ratio < 0.5 else 'Moderate' if de_ratio < 1.5 else 'Elevated'
        coverage_quality = 'Strong' if coverage > 5 else 'Adequate' if coverage > 3 else 'Tight'
        return f"{leverage} leverage ({de_ratio:.2f}x D/E) with {coverage_quality.lower()} interest coverage ({coverage:.1f}x). Refinancing risk: {refi_risk}."
    
    def _assess_diversification(self, geo_breakdown: Dict) -> str:
        """Assess geographic diversification"""
        values = list(geo_breakdown.values())
        max_concentration = max(values) if values else 100
        
        if max_concentration > 80:
            return "Limited"
        elif max_concentration > 60:
            return "Moderate"
        else:
            return "Strong"
    
    def _generate_nwc_recommendations(self, ccc: float, avg_nwc_pct: float, volatility: str) -> List[str]:
        """Generate working capital recommendations"""
        recs = []
        
        if ccc > 90:
            recs.append("Focus on reducing cash conversion cycle through improved collections and inventory management")
        if abs(avg_nwc_pct) > 15:
            recs.append("Review working capital efficiency - high NWC relative to revenue may indicate operational inefficiencies")
        if volatility == 'High':
            recs.append("Address working capital volatility to improve cash flow predictability")
        if not recs:
            recs.append("Maintain current working capital management practices")
        
        return recs
    
    def _generate_capex_recommendations(self, growth_capex: float, total_capex: float, intensity: str) -> List[str]:
        """Generate CapEx recommendations"""
        recs = []
        
        growth_pct = (growth_capex / total_capex * 100) if total_capex > 0 else 0
        
        if growth_pct > 50:
            recs.append("High growth CapEx indicates expansion phase - validate projected returns on capital deployed")
        if intensity == 'High':
            recs.append("Capital-intensive business model - ensure strong returns on invested capital to justify spend levels")
        
        recs.append("Review CapEx projects for ROI validation and prioritization")
        
        return recs
    
    async def _detect_deep_dive_anomalies(
        self,
        working_capital: Dict[str, Any],
        capex_analysis: Dict[str, Any],
        customer_concentration: Dict[str, Any],
        segment_analysis: Dict[str, Any],
        debt_schedule: Dict[str, Any],
        state: DiligenceState
    ) -> Dict[str, Any]:
        """
        Detect financial operational anomalies
        
        Returns:
            Anomaly detection results for operational/financial domain
        """
        anomalies = []
        
        # Check for poor working capital efficiency
        wc_analysis = working_capital.get('nwc_analysis', {})
        ccc = wc_analysis.get('cash_conversion_cycle', {}).get('ccc_days', 0)
        efficiency = wc_analysis.get('efficiency_score', 100)
        
        if ccc > 120:
            anomalies.append({
                'type': 'working_capital_inefficiency',
                'severity': 'high',
                'description': f'Excessive cash conversion cycle: {ccc:.0f} days',
                'impact': 'Significant working capital tied up in operations',
                'recommendation': 'Implement working capital optimization program focusing on collections and inventory turns'
            })
        
        if efficiency < 40:
            anomalies.append({
                'type': 'operational_inefficiency',
                'severity': 'high',
                'description': f'Low working capital efficiency score: {efficiency:.1f}/100',
                'impact': 'Poor operational efficiency relative to benchmarks',
                'recommendation': 'Conduct operational efficiency review and implement improvement initiatives'
            })
        
        # Check for unusual CapEx patterns
        capex = capex_analysis.get('capex_analysis', {})
        growth_pct = capex.get('growth_capex_pct', 0)
        avg_capex_intensity = capex.get('avg_capex_pct_revenue', 0)
        
        if growth_pct > 70:
            anomalies.append({
                'type': 'aggressive_capex',
                'severity': 'medium',
                'description': f'High growth CapEx allocation: {growth_pct:.0f}% of total',
                'impact': 'Elevated capital deployment risk',
                'recommendation': 'Validate ROI assumptions and strategic rationale for growth investments'
            })
        
        if avg_capex_intensity > 20:
            anomalies.append({
                'type': 'capital_intensity',
                'severity': 'medium',
                'description': f'Very high capital intensity: {avg_capex_intensity:.1f}% of revenue',
                'impact': 'Significant ongoing capital requirements',
                'recommendation': 'Assess capital efficiency and explore asset-light alternatives'
            })
        
        # Check for debt covenant stress
        debt = debt_schedule.get('debt_analysis', {})
        debt_to_equity = debt.get('debt_to_equity', 0)
        covenant = debt.get('covenant_compliance', {})
        interest_coverage = covenant.get('interest_coverage', {}).get('actual', 999)
        
        if debt_to_equity > 2.0:
            anomalies.append({
                'type': 'high_leverage',
                'severity': 'high',
                'description': f'Elevated leverage: {debt_to_equity:.2f}x D/E ratio',
                'impact': 'Financial flexibility constraints and covenant risk',
                'recommendation': 'Evaluate deleveraging options and covenant headroom'
            })
        
        if interest_coverage < 2.5:
            anomalies.append({
                'type': 'covenant_stress',
                'severity': 'critical',
                'description': f'Tight interest coverage: {interest_coverage:.2f}x',
                'impact': 'High risk of covenant breach',
                'recommendation': 'Immediate action required - negotiate covenant relief or refinance debt'
            })
        
        return {
            'anomalies_detected': anomalies,
            'risk_level': 'Critical' if len([a for a in anomalies if a['severity'] == 'critical']) > 0 else 'High' if len([a for a in anomalies if a['severity'] == 'high']) > 0 else 'Medium' if anomalies else 'Low',
            'total_anomalies': len(anomalies)
        }


# Convenience function for standalone usage
async def analyze_financial_deep_dive(ticker: str, state: DiligenceState) -> Dict[str, Any]:
    """
    Convenience function to run financial deep dive analysis
    
    Args:
        ticker: Stock ticker symbol
        state: Diligence state with financial data
        
    Returns:
        Deep dive analysis results
    """
    agent = FinancialDeepDiveAgent()
    return await agent.run(state)
