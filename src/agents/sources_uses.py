"""
Sources & Uses Generator

Generates comprehensive Sources & Uses of Funds table for M&A transactions.
This is CRITICAL for showing how the deal will be financed.

Key Outputs:
- Uses of Funds (equity price, debt refinancing, fees)
- Sources of Funds (cash, debt, equity)
- Pro forma capitalization
- Financing structure analysis
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState


class SourcesUsesGenerator(BaseAgent):
    """
    Generates Sources & Uses table for M&A transactions
    
    This answers the question: "How exactly will we pay for this deal?"
    """
    
    def __init__(self):
        super().__init__("sources_uses")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run method required by BaseAgent
        
        Args:
            state: DiligenceState containing all analysis data
            
        Returns:
            Dict with data, errors, warnings, recommendations
        """
        try:
            deal_terms = state.get('deal_terms', {})
            target_data = state.get('financial_data', {})
            acquirer_data = state.get('acquirer_data', {})
            deal_value = state.get('deal_value', 0)
            
            # Call the generate method
            result = self.generate(deal_terms, target_data, acquirer_data, deal_value)
            
            # Return in BaseAgent format
            return {
                "data": result,
                "errors": [],
                "warnings": [],
                "recommendations": [
                    "Review financing structure with capital markets team",
                    "Validate debt capacity with rating agencies",
                    "Assess impact on leverage ratios and credit metrics",
                    "Consider alternative financing structures"
                ]
            }
        except Exception as e:
            logger.error(f"Sources & Uses analysis failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
        
    def generate(
        self,
        deal_terms: Dict[str, Any],
        target_data: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        valuation: float
    ) -> Dict[str, Any]:
        """
        Generate complete Sources & Uses analysis
        
        Args:
            deal_terms: Deal structure and terms
            target_data: Target company financial data
            acquirer_data: Acquirer company financial data
            valuation: Purchase price (enterprise value)
            
        Returns:
            Complete Sources & Uses breakdown
        """
        logger.info("Generating Sources & Uses analysis")
        
        try:
            # 1. Calculate Uses of Funds
            uses = self._calculate_uses(deal_terms, target_data, valuation)
            
            # 2. Calculate Sources of Funds
            sources = self._calculate_sources(deal_terms, acquirer_data, uses['total_uses'])
            
            # 3. Pro Forma Capitalization
            pro_forma_cap = self._calculate_pro_forma_cap(
                acquirer_data,
                target_data,
                sources,
                deal_terms
            )
            
            # 4. Financing Structure Analysis
            financing_analysis = self._analyze_financing_structure(
                sources,
                acquirer_data,
                deal_terms
            )
            
            result = {
                "analysis_date": datetime.now().isoformat(),
                "uses_of_funds": uses,
                "sources_of_funds": sources,
                "pro_forma_capitalization": pro_forma_cap,
                "financing_analysis": financing_analysis,
                "balance_check": self._verify_balance(uses, sources),
                "summary": self._create_summary(uses, sources, pro_forma_cap)
            }
            
            logger.info(f"Sources & Uses generated: ${uses['total_uses']/1e9:.1f}B transaction")
            return result
            
        except Exception as e:
            logger.error(f"Error generating Sources & Uses: {str(e)}")
            raise
    
    def _calculate_uses(
        self,
        deal_terms: Dict[str, Any],
        target_data: Dict[str, Any],
        valuation: float
    ) -> Dict[str, Any]:
        """Calculate all uses of funds"""
        
        # 1. Equity Purchase Price
        equity_purchase_price = valuation
        
        # 2. Refinance Target Debt (if applicable)
        target_balance = target_data.get('balance_sheet', [{}])[0]
        target_debt = target_balance.get('totalDebt', 0)
        refinance_debt = deal_terms.get('refinance_target_debt', True)
        debt_to_refinance = target_debt if refinance_debt else 0
        
        # 3. Transaction Fees
        # Standard M&A advisory fees (1-2% of deal size)
        advisory_fee_pct = deal_terms.get('advisory_fee_pct', 0.015)  # 1.5% default
        advisory_fees = equity_purchase_price * advisory_fee_pct
        
        # Legal, accounting, other
        other_transaction_fees = equity_purchase_price * 0.005  # 0.5% default
        
        total_transaction_fees = advisory_fees + other_transaction_fees
        
        # 4. Financing Fees
        # Debt financing fees (typically 2-3% of new debt)
        financing_fee_pct = deal_terms.get('financing_fee_pct', 0.025)  # 2.5% default
        
        # Calculate total cash needed
        cash_needed = equity_purchase_price + debt_to_refinance + total_transaction_fees
        
        # Estimate financing fees (will adjust after calculating sources)
        estimated_new_debt = cash_needed * 0.5  # Rough estimate
        financing_fees = estimated_new_debt * financing_fee_pct
        
        # 5. Total Uses
        total_uses = equity_purchase_price + debt_to_refinance + total_transaction_fees + financing_fees
        
        return {
            "equity_purchase_price": equity_purchase_price,
            "equity_purchase_price_pct": (equity_purchase_price / total_uses * 100),
            "refinance_target_debt": debt_to_refinance,
            "refinance_target_debt_pct": (debt_to_refinance / total_uses * 100),
            "advisory_fees": advisory_fees,
            "other_transaction_fees": other_transaction_fees,
            "total_transaction_fees": total_transaction_fees,
            "transaction_fees_pct": (total_transaction_fees / total_uses * 100),
            "financing_fees": financing_fees,
            "financing_fees_pct": (financing_fees / total_uses * 100),
            "total_uses": total_uses,
            "breakdown": [
                {"item": "Equity Purchase Price", "amount": equity_purchase_price},
                {"item": "Refinance Target Debt", "amount": debt_to_refinance},
                {"item": "Transaction Fees", "amount": total_transaction_fees},
                {"item": "Financing Fees", "amount": financing_fees}
            ]
        }
    
    def _calculate_sources(
        self,
        deal_terms: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        total_uses: float
    ) -> Dict[str, Any]:
        """Calculate all sources of funds"""
        
        # 1. Acquirer Cash on Hand
        acquirer_balance = acquirer_data.get('balance_sheet', [{}])[0]
        total_cash = acquirer_balance.get('cashAndCashEquivalents', 0)
        
        # Use portion of cash (typically keep minimum cash buffer)
        cash_buffer_pct = deal_terms.get('cash_buffer_pct', 0.20)  # Keep 20% buffer
        available_cash = total_cash * (1 - cash_buffer_pct)
        
        cash_used = min(available_cash, deal_terms.get('cash_to_use', available_cash))
        
        # 2. New Debt Financing
        cash_stock_split = deal_terms.get('cash_percentage', 0.5)  # Default 50/50
        cash_consideration = total_uses * cash_stock_split
        
        # Debt needed = cash portion - available cash
        new_debt = max(0, cash_consideration - cash_used)
        
        # 3. New Equity Issuance (stock consideration)
        stock_consideration = total_uses * (1 - cash_stock_split)
        new_equity = stock_consideration
        
        # 4. Rollover Equity (if any target shareholders rolling over)
        rollover_equity = deal_terms.get('rollover_equity', 0)
        
        # Adjust if total doesn't match
        total_sources = cash_used + new_debt + new_equity + rollover_equity
        
        if total_sources != total_uses:
            # Adjust new debt to balance
            new_debt = total_uses - (cash_used + new_equity + rollover_equity)
        
        return {
            "acquirer_cash": cash_used,
            "acquirer_cash_pct": (cash_used / total_uses * 100),
            "new_debt_financing": new_debt,
            "new_debt_financing_pct": (new_debt / total_uses * 100),
            "new_equity_issuance": new_equity,
            "new_equity_issuance_pct": (new_equity / total_uses * 100),
            "rollover_equity": rollover_equity,
            "rollover_equity_pct": (rollover_equity / total_uses * 100) if rollover_equity > 0 else 0,
            "total_sources": total_uses,  # Must equal total uses
            "breakdown": [
                {"item": "Acquirer Cash", "amount": cash_used},
                {"item": "New Debt Financing", "amount": new_debt},
                {"item": "New Equity Issuance", "amount": new_equity},
                {"item": "Rollover Equity", "amount": rollover_equity}
            ]
        }
    
    def _calculate_pro_forma_cap(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        sources: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate pro forma capitalization table"""
        
        # Existing debt
        acquirer_balance = acquirer_data.get('balance_sheet', [{}])[0]
        acquirer_existing_debt = acquirer_balance.get('totalDebt', 0)
        
        target_balance = target_data.get('balance_sheet', [{}])[0]
        target_existing_debt = target_balance.get('totalDebt', 0)
        
        # New debt from transaction
        new_debt = sources.get('new_debt_financing', 0)
        
        # Pro forma total debt
        # (Acquirer debt + New debt, Target debt gets refinanced)
        pro_forma_debt = acquirer_existing_debt + new_debt
        
        # Equity value calculation
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        acquirer_shares = acquirer_income.get('weightedAverageShsOut', 0)
        acquirer_stock_price = deal_terms.get('acquirer_stock_price', 100)
        
        existing_equity_value = acquirer_shares * acquirer_stock_price
        new_equity_issued = sources.get('new_equity_issuance', 0)
        
        pro_forma_equity_value = existing_equity_value + new_equity_issued
        
        # Total capitalization
        pro_forma_total_cap = pro_forma_debt + pro_forma_equity_value
        
        # Leverage metrics
        pro_forma_ebitda = acquirer_income.get('ebitda', 0) + target_data.get('income_statement', [{}])[0].get('ebitda', 0)
        debt_to_ebitda = pro_forma_debt / pro_forma_ebitda if pro_forma_ebitda > 0 else 0
        debt_to_cap = pro_forma_debt / pro_forma_total_cap if pro_forma_total_cap > 0 else 0
        
        return {
            "existing_acquirer_debt": acquirer_existing_debt,
            "new_debt_financing": new_debt,
            "pro_forma_total_debt": pro_forma_debt,
            "existing_equity_value": existing_equity_value,
            "new_equity_issued": new_equity_issued,
            "pro_forma_equity_value": pro_forma_equity_value,
            "pro_forma_total_capitalization": pro_forma_total_cap,
            "debt_to_equity_ratio": pro_forma_debt / pro_forma_equity_value if pro_forma_equity_value > 0 else 0,
            "debt_to_total_cap_pct": debt_to_cap * 100,
            "equity_to_total_cap_pct": (1 - debt_to_cap) * 100,
            "pro_forma_debt_to_ebitda": debt_to_ebitda,
            "leverage_metrics": {
                "debt_ebitda": debt_to_ebitda,
                "debt_cap_pct": debt_to_cap * 100,
                "rating": self._assess_leverage(debt_to_ebitda, debt_to_cap)
            }
        }
    
    def _analyze_financing_structure(
        self,
        sources: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the financing structure"""
        
        total = sources.get('total_sources', 0)
        debt_pct = sources.get('new_debt_financing_pct', 0)
        equity_pct = sources.get('new_equity_issuance_pct', 0)
        
        # Assess structure
        if debt_pct > 70:
            structure_type = "HIGHLY LEVERAGED"
            risk_assessment = "HIGH - Significant debt burden"
        elif debt_pct > 50:
            structure_type = "MODERATELY LEVERAGED"
            risk_assessment = "MODERATE - Balanced structure"
        elif debt_pct > 30:
            structure_type = "CONSERVATIVE"
            risk_assessment = "LOW - Equity-heavy structure"
        else:
            structure_type = "ALL EQUITY"
            risk_assessment = "VERY LOW - Minimal leverage"
        
        return {
            "structure_type": structure_type,
            "debt_percentage": debt_pct,
            "equity_percentage": equity_pct,
            "risk_assessment": risk_assessment,
            "interest_coverage_estimate": self._estimate_interest_coverage(sources, acquirer_data, deal_terms),
            "recommendation": self._recommend_financing_structure(debt_pct, equity_pct)
        }
    
    def _assess_leverage(self, debt_to_ebitda: float, debt_to_cap: float) -> str:
        """Assess leverage level"""
        if debt_to_ebitda > 5 or debt_to_cap > 0.6:
            return "HIGH LEVERAGE - May face rating pressure"
        elif debt_to_ebitda > 3 or debt_to_cap > 0.4:
            return "MODERATE LEVERAGE - Within acceptable range"
        else:
            return "CONSERVATIVE LEVERAGE - Strong credit profile"
    
    def _estimate_interest_coverage(
        self,
        sources: Dict[str, Any],
        acquirer_data: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> float:
        """Estimate interest coverage ratio"""
        
        new_debt = sources.get('new_debt_financing', 0)
        interest_rate = deal_terms.get('debt_interest_rate', 0.05)
        annual_interest = new_debt * interest_rate
        
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        ebitda = acquirer_income.get('ebitda', 0)
        
        interest_coverage = ebitda / annual_interest if annual_interest > 0 else 999
        return interest_coverage
    
    def _recommend_financing_structure(self, debt_pct: float, equity_pct: float) -> str:
        """Recommend optimal financing structure"""
        if debt_pct > 70:
            return "CAUTION: Consider reducing leverage to maintain financial flexibility"
        elif debt_pct < 30:
            return "OPPORTUNITY: Could increase debt to optimize capital structure and reduce dilution"
        else:
            return "OPTIMAL: Well-balanced debt/equity mix"
    
    def _verify_balance(
        self,
        uses: Dict[str, Any],
        sources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify sources = uses"""
        total_uses = uses.get('total_uses', 0)
        total_sources = sources.get('total_sources', 0)
        
        balanced = abs(total_uses - total_sources) < 1  # Within $1 rounding
        
        return {
            "is_balanced": balanced,
            "total_uses": total_uses,
            "total_sources": total_sources,
            "difference": total_sources - total_uses,
            "status": "BALANCED" if balanced else "IMBALANCED - NEEDS ADJUSTMENT"
        }
    
    def _create_summary(
        self,
        uses: Dict[str, Any],
        sources: Dict[str, Any],
        pro_forma_cap: Dict[str, Any]
    ) -> str:
        """Create executive summary"""
        
        total = uses.get('total_uses', 0)
        debt_pct = sources.get('new_debt_financing_pct', 0)
        equity_pct = sources.get('new_equity_issuance_pct', 0)
        
        summary = f"""
SOURCES & USES SUMMARY

Total Transaction Size: ${total/1e9:.1f}B

USES:
• Purchase Price: ${uses.get('equity_purchase_price', 0)/1e9:.1f}B ({uses.get('equity_purchase_price_pct', 0):.1f}%)
• Refinance Debt: ${uses.get('refinance_target_debt', 0)/1e9:.1f}B ({uses.get('refinance_target_debt_pct', 0):.1f}%)
• Fees: ${uses.get('total_transaction_fees', 0)/1e6:.1f}M + ${uses.get('financing_fees', 0)/1e6:.1f}M

SOURCES:
• Cash: ${sources.get('acquirer_cash', 0)/1e9:.1f}B ({sources.get('acquirer_cash_pct', 0):.1f}%)
• New Debt: ${sources.get('new_debt_financing', 0)/1e9:.1f}B ({debt_pct:.1f}%)
• New Equity: ${sources.get('new_equity_issuance', 0)/1e9:.1f}B ({equity_pct:.1f}%)

PRO FORMA CAPITALIZATION:
• Total Debt: ${pro_forma_cap.get('pro_forma_total_debt', 0)/1e9:.1f}B
• Debt/EBITDA: {pro_forma_cap.get('pro_forma_debt_to_ebitda', 0):.1f}x
• Debt/Cap: {pro_forma_cap.get('debt_to_total_cap_pct', 0):.1f}%
"""
        return summary.strip()


# Test utility
def test_sources_uses():
    """Test the Sources & Uses generator"""
    
    generator = SourcesUsesGenerator()
    
    # Sample deal terms
    deal_terms = {
        'cash_percentage': 0.5,
        'debt_interest_rate': 0.05,
        'acquirer_stock_price': 150,
        'refinance_target_debt': True
    }
    
    # Sample target data
    target_data = {
        'balance_sheet': [{
            'totalDebt': 5000000000  # $5B debt
        }],
        'income_statement': [{
            'ebitda': 3000000000  # $3B EBITDA
        }]
    }
    
    # Sample acquirer data
    acquirer_data = {
        'balance_sheet': [{
            'cashAndCashEquivalents': 10000000000,  # $10B cash
            'totalDebt': 15000000000  # $15B debt
        }],
        'income_statement': [{
            'ebitda': 15000000000,  # $15B EBITDA
            'weightedAverageShsOut': 1000000000  # 1B shares
        }]
    }
    
    valuation = 30000000000  # $30B
    
    result = generator.generate(deal_terms, target_data, acquirer_data, valuation)
    
    print("Sources & Uses Analysis:")
    print(result['summary'])
    print(f"\nBalance Check: {result['balance_check']['status']}")
    
    return result


if __name__ == "__main__":
    test_sources_uses()
