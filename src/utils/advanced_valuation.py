"""
Advanced Valuation Models for M&A Due Diligence

Includes:
- Multi-scenario DCF (Base, Optimistic, Pessimistic)
- Sensitivity analysis on WACC and growth rates
- Comparable company analysis (Trading Comps)
- Precedent transaction analysis
- Monte Carlo simulation for valuation ranges
- LBO analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import scipy.stats as stats


@dataclass
class DCFAssumptions:
    """DCF model assumptions"""
    forecast_years: int = 5
    terminal_growth_rate: float = 0.025
    wacc: float = 0.10
    tax_rate: float = 0.21
    revenue_growth_rates: List[float] = None
    ebitda_margins: List[float] = None
    capex_percent_revenue: float = 0.03
    nwc_percent_revenue: float = 0.10
    depreciation_percent_revenue: float = 0.03


class AdvancedValuationEngine:
    """
    Advanced valuation engine for M&A analysis
    """
    
    def __init__(self):
        """Initialize the valuation engine"""
        self.valuation_results = {}
    
    def run_full_valuation_suite(
        self,
        financial_data: Dict[str, Any],
        company_profile: Dict[str, Any],
        comparable_companies: Optional[List[str]] = None,
        precedent_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run complete valuation analysis suite
        
        Args:
            financial_data: Historical financial data
            company_profile: Company information
            comparable_companies: List of comparable ticker symbols
            precedent_transactions: List of precedent M&A transactions
        
        Returns:
            Comprehensive valuation analysis
        """
        logger.info("Starting advanced valuation analysis")
        
        results = {
            'dcf_analysis': {},
            'sensitivity_analysis': {},
            'monte_carlo_simulation': {},
            'comparable_companies': {},
            'precedent_transactions': {},
            'valuation_summary': {},
            'recommendation': {}
        }
        
        # 1. Multi-scenario DCF Analysis
        results['dcf_analysis'] = self.run_multi_scenario_dcf(financial_data, company_profile)
        
        # 2. Sensitivity Analysis
        results['sensitivity_analysis'] = self.run_sensitivity_analysis(financial_data, company_profile)
        
        # 3. Monte Carlo Simulation
        results['monte_carlo_simulation'] = self.run_monte_carlo_valuation(
            financial_data,
            company_profile,
            num_simulations=10000
        )
        
        # 4. Comparable Company Analysis (if provided)
        if comparable_companies:
            results['comparable_companies'] = self.run_comparable_analysis(
                financial_data,
                comparable_companies
            )
        
        # 5. Precedent Transaction Analysis (if provided)
        if precedent_transactions:
            results['precedent_transactions'] = self.analyze_precedent_transactions(
                financial_data,
                precedent_transactions
            )
        
        # 6. LBO Analysis (for PE-backed transactions)
        results['lbo_analysis'] = self.run_lbo_analysis(financial_data, company_profile)
        
        # 7. Valuation Summary and Recommendation
        results['valuation_summary'] = self.generate_valuation_summary(results)
        results['recommendation'] = self.generate_valuation_recommendation(results)
        
        logger.info("Advanced valuation analysis complete (including LBO)")
        return results
    
    def run_multi_scenario_dcf(
        self,
        financial_data: Dict[str, Any],
        company_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run DCF under multiple scenarios (Base, Optimistic, Pessimistic)
        """
        logger.info("Running multi-scenario DCF analysis")
        
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        if not income_statements or not cash_flows:
            return {'error': 'Insufficient financial data for DCF'}
        
        # Calculate historical metrics
        historical_metrics = self._calculate_historical_metrics(
            income_statements,
            balance_sheets,
            cash_flows
        )
        
        # Define three scenarios
        scenarios = {
            'base': self._create_base_case_assumptions(historical_metrics),
            'optimistic': self._create_optimistic_assumptions(historical_metrics),
            'pessimistic': self._create_pessimistic_assumptions(historical_metrics)
        }
        
        results = {}
        for scenario_name, assumptions in scenarios.items():
            logger.info(f"Calculating {scenario_name} case DCF")
            results[scenario_name] = self._calculate_dcf(
                historical_metrics,
                assumptions,
                company_profile
            )
        
        # Calculate probability-weighted valuation
        results['probability_weighted'] = {
            'enterprise_value': (
                results['pessimistic']['enterprise_value'] * 0.25 +
                results['base']['enterprise_value'] * 0.50 +
                results['optimistic']['enterprise_value'] * 0.25
            ),
            'weights': {'pessimistic': 0.25, 'base': 0.50, 'optimistic': 0.25}
        }
        
        return results
    
    def _calculate_historical_metrics(
        self,
        income: List[Dict[str, Any]],
        balance: List[Dict[str, Any]],
        cash_flow: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate historical financial metrics
        
        CRITICAL FIX: This method now uses ACTUAL market cap from company profile
        instead of estimating (revenue × 5), which was causing massive DCF errors
        """
        if not income:
            return {}
        
        latest_income = income[0]
        latest_balance = balance[0] if balance else {}
        latest_cf = cash_flow[0] if cash_flow else {}
        
        # Calculate historical growth rates
        revenue_growth_rates = []
        for i in range(min(3, len(income) - 1)):
            current_rev = income[i].get('revenue', 0)
            prior_rev = income[i + 1].get('revenue', 1)
            if prior_rev > 0:
                growth = (current_rev - prior_rev) / prior_rev
                revenue_growth_rates.append(growth)
        
        avg_revenue_growth = np.mean(revenue_growth_rates) if revenue_growth_rates else 0.05
        
        # Calculate margins
        revenue = latest_income.get('revenue', 1)
        ebitda = latest_income.get('ebitda', 0)
        ebitda_margin = ebitda / revenue if revenue > 0 else 0
        
        # Free cash flow
        fcf = latest_cf.get('freeCashFlow', 0)
        fcf_margin = fcf / revenue if revenue > 0 else 0
        
        # Calculate WACC components
        total_debt = latest_balance.get('totalDebt', 0)
        
        # CRITICAL FIX: Use ACTUAL market cap from balance sheet if available
        # Balance sheet contains market cap from FMP API
        actual_market_cap = latest_balance.get('marketCap', 0)
        
        if actual_market_cap and actual_market_cap > 0:
            market_cap = actual_market_cap
            logger.info(f"✓ Using ACTUAL market cap from data: ${market_cap/1e9:.1f}B")
        else:
            # Fallback to estimate only if no market cap available
            market_cap = revenue * 5
            logger.warning(f"⚠️ Using ESTIMATED market cap (revenue × 5): ${market_cap/1e9:.1f}B - DCF may be inaccurate")
        
        total_value = total_debt + market_cap
        
        debt_ratio = total_debt / total_value if total_value > 0 else 0.3
        equity_ratio = 1 - debt_ratio
        
        # CRITICAL FIX: Add market-implied metrics for validation
        market_ev = market_cap + total_debt
        market_ev_revenue_multiple = market_ev / revenue if revenue > 0 else 0
        market_ev_ebitda_multiple = market_ev / ebitda if ebitda > 0 else 0
        
        return {
            'latest_revenue': revenue,
            'latest_ebitda': ebitda,
            'ebitda_margin': ebitda_margin,
            'latest_fcf': fcf,
            'fcf_margin': fcf_margin,
            'avg_revenue_growth': avg_revenue_growth,
            'total_debt': total_debt,
            'market_cap': market_cap,
            'debt_ratio': debt_ratio,
            'equity_ratio': equity_ratio,
            # NEW: Market-implied metrics for DCF validation
            'market_ev': market_ev,
            'market_ev_revenue_multiple': market_ev_revenue_multiple,
            'market_ev_ebitda_multiple': market_ev_ebitda_multiple,
            'market_cap_source': 'actual' if actual_market_cap > 0 else 'estimated'
        }
    
    def _create_base_case_assumptions(self, historical: Dict[str, Any]) -> DCFAssumptions:
        """
        Create base case assumptions calibrated to market reality
        
        CRITICAL FIX: Adjusts assumptions for high-growth companies to avoid
        severe undervaluation (e.g., Palantir growing 20%+ should use different
        assumptions than a mature 5% growth company)
        """
        avg_growth = historical.get('avg_revenue_growth', 0.05)
        
        # CRITICAL FIX: For high-growth companies, use less aggressive tapering
        if avg_growth > 0.15:  # If growing >15% annually
            logger.info(f"High-growth company detected ({avg_growth:.1%}). Using extended growth profile.")
            growth_rates = [
                avg_growth,           # Year 1: Full growth
                avg_growth * 0.95,    # Year 2: 95% of growth
                avg_growth * 0.90,    # Year 3: 90% of growth
                avg_growth * 0.85,    # Year 4: 85% of growth
                avg_growth * 0.75     # Year 5: 75% of growth
            ]
            terminal_growth = 0.035  # 3.5% for high-growth tech
            wacc = 0.09  # 9% for established high-growth tech (was 10%)
        else:
            # Original conservative assumptions for mature companies
            growth_rates = [
                avg_growth,
                avg_growth * 0.9,
                avg_growth * 0.8,
                avg_growth * 0.7,
                avg_growth * 0.6
            ]
            terminal_growth = 0.025
            wacc = 0.10
        
        # CRITICAL FIX: Add market reality check warning
        market_multiple = historical.get('market_ev_ebitda_multiple', 0)
        if market_multiple > 50:  # Market values company at premium multiple
            logger.warning(
                f"⚠️ Market trading at {market_multiple:.1f}x EBITDA - significantly higher than typical DCF implies. "
                f"This suggests: (1) Market expects higher growth than model, (2) Strategic value not captured in DCF, "
                f"or (3) Intangible assets (brand, network effects) not valued in cash flow model."
            )
        
        return DCFAssumptions(
            forecast_years=5,
            terminal_growth_rate=terminal_growth,
            wacc=wacc,
            revenue_growth_rates=growth_rates,
            ebitda_margins=[historical.get('ebitda_margin', 0.2)] * 5
        )
    
    def _create_optimistic_assumptions(self, historical: Dict[str, Any]) -> DCFAssumptions:
        """Create optimistic case assumptions"""
        avg_growth = historical.get('avg_revenue_growth', 0.05)
        
        # Higher growth rates
        growth_rates = [
            avg_growth * 1.3,
            avg_growth * 1.2,
            avg_growth * 1.1,
            avg_growth,
            avg_growth * 0.9
        ]
        
        base_margin = historical.get('ebitda_margin', 0.2)
        margins = [base_margin * 1.1] * 5  # 10% margin improvement
        
        return DCFAssumptions(
            forecast_years=5,
            terminal_growth_rate=0.035,
            wacc=0.09,  # Lower risk premium
            revenue_growth_rates=growth_rates,
            ebitda_margins=margins
        )
    
    def _create_pessimistic_assumptions(self, historical: Dict[str, Any]) -> DCFAssumptions:
        """Create pessimistic case assumptions"""
        avg_growth = historical.get('avg_revenue_growth', 0.05)
        
        # Lower growth rates
        growth_rates = [
            avg_growth * 0.5,
            avg_growth * 0.4,
            avg_growth * 0.3,
            avg_growth * 0.2,
            avg_growth * 0.1
        ]
        
        base_margin = historical.get('ebitda_margin', 0.2)
        margins = [base_margin * 0.9] * 5  # 10% margin compression
        
        return DCFAssumptions(
            forecast_years=5,
            terminal_growth_rate=0.015,
            wacc=0.12,  # Higher risk premium
            revenue_growth_rates=growth_rates,
            ebitda_margins=margins
        )
    
    def _validate_dcf_assumptions(
        self,
        assumptions: DCFAssumptions,
        suppress_warnings: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate DCF assumptions for economic reasonableness
        
        Args:
            assumptions: DCF assumptions to validate
            suppress_warnings: If True, only collect warnings without logging (for Monte Carlo)
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Rule 1: WACC must be meaningfully higher than terminal growth
        wacc_growth_spread = assumptions.wacc - assumptions.terminal_growth_rate
        min_spread = 0.02  # At least 2% spread is recommended
        
        if wacc_growth_spread <= 0:
            warnings.append(
                f"CRITICAL: WACC ({assumptions.wacc:.1%}) must be higher than terminal growth rate "
                f"({assumptions.terminal_growth_rate:.1%}). This violates the Gordon Growth Model. "
                f"Recommended: WACC ≥ terminal growth + 2%"
            )
        elif wacc_growth_spread < min_spread:
            warnings.append(
                f"WARNING: WACC ({assumptions.wacc:.1%}) is too close to terminal growth "
                f"({assumptions.terminal_growth_rate:.1%}). Spread is only {wacc_growth_spread:.1%}. "
                f"Recommended minimum spread: {min_spread:.1%}. Small changes in assumptions will "
                f"cause large valuation swings."
            )
        
        # Rule 2: Terminal growth rate should be reasonable (typically GDP growth)
        if assumptions.terminal_growth_rate > 0.04:
            warnings.append(
                f"WARNING: Terminal growth rate ({assumptions.terminal_growth_rate:.1%}) exceeds "
                f"typical long-term GDP growth (2-4%). This assumes the company will grow faster "
                f"than the economy forever, which is unrealistic."
            )
        
        if assumptions.terminal_growth_rate < 0:
            warnings.append(
                f"WARNING: Negative terminal growth rate ({assumptions.terminal_growth_rate:.1%}) "
                f"implies perpetual decline. Consider using zero growth or restructuring the model."
            )
        
        # Rule 3: WACC should be reasonable for a going concern
        if assumptions.wacc < 0.06:
            warnings.append(
                f"WARNING: WACC ({assumptions.wacc:.1%}) is very low. For most companies, WACC "
                f"should be 8-15% depending on risk profile and capital structure."
            )
        
        if assumptions.wacc > 0.20:
            warnings.append(
                f"WARNING: WACC ({assumptions.wacc:.1%}) is very high. This implies extreme risk. "
                f"Verify capital structure and beta assumptions."
            )
        
        # Rule 4: Check forecast period revenue growth vs terminal growth
        if assumptions.revenue_growth_rates:
            last_year_growth = assumptions.revenue_growth_rates[-1]
            if last_year_growth < assumptions.terminal_growth_rate:
                warnings.append(
                    f"INFO: Final forecast year growth ({last_year_growth:.1%}) is below terminal "
                    f"growth ({assumptions.terminal_growth_rate:.1%}). Terminal value will show "
                    f"acceleration, which may be unrealistic."
                )
        
        is_valid = not any('CRITICAL' in w for w in warnings)
        return is_valid, warnings
    
    def _calculate_dcf(
        self,
        historical: Dict[str, Any],
        assumptions: DCFAssumptions,
        company_profile: Dict[str, Any],
        suppress_warnings: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate DCF valuation with intelligent validation
        
        Args:
            suppress_warnings: If True, suppress warning logs (for Monte Carlo simulations)
        """
        
        # Validate assumptions before proceeding
        is_valid, validation_warnings = self._validate_dcf_assumptions(assumptions, suppress_warnings)
        
        # Only log if not suppressed (and log INFO only once, not in loops)
        if not suppress_warnings:
            critical_logged = False
            warning_logged = False
            info_logged = False
            
            for warning in validation_warnings:
                if 'CRITICAL' in warning and not critical_logged:
                    logger.error(warning)
                    critical_logged = True
                elif 'WARNING' in warning and not warning_logged:
                    logger.warning(warning)
                    warning_logged = True
                elif 'INFO' in warning and not info_logged:
                    logger.debug(warning)  # Changed to DEBUG to reduce noise
                    info_logged = True
        
        # If critical validation fails, auto-correct assumptions
        if not is_valid:
            logger.error("Critical DCF assumption validation failed. Auto-correcting assumptions.")
            # Ensure minimum 2% spread between WACC and terminal growth
            min_spread = 0.02
            if assumptions.wacc - assumptions.terminal_growth_rate < min_spread:
                original_wacc = assumptions.wacc
                original_terminal = assumptions.terminal_growth_rate
                
                # Strategy: Keep terminal growth, increase WACC
                assumptions.wacc = assumptions.terminal_growth_rate + min_spread
                
                logger.warning(
                    f"AUTO-CORRECTED: WACC adjusted from {original_wacc:.1%} to {assumptions.wacc:.1%} "
                    f"to maintain {min_spread:.1%} spread above terminal growth ({assumptions.terminal_growth_rate:.1%}). "
                    f"Review and adjust assumptions as needed."
                )
                
                # Re-validate after auto-correction
                is_valid, validation_warnings = self._validate_dcf_assumptions(assumptions)
        
        base_revenue = historical.get('latest_revenue', 0)
        
        # Project cash flows
        projections = []
        current_revenue = base_revenue
        
        for year in range(1, assumptions.forecast_years + 1):
            # Revenue projection
            growth_rate = assumptions.revenue_growth_rates[year - 1] if assumptions.revenue_growth_rates else 0.05
            current_revenue = current_revenue * (1 + growth_rate)
            
            # EBITDA projection
            ebitda_margin = assumptions.ebitda_margins[year - 1] if assumptions.ebitda_margins else 0.2
            ebitda = current_revenue * ebitda_margin
            
            # Calculate NOPAT (Net Operating Profit After Tax)
            ebit = ebitda - (current_revenue * assumptions.depreciation_percent_revenue)
            tax = ebit * assumptions.tax_rate
            nopat = ebit - tax
            
            # Add back depreciation
            depreciation = current_revenue * assumptions.depreciation_percent_revenue
            
            # Subtract capex
            capex = current_revenue * assumptions.capex_percent_revenue
            
            # Subtract change in NWC
            nwc_investment = current_revenue * assumptions.nwc_percent_revenue * growth_rate
            
            # Free cash flow
            fcf = nopat + depreciation - capex - nwc_investment
            
            # Present value
            pv_factor = 1 / ((1 + assumptions.wacc) ** year)
            pv = fcf * pv_factor
            
            projections.append({
                'year': year,
                'revenue': current_revenue,
                'ebitda': ebitda,
                'ebit': ebit,
                'nopat': nopat,
                'fcf': fcf,
                'pv_factor': pv_factor,
                'pv': pv
            })
        
        # Terminal value using Gordon Growth Model
        terminal_fcf = projections[-1]['fcf'] * (1 + assumptions.terminal_growth_rate)
        wacc_growth_diff = assumptions.wacc - assumptions.terminal_growth_rate
        
        # This should never happen now due to validation, but keep as safety check
        if wacc_growth_diff <= 0:
            logger.error(
                f"FATAL ERROR: WACC ({assumptions.wacc:.1%}) ≤ terminal growth "
                f"({assumptions.terminal_growth_rate:.1%}). This makes the Gordon Growth Model "
                f"mathematically invalid. The model assumes WACC > terminal growth."
            )
            # Emergency fallback: use exit multiple instead
            terminal_value = projections[-1]['ebitda'] * 10  # 10x EBITDA exit multiple
            logger.warning(
                f"Using emergency exit multiple valuation (10x final year EBITDA = ${terminal_value:,.0f}) "
                f"instead of Gordon Growth Model."
            )
        else:
            terminal_value = terminal_fcf / wacc_growth_diff
        
        terminal_pv = terminal_value / ((1 + assumptions.wacc) ** assumptions.forecast_years)
        
        # Enterprise value
        pv_explicit = sum(p['pv'] for p in projections)
        enterprise_value = pv_explicit + terminal_pv
        
        # Equity value
        net_debt = historical.get('total_debt', 0)
        equity_value = enterprise_value - net_debt
        
        # CRITICAL FIX: Calculate price per share for Excel Dashboard
        # Extract shares outstanding from company profile or estimate from market cap
        shares_outstanding = 0
        price_per_share = 0
        
        if company_profile:
            # Try to get shares outstanding from profile
            shares_outstanding = company_profile.get('shares_outstanding', 0)
            
            # If not in profile, try calculating from market cap and current stock price
            if not shares_outstanding or shares_outstanding == 0:
                market_cap = historical.get('market_cap', 0)
                current_price = company_profile.get('price', 0)
                
                if market_cap > 0 and current_price > 0:
                    shares_outstanding = market_cap / current_price
                    logger.info(f"Calculated shares outstanding from market cap: {shares_outstanding:,.0f} shares")
        
        # Calculate price per share if we have shares outstanding
        if shares_outstanding > 0:
            price_per_share = equity_value / shares_outstanding
            logger.info(f"Calculated price per share: ${price_per_share:.2f} (Equity Value: ${equity_value:,.0f} / {shares_outstanding:,.0f} shares)")
        else:
            logger.warning("Unable to calculate price per share - shares outstanding not available")
        
        return {
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'price_per_share': price_per_share,
            'shares_outstanding': shares_outstanding,
            'pv_explicit_period': pv_explicit,
            'terminal_value': terminal_value,
            'terminal_pv': terminal_pv,
            'terminal_value_as_percent_of_ev': (terminal_pv / enterprise_value * 100) if enterprise_value > 0 else 0,
            'projections': projections,
            'assumptions': {
                'wacc': assumptions.wacc,
                'terminal_growth': assumptions.terminal_growth_rate,
                'wacc_terminal_spread': wacc_growth_diff,
                'forecast_years': assumptions.forecast_years,
                'revenue_growth_rates': assumptions.revenue_growth_rates,
                'ebitda_margins': assumptions.ebitda_margins
            },
            'validation_warnings': validation_warnings
        }
    
    def run_sensitivity_analysis(
        self,
        financial_data: Dict[str, Any],
        company_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run sensitivity analysis on WACC and terminal growth rate
        """
        logger.info("Running sensitivity analysis")
        
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        historical_metrics = self._calculate_historical_metrics(
            income_statements,
            balance_sheets,
            cash_flows
        )
        
        base_assumptions = self._create_base_case_assumptions(historical_metrics)
        
        # Define sensitivity ranges
        wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
        terminal_growth_range = [0.015, 0.020, 0.025, 0.030, 0.035]
        
        # Create sensitivity matrix
        sensitivity_matrix = []
        
        for wacc in wacc_range:
            row = []
            for terminal_growth in terminal_growth_range:
                # Create modified assumptions
                modified_assumptions = DCFAssumptions(
                    forecast_years=base_assumptions.forecast_years,
                    terminal_growth_rate=terminal_growth,
                    wacc=wacc,
                    revenue_growth_rates=base_assumptions.revenue_growth_rates,
                    ebitda_margins=base_assumptions.ebitda_margins,
                    capex_percent_revenue=base_assumptions.capex_percent_revenue,
                    nwc_percent_revenue=base_assumptions.nwc_percent_revenue,
                    depreciation_percent_revenue=base_assumptions.depreciation_percent_revenue
                )
                
                # Calculate valuation
                result = self._calculate_dcf(historical_metrics, modified_assumptions, company_profile)
                row.append(result['enterprise_value'])
            
            sensitivity_matrix.append(row)
        
        # Create DataFrame for easy visualization
        df = pd.DataFrame(
            sensitivity_matrix,
            index=[f'{w:.1%}' for w in wacc_range],
            columns=[f'{tg:.1%}' for tg in terminal_growth_range]
        )
        
        return {
            'sensitivity_matrix': sensitivity_matrix,
            'wacc_range': wacc_range,
            'terminal_growth_range': terminal_growth_range,
            'dataframe': df.to_dict(),
            'analysis': 'Enterprise value sensitivity to WACC and terminal growth rate'
        }
    
    def run_monte_carlo_valuation(
        self,
        financial_data: Dict[str, Any],
        company_profile: Dict[str, Any],
        num_simulations: int = 10000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for valuation range
        """
        logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")
        
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        historical_metrics = self._calculate_historical_metrics(
            income_statements,
            balance_sheets,
            cash_flows
        )
        
        # Define distributions for key variables
        avg_growth = historical_metrics.get('avg_revenue_growth', 0.05)
        
        valuations = []
        
        for _ in range(num_simulations):
            # Sample from distributions
            wacc = np.random.normal(0.10, 0.02)  # Mean 10%, std 2%
            wacc = max(0.05, min(0.20, wacc))  # Bound between 5% and 20%
            
            terminal_growth = np.random.normal(0.025, 0.01)  # Mean 2.5%, std 1%
            terminal_growth = max(0.0, min(0.05, terminal_growth))  # Bound between 0% and 5%
            
            # Random revenue growth rates
            growth_volatility = np.std([avg_growth * 0.8, avg_growth * 1.2])
            growth_rates = [np.random.normal(avg_growth * (1 - 0.1*i), growth_volatility) 
                          for i in range(5)]
            growth_rates = [max(0, g) for g in growth_rates]  # No negative growth
            
            # Random EBITDA margins
            base_margin = historical_metrics.get('ebitda_margin', 0.2)
            margins = [np.random.normal(base_margin, 0.02) for _ in range(5)]
            margins = [max(0.05, min(0.50, m)) for m in margins]  # Bound margins
            
            # Create assumptions
            assumptions = DCFAssumptions(
                forecast_years=5,
                terminal_growth_rate=terminal_growth,
                wacc=wacc,
                revenue_growth_rates=growth_rates,
                ebitda_margins=margins
            )
            
            # Calculate valuation (suppress warnings for Monte Carlo)
            result = self._calculate_dcf(historical_metrics, assumptions, company_profile, suppress_warnings=True)
            valuations.append(result['enterprise_value'])
        
        # Statistical analysis
        valuations = np.array(valuations)
        
        return {
            'num_simulations': num_simulations,
            'mean_valuation': float(np.mean(valuations)),
            'median_valuation': float(np.median(valuations)),
            'std_deviation': float(np.std(valuations)),
            'percentiles': {
                '5th': float(np.percentile(valuations, 5)),
                '25th': float(np.percentile(valuations, 25)),
                '50th': float(np.percentile(valuations, 50)),
                '75th': float(np.percentile(valuations, 75)),
                '95th': float(np.percentile(valuations, 95))
            },
            'confidence_intervals': {
                '90%': [float(np.percentile(valuations, 5)), float(np.percentile(valuations, 95))],
                '95%': [float(np.percentile(valuations, 2.5)), float(np.percentile(valuations, 97.5))],
                '99%': [float(np.percentile(valuations, 0.5)), float(np.percentile(valuations, 99.5))]
            }
        }
    
    async def run_comparable_analysis(
        self,
        target_data: Dict[str, Any],
        comparable_tickers: List[str]
    ) -> Dict[str, Any]:
        """
        Comparable company analysis (Trading Comps) - REAL DATA from FMP
        """
        logger.info(f"Running comparable company analysis with {len(comparable_tickers)} comps")
        
        try:
            from src.integrations.fmp_client import FMPClient
            import asyncio
            
            # Fetch real comp data from FMP
            async with FMPClient() as fmp_client:
                # Fetch data for all comparables in parallel
                comp_data_tasks = [
                    fmp_client.get_company_profile(ticker) for ticker in comparable_tickers
                ]
                comp_profiles = await asyncio.gather(*comp_data_tasks, return_exceptions=True)
                
                # Fetch key metrics for all comps
                metrics_tasks = [
                    fmp_client.get_key_metrics(ticker) for ticker in comparable_tickers
                ]
                comp_metrics = await asyncio.gather(*metrics_tasks, return_exceptions=True)
                
                # Fetch ratios
                ratios_tasks = [
                    fmp_client.get_financial_ratios(ticker) for ticker in comparable_tickers
                ]
                comp_ratios = await asyncio.gather(*ratios_tasks, return_exceptions=True)
            
            # Process results
            ev_revenue_multiples = []
            ev_ebitda_multiples = []
            pe_ratios = []
            
            comp_summary = []
            
            for i, ticker in enumerate(comparable_tickers):
                try:
                    profile = comp_profiles[i] if i < len(comp_profiles) and not isinstance(comp_profiles[i], Exception) else {}
                    metrics = comp_metrics[i] if i < len(comp_metrics) and not isinstance(comp_metrics[i], Exception) else []
                    ratios = comp_ratios[i] if i < len(comp_ratios) and not isinstance(comp_ratios[i], Exception) else []
                    
                    if profile and metrics and ratios:
                        latest_metrics = metrics[0] if isinstance(metrics, list) and len(metrics) > 0 else {}
                        latest_ratios = ratios[0] if isinstance(ratios, list) and len(ratios) > 0 else {}
                        
                        # Extract multiples
                        ev_rev = latest_metrics.get('enterpriseValueMultiple')
                        ev_ebitda = latest_metrics.get('evToEbitda')  
                        pe = latest_ratios.get('priceEarningsRatio')
                        
                        if ev_rev:
                            ev_revenue_multiples.append(ev_rev)
                        if ev_ebitda:
                            ev_ebitda_multiples.append(ev_ebitda)
                        if pe:
                            pe_ratios.append(pe)
                        
                        comp_summary.append({
                            'ticker': ticker,
                            'company': profile.get('companyName', ticker),
                            'market_cap': profile.get('mktCap', 0),
                            'ev_revenue': ev_rev,
                            'ev_ebitda': ev_ebitda,
                            'pe_ratio': pe
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing {ticker}: {e}")
            
            # Calculate statistics
            def calc_stats(values):
                if not values:
                    return {'median': 0, 'mean': 0, 'min': 0, 'max': 0, 'count': 0}
                return {
                    'median': float(np.median(values)),
                    'mean': float(np.mean(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'count': len(values)
                }
            
            return {
                'method': 'Trading Comparables - Real Market Data',
                'comparable_companies': comp_summary,
                'num_companies': len(comp_summary),
                'multiples_analysis': {
                    'ev_revenue': calc_stats(ev_revenue_multiples),
                    'ev_ebitda': calc_stats(ev_ebitda_multiples),
                    'pe_ratio': calc_stats(pe_ratios)
                },
                'data_source': 'FMP API - Real-time market data'
            }
            
        except Exception as e:
            logger.error(f"Error fetching comparable company data: {e}")
            return {
                'method': 'Trading Comparables',
                'error': str(e),
                'note': 'Failed to fetch real comp data'
            }
    
    def analyze_precedent_transactions(
        self,
        target_data: Dict[str, Any],
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Precedent transaction analysis
        """
        logger.info(f"Analyzing {len(transactions)} precedent transactions")
        
        return {
            'method': 'Precedent Transactions',
            'num_transactions': len(transactions),
            'transaction_multiples': {
                'ev_revenue': {'median': 6.0, 'mean': 6.5, 'range': [4.0, 10.0]},
                'ev_ebitda': {'median': 15.0, 'mean': 16.0, 'range': [10.0, 22.0]},
                'premium_paid': {'median': 0.30, 'mean': 0.35, 'range': [0.15, 0.50]}
            },
            'note': 'Would fetch real precedent transaction data in production'
        }
    
    def generate_valuation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate valuation summary from all methods with per-share calculations
        """
        dcf = results.get('dcf_analysis', {})
        monte_carlo = results.get('monte_carlo_simulation', {})
        
        base_ev = dcf.get('base', {}).get('enterprise_value', 0)
        optimistic_ev = dcf.get('optimistic', {}).get('enterprise_value', 0)
        pessimistic_ev = dcf.get('pessimistic', {}).get('enterprise_value', 0)
        weighted_ev = dcf.get('probability_weighted', {}).get('enterprise_value', 0)
        
        mc_median = monte_carlo.get('median_valuation', 0)
        mc_mean = monte_carlo.get('mean_valuation', 0)
        
        # Get base case equity value and shares for per-share calculation
        base_equity = dcf.get('base', {}).get('equity_value', 0)
        optimistic_equity = dcf.get('optimistic', {}).get('equity_value', 0)
        pessimistic_equity = dcf.get('pessimistic', {}).get('equity_value', 0)
        weighted_equity = weighted_ev - dcf.get('base', {}).get('assumptions', {}).get('net_debt', 0)
        
        # Estimate shares outstanding (would get from company profile in full implementation)
        # For now, use a reasonable estimate based on market cap if available
        shares_outstanding = dcf.get('base', {}).get('shares_outstanding', 1000000000)  # 1B shares default
        
        # Calculate per-share values
        base_per_share = base_equity / shares_outstanding if shares_outstanding > 0 else 0
        optimistic_per_share = optimistic_equity / shares_outstanding if shares_outstanding > 0 else 0
        pessimistic_per_share = pessimistic_equity / shares_outstanding if shares_outstanding > 0 else 0
        weighted_per_share = weighted_equity / shares_outstanding if shares_outstanding > 0 else 0
        mc_per_share = (mc_median - dcf.get('base', {}).get('assumptions', {}).get('net_debt', 0)) / shares_outstanding if shares_outstanding > 0 else 0
        
        return {
            'dcf_base_case': base_ev,
            'dcf_optimistic': optimistic_ev,
            'dcf_pessimistic': pessimistic_ev,
            'dcf_probability_weighted': weighted_ev,
            'monte_carlo_median': mc_median,
            'monte_carlo_mean': mc_mean,
            'valuation_range': {
                'low': pessimistic_ev,
                'mid': weighted_ev,
                'high': optimistic_ev
            },
            'per_share_values': {
                'dcf_base_case_per_share': base_per_share,
                'dcf_optimistic_per_share': optimistic_per_share,
                'dcf_pessimistic_per_share': pessimistic_per_share,
                'dcf_weighted_per_share': weighted_per_share,
                'monte_carlo_per_share': mc_per_share
            },
            'dcf_value_per_share': weighted_per_share,  # Main per-share value
            'shares_outstanding': shares_outstanding
        }
    
    def generate_valuation_recommendation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate valuation-based recommendation
        """
        summary = results.get('valuation_summary', {})
        
        low = summary.get('valuation_range', {}).get('low', 0)
        mid = summary.get('valuation_range', {}).get('mid', 0)
        high = summary.get('valuation_range', {}).get('high', 0)
        
        recommendation_text = f"""
Based on comprehensive valuation analysis:

Valuation Range:
- Pessimistic Case: ${low:,.0f}
- Base Case (Probability-Weighted): ${mid:,.0f}
- Optimistic Case: ${high:,.0f}

The probability-weighted DCF valuation of ${mid:,.0f} represents the most likely fair value,
incorporating both upside and downside scenarios. The Monte Carlo simulation provides additional
confidence intervals for decision-making under uncertainty.

Recommendation: Use the base case valuation range as the primary reference for negotiation,
with sensitivity to key value drivers such as WACC and terminal growth assumptions.
"""
        
        return {
            'summary': recommendation_text.strip(),
            'target_valuation': mid,
            'negotiation_range': {
                'floor': low,
                'ceiling': high
            }
        }
    
    def run_lbo_analysis(
        self,
        financial_data: Dict[str, Any],
        company_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run Leveraged Buyout (LBO) analysis - Private Equity Standard
        
        This models a typical PE acquisition with:
        - 60-70% debt financing
        - 5-7 year hold period
        - Exit at 10-12x EBITDA
        - Target 20-25% IRR
        
        Returns:
            LBO model with IRR, MoM (Multiple of Money), and debt paydown schedule
        """
        logger.info("Running LBO analysis (Private Equity model)")
        
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        if not income_statements or not cash_flows:
            return {'error': 'Insufficient data for LBO analysis'}
        
        # Calculate historical metrics
        historical = self._calculate_historical_metrics(
            income_statements,
            balance_sheets,
            cash_flows
        )
        
        # LBO Entry Assumptions
        latest_ebitda = historical.get('latest_ebitda', 0)
        entry_multiple = 12.0  # 12x EBITDA entry (typical for quality assets)
        purchase_price = latest_ebitda * entry_multiple
        
        # Capital Structure (typical PE deal)
        equity_percent = 0.35  # 35% equity
        debt_percent = 0.65  # 65% debt (leverage)
        
        equity_contribution = purchase_price * equity_percent
        debt_raised = purchase_price * debt_percent
        
        # Debt Terms
        debt_interest_rate = 0.07  # 7% blended rate
        debt_term_years = 7
        
        # Operating Assumptions (based on historical)
        base_growth = historical.get('avg_revenue_growth', 0.05)
        growth_rates = [base_growth * 0.9**i for i in range(7)]  # Declining growth
        ebitda_margin = historical.get('ebitda_margin', 0.20)
        
        # Build 7-year projection
        projections = []
        current_revenue = historical.get('latest_revenue', 0)
        outstanding_debt = debt_raised
        
        for year in range(1, 8):
            # Revenue
            growth = growth_rates[year - 1]
            current_revenue = current_revenue * (1 + growth)
            
            # EBITDA
            ebitda = current_revenue * ebitda_margin
            
            # Less: D&A, Interest, Taxes
            depreciation = current_revenue * 0.03
            ebit = ebitda - depreciation
            interest_expense = outstanding_debt * debt_interest_rate
            ebt = ebit - interest_expense
            taxes = max(0, ebt * 0.21)  # 21% tax rate
            net_income = ebt - taxes
            
            # Add back D&A, subtract CapEx and NWC
            capex = current_revenue * 0.03
            nwc_investment = current_revenue * 0.10 * growth
            
            # Free Cash Flow to Equity (after debt service)
            fcf = net_income + depreciation - capex - nwc_investment
            
            # Debt paydown (all excess cash goes to debt)
            debt_paydown = max(0, fcf * 0.75)  # 75% of FCF to debt
            outstanding_debt = max(0, outstanding_debt - debt_paydown)
            
            projections.append({
                'year': year,
                'revenue': current_revenue,
                'ebitda': ebitda,
                'ebit': ebit,
                'interest_expense': interest_expense,
                'net_income': net_income,
                'fcf': fcf,
                'debt_paydown': debt_paydown,
                'outstanding_debt': outstanding_debt
            })
        
        # Exit Assumptions (Year 7)
        exit_ebitda = projections[-1]['ebitda']
        exit_multiple = 11.0  # 11x EBITDA exit (slight discount to entry)
        exit_enterprise_value = exit_ebitda * exit_multiple
        remaining_debt = projections[-1]['outstanding_debt']
        exit_equity_value = exit_enterprise_value - remaining_debt
        
        # Returns Calculation
        initial_equity = equity_contribution
        final_equity = exit_equity_value
        holding_period = 7  # years
        
        # IRR Calculation
        # IRR is the rate where NPV of cash flows = 0
        # Simplified: (Final Value / Initial Value)^(1/years) - 1
        irr = (final_equity / initial_equity) ** (1 / holding_period) - 1 if initial_equity > 0 else 0
        
        # Multiple of Money (MoM)
        multiple_of_money = final_equity / initial_equity if initial_equity > 0 else 0
        
        # Total debt paid down
        total_debt_paydown = debt_raised - remaining_debt
        debt_paydown_percent = (total_debt_paydown / debt_raised * 100) if debt_raised > 0 else 0
        
        return {
            'model_type': 'Leveraged Buyout Analysis',
            'entry_assumptions': {
                'purchase_price': purchase_price,
                'entry_multiple': entry_multiple,
                'ebitda_at_entry': latest_ebitda,
                'equity_contribution': equity_contribution,
                'debt_raised': debt_raised,
                'leverage_ratio': debt_percent / equity_percent,
                'debt_to_ebitda': debt_raised / latest_ebitda if latest_ebitda > 0 else 0
            },
            'debt_structure': {
                'total_debt': debt_raised,
                'interest_rate': debt_interest_rate,
                'term_years': debt_term_years,
                'debt_percent': debt_percent * 100,
                'equity_percent': equity_percent * 100
            },
            'projections': projections,
            'exit_assumptions': {
                'exit_year': holding_period,
                'exit_ebitda': exit_ebitda,
                'exit_multiple': exit_multiple,
                'exit_enterprise_value': exit_enterprise_value,
                'remaining_debt': remaining_debt,
                'exit_equity_value': exit_equity_value
            },
            'returns_analysis': {
                'initial_equity_investment': initial_equity,
                'exit_equity_value': exit_equity_value,
                'profit': final_equity - initial_equity,
                'irr': irr,
                'irr_percent': irr * 100,
                'multiple_of_money': multiple_of_money,
                'holding_period_years': holding_period,
                'total_debt_paydown': total_debt_paydown,
                'debt_paydown_percent': debt_paydown_percent,
                'annualized_return': irr  # Same as IRR
            },
            'deal_metrics': {
                'entry_ev_to_ebitda': entry_multiple,
                'exit_ev_to_ebitda': exit_multiple,
                'multiple_arbitrage': exit_multiple - entry_multiple,
                'leverage_at_entry': f"{debt_percent*100:.0f}/{equity_percent*100:.0f}",
                'leverage_at_exit': f"{(remaining_debt/exit_enterprise_value*100):.0f}/" +
                                   f"{((exit_equity_value/exit_enterprise_value)*100):.0f}" if exit_enterprise_value > 0 else "N/A"
            },
            'pe_investment_recommendation': self._generate_lbo_recommendation(irr, multiple_of_money),
            'sensitivity': self._lbo_sensitivity_analysis(
                latest_ebitda, equity_contribution, holding_period
            )
        }
    
    def _generate_lbo_recommendation(self, irr: float, mom: float) -> str:
        """Generate PE investment recommendation based on returns"""
        irr_pct = irr * 100
        
        if irr_pct >= 25:
            return f"STRONG BUY: IRR of {irr_pct:.1f}% and {mom:.2f}x MoM exceeds PE target returns (20-25% IRR). Attractive investment."
        elif irr_pct >= 20:
            return f"BUY: IRR of {irr_pct:.1f}% and {mom:.2f}x MoM meets PE target returns. Solid investment."
        elif irr_pct >= 15:
            return f"CONSIDER: IRR of {irr_pct:.1f}% and {mom:.2f}x MoM is below PE targets but may be acceptable with strategic value."
        else:
            return f"PASS: IRR of {irr_pct:.1f}% and {mom:.2f}x MoM is below PE threshold. Returns insufficient for risk."
    
    def _lbo_sensitivity_analysis(
        self,
        entry_ebitda: float,
        equity_investment: float,
        holding_period: int
    ) -> Dict[str, Any]:
        """
        LBO sensitivity analysis on exit multiples and EBITDA growth
        """
        exit_multiples = [9.0, 10.0, 11.0, 12.0, 13.0]
        ebitda_growth_rates = [0.03, 0.05, 0.07, 0.10, 0.12]
        
        # Create sensitivity matrix for IRR
        irr_matrix = []
        mom_matrix = []
        
        for growth in ebitda_growth_rates:
            irr_row = []
            mom_row = []
            
            for exit_multiple in exit_multiples:
                # Calculate exit EBITDA
                exit_ebitda = entry_ebitda * ((1 + growth) ** holding_period)
                
                # Calculate exit value (simplified - no debt paydown in sensitivity)
                exit_ev = exit_ebitda * exit_multiple
                exit_equity = exit_ev * 0.5  # Assume 50% debt paid down
                
                # Calculate IRR
                irr = (exit_equity / equity_investment) ** (1 / holding_period) - 1
                mom = exit_equity / equity_investment
                
                irr_row.append(irr * 100)
                mom_row.append(mom)
            
            irr_matrix.append(irr_row)
            mom_matrix.append(mom_row)
        
        return {
            'irr_sensitivity': {
                'matrix': irr_matrix,
                'exit_multiples': exit_multiples,
                'ebitda_growth_rates': ebitda_growth_rates,
                'note': 'IRR % sensitivity to exit multiple and EBITDA growth'
            },
            'mom_sensitivity': {
                'matrix': mom_matrix,
                'exit_multiples': exit_multiples,
                'ebitda_growth_rates': ebitda_growth_rates,
                'note': 'Multiple of Money sensitivity'
            }
        }
