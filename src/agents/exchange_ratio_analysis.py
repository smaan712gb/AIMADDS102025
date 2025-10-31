"""
Exchange Ratio Analysis

For stock-for-stock deals, analyzes the fairness of the proposed exchange ratio.
Critical for ensuring target shareholders receive fair value.

Key Outputs:
- Current trading-based exchange ratio
- Valuation-based exchange ratios (DCF, P/E, P/B)
- Premium analysis (1-day, 30-day, 52-week)
- Comparison to precedent transactions
- Fairness assessment
"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..core.state import DiligenceState


class ExchangeRatioAnalyzer(BaseAgent):
    """
    Analyzes exchange ratio fairness for stock-for-stock M&A transactions
    
    This answers: "Is the proposed stock exchange ratio fair to target shareholders?"
    """
    
    def __init__(self):
        super().__init__("exchange_ratio_analysis")
    
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
            valuation_data = state.get('valuation_models', {})
            
            # Call the analyze method
            result = self.analyze(acquirer_data, target_data, deal_terms, valuation_data)
            
            # Return in BaseAgent format
            return {
                "data": result,
                "errors": [],
                "warnings": [],
                "recommendations": [
                    "Review exchange ratio with financial advisors",
                    "Validate premium against precedent transactions",
                    "Consider collar structures for exchange ratio protection",
                    "Assess fairness opinion requirements"
                ]
            }
        except Exception as e:
            logger.error(f"Exchange ratio analysis failed: {e}")
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
        deal_terms: Dict[str, Any],
        valuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive exchange ratio analysis
        
        Args:
            acquirer_data: Financial and market data for acquirer
            target_data: Financial and market data for target
            deal_terms: Proposed deal terms including exchange ratio
            valuation_data: DCF and comparable valuations
            
        Returns:
            Complete exchange ratio analysis
        """
        logger.info("Calculating exchange ratio analysis")
        
        try:
            # 1. Current market-based ratio
            market_ratio = self._calculate_market_ratio(
                acquirer_data,
                target_data
            )
            
            # 2. Proposed deal terms
            proposed_ratio = self._extract_proposed_ratio(deal_terms)
            
            # 3. Valuation-based ratios
            valuation_ratios = self._calculate_valuation_ratios(
                acquirer_data,
                target_data,
                valuation_data
            )
            
            # 4. Premium analysis
            premium_analysis = self._analyze_premiums(
                market_ratio,
                proposed_ratio,
                target_data
            )
            
            # 5. Fairness assessment
            fairness = self._assess_fairness(
                proposed_ratio,
                market_ratio,
                valuation_ratios,
                premium_analysis
            )
            
            result = {
                "analysis_date": datetime.now().isoformat(),
                "market_based_ratio": market_ratio,
                "proposed_ratio": proposed_ratio,
                "valuation_based_ratios": valuation_ratios,
                "premium_analysis": premium_analysis,
                "fairness_assessment": fairness,
                "summary": self._create_summary(
                    market_ratio,
                    proposed_ratio,
                    valuation_ratios,
                    premium_analysis,
                    fairness
                )
            }
            
            logger.info("Exchange ratio analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"Error in exchange ratio analysis: {str(e)}")
            raise
    
    def _calculate_market_ratio(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate exchange ratio based on current market prices"""
        
        # Get stock prices (from deal terms or market data)
        acquirer_price = acquirer_data.get('current_stock_price', 100)
        target_price = target_data.get('current_stock_price', 50)
        
        # Market-implied exchange ratio
        market_ratio = target_price / acquirer_price if acquirer_price > 0 else 0
        
        # Historical prices for premium calculation
        target_1day_ago = target_data.get('price_1day_ago', target_price)
        target_30day_avg = target_data.get('price_30day_avg', target_price)
        target_52week_high = target_data.get('price_52week_high', target_price * 1.2)
        target_52week_low = target_data.get('price_52week_low', target_price * 0.8)
        
        return {
            "acquirer_current_price": acquirer_price,
            "target_current_price": target_price,
            "market_implied_ratio": market_ratio,
            "target_price_history": {
                "1_day_ago": target_1day_ago,
                "30_day_average": target_30day_avg,
                "52_week_high": target_52week_high,
                "52_week_low": target_52week_low
            }
        }
    
    def _extract_proposed_ratio(self, deal_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Extract proposed exchange ratio from deal terms"""
        
        # Exchange ratio: # of acquirer shares per target share
        proposed_ratio = deal_terms.get('exchange_ratio', 0)
        
        # If not provided, calculate from prices and premium
        if proposed_ratio == 0:
            acquirer_price = deal_terms.get('acquirer_stock_price', 100)
            target_price = deal_terms.get('target_stock_price', 50)
            premium = deal_terms.get('premium_percent', 0.30)  # Default 30% premium
            
            target_price_with_premium = target_price * (1 + premium)
            proposed_ratio = target_price_with_premium / acquirer_price if acquirer_price > 0 else 0
        
        # Implied price per target share
        acquirer_price = deal_terms.get('acquirer_stock_price', 100)
        implied_target_price = proposed_ratio * acquirer_price
        
        return {
            "proposed_exchange_ratio": proposed_ratio,
            "acquirer_stock_price": acquirer_price,
            "implied_price_per_target_share": implied_target_price,
            "form": f"{proposed_ratio:.4f} acquirer shares per target share"
        }
    
    def _calculate_valuation_ratios(
        self,
        acquirer_data: Dict[str, Any],
        target_data: Dict[str, Any],
        valuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate exchange ratios based on various valuation methods"""
        
        acquirer_income = acquirer_data.get('income_statement', [{}])[0]
        target_income = target_data.get('income_statement', [{}])[0]
        
        # Get share counts
        acquirer_shares = acquirer_income.get('weightedAverageShsOut', 1)
        target_shares = target_income.get('weightedAverageShsOut', 1)
        
        # DCF-based ratio
        dcf_data = valuation_data.get('dcf_advanced', {})
        dcf_analysis = dcf_data.get('dcf_analysis', {})
        target_ev = dcf_analysis.get('base', {}).get('enterprise_value', 0)
        
        acquirer_price = acquirer_data.get('current_stock_price', 100)
        acquirer_market_cap = acquirer_shares * acquirer_price
        
        # DCF ratio (based on enterprise values)
        dcf_ratio = (target_ev / target_shares) / acquirer_price if acquirer_price > 0 and target_shares > 0 else 0
        
        # P/E-based ratio
        acquirer_eps = acquirer_income.get('netIncome', 0) / acquirer_shares if acquirer_shares > 0 else 0
        target_eps = target_income.get('netIncome', 0) / target_shares if target_shares > 0 else 0
        
        acquirer_pe = acquirer_price / acquirer_eps if acquirer_eps > 0 else 0
        target_fair_value_pe = target_eps * acquirer_pe
        pe_ratio = target_fair_value_pe / acquirer_price if acquirer_price > 0 else 0
        
        # P/B-based ratio
        acquirer_balance = acquirer_data.get('balance_sheet', [{}])[0]
        target_balance = target_data.get('balance_sheet', [{}])[0]
        
        acquirer_equity = acquirer_balance.get('totalStockholdersEquity', 0)
        target_equity = target_balance.get('totalStockholdersEquity', 0)
        
        acquirer_bvps = acquirer_equity / acquirer_shares if acquirer_shares > 0 else 0
        target_bvps = target_equity / target_shares if target_shares > 0 else 0
        
        acquirer_pb = acquirer_price / acquirer_bvps if acquirer_bvps > 0 else 0
        target_fair_value_pb = target_bvps * acquirer_pb
        pb_ratio = target_fair_value_pb / acquirer_price if acquirer_price > 0 else 0
        
        # Contribution-based ratio
        acquirer_ebitda = acquirer_income.get('ebitda', 1)
        target_ebitda = target_income.get('ebitda', 1)
        contribution_pct = target_ebitda / (acquirer_ebitda + target_ebitda) if (acquirer_ebitda + target_ebitda) > 0 else 0
        
        # Contribution ratio assumes equity issued = contribution %
        contribution_ratio = (contribution_pct / (1 - contribution_pct)) if contribution_pct < 1 else 0
        
        return {
            "dcf_based": {
                "ratio": dcf_ratio,
                "target_value_per_share": target_ev / target_shares if target_shares > 0 else 0,
                "methodology": "Based on DCF enterprise value"
            },
            "pe_based": {
                "ratio": pe_ratio,
                "target_value_per_share": target_fair_value_pe,
                "acquirer_pe_multiple": acquirer_pe,
                "methodology": "Apply acquirer's P/E to target earnings"
            },
            "pb_based": {
                "ratio": pb_ratio,
                "target_value_per_share": target_fair_value_pb,
                "acquirer_pb_multiple": acquirer_pb,
                "methodology": "Apply acquirer's P/B to target book value"
            },
            "contribution_based": {
                "ratio": contribution_ratio,
                "target_contribution_pct": contribution_pct * 100,
                "methodology": "Based on relative EBITDA contribution"
            }
        }
    
    def _analyze_premiums(
        self,
        market_ratio: Dict[str, Any],
        proposed_ratio: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze premiums offered vs various baselines"""
        
        target_current = market_ratio.get('target_current_price', 0)
        implied_price = proposed_ratio.get('implied_price_per_target_share', 0)
        
        # Premium to current price
        premium_to_current = ((implied_price / target_current) - 1) * 100 if target_current > 0 else 0
        
        # Premium to historical prices
        price_hist = market_ratio.get('target_price_history', {})
        premium_to_1day = ((implied_price / price_hist.get('1_day_ago', target_current)) - 1) * 100
        premium_to_30day = ((implied_price / price_hist.get('30_day_average', target_current)) - 1) * 100
        
        # Comparison to 52-week range
        high_52w = price_hist.get('52_week_high', target_current * 1.2)
        low_52w = price_hist.get('52_week_low', target_current * 0.8)
        position_in_range = ((target_current - low_52w) / (high_52w - low_52w) * 100) if (high_52w - low_52w) > 0 else 50
        
        return {
            "premium_to_current_pct": premium_to_current,
            "premium_to_1day_pct": premium_to_1day,
            "premium_to_30day_pct": premium_to_30day,
            "vs_52week_high_pct": ((implied_price / high_52w) - 1) * 100,
            "vs_52week_low_pct": ((implied_price / low_52w) - 1) * 100,
            "target_position_in_52w_range_pct": position_in_range,
            "implied_target_price": implied_price,
            "assessment": self._assess_premium_level(premium_to_current, premium_to_30day)
        }
    
    def _assess_premium_level(self, current_premium: float, avg_30day_premium: float) -> str:
        """Assess if premium is fair"""
        avg_premium = (current_premium + avg_30day_premium) / 2
        
        if avg_premium > 50:
            return "VERY HIGH PREMIUM - Exceptional offer, likely to be accepted"
        elif avg_premium > 30:
            return "HIGH PREMIUM - Attractive offer above market norms"
        elif avg_premium > 20:
            return "MODERATE PREMIUM - Typical M&A premium"
        elif avg_premium > 10:
            return "LOW PREMIUM - May face shareholder resistance"
        else:
            return "MINIMAL PREMIUM - Likely insufficient for shareholder approval"
    
    def _assess_fairness(
        self,
        proposed_ratio: Dict[str, Any],
        market_ratio: Dict[str, Any],
        valuation_ratios: Dict[str, Any],
        premium_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall fairness of exchange ratio"""
        
        proposed = proposed_ratio.get('proposed_exchange_ratio', 0)
        
        # Compare to various benchmarks
        dcf_ratio = valuation_ratios.get('dcf_based', {}).get('ratio', 0)
        pe_ratio = valuation_ratios.get('pe_based', {}).get('ratio', 0)
        pb_ratio = valuation_ratios.get('pb_based', {}).get('ratio', 0)
        
        # Calculate average valuation-based ratio
        ratios_list = [r for r in [dcf_ratio, pe_ratio, pb_ratio] if r > 0]
        avg_valuation_ratio = sum(ratios_list) / len(ratios_list) if ratios_list else 0
        
        # Fairness delta
        fairness_delta_pct = ((proposed / avg_valuation_ratio) - 1) * 100 if avg_valuation_ratio > 0 else 0
        
        # Overall assessment
        premium_to_current = premium_analysis.get('premium_to_current_pct', 0)
        
        if fairness_delta_pct > 10 and premium_to_current > 30:
            overall_rating = "GENEROUS"
            recommendation = "STRONG ACCEPT - Highly favorable terms for target shareholders"
        elif fairness_delta_pct > 0 and premium_to_current > 20:
            overall_rating = "FAIR"
            recommendation = "ACCEPT - Fair valuation with adequate premium"
        elif fairness_delta_pct > -10 and premium_to_current > 15:
            overall_rating = "ACCEPTABLE"
            recommendation = "CONSIDER - Within reasonable range"
        else:
            overall_rating = "INADEQUATE"
            recommendation = "CAUTION - May be insufficient for shareholder approval"
        
        return {
            "proposed_vs_valuation_delta_pct": fairness_delta_pct,
            "overall_rating": overall_rating,
            "recommendation": recommendation,
            "valuation_range": {
                "low": min(ratios_list) if ratios_list else 0,
                "high": max(ratios_list) if ratios_list else 0,
                "average": avg_valuation_ratio,
                "proposed": proposed
            },
            "key_factors": [
                f"DCF-based ratio: {dcf_ratio:.4f}",
                f"P/E-based ratio: {pe_ratio:.4f}",
                f"P/B-based ratio: {pb_ratio:.4f}",
                f"Proposed ratio: {proposed:.4f}",
                f"Premium to current: {premium_to_current:.1f}%"
            ]
        }
    
    def _create_summary(
        self,
        market_ratio: Dict[str, Any],
        proposed_ratio: Dict[str, Any],
        valuation_ratios: Dict[str, Any],
        premium_analysis: Dict[str, Any],
        fairness: Dict[str, Any]
    ) -> str:
        """Create executive summary"""
        
        proposed = proposed_ratio.get('proposed_exchange_ratio', 0)
        implied_price = proposed_ratio.get('implied_price_per_target_share', 0)
        target_current = market_ratio.get('target_current_price', 0)
        premium = premium_analysis.get('premium_to_current_pct', 0)
        rating = fairness.get('overall_rating', '')
        
        summary = f"""
EXCHANGE RATIO ANALYSIS SUMMARY

PROPOSED TERMS:
• Exchange Ratio: {proposed:.4f}x acquirer shares per target share
• Implied Price: ${implied_price:.2f} per target share
• Current Price: ${target_current:.2f}
• Premium: {premium:+.1f}%

VALUATION-BASED RATIOS:
• DCF-Based: {valuation_ratios.get('dcf_based', {}).get('ratio', 0):.4f}x
• P/E-Based: {valuation_ratios.get('pe_based', {}).get('ratio', 0):.4f}x
• P/B-Based: {valuation_ratios.get('pb_based', {}).get('ratio', 0):.4f}x

FAIRNESS ASSESSMENT: {rating}
{fairness.get('recommendation', '')}
"""
        return summary.strip()


# Test utility
def test_exchange_ratio_analysis():
    """Test the exchange ratio analyzer"""
    
    analyzer = ExchangeRatioAnalyzer()
    
    # Sample acquirer data
    acquirer_data = {
        'current_stock_price': 150,
        'income_statement': [{
            'netIncome': 10000000000,
            'ebitda': 15000000000,
            'weightedAverageShsOut': 1000000000
        }],
        'balance_sheet': [{
            'totalStockholdersEquity': 50000000000
        }]
    }
    
    # Sample target data
    target_data = {
        'current_stock_price': 75,
        'price_1day_ago': 74,
        'price_30day_avg': 70,
        'price_52week_high': 85,
        'price_52week_low': 60,
        'income_statement': [{
            'netIncome': 2000000000,
            'ebitda': 3000000000,
            'weightedAverageShsOut': 200000000
        }],
        'balance_sheet': [{
            'totalStockholdersEquity': 10000000000
        }]
    }
    
    # Sample deal terms
    deal_terms = {
        'exchange_ratio': 0.65,  # 0.65 acquirer shares per target share
        'acquirer_stock_price': 150,
        'target_stock_price': 75
    }
    
    # Sample valuation
    valuation_data = {
        'dcf_advanced': {
            'dcf_analysis': {
                'base': {
                    'enterprise_value': 20000000000
                }
            }
        }
    }
    
    result = analyzer.analyze(acquirer_data, target_data, deal_terms, valuation_data)
    
    print("Exchange Ratio Analysis:")
    print(result['summary'])
    print(f"\nFairness Rating: {result['fairness_assessment']['overall_rating']}")
    
    return result


if __name__ == "__main__":
    test_exchange_ratio_analysis()
