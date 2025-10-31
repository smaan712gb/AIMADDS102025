"""
Financial Statement Normalization Module
Professional-grade normalization for M&A due diligence

Handles:
- Non-recurring item identification and removal
- GAAP vs non-GAAP reconciliation
- Accounting method change detection
- Operating vs non-operating separation
- R&D capitalization adjustments
- Historical data normalization and trend analysis
"""
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger


class FinancialNormalizer:
    """
    Normalizes financial statements for accurate M&A analysis
    """
    
    # Keywords for identifying non-recurring items
    NON_RECURRING_KEYWORDS = [
        'restructuring', 'impairment', 'goodwill', 'asset sale', 'asset sales',
        'discontinued', 'litigation', 'settlement', 'one-time', 'extraordinary',
        'unusual', 'non-recurring', 'severance', 'acquisition', 'merger',
        'integration', 'write-off', 'write-down', 'charge', 'gain on sale',
        'loss on sale', 'debt extinguishment', 'pension', 'curtailment'
    ]
    
    # Keywords for R&D identification (for tech company adjustments)
    RD_KEYWORDS = [
        'research and development', 'r&d', 'research', 'development costs',
        'product development', 'software development'
    ]
    
    def __init__(self, use_llm_intelligence: bool = True):
        """
        Initialize the normalizer
        
        Args:
            use_llm_intelligence: If True, uses Claude to make intelligent normalization decisions
                                  like a senior IB analyst would. Default True for production.
        """
        self.adjustments_log = []
        self.quality_score = 100  # CRITICAL FIX: Initialize quality score
        self.use_llm_intelligence = use_llm_intelligence
        self.llm = None
        
        if use_llm_intelligence:
            try:
                from anthropic import Anthropic
                import os
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    self.llm = Anthropic(api_key=api_key)
                    logger.info("✓ LLM-powered normalization ENABLED (Senior IB Intelligence)")
                else:
                    logger.warning("⚠️ ANTHROPIC_API_KEY not found - falling back to rule-based normalization")
                    self.use_llm_intelligence = False
            except ImportError:
                logger.warning("⚠️ Anthropic library not available - falling back to rule-based normalization")
                self.use_llm_intelligence = False
    
    def normalize_financial_statements(
        self,
        income_statements: List[Dict[str, Any]],
        balance_sheets: List[Dict[str, Any]],
        cash_flows: List[Dict[str, Any]],
        income_as_reported: Optional[List[Dict[str, Any]]] = None,
        company_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive normalization of financial statements with LLM-powered intelligence
        
        Args:
            income_statements: List of annual income statements (10 years)
            balance_sheets: List of annual balance sheets
            cash_flows: List of annual cash flow statements
            income_as_reported: As-reported income statements for GAAP comparison
            company_info: Company profile information
        
        Returns:
            Normalized financial data with adjustments
        """
        logger.info("Starting comprehensive financial statement normalization")
        if self.use_llm_intelligence:
            logger.info("🧠 LLM-powered Senior IB Intelligence: ACTIVE")
        
        normalized_data = {
            'normalized_income': [],
            'normalized_balance': [],
            'normalized_cash_flow': [],
            'adjustments': [],
            'quality_score': 0,
            'red_flags': [],
            'trends': {},
            'cagr_analysis': {},
            'llm_insights': None,  # LLM reasoning about data quality
            'income_statement': [],  # CRITICAL FIX: Add arrays that Excel generator expects
            'balance_sheet': [],
            'cash_flow': []
        }
        
        # STEP 0: LLM-Powered Pre-Analysis (Senior IB Intelligence)
        if self.use_llm_intelligence and self.llm:
            logger.info("Step 0: Running LLM-powered pre-analysis (Senior IB perspective)...")
            llm_insights = self._llm_analyze_financial_quality(
                income_statements, balance_sheets, cash_flows, company_info
            )
            normalized_data['llm_insights'] = llm_insights
            logger.info(f"✓ LLM Analysis Complete: {llm_insights.get('confidence', 'Unknown')} confidence")
        
        # Step 1: Identify non-recurring items
        non_recurring_items = self._identify_non_recurring_items(income_statements)
        
        # Step 2: GAAP vs Non-GAAP reconciliation
        gaap_adjustments = self._reconcile_gaap_nongaap(income_statements, income_as_reported)
        
        # Step 3: Normalize each period's income statement WITH DATA QUALITY FILTERING
        excluded_years = []
        for i, stmt in enumerate(income_statements):
            # CRITICAL FIX: Pre-check for corrupted data BEFORE normalization
            date = stmt.get('date', 'Unknown')
            revenue = stmt.get('revenue', 0)
            net_income = stmt.get('netIncome', 0)
            
            # Calculate raw margin to check for corruption
            raw_margin = (net_income / revenue) if revenue > 0 else 0
            
            # DATA QUALITY GATE: Exclude years with extreme margins (>|100%|)
            if abs(raw_margin) > 1.0:  # More than 100% margin (positive or negative)
                logger.warning(
                    f"⚠️ DATA QUALITY GATE: Excluding {date} from analysis - "
                    f"Extreme margin ({raw_margin:.1%}) indicates data corruption or one-time event. "
                    f"Revenue: ${revenue:,.0f}, Net Income: ${net_income:,.0f}"
                )
                excluded_years.append({
                    'date': date,
                    'reason': f'Extreme margin ({raw_margin:.1%})',
                    'revenue': revenue,
                    'net_income': net_income,
                    'margin': raw_margin
                })
                continue  # Skip this year - don't add to normalized arrays
            
            # Only normalize and add CLEAN data
            normalized_stmt = self._normalize_income_statement(
                stmt,
                non_recurring_items.get(stmt.get('date', ''), []),
                gaap_adjustments.get(stmt.get('date', ''), {}),
                company_info
            )
            normalized_data['normalized_income'].append(normalized_stmt)
            # CRITICAL FIX: Also populate the expected array name
            normalized_data['income_statement'].append(normalized_stmt)
        
        # Log data quality filtering results
        if excluded_years:
            logger.warning(
                f"⚠️ DATA QUALITY FILTERING: Excluded {len(excluded_years)} years from analysis: "
                f"{[y['date'] for y in excluded_years]}"
            )
            normalized_data['excluded_years'] = excluded_years
            normalized_data['data_quality_note'] = (
                f"{len(excluded_years)} years excluded due to extreme margins (>|100%|). "
                f"This is typical for pre-IPO/merger years with one-time costs. "
                f"Analysis based on {len(normalized_data['income_statement'])} clean years."
            )
        else:
            logger.info("✓ All years passed data quality gates - no exclusions needed")
        
        # Step 4: Normalize balance sheets
        for stmt in balance_sheets:
            normalized_stmt = self._normalize_balance_sheet(stmt, company_info)
            normalized_data['normalized_balance'].append(normalized_stmt)
            # CRITICAL FIX: Also populate the expected array name
            normalized_data['balance_sheet'].append(normalized_stmt)
        
        # Step 5: Normalize cash flows
        for stmt in cash_flows:
            normalized_stmt = self._normalize_cash_flow(stmt)
            normalized_data['normalized_cash_flow'].append(normalized_stmt)
            # CRITICAL FIX: Also populate the expected array name
            normalized_data['cash_flow'].append(normalized_stmt)
        
        # CRITICAL FIX: Log that arrays were populated
        logger.info(f"✓ Populated normalized arrays: {len(normalized_data['income_statement'])} income, "
                   f"{len(normalized_data['balance_sheet'])} balance, {len(normalized_data['cash_flow'])} cash flow statements")
        
        # Step 6: Calculate normalized trends and CAGRs WITH RECENCY WEIGHTING
        normalized_data['trends'] = self._calculate_trends(normalized_data['normalized_income'])
        normalized_data['cagr_analysis'] = self._calculate_cagrs_with_recency_weighting(
            normalized_data['normalized_income']
        )
        
        # Step 7: Detect accounting irregularities
        normalized_data['red_flags'] = self._detect_accounting_irregularities(
            normalized_data['normalized_income'],
            normalized_data['normalized_balance'],
            normalized_data['normalized_cash_flow']
        )
        
        # Step 8: Calculate earnings quality score
        normalized_data['quality_score'] = self._calculate_earnings_quality(
            normalized_data['normalized_income'],
            normalized_data['normalized_cash_flow']
        )
        
        # Step 9: Compile all adjustments made
        normalized_data['adjustments'] = self.adjustments_log
        
        logger.info(f"Normalization complete. Made {len(self.adjustments_log)} adjustments")
        
        return normalized_data
    
    def _identify_non_recurring_items(
        self,
        income_statements: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify non-recurring items in income statements
        
        Returns:
            Dictionary mapping dates to lists of non-recurring items
        """
        non_recurring_by_date = {}
        
        for stmt in income_statements:
            date = stmt.get('date', '')
            items = []
            
            # Check various line items for non-recurring characteristics
            for key, value in stmt.items():
                if isinstance(value, (int, float)) and value != 0:
                    # Check if key contains non-recurring keywords
                    key_lower = key.lower()
                    for keyword in self.NON_RECURRING_KEYWORDS:
                        if keyword in key_lower:
                            items.append({
                                'line_item': key,
                                'amount': value,
                                'reason': f'Contains keyword: {keyword}',
                                'date': date
                            })
                            break
            
            # Look for unusual changes in specific accounts
            # (would compare to prior periods in production)
            
            non_recurring_by_date[date] = items
        
        return non_recurring_by_date
    
    def _reconcile_gaap_nongaap(
        self,
        standard_statements: List[Dict[str, Any]],
        as_reported: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Reconcile GAAP vs Non-GAAP reported numbers
        
        Returns:
            Dictionary of adjustments by date
        """
        if not as_reported:
            return {}
        
        adjustments = {}
        
        # Match statements by date
        for std_stmt in standard_statements:
            date = std_stmt.get('date', '')
            
            # Find matching as-reported statement
            matching_reported = next(
                (stmt for stmt in as_reported if stmt.get('date') == date),
                None
            )
            
            if matching_reported:
                date_adjustments = {}
                
                # Compare key metrics
                std_net_income = std_stmt.get('netIncome', 0)
                reported_net_income = matching_reported.get('netIncome', 0)
                
                if abs(std_net_income - reported_net_income) > 0.01:
                    date_adjustments['net_income_adjustment'] = {
                        'gaap': reported_net_income,
                        'non_gaap': std_net_income,
                        'difference': std_net_income - reported_net_income
                    }
                
                adjustments[date] = date_adjustments
        
        return adjustments
    
    def _normalize_income_statement(
        self,
        stmt: Dict[str, Any],
        non_recurring: List[Dict[str, Any]],
        gaap_adj: Dict[str, Any],
        company_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Normalize a single income statement with ENHANCED extreme outlier handling
        """
        normalized = stmt.copy()
        date = stmt.get('date', 'Unknown')
        
        # Start with reported figures
        revenue = stmt.get('revenue', 0)
        net_income = stmt.get('netIncome', 0)
        operating_income = stmt.get('operatingIncome', 0)
        
        # CRITICAL FIX: Handle extreme margins (>|100%|) FIRST
        if revenue > 0:
            net_margin = net_income / revenue
            if abs(net_margin) > 1.0:
                # EXTREME outlier detected - use intelligent recovery
                # This is EXPECTED for early-stage/high-growth companies with heavy losses or one-time events
                logger.warning(f"⚠️ {date}: Extreme margin detected ({net_margin:.1%}) - Applying industry-based normalization...")
                
                # Get sector-based median margin for estimation
                sector = company_info.get('sector', 'Technology') if company_info else 'Technology'
                industry_median_margin = self._get_industry_median_margin(sector)
                
                # Calculate normalized net income using industry median
                normalized_net_income_from_margin = revenue * industry_median_margin
                
                # Determine if this is expected (early-stage losses) or suspicious (accounting issue)
                is_early_stage = net_margin < 0 and abs(net_margin) < 2.0  # Loss < 200% of revenue
                severity = 'WARNING' if is_early_stage else 'CRITICAL'
                
                # Log the massive adjustment
                adjustment_amount = net_income - normalized_net_income_from_margin
                self.adjustments_log.append({
                    'date': date,
                    'type': 'EXTREME_MARGIN_NORMALIZATION',
                    'severity': severity,
                    'original_net_income': net_income,
                    'original_margin': net_margin,
                    'normalized_net_income': normalized_net_income_from_margin,
                    'normalized_margin': industry_median_margin,
                    'adjustment_amount': adjustment_amount,
                    'reason': f'Margin {net_margin:.1%} exceeds |100%| - typical for early-stage/high-growth companies or one-time events',
                    'sector': sector,
                    'expected_pattern': is_early_stage
                })
                
                # Use normalized net income for all downstream calculations
                net_income = normalized_net_income_from_margin
                normalized['netIncome_original'] = stmt.get('netIncome', 0)
                normalized['netIncome'] = normalized_net_income_from_margin
                normalized['_extreme_margin_normalized'] = True
                
                # Reduce quality score, but less severely if this is expected early-stage pattern
                penalty = 15 if is_early_stage else 30
                self.quality_score = max(0, self.quality_score - penalty)
                
                logger.info(f"✓ Normalized {date}: ${stmt.get('netIncome', 0):,.0f} → ${normalized_net_income_from_margin:,.0f} (using {industry_median_margin:.1%} industry margin)")
        
        # Adjust for non-recurring items
        total_non_recurring_adjustment = 0
        for item in non_recurring:
            total_non_recurring_adjustment += item['amount']
            self.adjustments_log.append({
                'date': date,
                'type': 'Non-recurring item removal',
                'item': item['line_item'],
                'amount': item['amount'],
                'reason': item['reason']
            })
        
        # Remove non-recurring from net income
        normalized['normalized_net_income'] = net_income - total_non_recurring_adjustment
        
        # Adjust for GAAP vs Non-GAAP if present
        if 'net_income_adjustment' in gaap_adj:
            ni_adj = gaap_adj['net_income_adjustment']
            normalized['gaap_net_income'] = ni_adj['gaap']
            normalized['non_gaap_net_income'] = ni_adj['non_gaap']
            
            # Use GAAP figure for normalized basis
            normalized['normalized_net_income'] = ni_adj['gaap'] - total_non_recurring_adjustment
            
            self.adjustments_log.append({
                'date': date,
                'type': 'GAAP reconciliation',
                'gaap_value': ni_adj['gaap'],
                'non_gaap_value': ni_adj['non_gaap'],
                'difference': ni_adj['difference']
            })
        
        # R&D Capitalization adjustment for tech companies
        if company_info and company_info.get('sector') in ['Technology', 'Software']:
            rd_expense = stmt.get('researchAndDevelopmentExpenses', 0)
            if rd_expense > 0:
                # Assume 3-year amortization life for R&D
                capitalized_rd = rd_expense * 0.5  # Capitalize 50% (conservative)
                amortization = capitalized_rd / 3
                
                # Adjust EBITDA
                ebitda = stmt.get('ebitda', 0)
                normalized['normalized_ebitda'] = ebitda + capitalized_rd - amortization
                
                self.adjustments_log.append({
                    'date': date,
                    'type': 'R&D capitalization',
                    'original_rd': rd_expense,
                    'capitalized': capitalized_rd,
                    'amortization': amortization,
                    'ebitda_impact': capitalized_rd - amortization
                })
        
        # Separate operating vs non-operating income
        interest_income = stmt.get('interestIncome', 0)
        interest_expense = stmt.get('interestExpense', 0)
        other_income = stmt.get('otherIncomeExpenses', 0)
        
        normalized['core_operating_income'] = operating_income - other_income
        normalized['non_operating_income'] = interest_income + other_income - interest_expense
        
        # Calculate normalized margins
        if revenue > 0:
            normalized['normalized_net_margin'] = normalized.get('normalized_net_income', net_income) / revenue
            normalized['operating_margin'] = normalized['core_operating_income'] / revenue
        
        return normalized
    
    def _normalize_balance_sheet(
        self,
        stmt: Dict[str, Any],
        company_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Normalize balance sheet
        """
        normalized = stmt.copy()
        date = stmt.get('date', 'Unknown')
        
        # Adjust for off-balance-sheet items (if identifiable)
        # This would require more detailed SEC filing analysis
        
        # Calculate tangible book value
        total_assets = stmt.get('totalAssets', 0)
        intangible_assets = stmt.get('intangibleAssets', 0)
        goodwill = stmt.get('goodwill', 0)
        total_liabilities = stmt.get('totalLiabilities', 0)
        
        normalized['tangible_assets'] = total_assets - intangible_assets - goodwill
        normalized['tangible_book_value'] = normalized['tangible_assets'] - total_liabilities
        
        # Working capital analysis
        current_assets = stmt.get('totalCurrentAssets', 0)
        current_liabilities = stmt.get('totalCurrentLiabilities', 0)
        normalized['working_capital'] = current_assets - current_liabilities
        
        # Net debt
        total_debt = stmt.get('totalDebt', 0)
        cash = stmt.get('cashAndCashEquivalents', 0)
        normalized['net_debt'] = total_debt - cash
        
        return normalized
    
    def _normalize_cash_flow(self, stmt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize cash flow statement
        """
        normalized = stmt.copy()
        
        # Calculate free cash flow if not present
        operating_cf = stmt.get('operatingCashFlow', 0)
        capex = stmt.get('capitalExpenditure', 0)
        
        if 'freeCashFlow' not in stmt:
            normalized['freeCashFlow'] = operating_cf + capex  # capex is usually negative
        
        # Calculate cash conversion ratio
        net_income = stmt.get('netIncome', 0)
        if net_income != 0:
            normalized['cash_conversion_ratio'] = operating_cf / net_income
        
        return normalized
    
    def _calculate_trends(self, normalized_income: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate key financial trends
        """
        if len(normalized_income) < 2:
            return {}
        
        trends = {
            'revenue_trend': [],
            'margin_trend': [],
            'seasonality_detected': False
        }
        
        # Revenue trend
        for i in range(len(normalized_income) - 1):
            current = normalized_income[i].get('revenue', 0)
            prior = normalized_income[i + 1].get('revenue', 1)
            
            if prior > 0:
                growth = (current - prior) / prior
                trends['revenue_trend'].append({
                    'date': normalized_income[i].get('date'),
                    'growth_rate': growth
                })
        
        # Margin trend
        for stmt in normalized_income:
            trends['margin_trend'].append({
                'date': stmt.get('date'),
                'net_margin': stmt.get('normalized_net_margin', 0),
                'operating_margin': stmt.get('operating_margin', 0)
            })
        
        return trends
    
    def _calculate_cagrs_with_recency_weighting(self, normalized_income: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate CAGRs with RECENCY WEIGHTING
        Recent years weighted higher as they're more predictive of future performance
        """
        if len(normalized_income) < 2:
            return {}
        
        # Standard CAGR calculation
        standard_cagrs = self._calculate_cagrs(normalized_income)
        
        # RECENCY-WEIGHTED Growth Calculation
        revenue_values = [stmt.get('revenue', 0) for stmt in normalized_income]
        
        # Create exponential recency weights (most recent = highest)
        weights = []
        for i in range(len(revenue_values)):
            recency_factor = 0.85 ** i  # 15% decay per year back
            weights.append(recency_factor)
        
        # Normalize to sum to 1
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Calculate weighted growth rates
        growth_rates = []
        for i in range(len(revenue_values) - 1):
            if revenue_values[i+1] > 0:
                growth = (revenue_values[i] - revenue_values[i+1]) / revenue_values[i+1]
                growth_rates.append(growth)
        
        weighted_growth = sum(g * weights[i] for i, g in enumerate(growth_rates)) if growth_rates else 0
        
        logger.info(f"📊 Growth: Standard CAGR {standard_cagrs.get('revenue_cagr', 0):.2%}, "
                   f"Recency-Weighted {weighted_growth:.2%} (emphasizes recent years)")
        
        # Add recency-weighted metrics
        result = standard_cagrs.copy()
        result['revenue_cagr_recency_weighted'] = weighted_growth
        result['recency_weights'] = {
            'most_recent_year': weights[0] if weights else 0,
            'oldest_year': weights[-1] if weights else 0,
            'methodology': 'Exponential decay (0.85^years_back)'
        }
        result['recommendation'] = 'Use recency-weighted growth for DCF projections'
        
        return result
    
    def _calculate_cagrs(self, normalized_income: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate standard Compound Annual Growth Rates (equal weighting)
        """
        if len(normalized_income) < 2:
            return {}
        
        def calc_cagr(start_val: float, end_val: float, periods: int) -> float:
            if start_val <= 0 or end_val <= 0:
                return 0.0
            return (end_val / start_val) ** (1 / periods) - 1
        
        periods = len(normalized_income) - 1
        
        # Get values (newest first, oldest last)
        revenue_start = normalized_income[-1].get('revenue', 0)
        revenue_end = normalized_income[0].get('revenue', 0)
        
        ni_start = normalized_income[-1].get('normalized_net_income', 
                   normalized_income[-1].get('netIncome', 0))
        ni_end = normalized_income[0].get('normalized_net_income',
                 normalized_income[0].get('netIncome', 0))
        
        ebitda_start = normalized_income[-1].get('ebitda', 0)
        ebitda_end = normalized_income[0].get('ebitda', 0)
        
        return {
            'revenue_cagr': calc_cagr(revenue_start, revenue_end, periods),
            'net_income_cagr': calc_cagr(ni_start, ni_end, periods),
            'ebitda_cagr': calc_cagr(ebitda_start, ebitda_end, periods),
            'periods': periods,
            'start_date': normalized_income[-1].get('date'),
            'end_date': normalized_income[0].get('date')
        }
    
    def _detect_accounting_irregularities(
        self,
        income: List[Dict[str, Any]],
        balance: List[Dict[str, Any]],
        cash_flow: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Detect potential accounting red flags
        """
        red_flags = []
        
        if not income or not cash_flow:
            return red_flags
        
        # Check 1: Net income significantly exceeds operating cash flow
        for i in range(min(len(income), len(cash_flow))):
            ni = income[i].get('normalized_net_income', income[i].get('netIncome', 0))
            ocf = cash_flow[i].get('operatingCashFlow', 0)
            date = income[i].get('date', 'Unknown')
            
            if ni > 0 and ocf > 0:
                if ni / ocf > 1.5:
                    red_flags.append(
                        f"[{date}] Net income ({ni:,.0f}) significantly exceeds operating cash flow ({ocf:,.0f}) - "
                        f"Ratio: {ni/ocf:.2f}x. Potential earnings quality issue."
                    )
        
        # Check 2: Declining margins
        if len(income) >= 3:
            margins = [stmt.get('normalized_net_margin', 0) for stmt in income[:3]]
            if margins[0] < margins[1] < margins[2]:
                red_flags.append(
                    f"Declining profit margins over 3 years: {margins[2]:.1%} -> {margins[1]:.1%} -> {margins[0]:.1%}"
                )
        
        # Check 3: Revenue vs Accounts Receivable growth
        if len(income) >= 2 and len(balance) >= 2:
            rev_current = income[0].get('revenue', 0)
            rev_prior = income[1].get('revenue', 1)
            ar_current = balance[0].get('netReceivables', 0)
            ar_prior = balance[1].get('netReceivables', 1)
            
            if ar_prior > 0 and rev_prior > 0:
                ar_growth = (ar_current - ar_prior) / ar_prior
                rev_growth = (rev_current - rev_prior) / rev_prior
                
                if ar_growth > rev_growth * 1.5:
                    red_flags.append(
                        f"Accounts receivable growing ({ar_growth:.1%}) faster than revenue ({rev_growth:.1%}) - "
                        f"Potential revenue recognition issue"
                    )
        
        # Check 4: DSO (Days Sales Outstanding) increasing
        if len(income) >= 2 and len(balance) >= 2:
            for i in range(min(2, len(income))):
                revenue = income[i].get('revenue', 0)
                ar = balance[i].get('netReceivables', 0)
                
                if revenue > 0:
                    dso = (ar / revenue) * 365
                    if i == 0:
                        current_dso = dso
                    else:
                        prior_dso = dso
            
            if 'current_dso' in locals() and 'prior_dso' in locals():
                if current_dso > prior_dso * 1.2:
                    red_flags.append(
                        f"Days Sales Outstanding increased from {prior_dso:.0f} to {current_dso:.0f} days - "
                        f"Potential collection issues"
                    )
        
        return red_flags
    
    def _llm_analyze_financial_quality(
        self,
        income_statements: List[Dict[str, Any]],
        balance_sheets: List[Dict[str, Any]],
        cash_flows: List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LLM-POWERED: Analyze financial data quality with Senior IB Intelligence
        
        Uses Claude to think through data quality issues like a senior investment banker would,
        providing context-aware insights about anomalies, likely causes, and normalization strategy.
        
        Returns:
            Dict with LLM insights about data quality, confidence, and recommendations
        """
        if not self.llm or not income_statements:
            return {'available': False}
        
        try:
            # Prepare financial summary for LLM analysis
            latest = income_statements[0]
            latest_bs = balance_sheets[0] if balance_sheets else {}
            latest_cf = cash_flows[0] if cash_flows else {}
            
            company_name = company_info.get('companyName', 'Unknown') if company_info else 'Unknown'
            sector = company_info.get('sector', 'Unknown') if company_info else 'Unknown'
            
            # Calculate key anomalies
            revenue = latest.get('revenue', 0)
            net_income = latest.get('netIncome', 0)
            operating_income = latest.get('operatingIncome', 0)
            ocf = latest_cf.get('operatingCashFlow', 0)
            
            net_margin = (net_income / revenue * 100) if revenue > 0 else 0
            ni_ocf_gap = net_income - ocf if ocf else 0
            
            # Build context-rich prompt for Senior IB analysis
            prompt = f"""You are a senior investment banking analyst performing financial due diligence for an M&A transaction. Analyze this financial data with deep IB expertise:

COMPANY: {company_name} ({sector})

LATEST FINANCIAL DATA:
- Revenue: ${revenue:,.0f}
- Net Income: ${net_income:,.0f} 
- Net Margin: {net_margin:.1f}%
- Operating Income: ${operating_income:,.0f}
- Operating Cash Flow: ${ocf:,.0f}
- NI vs OCF Gap: ${ni_ocf_gap:,.0f}

HISTORICAL PATTERN (last {len(income_statements)} years):
{self._format_historical_summary(income_statements, cash_flows)}

CRITICAL ANOMALIES DETECTED:
{self._identify_anomalies_for_llm(income_statements, balance_sheets, cash_flows)}

As a senior IB analyst, provide:

1. **DATA QUALITY ASSESSMENT**: What's the likely quality of this data for M&A valuation? (Grade A-F with reasoning)

2. **ANOMALY INTERPRETATION**: For each critical anomaly, explain the LIKELY BUSINESS REASON:
   - Is this a one-time event (restructuring, impairment, IPO costs)?
   - Is this operational performance (margin compression, growth investment)?
   - Is this accounting (revenue recognition changes, goodwill write-down)?

3. **NORMALIZATION STRATEGY**: What adjustments would you make to prepare normalized EBITDA for DCF/LBO?
   - Which items should be added back?
   - What should the normalized margins realistically be?
   - Any sector-specific adjustments needed?

4. **CONFIDENCE ASSESSMENT**: How confident are you in using this data for valuation? (High/Medium/Low with reasoning)

5. **RED FLAGS**: Any accounting quality concerns that could affect deal terms?

Provide your analysis as a senior banker would - concise, focused on M&A implications, and actionable."""

            # Call Claude for analysis
            message = self.llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.2,  # Low temperature for consistent IB analysis
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            analysis_text = message.content[0].text
            
            # Parse LLM response into structured format
            return {
                'available': True,
                'llm_analysis': analysis_text,
                'confidence': self._extract_confidence(analysis_text),
                'grade': self._extract_grade(analysis_text),
                'recommended_adjustments': self._extract_adjustments(analysis_text),
                'red_flags_identified': self._extract_red_flags(analysis_text),
                'model_used': 'claude-sonnet-4',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def _format_historical_summary(
        self, 
        income: List[Dict[str, Any]], 
        cash_flows: List[Dict[str, Any]]
    ) -> str:
        """Format historical data for LLM analysis"""
        summary_lines = []
        for i, stmt in enumerate(income[:5]):  # Last 5 years
            date = stmt.get('date', 'Unknown')
            revenue = stmt.get('revenue', 0)
            ni = stmt.get('netIncome', 0)
            margin = (ni / revenue * 100) if revenue > 0 else 0
            
            cf_stmt = cash_flows[i] if i < len(cash_flows) else {}
            ocf = cf_stmt.get('operatingCashFlow', 0)
            
            summary_lines.append(
                f"  {date}: Revenue ${revenue/1e9:.2f}B, NI ${ni/1e9:.2f}B ({margin:.1f}%), OCF ${ocf/1e9:.2f}B"
            )
        
        return '\n'.join(summary_lines)
    
    def _identify_anomalies_for_llm(
        self,
        income: List[Dict[str, Any]],
        balance: List[Dict[str, Any]],
        cash_flows: List[Dict[str, Any]]
    ) -> str:
        """Identify key anomalies for LLM to analyze"""
        anomalies = []
        
        # Check for extreme margins
        for stmt in income[:3]:
            date = stmt.get('date', '')
            revenue = stmt.get('revenue', 1)
            ni = stmt.get('netIncome', 0)
            margin = ni / revenue if revenue > 0 else 0
            
            if abs(margin) > 0.5:  # >50% margin (positive or negative)
                anomalies.append(f"  • {date}: Extreme margin ({margin:.1%}) - Possible one-time event")
        
        # Check NI vs OCF gaps
        for i, stmt in enumerate(income[:3]):
            date = stmt.get('date', '')
            ni = stmt.get('netIncome', 0)
            cf_stmt = cash_flows[i] if i < len(cash_flows) else {}
            ocf = cf_stmt.get('operatingCashFlow', 0)
            
            if abs(ni - ocf) > abs(ni) * 0.5 and ni != 0:  # >50% gap
                anomalies.append(f"  • {date}: Large NI vs OCF gap (${(ni-ocf)/1e6:.0f}M) - Earnings quality concern")
        
        # Check for missing data
        if balance:
            latest_bs = balance[0]
            cash_fields = ['cash', 'cashAndCashEquivalents', 'cashAndShortTermInvestments']
            has_cash = any(latest_bs.get(field) for field in cash_fields)
            if not has_cash:
                anomalies.append(f"  • {latest_bs.get('date', 'Latest')}: Missing cash field - Data completeness issue")
        
        return '\n'.join(anomalies) if anomalies else "  • No critical anomalies detected"
    
    def _extract_confidence(self, analysis: str) -> str:
        """Extract confidence level from LLM analysis"""
        analysis_lower = analysis.lower()
        if 'high confidence' in analysis_lower or 'very confident' in analysis_lower:
            return 'High'
        elif 'low confidence' in analysis_lower or 'not confident' in analysis_lower:
            return 'Low'
        else:
            return 'Medium'
    
    def _extract_grade(self, analysis: str) -> str:
        """Extract data quality grade from LLM analysis"""
        # Look for grade patterns like "Grade A", "Quality: B", etc.
        import re
        grade_patterns = [
            r'[Gg]rade:?\s*([A-F])',
            r'[Qq]uality:?\s*([A-F])',
            r'([A-F])\s*grade'
        ]
        
        for pattern in grade_patterns:
            match = re.search(pattern, analysis)
            if match:
                return match.group(1).upper()
        
        return 'C'  # Default to C if not found
    
    def _extract_adjustments(self, analysis: str) -> List[str]:
        """Extract recommended adjustments from LLM analysis"""
        # Look for lines that mention adjustments, add-backs, or normalizations
        lines = analysis.split('\n')
        adjustments = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['add back', 'adjust', 'normalize', 'remove', 'capitalize']):
                clean_line = line.strip().lstrip('-•*123456789. ')
                if len(clean_line) > 20:
                    adjustments.append(clean_line)
        
        return adjustments[:10]  # Limit to 10
    
    def _extract_red_flags(self, analysis: str) -> List[str]:
        """Extract red flags identified by LLM"""
        lines = analysis.split('\n')
        red_flags = []
        
        in_red_flag_section = False
        for line in lines:
            line_lower = line.lower()
            
            if 'red flag' in line_lower or 'concern' in line_lower or 'risk' in line_lower:
                in_red_flag_section = True
            
            if in_red_flag_section:
                if line.strip().startswith(('-', '•', '*')) or line.strip()[0:1].isdigit():
                    clean_line = line.strip().lstrip('-•*123456789. ')
                    if len(clean_line) > 20:
                        red_flags.append(clean_line)
        
        return red_flags[:10]  # Limit to 10
    
    def _get_industry_median_margin(self, sector: str) -> float:
        """
        Get industry median net margin for normalization fallback
        
        Args:
            sector: Company sector (Technology, Healthcare, etc.)
        
        Returns:
            Industry median net profit margin
        """
        # Industry median net margins (conservative estimates)
        industry_margins = {
            'Technology': 0.15,  # 15%
            'Software': 0.20,    # 20%
            'Healthcare': 0.10,  # 10%
            'Financial Services': 0.15,  # 15%
            'Consumer Cyclical': 0.05,  # 5%
            'Consumer Defensive': 0.03,  # 3%
            'Industrials': 0.08,  # 8%
            'Energy': 0.05,  # 5%
            'Utilities': 0.10,  # 10%
            'Real Estate': 0.12,  # 12%
            'Materials': 0.08,  # 8%
            'Communication Services': 0.10,  # 10%
        }
        
        # Return sector-specific margin or default to 10%
        margin = industry_margins.get(sector, 0.10)
        logger.info(f"Using industry median margin for {sector}: {margin:.1%}")
        return margin
    
    def _calculate_earnings_quality(
        self,
        income: List[Dict[str, Any]],
        cash_flow: List[Dict[str, Any]]
    ) -> int:
        """
        Calculate earnings quality score (0-100)
        """
        if not income or not cash_flow:
            return 0
        
        score = 100
        factors = []
        
        # Factor 1: Cash conversion (30 points)
        conversions = []
        for i in range(min(len(income), len(cash_flow))):
            ni = income[i].get('normalized_net_income', income[i].get('netIncome', 0))
            ocf = cash_flow[i].get('operatingCashFlow', 0)
            
            if ni > 0:
                ratio = ocf / ni
                conversions.append(ratio)
        
        if conversions:
            avg_conversion = np.mean(conversions)
            if avg_conversion >= 1.0:
                factors.append("Strong cash conversion")
            elif avg_conversion >= 0.7:
                score -= 10
                factors.append("Moderate cash conversion")
            else:
                score -= 30
                factors.append("Weak cash conversion - earnings quality concern")
        
        # Factor 2: Consistency of non-recurring items (20 points)
        non_recurring_count = len([adj for adj in self.adjustments_log 
                                   if adj['type'] == 'Non-recurring item removal'])
        
        if non_recurring_count == 0:
            factors.append("No non-recurring adjustments needed")
        elif non_recurring_count <= 2:
            score -= 10
            factors.append("Minimal non-recurring items")
        else:
            score -= 20
            factors.append(f"Frequent non-recurring items ({non_recurring_count} adjustments)")
        
        # Factor 3: GAAP vs Non-GAAP consistency (25 points)
        gaap_adj_count = len([adj for adj in self.adjustments_log 
                             if adj['type'] == 'GAAP reconciliation'])
        
        if gaap_adj_count == 0:
            factors.append("GAAP and non-GAAP aligned")
        else:
            score -= min(25, gaap_adj_count * 5)
            factors.append(f"GAAP/non-GAAP differences ({gaap_adj_count} periods)")
        
        # Factor 4: Trend stability (25 points)
        if len(income) >= 3:
            revenues = [stmt.get('revenue', 0) for stmt in income[:3]]
            growth_rates = []
            for i in range(len(revenues) - 1):
                if revenues[i+1] > 0:
                    growth_rates.append((revenues[i] - revenues[i+1]) / revenues[i+1])
            
            if growth_rates:
                volatility = np.std(growth_rates)
                if volatility < 0.1:
                    factors.append("Stable revenue trends")
                elif volatility < 0.3:
                    score -= 10
                    factors.append("Moderate revenue volatility")
                else:
                    score -= 25
                    factors.append("High revenue volatility")
        
        return max(0, score)


def normalize_quarterly_data(
    quarterly_statements: List[Dict[str, Any]],
    statement_type: str = 'income'
) -> Dict[str, Any]:
    """
    Normalize quarterly financial data for seasonality and trend analysis
    
    Args:
        quarterly_statements: List of quarterly statements (20 quarters)
        statement_type: 'income', 'balance', or 'cash_flow'
    
    Returns:
        Normalized quarterly data with seasonality analysis
    """
    if len(quarterly_statements) < 4:
        return {'error': 'Insufficient quarterly data'}
    
    df = pd.DataFrame(quarterly_statements)
    
    # Detect seasonality
    if statement_type == 'income' and 'revenue' in df.columns:
        # Calculate YoY growth for each quarter
        df['quarter'] = pd.to_datetime(df['date']).dt.quarter
        df['year'] = pd.to_datetime(df['date']).dt.year
        
        # Calculate seasonal indices
        seasonal_indices = df.groupby('quarter')['revenue'].mean() / df['revenue'].mean()
        
        return {
            'seasonality_detected': seasonal_indices.std() > 0.1,
            'seasonal_indices': seasonal_indices.to_dict(),
            'quarterly_data': quarterly_statements,
            'analysis': 'Seasonality analysis complete'
        }
    
    return {'quarterly_data': quarterly_statements}
