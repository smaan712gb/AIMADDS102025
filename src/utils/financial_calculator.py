"""
Financial Calculator Tool System for M&A Analysis

Provides accurate, verifiable financial calculations for:
- DCF Valuation (3 methods: Standard, Sensitivity, Multiple Scenarios)
- LBO Analysis
- M&A Critical Metrics
- Synergy Valuation

Designed for function calling by LLMs to ensure 100% accurate calculations.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from loguru import logger


@dataclass
class DCFInputs:
    """Inputs for DCF valuation"""
    free_cash_flows: List[float]
    wacc: float
    terminal_growth_rate: float
    terminal_year_fcf: Optional[float] = None


@dataclass
class LBOInputs:
    """Inputs for LBO analysis"""
    purchase_price: float
    entry_multiple: float
    exit_multiple: float
    holding_period_years: int
    debt_financing_pct: float
    interest_rate: float
    annual_fcf: List[float]


class FinancialCalculator:
    """
    Investment Banking-Grade Financial Calculator
    
    Provides tools for LLMs to execute accurate financial calculations
    instead of attempting to calculate within token generation.
    """
    
    def __init__(self):
        """Initialize calculator"""
        logger.info("Financial Calculator initialized")
    
    # ========== DCF VALUATION METHODS ==========
    
    def calculate_dcf_standard(
        self,
        free_cash_flows: List[float],
        wacc: float,
        terminal_growth_rate: float,
        shares_outstanding: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate standard DCF valuation
        
        Args:
            free_cash_flows: List of projected FCF for explicit forecast period
            wacc: Weighted Average Cost of Capital (decimal, e.g., 0.10 for 10%)
            terminal_growth_rate: Terminal growth rate (decimal)
            shares_outstanding: Number of shares for per-share valuation
            
        Returns:
            Dictionary with enterprise value, equity value, and breakdown
        """
        try:
            # Validate inputs
            if wacc <= 0 or wacc >= 1:
                return {"error": "WACC must be between 0 and 1"}
            if terminal_growth_rate >= wacc:
                return {"error": "Terminal growth rate must be less than WACC"}
            if not free_cash_flows or len(free_cash_flows) == 0:
                return {"error": "Free cash flows list cannot be empty"}
            
            # Calculate present value of explicit forecast period
            pv_fcf = []
            for year, fcf in enumerate(free_cash_flows, start=1):
                discount_factor = (1 + wacc) ** year
                pv = fcf / discount_factor
                pv_fcf.append({
                    'year': year,
                    'fcf': fcf,
                    'discount_factor': discount_factor,
                    'present_value': pv
                })
            
            pv_explicit_period = sum(item['present_value'] for item in pv_fcf)
            
            # Calculate terminal value
            terminal_fcf = free_cash_flows[-1] * (1 + terminal_growth_rate)
            terminal_value = terminal_fcf / (wacc - terminal_growth_rate)
            
            # Discount terminal value to present
            terminal_year = len(free_cash_flows)
            pv_terminal_value = terminal_value / ((1 + wacc) ** terminal_year)
            
            # Enterprise value
            enterprise_value = pv_explicit_period + pv_terminal_value
            
            result = {
                'enterprise_value': enterprise_value,
                'pv_explicit_period': pv_explicit_period,
                'pv_terminal_value': pv_terminal_value,
                'terminal_value': terminal_value,
                'terminal_fcf': terminal_fcf,
                'wacc': wacc,
                'terminal_growth_rate': terminal_growth_rate,
                'forecast_years': terminal_year,
                'explicit_period_breakdown': pv_fcf,
                'methodology': 'Standard DCF (FCFF)'
            }
            
            # Calculate equity value per share if shares provided
            if shares_outstanding and shares_outstanding > 0:
                equity_value_per_share = enterprise_value / shares_outstanding
                result['shares_outstanding'] = shares_outstanding
                result['equity_value_per_share'] = equity_value_per_share
            
            return result
            
        except Exception as e:
            logger.error(f"DCF calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_dcf_sensitivity(
        self,
        free_cash_flows: List[float],
        base_wacc: float,
        base_terminal_growth: float,
        wacc_range: Tuple[float, float] = (-0.02, 0.02),
        growth_range: Tuple[float, float] = (-0.01, 0.01),
        steps: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate DCF with sensitivity analysis
        
        Args:
            free_cash_flows: Projected FCF
            base_wacc: Base WACC
            base_terminal_growth: Base terminal growth rate
            wacc_range: WACC sensitivity range (min, max adjustment)
            growth_range: Growth rate sensitivity range (min, max adjustment)
            steps: Number of steps in sensitivity table
            
        Returns:
            Sensitivity analysis with valuation matrix
        """
        try:
            # Calculate base case
            base_valuation = self.calculate_dcf_standard(
                free_cash_flows, base_wacc, base_terminal_growth
            )
            
            if 'error' in base_valuation:
                return base_valuation
            
            # Generate sensitivity ranges
            wacc_values = np.linspace(
                base_wacc + wacc_range[0],
                base_wacc + wacc_range[1],
                steps
            )
            growth_values = np.linspace(
                base_terminal_growth + growth_range[0],
                base_terminal_growth + growth_range[1],
                steps
            )
            
            # Build sensitivity matrix
            sensitivity_matrix = []
            for wacc in wacc_values:
                row = []
                for growth in growth_values:
                    if growth < wacc:  # Valid only if growth < wacc
                        val = self.calculate_dcf_standard(
                            free_cash_flows, wacc, growth
                        )
                        row.append(val.get('enterprise_value', None))
                    else:
                        row.append(None)
                sensitivity_matrix.append(row)
            
            return {
                'base_case': base_valuation,
                'sensitivity_matrix': sensitivity_matrix,
                'wacc_values': wacc_values.tolist(),
                'growth_values': growth_values.tolist(),
                'base_wacc': base_wacc,
                'base_terminal_growth': base_terminal_growth,
                'methodology': 'DCF with Sensitivity Analysis'
            }
            
        except Exception as e:
            logger.error(f"Sensitivity analysis error: {e}")
            return {"error": str(e)}
    
    def calculate_dcf_scenarios(
        self,
        bull_fcf: List[float],
        base_fcf: List[float],
        bear_fcf: List[float],
        wacc_bull: float,
        wacc_base: float,
        wacc_bear: float,
        terminal_growth_bull: float,
        terminal_growth_base: float,
        terminal_growth_bear: float,
        probability_bull: float = 0.25,
        probability_base: float = 0.50,
        probability_bear: float = 0.25
    ) -> Dict[str, Any]:
        """
        Calculate DCF with multiple scenarios (Bull/Base/Bear)
        
        Args:
            bull_fcf, base_fcf, bear_fcf: FCF projections for each scenario
            wacc_*: WACC for each scenario
            terminal_growth_*: Terminal growth for each scenario
            probability_*: Probability weights for each scenario
            
        Returns:
            Scenario analysis with probability-weighted valuation
        """
        try:
            # Validate probabilities sum to 1.0
            total_prob = probability_bull + probability_base + probability_bear
            if abs(total_prob - 1.0) > 0.01:
                return {"error": f"Probabilities must sum to 1.0 (got {total_prob})"}
            
            # Calculate each scenario
            bull_case = self.calculate_dcf_standard(bull_fcf, wacc_bull, terminal_growth_bull)
            base_case = self.calculate_dcf_standard(base_fcf, wacc_base, terminal_growth_base)
            bear_case = self.calculate_dcf_standard(bear_fcf, wacc_bear, terminal_growth_bear)
            
            # Check for errors
            if any('error' in case for case in [bull_case, base_case, bear_case]):
                return {"error": "One or more scenario calculations failed"}
            
            # Calculate probability-weighted value
            weighted_value = (
                bull_case['enterprise_value'] * probability_bull +
                base_case['enterprise_value'] * probability_base +
                bear_case['enterprise_value'] * probability_bear
            )
            
            return {
                'probability_weighted_value': weighted_value,
                'bull_case': {
                    **bull_case,
                    'probability': probability_bull,
                    'scenario': 'Bull'
                },
                'base_case': {
                    **base_case,
                    'probability': probability_base,
                    'scenario': 'Base'
                },
                'bear_case': {
                    **bear_case,
                    'probability': probability_bear,
                    'scenario': 'Bear'
                },
                'valuation_range': {
                    'low': bear_case['enterprise_value'],
                    'mid': base_case['enterprise_value'],
                    'high': bull_case['enterprise_value']
                },
                'methodology': 'DCF with Multiple Scenarios (Bull/Base/Bear)'
            }
            
        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")
            return {"error": str(e)}
    
    # ========== LBO ANALYSIS ==========
    
    def calculate_lbo_returns(
        self,
        purchase_price: float,
        entry_multiple: float,
        exit_multiple: float,
        holding_period_years: int,
        debt_financing_pct: float,
        interest_rate: float,
        annual_fcf: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate LBO returns (IRR, MOIC)
        
        Args:
            purchase_price: Total purchase price
            entry_multiple: Entry EBITDA multiple
            exit_multiple: Exit EBITDA multiple
            holding_period_years: Holding period (typically 3, 5, or 7 years)
            debt_financing_pct: Debt as % of purchase price (e.g., 0.60 for 60%)
            interest_rate: Interest rate on debt
            annual_fcf: Annual free cash flow projections
            
        Returns:
            LBO analysis with IRR and cash-on-cash returns
        """
        try:
            # Validate inputs
            if holding_period_years != len(annual_fcf):
                return {"error": f"FCF projections ({len(annual_fcf)}) must match holding period ({holding_period_years})"}
            
            # Calculate initial structure
            initial_debt = purchase_price * debt_financing_pct
            initial_equity = purchase_price * (1 - debt_financing_pct)
            
            # Calculate debt paydown
            debt_balance = initial_debt
            debt_schedule = []
            
            for year, fcf in enumerate(annual_fcf, start=1):
                interest_payment = debt_balance * interest_rate
                principal_payment = min(fcf - interest_payment, debt_balance) if fcf > interest_payment else 0
                debt_balance -= principal_payment
                
                debt_schedule.append({
                    'year': year,
                    'beginning_balance': debt_balance + principal_payment,
                    'interest_payment': interest_payment,
                    'principal_payment': principal_payment,
                    'ending_balance': debt_balance,
                    'fcf': fcf
                })
            
            # Calculate exit value
            # Assume exit EBITDA = final year EBITDA
            # For simplicity, estimate EBITDA from entry multiple
            entry_ebitda = purchase_price / entry_multiple
            exit_ebitda = entry_ebitda * (1.05 ** holding_period_years)  # Assume 5% growth
            exit_enterprise_value = exit_ebitda * exit_multiple
            
            # Calculate equity proceeds
            final_debt = debt_schedule[-1]['ending_balance']
            equity_proceeds = exit_enterprise_value - final_debt
            
            # Calculate returns
            moic = equity_proceeds / initial_equity  # Multiple on Invested Capital
            
            # Calculate IRR using numpy-financial (np.irr is deprecated)
            cash_flows = [-initial_equity] + [0] * (holding_period_years - 1) + [equity_proceeds]
            try:
                import numpy_financial as npf
                irr = npf.irr(cash_flows)
            except ImportError:
                # Fallback: approximate IRR using MOIC
                irr = (moic ** (1/holding_period_years)) - 1
                logger.warning("numpy_financial not available, using approximate IRR calculation")
            
            return {
                'purchase_price': purchase_price,
                'entry_multiple': entry_multiple,
                'exit_multiple': exit_multiple,
                'initial_debt': initial_debt,
                'initial_equity': initial_equity,
                'debt_financing_pct': debt_financing_pct,
                'final_debt': final_debt,
                'exit_enterprise_value': exit_enterprise_value,
                'equity_proceeds': equity_proceeds,
                'moic': moic,
                'irr': irr,
                'holding_period_years': holding_period_years,
                'debt_paydown_schedule': debt_schedule,
                'cash_on_cash_return': moic,
                'annualized_return': irr,
                'methodology': 'LBO Analysis'
            }
            
        except Exception as e:
            logger.error(f"LBO calculation error: {e}")
            return {"error": str(e)}
    
    # ========== M&A CRITICAL METRICS ==========
    
    def calculate_synergies(
        self,
        revenue_synergies: float,
        cost_synergies: float,
        synergy_realization_years: int,
        tax_rate: float,
        wacc: float
    ) -> Dict[str, Any]:
        """
        Calculate NPV of synergies
        
        Args:
            revenue_synergies: Annual revenue synergies at full realization
            cost_synergies: Annual cost synergies at full realization
            synergy_realization_years: Years to reach full synergy run-rate
            tax_rate: Corporate tax rate
            wacc: Discount rate
            
        Returns:
            NPV of synergies and breakdown
        """
        try:
            total_synergies = revenue_synergies + cost_synergies
            after_tax_synergies = total_synergies * (1 - tax_rate)
            
            # Assume linear ramp-up to full synergies
            synergy_stream = []
            for year in range(1, synergy_realization_years + 1):
                year_synergy = after_tax_synergies * (year / synergy_realization_years)
                pv = year_synergy / ((1 + wacc) ** year)
                synergy_stream.append({
                    'year': year,
                    'synergy_amount': year_synergy,
                    'present_value': pv
                })
            
            # Terminal value of synergies (perpetuity)
            terminal_synergy = after_tax_synergies / wacc
            pv_terminal = terminal_synergy / ((1 + wacc) ** synergy_realization_years)
            
            npv_synergies = sum(s['present_value'] for s in synergy_stream) + pv_terminal
            
            return {
                'npv_synergies': npv_synergies,
                'revenue_synergies': revenue_synergies,
                'cost_synergies': cost_synergies,
                'total_synergies_pretax': total_synergies,
                'after_tax_synergies': after_tax_synergies,
                'synergy_ramp_schedule': synergy_stream,
                'pv_terminal_synergies': pv_terminal,
                'realization_period': synergy_realization_years,
                'methodology': 'Synergy Valuation'
            }
            
        except Exception as e:
            logger.error(f"Synergy calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_accretion_dilution(
        self,
        acquirer_eps: float,
        target_earnings: float,
        purchase_price: float,
        shares_issued: float,
        cost_of_debt: float,
        debt_used: float,
        tax_rate: float,
        synergies: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate accretion/dilution analysis
        
        Args:
            acquirer_eps: Acquirer's current EPS
            target_earnings: Target's earnings
            purchase_price: Total purchase price
            shares_issued: New shares issued for acquisition
            cost_of_debt: Interest rate on debt used
            debt_used: Amount of debt financing
            tax_rate: Tax rate
            synergies: Expected after-tax synergies
            
        Returns:
            Accretion/dilution analysis
        """
        try:
            # Calculate financing costs
            interest_expense = debt_used * cost_of_debt
            after_tax_interest = interest_expense * (1 - tax_rate)
            
            # Pro forma earnings
            pro_forma_earnings = target_earnings + synergies - after_tax_interest
            
            # Pro forma EPS
            # Assuming acquirer has enough shares to calculate
            # This is simplified - would need acquirer's share count
            pro_forma_eps = acquirer_eps + (pro_forma_earnings / shares_issued) if shares_issued > 0 else acquirer_eps
            
            # Accretion/Dilution
            accretion_dilution = pro_forma_eps - acquirer_eps
            accretion_pct = (accretion_dilution / acquirer_eps) * 100 if acquirer_eps != 0 else 0
            
            return {
                'acquirer_eps': acquirer_eps,
                'pro_forma_eps': pro_forma_eps,
                'accretion_dilution': accretion_dilution,
                'accretion_pct': accretion_pct,
                'is_accretive': accretion_dilution > 0,
                'target_earnings_contribution': target_earnings,
                'synergies': synergies,
                'financing_cost': after_tax_interest,
                'methodology': 'Accretion/Dilution Analysis'
            }
            
        except Exception as e:
            logger.error(f"Accretion/dilution calculation error: {e}")
            return {"error": str(e)}
    
    def calculate_payback_period(
        self,
        initial_investment: float,
        annual_cash_flows: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate payback period
        
        Args:
            initial_investment: Initial investment amount
            annual_cash_flows: Annual cash flow projections
            
        Returns:
            Payback period analysis
        """
        try:
            cumulative_cf = 0
            payback_year = None
            
            for year, cf in enumerate(annual_cash_flows, start=1):
                cumulative_cf += cf
                if cumulative_cf >= initial_investment and payback_year is None:
                    # Interpolate for exact payback
                    previous_cumulative = cumulative_cf - cf
                    fraction = (initial_investment - previous_cumulative) / cf
                    payback_year = year - 1 + fraction
                    break
            
            if payback_year is None:
                payback_year = "Beyond projection period"
            
            return {
                'payback_period_years': payback_year,
                'initial_investment': initial_investment,
                'cumulative_cash_flows': cumulative_cf,
                'annual_cash_flows': annual_cash_flows,
                'methodology': 'Payback Period Analysis'
            }
            
        except Exception as e:
            logger.error(f"Payback period calculation error: {e}")
            return {"error": str(e)}
    
    # ========== UTILITY FUNCTIONS ==========
    
    def calculate_wacc(
        self,
        cost_of_equity: float,
        cost_of_debt: float,
        tax_rate: float,
        market_value_equity: float,
        market_value_debt: float
    ) -> Dict[str, Any]:
        """
        Calculate Weighted Average Cost of Capital
        
        Args:
            cost_of_equity: Cost of equity (CAPM or other method)
            cost_of_debt: Pre-tax cost of debt
            tax_rate: Corporate tax rate
            market_value_equity: Market value of equity
            market_value_debt: Market value of debt
            
        Returns:
            WACC calculation
        """
        try:
            total_value = market_value_equity + market_value_debt
            
            if total_value == 0:
                return {"error": "Total capital cannot be zero"}
            
            weight_equity = market_value_equity / total_value
            weight_debt = market_value_debt / total_value
            
            after_tax_cost_debt = cost_of_debt * (1 - tax_rate)
            
            wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_cost_debt)
            
            return {
                'wacc': wacc,
                'cost_of_equity': cost_of_equity,
                'after_tax_cost_of_debt': after_tax_cost_debt,
                'weight_equity': weight_equity,
                'weight_debt': weight_debt,
                'market_value_equity': market_value_equity,
                'market_value_debt': market_value_debt,
                'methodology': 'WACC Calculation'
            }
            
        except Exception as e:
            logger.error(f"WACC calculation error: {e}")
            return {"error": str(e)}

    # ========== ENHANCED FINANCIAL ANALYSIS METHODS ==========

    @staticmethod
    def calculate_revenue_growth(revenue_series: List[float]) -> Dict[str, Any]:
        """Calculate historical revenue growth rates with full audit trail"""
        try:
            revenue = np.array(revenue_series)
            if len(revenue) < 2:
                return {"error": "Need at least 2 years of revenue data"}

            growth_rates = (revenue[1:] / revenue[:-1]) - 1

            return {
                "yoy_growth_rates": growth_rates.tolist(),
                "cagr": (revenue[-1] / revenue[0]) ** (1/(len(revenue)-1)) - 1,
                "average_growth": np.mean(growth_rates),
                "std_dev": np.std(growth_rates),
                "min_growth": np.min(growth_rates),
                "max_growth": np.max(growth_rates),
                "calculation_steps": {
                    "formula": "CAGR = (Ending Value / Beginning Value)^(1/periods) - 1",
                    "inputs": {"revenue": revenue_series},
                    "intermediate": growth_rates.tolist()
                }
            }
        except Exception as e:
            logger.error(f"Revenue growth calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def normalize_ebitda(
        reported_ebitda: float,
        adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Normalize EBITDA with documented adjustments and audit trail

        Args:
            reported_ebitda: Reported EBITDA from financials
            adjustments: Dict of adjustment categories and amounts
        """
        try:
            total_adjustments = sum(adjustments.values())
            normalized_ebitda = reported_ebitda + total_adjustments

            return {
                "reported_ebitda": reported_ebitda,
                "adjustments": adjustments,
                "total_adjustments": total_adjustments,
                "normalized_ebitda": normalized_ebitda,
                "adjustment_percentage": (total_adjustments / reported_ebitda) * 100 if reported_ebitda != 0 else 0,
                "audit_trail": {
                    "formula": "Normalized EBITDA = Reported EBITDA + Sum(Adjustments)",
                    "each_adjustment": [
                        f"{k}: ${v:,.0f}" for k, v in adjustments.items()
                    ]
                }
            }
        except Exception as e:
            logger.error(f"EBITDA normalization error: {e}")
            return {"error": str(e)}

    @staticmethod
    def calculate_working_capital(
        accounts_receivable: float,
        inventory: float,
        accounts_payable: float,
        revenue: float,
        cost_of_goods_sold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate working capital metrics with Days Sales Outstanding, etc."""
        try:
            # Use 70% of revenue as COGS if not provided
            cogs = cost_of_goods_sold or (revenue * 0.7)

            dso = (accounts_receivable / revenue) * 365 if revenue > 0 else 0
            dio = (inventory / cogs) * 365 if cogs > 0 else 0
            dpo = (accounts_payable / cogs) * 365 if cogs > 0 else 0
            cash_conversion_cycle = dso + dio - dpo

            return {
                "working_capital": accounts_receivable + inventory - accounts_payable,
                "dso": dso,
                "dio": dio,
                "dpo": dpo,
                "cash_conversion_cycle": cash_conversion_cycle,
                "working_capital_as_pct_revenue": (
                    (accounts_receivable + inventory - accounts_payable) / revenue * 100
                ) if revenue > 0 else 0,
                "calculation_details": {
                    "dso_formula": "DSO = (AR / Revenue) * 365",
                    "dio_formula": "DIO = (Inventory / COGS) * 365",
                    "dpo_formula": "DPO = (AP / COGS) * 365",
                    "inputs": {
                        "ar": accounts_receivable,
                        "inventory": inventory,
                        "ap": accounts_payable,
                        "revenue": revenue,
                        "cogs": cogs
                    }
                }
            }
        except Exception as e:
            logger.error(f"Working capital calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def calculate_dcf_value(
        free_cash_flows: List[float],
        terminal_value: float,
        wacc: float
    ) -> Dict[str, Any]:
        """Calculate DCF enterprise value with detailed breakdown"""
        try:
            periods = len(free_cash_flows)
            discount_factors = [(1 + wacc) ** i for i in range(1, periods + 1)]

            pv_fcfs = [
                fcf / df for fcf, df in zip(free_cash_flows, discount_factors)
            ]

            pv_terminal = terminal_value / ((1 + wacc) ** periods)
            enterprise_value = sum(pv_fcfs) + pv_terminal

            return {
                "enterprise_value": enterprise_value,
                "pv_forecast_period": sum(pv_fcfs),
                "pv_terminal_value": pv_terminal,
                "terminal_value_percentage": (pv_terminal / enterprise_value) * 100 if enterprise_value > 0 else 0,
                "calculation_breakdown": {
                    "free_cash_flows": free_cash_flows,
                    "discount_factors": discount_factors,
                    "present_values": pv_fcfs,
                    "wacc": wacc,
                    "formula": "EV = Σ(FCF / (1+WACC)^t) + TV / (1+WACC)^n"
                }
            }
        except Exception as e:
            logger.error(f"DCF value calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def calculate_wacc_enhanced(
        risk_free_rate: float,
        beta: float,
        market_risk_premium: float,
        cost_of_debt: float,
        tax_rate: float,
        debt_to_equity: float
    ) -> Dict[str, Any]:
        """Calculate WACC using CAPM for cost of equity"""
        try:
            cost_of_equity = risk_free_rate + (beta * market_risk_premium)
            after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)

            # Calculate weights
            total_capital = 1 + debt_to_equity
            equity_weight = 1 / total_capital
            debt_weight = debt_to_equity / total_capital

            wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)

            return {
                "wacc": wacc,
                "cost_of_equity": cost_of_equity,
                "cost_of_debt": cost_of_debt,
                "after_tax_cost_of_debt": after_tax_cost_of_debt,
                "equity_weight": equity_weight,
                "debt_weight": debt_weight,
                "calculation_steps": {
                    "cost_of_equity_formula": "Ke = Rf + β(Rm - Rf)",
                    "wacc_formula": "WACC = (E/V)*Ke + (D/V)*Kd*(1-T)",
                    "inputs": {
                        "risk_free_rate": risk_free_rate,
                        "beta": beta,
                        "market_risk_premium": market_risk_premium,
                        "debt_to_equity": debt_to_equity,
                        "tax_rate": tax_rate
                    }
                }
            }
        except Exception as e:
            logger.error(f"WACC calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def validate_three_statement_linkage(
        income_statement: Dict[str, Any],
        balance_sheet: Dict[str, Any],
        cash_flow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that three statements are properly linked"""
        try:
            checks = {}

            # Check 1: Net Income flows to Cash Flow Statement
            net_income = income_statement.get("net_income", 0)
            cf_net_income = cash_flow.get("net_income_starting", 0)
            checks["net_income_match"] = abs(net_income - cf_net_income) < 0.01

            # Check 2: Cash Flow Statement reconciles to Balance Sheet cash
            current_cash = balance_sheet.get("cash", 0)
            previous_cash = balance_sheet.get("previous_cash", 0)
            net_cash_change = cash_flow.get("net_change_cash", 0)
            checks["cash_balance_match"] = abs(current_cash - (previous_cash + net_cash_change)) < 0.01

            # Check 3: Balance Sheet balances
            total_assets = balance_sheet.get("total_assets", 0)
            total_liabilities = balance_sheet.get("total_liabilities", 0)
            equity = balance_sheet.get("equity", 0)
            checks["balance_sheet_balanced"] = abs(total_assets - (total_liabilities + equity)) < 0.01

            # Check 4: Retained Earnings roll-forward
            retained_earnings = balance_sheet.get("retained_earnings", 0)
            prev_retained_earnings = balance_sheet.get("previous_retained_earnings", 0)
            dividends = income_statement.get("dividends", 0)
            expected_re = prev_retained_earnings + net_income - dividends
            checks["retained_earnings_match"] = abs(retained_earnings - expected_re) < 0.01

            return {
                "all_checks_passed": all(checks.values()),
                "individual_checks": checks,
                "errors": [k for k, v in checks.items() if not v],
                "validation_summary": f"{sum(checks.values())}/{len(checks)} checks passed"
            }
        except Exception as e:
            logger.error(f"Three statement validation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def check_margin_reasonableness(
        gross_margin: float,
        ebitda_margin: float,
        net_margin: float,
        industry_benchmarks: Optional[Dict[str, tuple]] = None
    ) -> Dict[str, Any]:
        """Check if margins are within reasonable ranges"""
        try:
            issues = []
            industry_benchmarks = industry_benchmarks or {}

            # Basic logic checks
            if ebitda_margin > gross_margin:
                issues.append("EBITDA margin cannot exceed gross margin")

            if net_margin > ebitda_margin:
                issues.append("Net margin cannot exceed EBITDA margin")

            # Industry benchmark checks
            for margin_type, (min_val, max_val) in industry_benchmarks.items():
                actual_value = {"gross": gross_margin, "ebitda": ebitda_margin, "net": net_margin}.get(margin_type.lower())
                if actual_value is not None and not (min_val <= actual_value <= max_val):
                    issues.append(
                        f"{margin_type.title()} margin {actual_value:.1%} outside industry range "
                        f"{min_val:.1%}-{max_val:.1%}"
                    )

            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "margins_checked": {
                    "gross_margin": gross_margin,
                    "ebitda_margin": ebitda_margin,
                    "net_margin": net_margin
                },
                "recommendation": "Review margin calculations" if issues else "Margins appear reasonable"
            }
        except Exception as e:
            logger.error(f"Margin reasonableness check error: {e}")
            return {"error": str(e)}

    @staticmethod
    def check_growth_reasonableness(
        revenue_growth: float,
        market_growth: float,
        historical_growth: float,
        peer_growth: Optional[float] = None
    ) -> Dict[str, Any]:
        """Validate revenue growth assumptions"""
        try:
            issues = []

            # Check if growth is wildly different from historical
            if abs(revenue_growth - historical_growth) > 0.15:
                issues.append(
                    f"Projected growth {revenue_growth:.1%} differs significantly "
                    f"from historical {historical_growth:.1%}"
                )

            # Check vs market growth
            if revenue_growth > market_growth * 2:
                issues.append(
                    f"Projected growth {revenue_growth:.1%} implies aggressive "
                    f"market share gains (market growing at {market_growth:.1%})"
                )

            # Check vs peer growth
            if peer_growth and abs(revenue_growth - peer_growth) > 0.10:
                issues.append(
                    f"Projected growth {revenue_growth:.1%} differs from peer average {peer_growth:.1%}"
                )

            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "growth_metrics": {
                    "projected": revenue_growth,
                    "historical": historical_growth,
                    "market": market_growth,
                    "peer": peer_growth
                },
                "recommendation": "Review growth assumptions" if issues else "Growth assumptions appear reasonable"
            }
        except Exception as e:
            logger.error(f"Growth reasonableness check error: {e}")
            return {"error": str(e)}

    # ========== STATISTICAL ANALYSIS METHODS ==========

    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, Any]:
        """
        Calculate statistical measures for a list of values
        Used by agents for consistent statistical analysis
        """
        try:
            if not values or len(values) == 0:
                return {"error": "No values provided"}

            return {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std_dev": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "count": len(values),
                "sum": float(np.sum(values)),
                "calculation_method": "numpy statistical functions",
                "formula": "Standard statistical measures"
            }
        except Exception as e:
            logger.error(f"Statistical calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def calculate_volatility(values: List[float]) -> Dict[str, Any]:
        """Calculate volatility (coefficient of variation)"""
        try:
            if not values or len(values) == 0:
                return {"error": "No values provided"}

            mean_val = np.mean(values)
            std_val = np.std(values)
            volatility = std_val / mean_val if mean_val != 0 else 0

            assessment = 'Low' if volatility < 0.2 else 'Moderate' if volatility < 0.5 else 'High'

            return {
                "volatility": float(volatility),
                "std_dev": float(std_val),
                "mean": float(mean_val),
                "assessment": assessment,
                "formula": "Volatility = Std Dev / Mean"
            }
        except Exception as e:
            logger.error(f"Volatility calculation error: {e}")
            return {"error": str(e)}

    # ========== RATIO ANALYSIS METHODS ==========

    @staticmethod
    def calculate_financial_ratios(
        current_assets: float,
        current_liabilities: float,
        inventory: float,
        total_assets: float,
        total_liabilities: float,
        equity: float
    ) -> Dict[str, Any]:
        """Calculate standard financial ratios"""
        try:
            return {
                "current_ratio": current_assets / current_liabilities if current_liabilities > 0 else 0,
                "quick_ratio": (current_assets - inventory) / current_liabilities if current_liabilities > 0 else 0,
                "debt_to_assets": total_liabilities / total_assets if total_assets > 0 else 0,
                "debt_to_equity": total_liabilities / equity if equity > 0 else 0,
                "equity_ratio": equity / total_assets if total_assets > 0 else 0,
                "calculation_formulas": {
                    "current_ratio": "Current Assets / Current Liabilities",
                    "quick_ratio": "(Current Assets - Inventory) / Current Liabilities",
                    "debt_to_equity": "Total Liabilities / Equity"
                }
            }
        except Exception as e:
            logger.error(f"Ratio calculation error: {e}")
            return {"error": str(e)}

    # ========== GROWTH PROJECTION METHODS ==========

    @staticmethod
    def project_growth(
        base_value: float,
        growth_rate: float,
        periods: int,
        growth_type: str = 'compound'
    ) -> Dict[str, Any]:
        """Project future values with growth"""
        try:
            projections = []
            for year in range(1, periods + 1):
                if growth_type == 'compound':
                    value = base_value * ((1 + growth_rate) ** year)
                else:  # linear
                    value = base_value * (1 + (growth_rate * year))
                projections.append({
                    'year': year,
                    'value': value,
                    'growth_from_base': value - base_value
                })

            return {
                'projections': projections,
                'growth_rate': growth_rate,
                'base_value': base_value,
                'periods': periods,
                'growth_type': growth_type,
                'final_value': projections[-1]['value'] if projections else base_value,
                'formula': 'Compound: Value = Base * (1 + r)^t' if growth_type == 'compound' else 'Linear: Value = Base * (1 + r*t)'
            }
        except Exception as e:
            logger.error(f"Growth projection error: {e}")
            return {"error": str(e)}

    # ========== EFFICIENCY SCORING METHODS ==========

    @staticmethod
    def calculate_efficiency_score(
        actual_value: float,
        benchmark_value: float,
        score_type: str = 'lower_is_better'
    ) -> Dict[str, Any]:
        """
        Calculate efficiency score (0-100)
        
        Args:
            actual_value: The actual measured value
            benchmark_value: The benchmark or target value
            score_type: 'lower_is_better' or 'higher_is_better'
        """
        try:
            if score_type == 'lower_is_better':
                # Lower actual vs benchmark = higher score
                if actual_value <= benchmark_value:
                    score = 100
                else:
                    score = max(0, 100 - ((actual_value - benchmark_value) / benchmark_value * 100))
            else:  # higher_is_better
                if actual_value >= benchmark_value:
                    score = 100
                else:
                    score = (actual_value / benchmark_value * 100) if benchmark_value > 0 else 0

            return {
                'score': round(score, 1),
                'actual_value': actual_value,
                'benchmark_value': benchmark_value,
                'score_type': score_type,
                'interpretation': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair' if score >= 40 else 'Poor'
            }
        except Exception as e:
            logger.error(f"Efficiency score calculation error: {e}")
            return {"error": str(e)}

    # ========== TAX CALCULATION METHODS ==========

    @staticmethod
    def calculate_tax_expense(
        taxable_income: float,
        tax_rate: float,
        adjustments: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate tax expense with adjustments"""
        try:
            adjustments = adjustments or {}
            adjusted_income = taxable_income

            adjustment_details = []
            for adjustment_name, adjustment_value in adjustments.items():
                adjusted_income += adjustment_value
                adjustment_details.append({
                    'name': adjustment_name,
                    'amount': adjustment_value
                })

            tax_expense = adjusted_income * tax_rate

            return {
                'tax_expense': tax_expense,
                'effective_tax_rate': tax_rate,
                'taxable_income': taxable_income,
                'adjusted_income': adjusted_income,
                'adjustments': adjustment_details,
                'total_adjustments': sum(adjustments.values()),
                'calculation': f'Tax = Adjusted Income * {tax_rate:.1%}',
                'formula': 'Tax Expense = (Taxable Income + Adjustments) * Tax Rate'
            }
        except Exception as e:
            logger.error(f"Tax calculation error: {e}")
            return {"error": str(e)}

    # ========== INTENSITY & PERCENTAGE CALCULATIONS ==========

    @staticmethod
    def calculate_percentage_of_revenue(
        amount: float,
        revenue: float
    ) -> Dict[str, Any]:
        """Calculate amount as percentage of revenue"""
        try:
            percentage = (amount / revenue * 100) if revenue > 0 else 0

            return {
                'percentage': round(percentage, 2),
                'amount': amount,
                'revenue': revenue,
                'formula': '(Amount / Revenue) * 100'
            }
        except Exception as e:
            logger.error(f"Percentage calculation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def classify_intensity(
        percentage: float,
        low_threshold: float = 7.0,
        high_threshold: float = 15.0
    ) -> Dict[str, Any]:
        """Classify intensity based on percentage"""
        try:
            if percentage > high_threshold:
                classification = 'High'
            elif percentage > low_threshold:
                classification = 'Medium'
            else:
                classification = 'Low'

            return {
                'classification': classification,
                'percentage': percentage,
                'low_threshold': low_threshold,
                'high_threshold': high_threshold
            }
        except Exception as e:
            logger.error(f"Intensity classification error: {e}")
            return {"error": str(e)}

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available financial calculation tools for LLM function calling

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "calculate_dcf_standard",
                "description": "Calculate standard DCF valuation using FCFF approach",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "free_cash_flows": {"type": "array", "items": {"type": "number"}},
                        "wacc": {"type": "number"},
                        "terminal_growth_rate": {"type": "number"},
                        "shares_outstanding": {"type": "number"}
                    },
                    "required": ["free_cash_flows", "wacc", "terminal_growth_rate"]
                }
            },
            {
                "name": "calculate_dcf_sensitivity",
                "description": "Calculate DCF with sensitivity analysis on WACC and terminal growth",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "free_cash_flows": {"type": "array"},
                        "base_wacc": {"type": "number"},
                        "base_terminal_growth": {"type": "number"}
                    },
                    "required": ["free_cash_flows", "base_wacc", "base_terminal_growth"]
                }
            },
            {
                "name": "calculate_dcf_scenarios",
                "description": "Calculate DCF with multiple scenarios (Bull/Base/Bear)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bull_fcf": {"type": "array"},
                        "base_fcf": {"type": "array"},
                        "bear_fcf": {"type": "array"},
                        "wacc_bull": {"type": "number"},
                        "wacc_base": {"type": "number"},
                        "wacc_bear": {"type": "number"}
                    },
                    "required": ["bull_fcf", "base_fcf", "bear_fcf", "wacc_bull", "wacc_base", "wacc_bear"]
                }
            },
            {
                "name": "calculate_lbo_returns",
                "description": "Calculate LBO returns including IRR and MOIC",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "purchase_price": {"type": "number"},
                        "entry_multiple": {"type": "number"},
                        "exit_multiple": {"type": "number"},
                        "holding_period_years": {"type": "integer"},
                        "debt_financing_pct": {"type": "number"},
                        "interest_rate": {"type": "number"},
                        "annual_fcf": {"type": "array"}
                    },
                    "required": ["purchase_price", "entry_multiple", "exit_multiple", "holding_period_years"]
                }
            },
            {
                "name": "calculate_synergies",
                "description": "Calculate NPV of revenue and cost synergies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "revenue_synergies": {"type": "number"},
                        "cost_synergies": {"type": "number"},
                        "synergy_realization_years": {"type": "integer"},
                        "tax_rate": {"type": "number"},
                        "wacc": {"type": "number"}
                    },
                    "required": ["revenue_synergies", "cost_synergies", "synergy_realization_years", "tax_rate", "wacc"]
                }
            },
            {
                "name": "calculate_wacc",
                "description": "Calculate Weighted Average Cost of Capital",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cost_of_equity": {"type": "number"},
                        "cost_of_debt": {"type": "number"},
                        "tax_rate": {"type": "number"},
                        "market_value_equity": {"type": "number"},
                        "market_value_debt": {"type": "number"}
                    },
                    "required": ["cost_of_equity", "cost_of_debt", "tax_rate", "market_value_equity", "market_value_debt"]
                }
            },
            {
                "name": "calculate_revenue_growth",
                "description": "Calculate historical revenue growth rates with CAGR and audit trail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "revenue_series": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["revenue_series"]
                }
            },
            {
                "name": "normalize_ebitda",
                "description": "Normalize EBITDA with documented adjustments and audit trail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reported_ebitda": {"type": "number"},
                        "adjustments": {"type": "object"}
                    },
                    "required": ["reported_ebitda", "adjustments"]
                }
            },
            {
                "name": "calculate_working_capital",
                "description": "Calculate working capital metrics including DSO, DIO, DPO, and cash conversion cycle",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "accounts_receivable": {"type": "number"},
                        "inventory": {"type": "number"},
                        "accounts_payable": {"type": "number"},
                        "revenue": {"type": "number"},
                        "cost_of_goods_sold": {"type": "number"}
                    },
                    "required": ["accounts_receivable", "inventory", "accounts_payable", "revenue"]
                }
            },
            {
                "name": "calculate_dcf_value",
                "description": "Calculate DCF enterprise value with detailed breakdown",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "free_cash_flows": {"type": "array", "items": {"type": "number"}},
                        "terminal_value": {"type": "number"},
                        "wacc": {"type": "number"}
                    },
                    "required": ["free_cash_flows", "terminal_value", "wacc"]
                }
            },
            {
                "name": "calculate_wacc_enhanced",
                "description": "Calculate WACC using CAPM for cost of equity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "risk_free_rate": {"type": "number"},
                        "beta": {"type": "number"},
                        "market_risk_premium": {"type": "number"},
                        "cost_of_debt": {"type": "number"},
                        "tax_rate": {"type": "number"},
                        "debt_to_equity": {"type": "number"}
                    },
                    "required": ["risk_free_rate", "beta", "market_risk_premium", "cost_of_debt", "tax_rate", "debt_to_equity"]
                }
            },
            {
                "name": "validate_three_statement_linkage",
                "description": "Validate that income statement, balance sheet, and cash flow are properly linked",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "income_statement": {"type": "object"},
                        "balance_sheet": {"type": "object"},
                        "cash_flow": {"type": "object"}
                    },
                    "required": ["income_statement", "balance_sheet", "cash_flow"]
                }
            },
            {
                "name": "check_margin_reasonableness",
                "description": "Check if profit margins are within reasonable ranges and industry benchmarks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gross_margin": {"type": "number"},
                        "ebitda_margin": {"type": "number"},
                        "net_margin": {"type": "number"},
                        "industry_benchmarks": {"type": "object"}
                    },
                    "required": ["gross_margin", "ebitda_margin", "net_margin"]
                }
            },
            {
                "name": "check_growth_reasonableness",
                "description": "Validate revenue growth assumptions against historical, market, and peer data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "revenue_growth": {"type": "number"},
                        "market_growth": {"type": "number"},
                        "historical_growth": {"type": "number"},
                        "peer_growth": {"type": "number"}
                    },
                    "required": ["revenue_growth", "market_growth", "historical_growth"]
                }
            }
        ]
