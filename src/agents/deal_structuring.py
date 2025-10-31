"""
Deal Structuring Agent - Analyzes optimal M&A deal structure
Critical M&A capability for tax efficiency and negotiation strategy
"""
from typing import Dict, List, Any
import numpy as np
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..core.state import DiligenceState
from ..core.llm_factory import get_llm


class DealStructuringAgent(BaseAgent):
    """
    Deal Structuring Agent - Tax and Structure Optimization
    
    Analyzes:
    - Stock vs. cash vs. mixed consideration
    - Asset purchase vs. stock purchase
    - Tax implications (338(h)(10), 338(g))
    - Earnout provisions
    - Working capital adjustments
    - Purchase price allocation
    """
    
    def __init__(self):
        """Initialize Deal Structuring Agent"""
        super().__init__("deal_structuring")
    
    def _get_ebitda_safe(self, state: DiligenceState) -> tuple[float, bool]:
        """
        PRODUCTION-SAFE: Get EBITDA with multiple fallback locations
        
        Returns:
            (ebitda_value, is_valid)
        """
        # Try multiple locations in priority order
        locations = [
            lambda: state.get('ebitda'),
            lambda: state.get('financial_data', {}).get('ebitda'),
            lambda: state.get('normalized_financials', {}).get('historical', {}).get('income_statement', [{}])[0].get('ebitda'),
            lambda: state.get('financial_data', {}).get('income_statement', [{}])[0].get('ebitda'),
        ]
        
        for get_value in locations:
            try:
                value = get_value()
                if value and value > 0:
                    return float(value), True
            except (KeyError, IndexError, TypeError):
                continue
        
        return 0.0, False
    
    async def run(self, state: DiligenceState) -> Dict[str, Any]:
        """
        Analyze optimal deal structure
        
        Args:
            state: Current state with financial and tax data
            
        Returns:
            Deal structuring recommendations
        """
        errors = []
        warnings = []
        recommendations = []
        
        target_company = state.get("target_company", "Unknown")
        target_ticker = state.get("target_ticker", "")
        
        # CRITICAL FIX: Ensure deal_value is never None
        deal_value = state.get("deal_value", 0)
        if deal_value is None:
            deal_value = 0
            warnings.append("Deal value not specified, using $0 for calculations")
        
        # Ensure numeric
        try:
            deal_value = float(deal_value)
        except (TypeError, ValueError):
            deal_value = 0
            warnings.append(f"Invalid deal_value: {state.get('deal_value')}, using $0")
        
        logger.info(f"[DEAL STRUCTURE] Analyzing optimal structure for {target_company} (Deal Value: ${deal_value:,.0f})")
        
        # Get financial and tax data
        financial_data = state.get('financial_data', {})
        tax_analysis = state.get('tax_analysis', {})
        
        if not financial_data:
            errors.append("Financial data not available")
            return {
                "data": {},
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }
        
        # 1. Stock vs. Cash Analysis
        consideration_analysis = self._analyze_consideration_structure(
            target_data=financial_data,
            deal_value=deal_value,
            tax_data=tax_analysis
        )
        
        # 2. Asset vs. Stock Purchase
        purchase_structure = self._analyze_purchase_structure(
            target_data=financial_data,
            tax_data=tax_analysis
        )
        
        # 3. Earnout Provisions
        earnout_analysis = self._analyze_earnout_provisions(
            target_data=financial_data,
            deal_value=deal_value
        )
        
        # 4. Working Capital Adjustment
        wc_adjustment = self._calculate_working_capital_peg(
            financial_data
        )
        
        # 5. Purchase Price Allocation
        ppa = self._estimate_purchase_price_allocation(
            target_data=financial_data,
            deal_value=deal_value
        )
        
        # 6. Generate recommendations
        structure_recommendation = await self._generate_structure_recommendation(
            target_company,
            consideration_analysis,
            purchase_structure,
            earnout_analysis,
            ppa
        )
        
        result = {
            'consideration_structure': consideration_analysis,
            'purchase_structure': purchase_structure,
            'earnout_provisions': earnout_analysis,
            'working_capital_adjustment': wc_adjustment,
            'purchase_price_allocation': ppa,
            'recommended_structure': structure_recommendation,
            'deal_value': deal_value
        }
        
        logger.info(f"[DEAL STRUCTURE] Analysis complete for {target_company}")
        
        return {
            "data": result,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    def _analyze_consideration_structure(
        self,
        target_data: Dict,
        deal_value: float,
        tax_data: Dict
    ) -> Dict[str, Any]:
        """Analyze stock vs. cash consideration"""
        
        # CRITICAL FIX: Ensure deal_value is numeric
        if deal_value is None or deal_value <= 0:
            deal_value = 0
        
        # Calculate optimal mix
        structures = {
            'all_cash': {
                'cash': deal_value,
                'stock': 0,
                'pros': ['Immediate liquidity for sellers', 'No dilution for acquirer', 'Clean transaction'],
                'cons': ['Requires financing', 'Higher cash outlay', 'No tax deferral for sellers'],
                'tax_impact': 'Immediate taxable event for target shareholders'
            },
            'all_stock': {
                'cash': 0,
                'stock': deal_value,
                'pros': ['Tax-deferred for sellers', 'No cash required', 'Aligns seller interests'],
                'cons': ['Dilution for acquirer', 'Market risk', 'Complexity in valuation'],
                'tax_impact': 'Tax-free reorganization possible (Section 368)'
            },
            'mixed_60_40': {
                'cash': deal_value * 0.6,
                'stock': deal_value * 0.4,
                'pros': ['Balanced approach', 'Partial tax deferral', 'Moderate dilution'],
                'cons': ['More complex', 'Some financing required'],
                'tax_impact': 'Partially taxable transaction'
            }
        }
        
        return {
            'structures_analyzed': structures,
            'recommended_mix': 'mixed_60_40',
            'rationale': 'Balanced approach provides liquidity while maintaining alignment'
        }
    
    def _analyze_purchase_structure(
        self,
        target_data: Dict,
        tax_data: Dict
    ) -> Dict[str, Any]:
        """Analyze asset vs. stock purchase"""
        
        return {
            'asset_purchase': {
                'description': 'Purchase specific assets and assume specific liabilities',
                'tax_benefits': 'Step-up in asset basis, higher depreciation deductions',
                'pros': ['Cherry-pick assets', 'Avoid unknown liabilities', 'Tax benefits'],
                'cons': ['More complex', 'May require consents', 'Sales tax on assets'],
                'estimated_tax_benefit_npv': 'Calculate based on step-up value'
            },
            'stock_purchase': {
                'description': 'Purchase all stock of target company',
                'tax_benefits': 'Potential 338(h)(10) election for step-up',
                'pros': ['Simpler transaction', 'All contracts transfer', 'No sales tax'],
                'cons': ['Inherit all liabilities', 'Limited tax step-up without election'],
                'estimated_tax_benefit_npv': 'Lower unless 338(h)(10) election made'
            },
            'recommended_structure': 'stock_purchase_with_338h10',
            'rationale': 'Stock purchase with 338(h)(10) election provides tax benefits of asset purchase with simplicity of stock deal'
        }
    
    def _analyze_earnout_provisions(
        self,
        target_data: Dict,
        deal_value: float
    ) -> Dict[str, Any]:
        """Analyze earnout provisions"""
        
        # CRITICAL FIX: Ensure deal_value is numeric
        if deal_value is None or deal_value <= 0:
            deal_value = 0
        
        # Earnout scenarios
        base_deal_value = deal_value * 0.85  # 85% upfront
        earnout_potential = deal_value * 0.15  # 15% earnout
        
        return {
            'earnout_recommended': True if deal_value > 100_000_000 else False,
            'base_consideration': base_deal_value,
            'earnout_potential': earnout_potential,
            'earnout_metrics': [
                {'metric': 'Revenue Growth', 'threshold': '15% CAGR', 'payout': earnout_potential * 0.4},
                {'metric': 'EBITDA Margin', 'threshold': '25% margin', 'payout': earnout_potential * 0.3},
                {'metric': 'Customer Retention', 'threshold': '90% retention', 'payout': earnout_potential * 0.3}
            ],
            'earnout_period': '2 years post-close',
            'rationale': 'Bridges valuation gap and aligns management incentives'
        }
    
    def _calculate_working_capital_peg(self, financial_data: Dict) -> Dict[str, Any]:
        """Calculate working capital adjustment mechanism"""
        
        balance_sheets = financial_data.get('balance_sheet', [])
        
        if not balance_sheets:
            return {'error': 'No balance sheet data'}
        
        latest_bs = balance_sheets[0]
        
        # Calculate normalized working capital
        current_assets = latest_bs.get('totalCurrentAssets', 0)
        current_liabilities = latest_bs.get('totalCurrentLiabilities', 0)
        cash = latest_bs.get('cashAndCashEquivalents', 0)
        
        # NWC = Current Assets - Current Liabilities - Cash
        nwc = current_assets - current_liabilities - cash
        
        # Historical average for peg
        nwc_values = []
        for bs in balance_sheets[:4]:
            ca = bs.get('totalCurrentAssets', 0)
            cl = bs.get('totalCurrentLiabilities', 0)
            c = bs.get('cashAndCashEquivalents', 0)
            nwc_values.append(ca - cl - c)
        
        nwc_peg = np.mean(nwc_values) if nwc_values else nwc
        
        return {
            'latest_nwc': nwc,
            'normalized_nwc_peg': nwc_peg,
            'adjustment_mechanism': {
                'description': 'Purchase price adjusted dollar-for-dollar for NWC variance at close',
                'formula': 'Final Price = Base Price + (Actual NWC - NWC Peg)',
                'example': f'If NWC is ${nwc:,.0f} vs peg of ${nwc_peg:,.0f}, adjustment = ${(nwc - nwc_peg):,.0f}'
            }
        }
    
    def _estimate_purchase_price_allocation(
        self,
        target_data: Dict,
        deal_value: float
    ) -> Dict[str, Any]:
        """Estimate purchase price allocation to assets"""
        
        # CRITICAL FIX: Ensure deal_value is numeric
        if deal_value is None or deal_value <= 0:
            deal_value = 0
        
        balance_sheets = target_data.get('balance_sheet', [])
        
        if not balance_sheets:
            return {'error': 'No balance sheet data'}
        
        latest_bs = balance_sheets[0]
        
        # Get book values
        tangible_assets = latest_bs.get('totalAssets', 0) - latest_bs.get('intangibleAssets', 0)
        intangible_assets = latest_bs.get('intangibleAssets', 0)
        total_liabilities = latest_bs.get('totalLiabilities', 0)
        
        # Allocate purchase price
        net_tangible_assets = tangible_assets - total_liabilities
        
        # Goodwill calculation
        goodwill = deal_value - net_tangible_assets - intangible_assets
        
        allocation = {
            'purchase_price': deal_value,
            'net_tangible_assets': net_tangible_assets,
            'identifiable_intangibles': intangible_assets,
            'goodwill': max(0, goodwill),
            'allocation_percentages': {
                'tangible': (net_tangible_assets / deal_value * 100) if deal_value > 0 else 0,
                'intangible': (intangible_assets / deal_value * 100) if deal_value > 0 else 0,
                'goodwill': (max(0, goodwill) / deal_value * 100) if deal_value > 0 else 0
            }
        }
        
        return allocation
    
    async def _generate_structure_recommendation(
        self,
        company: str,
        consideration: Dict,
        purchase: Dict,
        earnout: Dict,
        ppa: Dict
    ) -> Dict[str, Any]:
        """Generate AI-powered deal structure recommendation"""
        
        try:
            prompt = f"""As an M&A structuring expert, provide recommendations for acquiring {company}.

CONSIDERATION OPTIONS:
- All Cash: ${consideration['structures_analyzed']['all_cash']['cash']:,.0f}
- All Stock: ${consideration['structures_analyzed']['all_stock']['stock']:,.0f}
- Mixed (60/40): Cash ${consideration['structures_analyzed']['mixed_60_40']['cash']:,.0f}, Stock ${consideration['structures_analyzed']['mixed_60_40']['stock']:,.0f}

PURCHASE STRUCTURE:
- Asset Purchase: {purchase['asset_purchase']['pros']}
- Stock Purchase: {purchase['stock_purchase']['pros']}

EARNOUT:
- Recommended: {earnout['earnout_recommended']}
- Potential: ${earnout['earnout_potential']:,.0f}

Provide:
1. Recommended deal structure (2-3 sentences)
2. Tax optimization strategy (2-3 sentences)
3. Key negotiation points (2-3 bullets)
4. Risk mitigation through structure (2-3 sentences)"""

            messages = [
                SystemMessage(content="You are an expert M&A structuring advisor with 20 years of experience."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                'summary': response.content,
                'recommended_consideration': consideration['recommended_mix'],
                'recommended_purchase_type': purchase['recommended_structure'],
                'use_earnout': earnout['earnout_recommended']
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                'error': str(e),
                'fallback_recommendation': 'Stock purchase with 338(h)(10) election, 60/40 cash/stock mix'
            }
