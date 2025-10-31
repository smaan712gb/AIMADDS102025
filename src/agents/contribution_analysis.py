"""
Contribution Analysis

Analyzes relative contribution of acquirer and target to justify exchange ratio.
Shows what percentage each party contributes to the combined entity.

Key Outputs:
- Revenue contribution %
- EBITDA contribution %
- Net Income contribution %
- EPS contribution %
- Ownership split comparison
"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState


class ContributionAnalyzer(BaseAgent):
    """
    Analyzes contribution metrics to justify M&A valuation and exchange ratio
    
    This answers: "Are we paying a fair price based on relative contributions?"
    """
    
    def __init__(self):
        super().__init__("contribution_analysis")
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Run method required by BaseAgent
        
        Args:
            state: DiligenceState containing all analysis data
            
        Returns:
            Dict with data, errors, warnings, recommendations
        """
        try:
            acquirer_data = state.get('acquirer_data', {})
            target_data = state.get('financial_data', {})
            deal_terms = state.get('deal_terms', {})
            
            # Call the analyze method
            result = self.analyze(acquirer_data, target_data, deal_terms)
            
            # Return in BaseAgent format
            return {
                "data": result,
                "errors": [],
                "warnings": [],
                "recommendations": [
                    "Review contribution analysis with board",
                    "Validate fairness of ownership split",
                    "Consider contribution-based adjustments to terms",
                    "Assess strategic value beyond financial metrics"
                ]
            }
        except Exception as e:
            logger.error(f"Contribution analysis failed: {e}")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
    
    def analyze(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive contribution analysis
        
        Args:
            acquirer_data: Financial data for acquiring company
            target_data: Financial data for target company
            deal_terms: Deal structure including exchange ratio
            
        Returns:
            Complete contribution analysis
        """
        logger.info("Calculating contribution analysis")
        
        try:
            # 1. Financial contributions
            financial_contribution = self._calculate_financial_contribution(
                acquirer_data,
                target_data
            )
            
            # 2. Ownership split
            ownership_split = self._calculate_ownership_split(
                acquirer_data,
                deal_terms
            )
            
            # 3. Contribution vs Ownership analysis
            fairness_analysis = self._analyze_fairness(
                financial_contribution,
                ownership_split
            )
            
            # 4. Relative valuation metrics
            relative_valuation = self._calculate_relative_valuation(
                acquirer_data,
                target_data,
                deal_terms
            )
            
            result = {
                "analysis_date": datetime.now().isoformat(),
                "financial_contribution": financial_contribution,
                "ownership_split": ownership_split,
                "fairness_analysis": fairness_analysis,
                "relative_valuation": relative_valuation,
                "summary": self._create_summary(financial_contribution, ownership_split, fairness_analysis)
            }
            
            logger.info("Contribution analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"Error in contribution analysis: {str(e)}")
            raise
    
    def _calculate_financial_contribution(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate contribution by financial metric"""
        
        # Extract financial data
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        target_income = target_data.get('income_statement', [{}])[0]
        
        # Revenue
        acquirer_revenue = acquirer_income.get('revenue', 0)
        target_revenue = target_income.get('revenue', 0)
        combined_revenue = acquirer_revenue + target_revenue
        
        revenue_contribution_acquirer = (acquirer_revenue / combined_revenue * 100) if combined_revenue > 0 else 0
        revenue_contribution_target = (target_revenue / combined_revenue * 100) if combined_revenue > 0 else 0
        
        # EBITDA
        acquirer_ebitda = acquirer_income.get('ebitda', 0)
        target_ebitda = target_income.get('ebitda', 0)
        combined_ebitda = acquirer_ebitda + target_ebitda
        
        ebitda_contribution_acquirer = (acquirer_ebitda / combined_ebitda * 100) if combined_ebitda > 0 else 0
        ebitda_contribution_target = (target_ebitda / combined_ebitda * 100) if combined_ebitda > 0 else 0
        
        # Net Income
        acquirer_ni = acquirer_income.get('netIncome', 0)
        target_ni = target_income.get('netIncome', 0)
        combined_ni = acquirer_ni + target_ni
        
        ni_contribution_acquirer = (acquirer_ni / combined_ni * 100) if combined_ni > 0 else 0
        ni_contribution_target = (target_ni / combined_ni * 100) if combined_ni > 0 else 0
        
        # Calculate weighted average contribution
        weighted_avg_acquirer = (
            revenue_contribution_acquirer * 0.3 +
            ebitda_contribution_acquirer * 0.4 +
            ni_contribution_acquirer * 0.3
        )
        weighted_avg_target = 100 - weighted_avg_acquirer
        
        return {
            "revenue": {
                "acquirer_amount": acquirer_revenue,
                "target_amount": target_revenue,
                "combined_amount": combined_revenue,
                "acquirer_contribution_pct": revenue_contribution_acquirer,
                "target_contribution_pct": revenue_contribution_target
            },
            "ebitda": {
                "acquirer_amount": acquirer_ebitda,
                "target_amount": target_ebitda,
                "combined_amount": combined_ebitda,
                "acquirer_contribution_pct": ebitda_contribution_acquirer,
                "target_contribution_pct": ebitda_contribution_target
            },
            "net_income": {
                "acquirer_amount": acquirer_ni,
                "target_amount": target_ni,
                "combined_amount": combined_ni,
                "acquirer_contribution_pct": ni_contribution_acquirer,
                "target_contribution_pct": ni_contribution_target
            },
            "weighted_average_contribution": {
                "acquirer_pct": weighted_avg_acquirer,
                "target_pct": weighted_avg_target,
                "methodology": "Revenue 30%, EBITDA 40%, Net Income 30%"
            }
        }
    
    def _calculate_ownership_split(
        self,
        acquirer_data: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate ownership split post-transaction"""
        
        # Extract shares data
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        acquirer_existing_shares = acquirer_income.get('weightedAverageShsOut', 0)
        
        # Calculate new shares issued
        stock_consideration = deal_terms.get('purchase_price', 0) * (1 - deal_terms.get('cash_percentage', 0.5))
        acquirer_stock_price = deal_terms.get('acquirer_stock_price', 100)
        new_shares_issued = stock_consideration / acquirer_stock_price if acquirer_stock_price > 0 else 0
        
        # Pro forma shares
        pro_forma_shares = acquirer_existing_shares + new_shares_issued
        
        # Ownership percentages
        acquirer_ownership_pct = (acquirer_existing_shares / pro_forma_shares * 100) if pro_forma_shares > 0 else 100
        target_ownership_pct = (new_shares_issued / pro_forma_shares * 100) if pro_forma_shares > 0 else 0
        
        return {
            "acquirer_existing_shares": acquirer_existing_shares,
            "new_shares_issued": new_shares_issued,
            "pro_forma_total_shares": pro_forma_shares,
            "acquirer_ownership_pct": acquirer_ownership_pct,
            "target_ownership_pct": target_ownership_pct,
            "dilution_pct": target_ownership_pct
        }
    
    def _analyze_fairness(
        self,
        financial_contribution: Dict[str, Any],
        ownership_split: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze if ownership split is fair based on contributions"""
        
        # Get weighted average contribution
        weighted_avg = financial_contribution.get('weighted_average_contribution', {})
        target_contribution_pct = weighted_avg.get('target_pct', 0)
        
        # Get ownership
        target_ownership_pct = ownership_split.get('target_ownership_pct', 0)
        
        # Calculate fairness delta
        fairness_delta = target_ownership_pct - target_contribution_pct
        fairness_delta_pct = (fairness_delta / target_contribution_pct * 100) if target_contribution_pct > 0 else 0
        
        # Assess fairness
        if abs(fairness_delta_pct) < 10:
            fairness_assessment = "FAIR - Ownership aligns with contribution"
            fairness_rating = "GOOD"
        elif fairness_delta_pct > 10:
            fairness_assessment = f"TARGET FAVORABLE - Target getting {fairness_delta_pct:.1f}% more ownership than contribution"
            fairness_rating = "TARGET FAVORED"
        elif fairness_delta_pct < -10:
            fairness_assessment = f"ACQUIRER FAVORABLE - Acquirer giving {abs(fairness_delta_pct):.1f}% less ownership than target contribution"
            fairness_rating = "ACQUIRER FAVORED"
        else:
            fairness_assessment = "BALANCED - Minor variance within acceptable range"
            fairness_rating = "ACCEPTABLE"
        
        # Contribution vs ownership table
        comparison = {
            "revenue": {
                "target_contribution_pct": financial_contribution['revenue']['target_contribution_pct'],
                "target_ownership_pct": target_ownership_pct,
                "delta_pct": target_ownership_pct - financial_contribution['revenue']['target_contribution_pct']
            },
            "ebitda": {
                "target_contribution_pct": financial_contribution['ebitda']['target_contribution_pct'],
                "target_ownership_pct": target_ownership_pct,
                "delta_pct": target_ownership_pct - financial_contribution['ebitda']['target_contribution_pct']
            },
            "net_income": {
                "target_contribution_pct": financial_contribution['net_income']['target_contribution_pct'],
                "target_ownership_pct": target_ownership_pct,
                "delta_pct": target_ownership_pct - financial_contribution['net_income']['target_contribution_pct']
            },
            "weighted_average": {
                "target_contribution_pct": target_contribution_pct,
                "target_ownership_pct": target_ownership_pct,
                "delta_pct": fairness_delta
            }
        }
        
        return {
            "fairness_delta_percentage_points": fairness_delta,
            "fairness_delta_percent": fairness_delta_pct,
            "fairness_assessment": fairness_assessment,
            "fairness_rating": fairness_rating,
            "detailed_comparison": comparison,
            "recommendation": self._generate_recommendation(fairness_rating, fairness_delta_pct)
        }
    
    def _calculate_relative_valuation(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        deal_terms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate relative valuation multiples"""
        
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        target_income = target_data.get('income_statement', [{}])[0]
        
        # Implied valuation for acquirer
        acquirer_shares = acquirer_income.get('weightedAverageShsOut', 0)
        acquirer_stock_price = deal_terms.get('acquirer_stock_price', 100)
        acquirer_market_cap = acquirer_shares * acquirer_stock_price
        
        # Target valuation
        target_valuation = deal_terms.get('purchase_price', 0)
        
        # Calculate multiples
        acquirer_revenue = acquirer_income.get('revenue', 1)
        target_revenue = target_income.get('revenue', 1)
        
        acquirer_ebitda = acquirer_income.get('ebitda', 1)
        target_ebitda = target_income.get('ebitda', 1)
        
        acquirer_p_revenue = acquirer_market_cap / acquirer_revenue if acquirer_revenue > 0 else 0
        target_p_revenue = target_valuation / target_revenue if target_revenue > 0 else 0
        
        acquirer_ev_ebitda = acquirer_market_cap / acquirer_ebitda if acquirer_ebitda > 0 else 0
        target_ev_ebitda = target_valuation / target_ebitda if target_ebitda > 0 else 0
        
        # Premium/discount analysis
        revenue_multiple_premium = ((target_p_revenue / acquirer_p_revenue) - 1) * 100 if acquirer_p_revenue > 0 else 0
        ebitda_multiple_premium = ((target_ev_ebitda / acquirer_ev_ebitda) - 1) * 100 if acquirer_ev_ebitda > 0 else 0
        
        return {
            "acquirer_multiples": {
                "market_cap": acquirer_market_cap,
                "price_to_revenue": acquirer_p_revenue,
                "ev_to_ebitda": acquirer_ev_ebitda
            },
            "target_multiples": {
                "purchase_price": target_valuation,
                "price_to_revenue": target_p_revenue,
                "ev_to_ebitda": target_ev_ebitda
            },
            "relative_premium_discount": {
                "revenue_multiple_premium_pct": revenue_multiple_premium,
                "ebitda_multiple_premium_pct": ebitda_multiple_premium,
                "assessment": self._assess_premium(revenue_multiple_premium, ebitda_multiple_premium)
            }
        }
    
    def _assess_premium(self, revenue_premium: float, ebitda_premium: float) -> str:
        """Assess if premium paid is reasonable"""
        avg_premium = (revenue_premium + ebitda_premium) / 2
        
        if avg_premium > 30:
            return "HIGH PREMIUM - Target valued significantly above acquirer multiples"
        elif avg_premium > 15:
            return "MODERATE PREMIUM - Typical acquisition premium"
        elif avg_premium > 0:
            return "LOW PREMIUM - Conservative valuation"
        elif avg_premium > -15:
            return "DISCOUNT - Target valued below acquirer multiples"
        else:
            return "SIGNIFICANT DISCOUNT - Opportunistic acquisition"
    
    def _generate_recommendation(self, fairness_rating: str, fairness_delta_pct: float) -> str:
        """Generate recommendation based on fairness analysis"""
        if fairness_rating == "GOOD":
            return "PROCEED - Fair exchange based on relative contributions"
        elif fairness_rating == "TARGET FAVORED":
            return f"REVIEW - Target receiving {abs(fairness_delta_pct):.1f}% premium to contribution; justify strategic premium"
        elif fairness_rating == "ACQUIRER FAVORED":
            return f"PROCEED - Acquirer-favorable terms with {abs(fairness_delta_pct):.1f}% value capture"
        else:
            return "ACCEPTABLE - Exchange ratio within reasonable range"
    
    def _create_summary(
        self,
        financial_contribution: Dict[str, Any],
        ownership_split: Dict[str, Any],
        fairness_analysis: Dict[str, Any]
    ) -> str:
        """Create executive summary"""
        
        weighted = financial_contribution.get('weighted_average_contribution', {})
        target_contrib_pct = weighted.get('target_pct', 0)
        target_own_pct = ownership_split.get('target_ownership_pct', 0)
        
        fairness = fairness_analysis.get('fairness_assessment', '')
        rating = fairness_analysis.get('fairness_rating', '')
        
        summary = f"""
CONTRIBUTION ANALYSIS SUMMARY

FINANCIAL CONTRIBUTION:
• Acquirer: {100-target_contrib_pct:.1f}% (Revenue, EBITDA, NI weighted)
• Target: {target_contrib_pct:.1f}%

OWNERSHIP SPLIT:
• Acquirer Shareholders: {100-target_own_pct:.1f}%
• Target Shareholders: {target_own_pct:.1f}%

FAIRNESS ASSESSMENT: {rating}
{fairness}

Conclusion: {fairness_analysis.get('recommendation', '')}
"""
        return summary.strip()


# Test utility
def test_contribution_analysis():
    """Test the contribution analyzer"""
    
    analyzer = ContributionAnalyzer()
    
    # Sample acquirer data
    acquirer_data = {
        'income_statement': [{
            'revenue': 50000000000,  # $50B
            'ebitda': 15000000000,   # $15B
            'netIncome': 10000000000,  # $10B
            'weightedAverageShsOut': 1000000000  # 1B shares
        }]
    }
    
    # Sample target data
    target_data = {
        'income_statement': [{
            'revenue': 10000000000,  # $10B
            'ebitda': 3000000000,    # $3B
            'netIncome': 2000000000   # $2B
        }]
    }
    
    # Sample deal terms
    deal_terms = {
        'purchase_price': 30000000000,  # $30B
        'cash_percentage': 0.5,
        'acquirer_stock_price': 150
    }
    
    result = analyzer.analyze(acquirer_data, target_data, deal_terms)
    
    print("Contribution Analysis:")
    print(result['summary'])
    print(f"\nFairness Rating: {result['fairness_analysis']['fairness_rating']}")
    
    return result


if __name__ == "__main__":
    test_contribution_analysis()
