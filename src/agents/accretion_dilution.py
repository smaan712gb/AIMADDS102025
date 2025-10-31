"""
Accretion/Dilution Analysis Agent

This agent calculates the impact of an M&A transaction on the acquirer's EPS.
This is THE most critical analysis for acquirer-side M&A decisions.

Key Outputs:
- Standalone EPS (acquirer & target)
- Pro forma combined EPS
- Accretion/dilution $ and % impact
- Sensitivity analysis (price, financing, synergies)
- Breakeven synergy analysis
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState

class AccretionDilutionAgent(BaseAgent):
    """
    Analyzes accretion/dilution impact of M&A transaction on acquirer EPS
    
    This is the #1 question from boards and management:
    "Is this deal accretive or dilutive to our earnings?"
    """
    
    def __init__(self):
        """Initialize the accretion/dilution agent"""
        super().__init__("accretion_dilution")
    
    def log_action(self, message: str, level: str = "info"):
        """Log actions"""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run method required by BaseAgent - calls analyze with state data
        
        Args:
            state: DiligenceState containing all analysis data
            
        Returns:
            Dict with data, errors, warnings, recommendations (BaseAgent format)
        """
        try:
            acquirer_data = state.get('acquirer_data', {})
            target_data = state.get('financial_data', {})
            deal_terms = state.get('deal_terms', {})
            valuation_data = state.get('valuation_models', {})
            
            # Call the analyze method
            result = await self.analyze(acquirer_data, target_data, deal_terms, valuation_data)
            
            # Return in BaseAgent format
            return {
                "data": result,
                "errors": [],
                "warnings": [],
                "recommendations": [
                    "Review accretion/dilution analysis with board",
                    "Validate synergy assumptions",
                    "Consider sensitivity scenarios for financing structure",
                    "Assess impact on credit metrics and leverage ratios"
                ]
            }
        except Exception as e:
            logger.error(f"Accretion/dilution analysis failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
        
    async def analyze(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        deal_terms: Dict[str, Any],
        valuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive accretion/dilution analysis
        
        Args:
            acquirer_data: Financial data for acquiring company
            target_data: Financial data for target company  
            deal_terms: Deal structure (cash/stock mix, financing)
            valuation_data: Target valuation from DCF/comps
            
        Returns:
            Complete accretion/dilution analysis including:
            - Standalone metrics
            - Pro forma metrics
            - Accretion/dilution impact
            - Sensitivity analysis
            - Breakeven analysis
        """
        self.log_action("Starting accretion/dilution analysis")
        
        try:
            # 1. Extract standalone metrics
            acquirer_standalone = self._calculate_standalone_metrics(
                acquirer_data, 
                "acquirer"
            )
            target_standalone = self._calculate_standalone_metrics(
                target_data,
                "target"
            )
            
            # 2. Calculate deal financing impact
            financing_impact = self._calculate_financing_impact(
                deal_terms,
                valuation_data,
                acquirer_data
            )
            
            # 3. Calculate pro forma combined metrics
            pro_forma = self._calculate_pro_forma_metrics(
                acquirer_standalone,
                target_standalone,
                financing_impact,
                deal_terms
            )
            
            # 4. Calculate accretion/dilution
            accretion_dilution = self._calculate_accretion_dilution(
                acquirer_standalone,
                pro_forma,
                deal_terms
            )
            
            # 5. Sensitivity analysis
            sensitivity = self._run_sensitivity_analysis(
                acquirer_standalone,
                target_standalone,
                deal_terms,
                valuation_data
            )
            
            # 6. Breakeven analysis
            breakeven = self._calculate_breakeven_synergies(
                acquirer_standalone,
                target_standalone,
                financing_impact,
                deal_terms
            )
            
            # 7. Multi-year forecast
            multiyear_impact = self._forecast_multiyear_impact(
                acquirer_data,
                target_data,
                deal_terms,
                accretion_dilution
            )
            
            result = {
                "analysis_date": datetime.now().isoformat(),
                "acquirer_standalone": acquirer_standalone,
                "target_standalone": target_standalone,
                "financing_impact": financing_impact,
                "pro_forma_combined": pro_forma,
                "accretion_dilution": accretion_dilution,
                "sensitivity_analysis": sensitivity,
                "breakeven_analysis": breakeven,
                "multiyear_forecast": multiyear_impact,
                "deal_recommendation": self._generate_recommendation(accretion_dilution),
                "key_assumptions": self._document_key_assumptions(deal_terms),
                "board_summary": self._create_board_summary(accretion_dilution, breakeven)
            }
            
            self.log_action(
                f"Accretion/dilution analysis complete: "
                f"{accretion_dilution['eps_impact_percent']:+.1f}% impact"
            )
            
            return result
            
        except Exception as e:
            self.log_action(f"Error in accretion/dilution analysis: {str(e)}", level="error")
            raise
    
    def _calculate_standalone_metrics(
        self,
        company_data: Dict[str, Any],
        company_type: str
    ) -> Dict[str, Any]:
        """Calculate standalone financial metrics for one company"""
        
        # Extract latest financial data
        income_statements = company_data.get('income_statement', [])
        balance_sheets = company_data.get('balance_sheet', [])
        
        if not income_statements or not balance_sheets:
            self.log_action(f"Missing financial data for {company_type}", level="warning")
            return {}
        
        latest_income = income_statements[0]
        latest_balance = balance_sheets[0]
        
        # Core earnings metrics
        net_income = latest_income.get('netIncome', 0)
        shares_outstanding = latest_balance.get('commonStock', 0)
        
        # Handle shares outstanding (may be in dollars, need to convert)
        # Try to get actual share count from income statement
        if 'weightedAverageShsOut' in latest_income:
            shares_outstanding = latest_income['weightedAverageShsOut']
        elif 'weightedAverageShsOutDil' in latest_income:
            shares_outstanding = latest_income['weightedAverageShsOutDil']
        
        # Calculate EPS
        eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
        
        # Tax metrics
        income_before_tax = latest_income.get('incomeBeforeTax', net_income)
        tax_rate = 0.21  # Default federal rate
        if income_before_tax > 0 and net_income > 0:
            tax_rate = 1 - (net_income / income_before_tax)
        
        return {
            "company_type": company_type,
            "net_income": net_income,
            "shares_outstanding": shares_outstanding,
            "eps": eps,
            "tax_rate": tax_rate,
            "revenue": latest_income.get('revenue', 0),
            "ebitda": latest_income.get('ebitda', 0),
            "operating_income": latest_income.get('operatingIncome', 0),
            "interest_expense": latest_income.get('interestExpense', 0),
            "date": latest_income.get('date', 'Latest')
        }
    
    def _calculate_financing_impact(
        self,
        deal_terms: Dict[str, Any],
        valuation_data: Dict[str, Any],
        acquirer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate impact of deal financing on earnings"""
        
        # Extract deal structure
        total_consideration = deal_terms.get('purchase_price', 0)
        if total_consideration == 0:
            # Use valuation from DCF
            dcf_data = valuation_data.get('dcf_advanced', {})
            dcf_analysis = dcf_data.get('dcf_analysis', {})
            base_case = dcf_analysis.get('base', {})
            total_consideration = base_case.get('enterprise_value', 0)
        
        cash_percentage = deal_terms.get('cash_percentage', 0.5)  # Default 50/50
        stock_percentage = 1 - cash_percentage
        
        cash_consideration = total_consideration * cash_percentage
        stock_consideration = total_consideration * stock_percentage
        
        # Debt financing for cash portion
        existing_cash = deal_terms.get('acquirer_cash_available', 0)
        debt_needed = max(0, cash_consideration - existing_cash)
        
        # Interest expense on new debt
        debt_interest_rate = deal_terms.get('debt_interest_rate', 0.05)  # Default 5%
        annual_interest_expense = debt_needed * debt_interest_rate
        
        # Tax benefit of interest
        tax_rate = deal_terms.get('tax_rate', 0.21)
        after_tax_interest = annual_interest_expense * (1 - tax_rate)
        
        # New shares issued for stock consideration
        acquirer_stock_price = deal_terms.get('acquirer_stock_price', 100)
        new_shares_issued = stock_consideration / acquirer_stock_price if acquirer_stock_price > 0 else 0
        
        return {
            "total_consideration": total_consideration,
            "cash_consideration": cash_consideration,
            "stock_consideration": stock_consideration,
            "cash_percentage": cash_percentage,
            "stock_percentage": stock_percentage,
            "debt_needed": debt_needed,
            "debt_interest_rate": debt_interest_rate,
            "annual_interest_expense": annual_interest_expense,
            "after_tax_interest_expense": after_tax_interest,
            "new_shares_issued": new_shares_issued,
            "acquirer_stock_price": acquirer_stock_price
        }
    
    def _calculate_pro_forma_metrics(
        self,
        acquirer_standalone: Dict[str, Any],
        target_standalone: Dict[str, Any],
        financing_impact: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate pro forma combined company metrics"""
        
        # Combined earnings before financing
        acquirer_ni = acquirer_standalone.get('net_income', 0)
        target_ni = target_standalone.get('net_income', 0)
        combined_ni_pre_financing = acquirer_ni + target_ni
        
        # Adjust for synergies (if provided)
        synergies_year1 = deal_terms.get('synergies_year1', 0)
        tax_rate = acquirer_standalone.get('tax_rate', 0.21)
        after_tax_synergies = synergies_year1 * (1 - tax_rate)
        
        # Subtract financing costs
        financing_cost = financing_impact.get('after_tax_interest_expense', 0)
        
        # Pro forma net income
        pro_forma_ni = combined_ni_pre_financing + after_tax_synergies - financing_cost
        
        # Pro forma shares outstanding
        acquirer_shares = acquirer_standalone.get('shares_outstanding', 0)
        new_shares = financing_impact.get('new_shares_issued', 0)
        pro_forma_shares = acquirer_shares + new_shares
        
        # Pro forma EPS
        pro_forma_eps = pro_forma_ni / pro_forma_shares if pro_forma_shares > 0 else 0
        
        return {
            "combined_net_income_pre_financing": combined_ni_pre_financing,
            "after_tax_synergies": after_tax_synergies,
            "financing_cost": financing_cost,
            "pro_forma_net_income": pro_forma_ni,
            "acquirer_shares_outstanding": acquirer_shares,
            "new_shares_issued": new_shares,
            "pro_forma_shares_outstanding": pro_forma_shares,
            "pro_forma_eps": pro_forma_eps,
            "ownership_existing_shareholders_pct": (acquirer_shares / pro_forma_shares * 100) if pro_forma_shares > 0 else 100,
            "ownership_new_shareholders_pct": (new_shares / pro_forma_shares * 100) if pro_forma_shares > 0 else 0
        }
    
    def _calculate_accretion_dilution(
        self,
        acquirer_standalone: Dict[str, Any],
        pro_forma: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate accretion/dilution impact"""
        
        acquirer_eps = acquirer_standalone.get('eps', 0)
        pro_forma_eps = pro_forma.get('pro_forma_eps', 0)
        
        # Calculate impact
        eps_impact_dollar = pro_forma_eps - acquirer_eps
        eps_impact_percent = (eps_impact_dollar / acquirer_eps * 100) if acquirer_eps > 0 else 0
        
        # Determine if accretive or dilutive
        is_accretive = eps_impact_dollar > 0
        impact_type = "ACCRETIVE" if is_accretive else "DILUTIVE" if eps_impact_dollar < 0 else "NEUTRAL"
        
        return {
            "acquirer_standalone_eps": acquirer_eps,
            "pro_forma_eps": pro_forma_eps,
            "eps_impact_dollar": eps_impact_dollar,
            "eps_impact_percent": eps_impact_percent,
            "is_accretive": is_accretive,
            "impact_type": impact_type,
            "impact_year": 1,  # First year impact
            "impact_summary": f"{impact_type}: {eps_impact_percent:+.1f}% ({eps_impact_dollar:+.2f})"
        }
    
    def _run_sensitivity_analysis(
        self,
        acquirer_standalone: Dict[str, Any],
        target_standalone: Dict[str, Any],
        deal_terms: Dict[str, Any],
        valuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run sensitivity analysis on key variables"""
        
        base_eps = acquirer_standalone.get('eps', 0)
        
        # Sensitivity to purchase price
        price_scenarios = []
        base_price = deal_terms.get('purchase_price', 0)
        if base_price == 0:
            dcf_data = valuation_data.get('dcf_advanced', {})
            base_price = dcf_data.get('dcf_analysis', {}).get('base', {}).get('enterprise_value', 0)
        
        for price_adj in [-0.10, -0.05, 0, 0.05, 0.10]:
            scenario_terms = deal_terms.copy()
            scenario_terms['purchase_price'] = base_price * (1 + price_adj)
            
            financing = self._calculate_financing_impact(scenario_terms, valuation_data, acquirer_standalone)
            pro_forma = self._calculate_pro_forma_metrics(acquirer_standalone, target_standalone, financing, scenario_terms)
            accretion = self._calculate_accretion_dilution(acquirer_standalone, pro_forma, scenario_terms)
            
            price_scenarios.append({
                "price_adjustment": price_adj,
                "purchase_price": scenario_terms['purchase_price'],
                "eps_impact_percent": accretion['eps_impact_percent']
            })
        
        # Sensitivity to synergies
        synergy_scenarios = []
        base_synergies = deal_terms.get('synergies_year1', 0)
        
        for synergy_adj in [0, 0.5, 1.0, 1.5, 2.0]:
            scenario_terms = deal_terms.copy()
            scenario_terms['synergies_year1'] = base_synergies * synergy_adj
            
            financing = self._calculate_financing_impact(scenario_terms, valuation_data, acquirer_standalone)
            pro_forma = self._calculate_pro_forma_metrics(acquirer_standalone, target_standalone, financing, scenario_terms)
            accretion = self._calculate_accretion_dilution(acquirer_standalone, pro_forma, scenario_terms)
            
            synergy_scenarios.append({
                "synergy_multiple": synergy_adj,
                "synergies_amount": scenario_terms['synergies_year1'],
                "eps_impact_percent": accretion['eps_impact_percent']
            })
        
        # Sensitivity to financing mix (cash vs stock)
        financing_scenarios = []
        for cash_pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
            scenario_terms = deal_terms.copy()
            scenario_terms['cash_percentage'] = cash_pct
            
            financing = self._calculate_financing_impact(scenario_terms, valuation_data, acquirer_standalone)
            pro_forma = self._calculate_pro_forma_metrics(acquirer_standalone, target_standalone, financing, scenario_terms)
            accretion = self._calculate_accretion_dilution(acquirer_standalone, pro_forma, scenario_terms)
            
            financing_scenarios.append({
                "cash_percentage": cash_pct,
                "stock_percentage": 1 - cash_pct,
                "eps_impact_percent": accretion['eps_impact_percent']
            })
        
        return {
            "price_sensitivity": price_scenarios,
            "synergy_sensitivity": synergy_scenarios,
            "financing_mix_sensitivity": financing_scenarios,
            "summary": "Sensitivity analysis shows EPS impact across multiple scenarios"
        }
    
    def _calculate_breakeven_synergies(
        self,
        acquirer_standalone: Dict[str, Any],
        target_standalone: Dict[str, Any],
        financing_impact: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate synergies needed for EPS neutrality"""
        
        acquirer_eps = acquirer_standalone.get('eps', 0)
        acquirer_shares = acquirer_standalone.get('shares_outstanding', 0)
        new_shares = financing_impact.get('new_shares_issued', 0)
        pro_forma_shares = acquirer_shares + new_shares
        
        # Target net income needed for EPS neutrality
        target_eps_neutral_ni = acquirer_eps * pro_forma_shares
        
        # Current combined NI (before synergies)
        acquirer_ni = acquirer_standalone.get('net_income', 0)
        target_ni = target_standalone.get('net_income', 0)
        financing_cost = financing_impact.get('after_tax_interest_expense', 0)
        current_combined_ni = acquirer_ni + target_ni - financing_cost
        
        # Breakeven synergies needed
        breakeven_synergies_pretax = max(0, target_eps_neutral_ni - current_combined_ni)
        
        # Convert to pre-tax
        tax_rate = acquirer_standalone.get('tax_rate', 0.21)
        breakeven_synergies_pretax_actual = breakeven_synergies_pretax / (1 - tax_rate)
        
        return {
            "breakeven_synergies_after_tax": breakeven_synergies_pretax,
            "breakeven_synergies_pretax": breakeven_synergies_pretax_actual,
            "current_synergies_assumed": deal_terms.get('synergies_year1', 0),
            "synergy_cushion": deal_terms.get('synergies_year1', 0) - breakeven_synergies_pretax_actual,
            "is_achievable": deal_terms.get('synergies_year1', 0) >= breakeven_synergies_pretax_actual,
            "summary": f"Deal requires ${breakeven_synergies_pretax_actual/1e6:.1f}M in synergies for EPS neutrality"
        }
    
    def _forecast_multiyear_impact(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        deal_terms: Dict[str, Any],
        year1_impact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forecast accretion/dilution over multiple years"""
        
        # Assume synergies ramp up over time
        synergy_ramp = {
            1: 0.5,  # 50% in Year 1
            2: 0.75, # 75% in Year 2
            3: 1.0,  # 100% in Year 3+
        }
        
        forecast = []
        for year in range(1, 6):
            ramp_factor = synergy_ramp.get(year, 1.0)
            
            # Adjust synergies for ramp
            year_terms = deal_terms.copy()
            base_synergies = deal_terms.get('synergies_year1', 0) / 0.5  # Assume Year 1 is 50% of full
            year_terms['synergies_year1'] = base_synergies * ramp_factor
            
            # Growth rates
            acquirer_growth = 0.05  # 5% annual growth assumption
            target_growth = 0.05
            
            # Simple forecast (would be more sophisticated in production)
            year_impact = {
                "year": year,
                "synergy_realization_pct": ramp_factor * 100,
                "estimated_eps_impact_percent": year1_impact['eps_impact_percent'] * ramp_factor,
                "notes": f"Year {year} assumes {ramp_factor*100:.0f}% synergy realization"
            }
            forecast.append(year_impact)
        
        return {
            "forecast_years": forecast,
            "summary": "Multi-year forecast shows improving accretion as synergies fully realized"
        }
    
    def _generate_recommendation(self, accretion_dilution: Dict[str, Any]) -> str:
        """Generate deal recommendation based on accretion/dilution"""
        
        impact_pct = accretion_dilution.get('eps_impact_percent', 0)
        impact_type = accretion_dilution.get('impact_type', 'NEUTRAL')
        
        if impact_type == "ACCRETIVE":
            if impact_pct > 5:
                return "STRONGLY RECOMMEND - Highly accretive transaction"
            elif impact_pct > 2:
                return "RECOMMEND - Accretive transaction with solid EPS uplift"
            else:
                return "NEUTRAL TO POSITIVE - Modestly accretive"
        elif impact_type == "DILUTIVE":
            if impact_pct < -5:
                return "CAUTION - Highly dilutive; requires exceptional strategic rationale"
            elif impact_pct < -2:
                return "PROCEED WITH CAUTION - Dilutive but may be justified by long-term synergies"
            else:
                return "ACCEPTABLE - Minor dilution, acceptable if synergies materialize"
        else:
            return "NEUTRAL - EPS neutral transaction"
    
    def _document_key_assumptions(self, deal_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Document all key assumptions used in analysis"""
        
        return {
            "purchase_price": deal_terms.get('purchase_price', 0),
            "cash_percentage": deal_terms.get('cash_percentage', 0.5),
            "stock_percentage": 1 - deal_terms.get('cash_percentage', 0.5),
            "debt_interest_rate": deal_terms.get('debt_interest_rate', 0.05),
            "tax_rate": deal_terms.get('tax_rate', 0.21),
            "year1_synergies": deal_terms.get('synergies_year1', 0),
            "acquirer_stock_price": deal_terms.get('acquirer_stock_price', 100),
            "synergy_realization_timeline": "50% Y1, 75% Y2, 100% Y3+",
            "growth_assumptions": "5% annual growth for both companies"
        }
    
    def _create_board_summary(
        self,
        accretion_dilution: Dict[str, Any],
        breakeven: Dict[str, Any]
    ) -> str:
        """Create executive summary for board presentation"""
        
        impact_type = accretion_dilution.get('impact_type', 'NEUTRAL')
        impact_pct = accretion_dilution.get('eps_impact_percent', 0)
        breakeven_synergies = breakeven.get('breakeven_synergies_pretax', 0)
        
        summary = f"""
BOARD SUMMARY - ACCRETION/DILUTION ANALYSIS

Impact: {impact_type} {impact_pct:+.1f}%

• Standalone Acquirer EPS: ${accretion_dilution.get('acquirer_standalone_eps', 0):.2f}
• Pro Forma Combined EPS: ${accretion_dilution.get('pro_forma_eps', 0):.2f}
• EPS Impact: ${accretion_dilution.get('eps_impact_dollar', 0):+.2f} ({impact_pct:+.1f}%)

Breakeven Analysis:
• Synergies required for EPS neutrality: ${breakeven_synergies/1e6:.1f}M
• Deal is {"ACHIEVABLE" if breakeven.get('is_achievable') else "CHALLENGING"} based on assumed synergies

Recommendation: {self._generate_recommendation(accretion_dilution)}
"""
        return summary.strip()


# Test utility
async def test_accretion_dilution_agent():
    """Test the accretion dilution agent with sample data"""
    
    agent = AccretionDilutionAgent()
    
    # Sample acquirer data
    acquirer_data = {
        'income_statement': [{
            'netIncome': 10000000000,  # $10B
            'weightedAverageShsOut': 1000000000,  # 1B shares
            'revenue': 50000000000,  # $50B
            'ebitda': 15000000000,  # $15B
            'incomeBeforeTax': 12000000000,
            'date': '2024-12-31'
        }],
        'balance_sheet': [{}]
    }
    
    # Sample target data
    target_data = {
        'income_statement': [{
            'netIncome': 2000000000,  # $2B
            'weightedAverageShsOut': 200000000,  # 200M shares
            'revenue': 10000000000,  # $10B
            'ebitda': 3000000000,  # $3B
            'incomeBeforeTax': 2400000000,
            'date': '2024-12-31'
        }],
        'balance_sheet': [{}]
    }
    
    # Sample deal terms
    deal_terms = {
        'purchase_price': 30000000000,  # $30B
        'cash_percentage': 0.5,  # 50% cash
        'debt_interest_rate': 0.05,  # 5%
        'tax_rate': 0.21,
        'acquirer_stock_price': 150,  # $150/share
        'synergies_year1': 1000000000,  # $1B synergies
        'acquirer_cash_available': 5000000000  # $5B cash
    }
    
    # Sample valuation data
    valuation_data = {
        'dcf_advanced': {
            'dcf_analysis': {
                'base': {
                    'enterprise_value': 30000000000
                }
            }
        }
    }
    
    result = await agent.analyze(
        acquirer_data,
        target_data,
        deal_terms,
        valuation_data
    )
    
    print("Accretion/Dilution Analysis Results:")
    print(f"Impact: {result['accretion_dilution']['impact_type']}")
    print(f"EPS Impact: {result['accretion_dilution']['eps_impact_percent']:+.1f}%")
    print(f"\nBoard Summary:\n{result['board_summary']}")
    
    return result


if __name__ == "__main__":
    # Run test
    import asyncio
    asyncio.run(test_accretion_dilution_agent())
