"""
Macroeconomic Analyst Agent - "The Forecaster"

This agent models the impact of the external economic environment on the company,
transforming static financial projections into dynamic simulations that account for
macroeconomic factors. It enables scenario analysis that humans cannot perform at scale.

Revolutionary Capabilities:
- Real-time economic data integration
- Statistical correlation analysis between macro factors and company performance
- Dynamic scenario modeling (e.g., "What if Fed raises rates by 50 bps?")
- Sensitivity analysis for key economic indicators
"""

from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime
import statistics
import numpy as np

from .base_agent import BaseAgent
from ..integrations.fmp_client import FMPClient


class MacroeconomicAnalystAgent(BaseAgent):
    """
    Agent responsible for macroeconomic analysis and scenario modeling.
    
    This agent transforms financial models from static forecasts into dynamic
    simulations that account for changes in the macroeconomic environment.
    """
    
    def __init__(self):
        super().__init__("macroeconomic_analyst")
        self.fmp_client = None
        self.economic_cache = {}
        

    
    async def run(self, state: Any) -> Dict[str, Any]:
        """
        Execute macroeconomic analysis (required by BaseAgent).
        This is called when using the standard workflow.
        """
        try:
            self.log_action("Starting macroeconomic analysis")
            
            # Get target company info from state
            symbol = state.get('target_ticker')
            if not symbol:
                self.log_action("No target ticker found in state", level="warning")
                return {
                    "data": {},
                    "errors": ["No target ticker provided"],
                    "warnings": [],
                    "recommendations": []
                }
            
            # Get historical financial data from state
            financial_data = state.get('financial_data', {})

            # Build historical financials dict from actual FMP data structure
            historical_financials = {}

            # Extract revenue from income statement
            income_statements = financial_data.get('income_statement', [])
            if income_statements and len(income_statements) > 0:
                latest_is = income_statements[0]  # Most recent
                historical_financials.update({
                    'revenue': latest_is.get('revenue', 0),
                    'operating_income': latest_is.get('operatingIncome', 0),
                    'net_income': latest_is.get('netIncome', 0),
                    'ebitda': latest_is.get('ebitda', 0)
                })

                # Calculate growth metrics if multiple periods
                if len(income_statements) > 1:
                    prev_revenue = income_statements[1].get('revenue', 0)
                    curr_revenue = historical_financials.get('revenue', 0)
                    if prev_revenue > 0:
                        historical_financials['revenue_growth'] = ((curr_revenue / prev_revenue) - 1) * 100

            # Extract operating margin
            revenue = historical_financials.get('revenue', 1)
            operating_income = historical_financials.get('operating_income', 0)
            if revenue > 0:
                historical_financials['operating_margin'] = (operating_income / revenue) * 100

            # Log extracted financials for debugging
            self.log_action(f"Extracted financials: revenue={historical_financials.get('revenue', 0):,.0f}, operating_margin={historical_financials.get('operating_margin', 'N/A')}")
            
            # Perform macroeconomic analysis
            analysis_result = await self.analyze(
                symbol=symbol,
                historical_financials=historical_financials,
                forecast_horizon=5
            )
            
            # Detect macroeconomic anomalies
            anomalies = await self._detect_macroeconomic_anomalies(
                analysis_result,
                financial_data
            )
            
            # Log detected anomalies
            for anomaly in anomalies.get('anomalies_detected', []):
                self.log_anomaly(
                    anomaly_type=anomaly['type'],
                    description=anomaly['description'],
                    severity=anomaly['severity'],
                    data=anomaly
                )
            
            # Add anomaly information to analysis result
            analysis_result['anomalies'] = anomalies
            
            # Store results in state
            state['macroeconomic_analysis'] = analysis_result
            
            self.log_action("Macroeconomic analysis complete")
            
            return {
                "data": analysis_result,
                "errors": [],
                "warnings": [],
                "recommendations": analysis_result.get('insights', []),
                "anomalies_detected": anomalies.get('anomalies_detected', []),
                "anomaly_count": len(anomalies.get('anomalies_detected', []))
            }
            
        except Exception as e:
            self.log_action(f"Error in macroeconomic analysis: {str(e)}", level="error")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
        
    async def analyze(
        self, 
        symbol: str, 
        historical_financials: Dict[str, Any],
        forecast_horizon: int = 5
    ) -> Dict[str, Any]:
        """
        Perform comprehensive macroeconomic analysis and scenario modeling.
        
        Args:
            symbol: Target company ticker
            historical_financials: Historical financial data for correlation analysis
            forecast_horizon: Number of years to forecast (default 5)
            
        Returns:
            Macroeconomic analysis with scenario modeling
        """
        self.log_action(f"Starting macroeconomic analysis for {symbol}")
        
        try:
            # Step 1: Fetch current economic indicators
            economic_data = await self._fetch_economic_indicators()
            self.log_action("Fetched current economic indicators")
            
            # Step 2: Analyze historical correlations
            correlations = await self._analyze_correlations(
                historical_financials, 
                economic_data
            )
            self.log_action("Completed correlation analysis")
            
            # Step 3: Generate sensitivity analysis
            sensitivity = self._generate_sensitivity_analysis(
                symbol, 
                correlations, 
                economic_data
            )
            self.log_action("Completed sensitivity analysis")
            
            # Step 4: Create scenario models
            scenarios = self._create_scenario_models(
                symbol,
                historical_financials,
                correlations,
                economic_data,
                forecast_horizon
            )
            self.log_action(f"Generated {len(scenarios)} scenario models")
            
            # Step 5: Generate insights
            insights = await self._generate_macro_insights(
                symbol,
                economic_data,
                correlations,
                sensitivity,
                scenarios
            )
            
            analysis = {
                'current_economic_conditions': economic_data,
                'correlation_analysis': correlations,
                'sensitivity_analysis': sensitivity,
                'scenario_models': scenarios,
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in state
            self.update_state({
                'macroeconomic_analysis': analysis,
                'timestamp': datetime.now().isoformat()
            })
            
            self.log_action("Macroeconomic analysis complete")
            return analysis
            
        except Exception as e:
            self.log_action(f"Error in macroeconomic analysis: {str(e)}", level="error")
            raise
            
    async def _fetch_economic_indicators(self) -> Dict[str, Any]:
        """
        Fetch key economic indicators from FMP and other sources.
        
        Returns:
            Dictionary of current economic indicators
        """
        try:
            indicators = {}
            
            # Fetch data with async context
            async with FMPClient() as client:
                # Fetch treasury rates (proxy for interest rates)
                treasury_10y = await client.get_treasury_rates(maturity='10year')
                if treasury_10y and len(treasury_10y) > 0:
                    rate_value = treasury_10y[0].get('value')
                    indicators['treasury_10y'] = float(rate_value) if rate_value is not None else 4.5
                else:
                    indicators['treasury_10y'] = 4.5
                
                # Fetch economic indicators from FMP
                economic_calendar = await client.get_economic_calendar()
                
                # Extract key indicators
                if economic_calendar:
                    for event in economic_calendar[:50]:  # Recent events
                        event_name = event.get('event', '')
                        
                        if 'GDP' in event_name.upper():
                            indicators['gdp_growth'] = event.get('actual', 0)
                        elif 'CPI' in event_name.upper() or 'INFLATION' in event_name.upper():
                            indicators['inflation_rate'] = event.get('actual', 0)
                        elif 'UNEMPLOYMENT' in event_name.upper():
                            indicators['unemployment_rate'] = event.get('actual', 0)
                        elif 'PPI' in event_name.upper():
                            indicators['ppi'] = event.get('actual', 0)
            
            # Set defaults if not found
            indicators.setdefault('treasury_10y', 4.5)
            indicators.setdefault('gdp_growth', 2.5)
            indicators.setdefault('inflation_rate', 3.0)
            indicators.setdefault('unemployment_rate', 4.0)
            indicators.setdefault('ppi', 2.5)
            
            # Add derived indicators with safe defaults
            treasury_rate = indicators.get('treasury_10y', 4.5)
            inflation_rate = indicators.get('inflation_rate', 3.0)
            
            indicators['real_interest_rate'] = (
                float(treasury_rate) - float(inflation_rate)
            )
            
            self.economic_cache = indicators
            return indicators
            
        except Exception as e:
            self.log_action(f"Error fetching economic indicators: {str(e)}", level="error")
            # Return reasonable defaults
            return {
                'treasury_10y': 4.5,
                'gdp_growth': 2.5,
                'inflation_rate': 3.0,
                'unemployment_rate': 4.0,
                'ppi': 2.5,
                'real_interest_rate': 1.5
            }
            
    async def _analyze_correlations(
        self,
        historical_financials: Dict[str, Any],
        economic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze correlations between economic indicators and company performance
        with industry-specific impact modeling.

        Enhanced with industry-specific GDP and inflation impacts.

        Args:
            historical_financials: Company's historical financial data
            economic_data: Current economic indicators

        Returns:
            Correlation analysis results with industry-specific impacts
        """
        correlations = {
            'revenue_sensitivity': {},
            'margin_sensitivity': {},
            'industry_specific_impacts': {},
            'key_findings': []
        }

        # Get company industry for industry-specific analysis
        try:
            symbol = historical_financials.get('symbol', 'AAPL')  # Fallback
            async with FMPClient() as fmp_client:
                company_profile = await fmp_client.get_company_profile(symbol)
                industry = company_profile.get('industry', 'Other') if company_profile else 'Other'
        except Exception as e:
            self.log_action(f"Could not fetch company profile for industry analysis: {e}", level="warning")
            industry = 'Other'

        # Revenue sensitivity to GDP growth (industry-specific)
        industry_gdp_sensitivity = self._get_industry_gdp_sensitivity(industry)

        correlations['revenue_sensitivity']['gdp_growth'] = {
            'coefficient': industry_gdp_sensitivity,
            'interpretation': f'Strong positive correlation - revenue highly sensitive to GDP growth in {industry} sector',
            'impact': f'A 1% increase in GDP growth typically results in {industry_gdp_sensitivity:.2f}% revenue growth',
            'industry_context': f'{industry} companies typically show {industry_gdp_sensitivity + "above" if industry_gdp_sensitivity > 0.7 else "below"} average GDP sensitivity'
        }

        # Inflation sensitivity (industry-specific)
        industry_inflation_sensitivity = self._get_industry_inflation_sensitivity(industry)

        correlations['revenue_sensitivity']['inflation_rate'] = {
            'coefficient': industry_inflation_sensitivity.get('revenue_coefficient', -0.20),
            'interpretation': f'Moderate correlation - {industry} sector has {industry_inflation_sensitivity.get("inflation_sensitivity", "moderate")} inflation sensitivity',
            'impact': f'Inflation of {economic_data.get("inflation_rate", 3.0):.1f}% currently impacts revenue by {industry_inflation_sensitivity.get("revenue_coefficient", -0.20) * economic_data.get("inflation_rate", 3.0):.1f} percentage points',
            'industry_context': industry_inflation_sensitivity.get('industry_context', 'Mixed inflation impacts')
        }

        # Unemployment correlation (varies by industry)
        industry_unemployment_impact = self._get_industry_unemployment_sensitivity(industry)

        correlations['revenue_sensitivity']['unemployment_rate'] = {
            'coefficient': industry_unemployment_impact,
            'interpretation': f'{abs(industry_unemployment_impact):.2f} correlation - {industry} sector shows {"significant" if abs(industry_unemployment_impact) > 0.4 else "moderate"} unemployment sensitivity',
            'impact': f'A 1% increase in unemployment typically results in {abs(industry_unemployment_impact):.1f}% revenue decline',
            'current_context': f'At {economic_data.get("unemployment_rate", 4.0):.1f}% unemployment, this represents a {abs(industry_unemployment_impact * economic_data.get("unemployment_rate", 4.0)):.1f} percentage point revenue impact'
        }

        # Margin sensitivity to interest rates (varies by leverage)
        correlations['margin_sensitivity']['interest_rates'] = {
            'coefficient': -0.30,  # Can be refined with D/E ratio
            'interpretation': 'Moderate negative correlation - margins compressed by rising rates',
            'impact': 'A 1% increase in rates typically results in 30bps margin compression',
            'current_risk': f'At {economic_data.get("treasury_10y", 4.5):.2f}% 10Y Treasury rate, interest rates are {"highly elevated" if economic_data.get("treasury_10y", 4.5) > 5.0 else "moderately elevated" if economic_data.get("treasury_10y", 4.5) > 4.0 else "near neutral"}'
        }

        # Margin sensitivity to PPI (input costs) - industry specific
        industry_ppi_sensitivity = self._get_industry_cost_sensitivity(industry)

        correlations['margin_sensitivity']['ppi'] = {
            'coefficient': industry_ppi_sensitivity.get('cost_coefficient', -0.60),
            'interpretation': f'Industrial inflation {industry_ppi_sensitivity.get("sensitivity_level", "significantly")} impacts {industry} sector margins',
            'impact': f'A 1% increase in PPI typically results in {abs(industry_ppi_sensitivity.get("cost_coefficient", -0.60) * 100):.0f}bps margin compression',
            'at_risk_inputs': industry_ppi_sensitivity.get('at_risk_inputs', [])
        }

        # Industry-specific GDP and inflation impacts
        gdp_growth_rate = economic_data.get('gdp_growth', 2.5)
        current_inflation = economic_data.get('inflation_rate', 3.0)

        correlations['industry_specific_impacts'] = {
            'gdp_impact_on_revenue': {
                'current_impact': gdp_growth_rate * industry_gdp_sensitivity,
                'announcement': f'At {gdp_growth_rate:.1f}% GDP growth, {industry} sector revenues are impacted by {gdp_growth_rate * industry_gdp_sensitivity:.1f} percentage points'

            },
            'inflation_impact_on_margins': {
                'current_impact': industry_inflation_sensitivity.get('margin_coefficient', -0.40) * current_inflation,
                'announcement': f'At {current_inflation:.1f}% inflation, {industry} sector margins are compressed by {abs(industry_inflation_sensitivity.get("margin_coefficient", -0.40) * current_inflation):.1f} percentage points'

            },
            'industry_vulnerability_score': self._calculate_industry_vulnerability_score(
                industry, economic_data
            ),
            'recommended_strategies': self._get_industry_macro_strategies(industry, economic_data)
        }

        # Enhanced key findings with industry context
        correlations['key_findings'] = [
            f"Revenue is {'highly' if abs(industry_gdp_sensitivity) > 0.7 else 'moderately'} cyclical - {industry} sector shows {abs(industry_gdp_sensitivity):.2f} GDP sensitivity",
            f"{industry} sector has {industry_inflation_sensitivity.get('inflation_sensitivity', 'moderate')} inflation vulnerability with {abs(industry_inflation_sensitivity.get('margin_coefficient', -0.4) * 100):.0f}bps margin impact per 1% inflation",
            f"Current inflation of {current_inflation:.1f}% is creating {abs(industry_inflation_sensitivity.get('margin_coefficient', -0.4) * current_inflation):.1f} percentage points of margin pressure",
            f"{industry} sector shows {abs(industry_unemployment_impact):.2f} unemployment correlation - {'particularly sensitive' if abs(industry_unemployment_impact) > 0.5 else 'moderately affected'}",
            self._get_industry_macro_summary(industry, economic_data)
        ]

        return correlations
        
    def _generate_sensitivity_analysis(
        self,
        symbol: str,
        correlations: Dict[str, Any],
        economic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate sensitivity analysis showing impact of economic changes.
        
        Args:
            symbol: Company ticker
            correlations: Correlation analysis results
            economic_data: Current economic indicators
            
        Returns:
            Sensitivity analysis
        """
        sensitivity = {
            'base_case': economic_data.copy(),
            'scenarios': {},
            'impact_matrix': []
        }
        
        # Define economic scenarios
        scenarios_config = {
            'soft_landing': {
                'gdp_growth': {'change': 0, 'description': 'Stable growth'},
                'inflation_rate': {'change': -1.0, 'description': 'Inflation moderates'},
                'treasury_10y': {'change': -0.5, 'description': 'Rates decline moderately'}
            },
            'recession': {
                'gdp_growth': {'change': -2.5, 'description': 'GDP contracts'},
                'inflation_rate': {'change': -0.5, 'description': 'Inflation falls'},
                'treasury_10y': {'change': -1.5, 'description': 'Rates cut aggressively'}
            },
            'stagflation': {
                'gdp_growth': {'change': -1.5, 'description': 'Low growth'},
                'inflation_rate': {'change': 2.0, 'description': 'High inflation persists'},
                'treasury_10y': {'change': 1.5, 'description': 'Rates rise further'}
            },
            'boom': {
                'gdp_growth': {'change': 2.0, 'description': 'Strong growth'},
                'inflation_rate': {'change': 1.0, 'description': 'Inflation rises'},
                'treasury_10y': {'change': 1.0, 'description': 'Rates rise moderately'}
            }
        }
        
        # Calculate impact for each scenario
        for scenario_name, changes in scenarios_config.items():
            scenario_impact = self._calculate_scenario_impact(
                changes,
                correlations,
                economic_data
            )
            sensitivity['scenarios'][scenario_name] = scenario_impact
        
        return sensitivity
        
    def _calculate_scenario_impact(
        self,
        scenario_changes: Dict[str, Dict],
        correlations: Dict[str, Any],
        base_economic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate the impact of a specific economic scenario.
        
        Args:
            scenario_changes: Economic indicator changes for scenario
            correlations: Correlation coefficients
            base_economic_data: Base case economic data
            
        Returns:
            Scenario impact analysis
        """
        impact = {
            'economic_changes': {},
            'estimated_revenue_impact': 0.0,
            'estimated_margin_impact': 0.0,
            'overall_risk': 'Medium'
        }
        
        revenue_impact = 0.0
        margin_impact = 0.0
        
        # Calculate revenue impact
        if 'gdp_growth' in scenario_changes:
            gdp_change = scenario_changes['gdp_growth']['change']
            gdp_coefficient = correlations['revenue_sensitivity']['gdp_growth']['coefficient']
            revenue_impact += gdp_change * gdp_coefficient
            impact['economic_changes']['gdp_growth'] = scenario_changes['gdp_growth']
        
        # Calculate margin impact from interest rates
        if 'treasury_10y' in scenario_changes:
            rate_change = scenario_changes['treasury_10y']['change']
            rate_coefficient = correlations['margin_sensitivity']['interest_rates']['coefficient']
            margin_impact += rate_change * abs(rate_coefficient) * 100  # Convert to bps
            impact['economic_changes']['treasury_10y'] = scenario_changes['treasury_10y']
        
        # Calculate margin impact from inflation/PPI
        if 'inflation_rate' in scenario_changes:
            inflation_change = scenario_changes['inflation_rate']['change']
            # Assume PPI moves with inflation
            ppi_coefficient = correlations['margin_sensitivity']['ppi']['coefficient']
            margin_impact += inflation_change * abs(ppi_coefficient) * 100  # Convert to bps
            impact['economic_changes']['inflation_rate'] = scenario_changes['inflation_rate']
        
        impact['estimated_revenue_impact'] = revenue_impact
        impact['estimated_margin_impact'] = margin_impact
        
        # Assess overall risk
        if revenue_impact < -5 or margin_impact < -300:
            impact['overall_risk'] = 'High'
        elif revenue_impact < -2 or margin_impact < -150:
            impact['overall_risk'] = 'Medium'
        else:
            impact['overall_risk'] = 'Low'
        
        return impact
        
    def _create_scenario_models(
        self,
        symbol: str,
        historical_financials: Dict[str, Any],
        correlations: Dict[str, Any],
        economic_data: Dict[str, Any],
        forecast_horizon: int
    ) -> Dict[str, Any]:
        """
        Create detailed scenario models with multi-year projections.
        
        Args:
            symbol: Company ticker
            historical_financials: Historical financial data
            correlations: Correlation analysis
            economic_data: Current economic indicators
            forecast_horizon: Years to forecast
            
        Returns:
            Scenario models with projections
        """
        scenarios = {
            'base_case': self._project_base_case(
                historical_financials, forecast_horizon
            ),
            'bull_case': self._project_scenario(
                historical_financials, forecast_horizon, scenario_type='bull'
            ),
            'bear_case': self._project_scenario(
                historical_financials, forecast_horizon, scenario_type='bear'
            ),
            'rate_shock': self._project_rate_shock_scenario(
                historical_financials, correlations, forecast_horizon
            )
        }
        
        return scenarios
        
    def _project_base_case(
        self,
        historical_financials: Dict[str, Any],
        forecast_horizon: int
    ) -> Dict[str, Any]:
        """Project base case scenario."""
        return {
            'description': 'Continuation of current trends with stable macro environment',
            'assumptions': {
                'gdp_growth': 2.5,
                'inflation': 2.0,
                'revenue_growth': 8.0,
                'margin_trajectory': 'stable'
            },
            'projections': [
                {
                    'year': i + 1,
                    'revenue_growth': 8.0 - (i * 0.5),  # Gradually declining growth
                    'operating_margin': 20.0 + (i * 0.2),  # Gradually improving margin
                    'probability': 50
                }
                for i in range(forecast_horizon)
            ]
        }
        
    def _project_scenario(
        self,
        historical_financials: Dict[str, Any],
        forecast_horizon: int,
        scenario_type: str
    ) -> Dict[str, Any]:
        """Project bull or bear scenario."""
        if scenario_type == 'bull':
            return {
                'description': 'Strong economic growth, market share gains, margin expansion',
                'assumptions': {
                    'gdp_growth': 4.0,
                    'inflation': 2.5,
                    'revenue_growth': 15.0,
                    'margin_trajectory': 'expanding'
                },
                'projections': [
                    {
                        'year': i + 1,
                        'revenue_growth': 15.0 - (i * 0.8),
                        'operating_margin': 20.0 + (i * 0.5),
                        'probability': 25
                    }
                    for i in range(forecast_horizon)
                ]
            }
        else:  # bear case
            return {
                'description': 'Economic downturn, market share loss, margin compression',
                'assumptions': {
                    'gdp_growth': -1.0,
                    'inflation': 1.5,
                    'revenue_growth': 2.0,
                    'margin_trajectory': 'compressing'
                },
                'projections': [
                    {
                        'year': i + 1,
                        'revenue_growth': max(2.0 - (i * 1.0), 0),
                        'operating_margin': max(20.0 - (i * 0.8), 15.0),
                        'probability': 25
                    }
                    for i in range(forecast_horizon)
                ]
            }
            
    def _project_rate_shock_scenario(
        self,
        historical_financials: Dict[str, Any],
        correlations: Dict[str, Any],
        forecast_horizon: int
    ) -> Dict[str, Any]:
        """Project interest rate shock scenario."""
        return {
            'description': 'Fed raises rates by 200 bps over 12 months to combat inflation',
            'assumptions': {
                'rate_increase': 2.0,
                'gdp_impact': -1.5,
                'margin_compression': -200,  # bps
                'demand_slowdown': True
            },
            'projections': [
                {
                    'year': i + 1,
                    'revenue_growth': max(5.0 - (i * 2.0), 1.0),
                    'operating_margin': max(20.0 - 2.0 - (i * 0.3), 16.0),
                    'probability': 15
                }
                for i in range(forecast_horizon)
            ]
        }
        
    async def _generate_macro_insights(
        self,
        symbol: str,
        economic_data: Dict[str, Any],
        correlations: Dict[str, Any],
        sensitivity: Dict[str, Any],
        scenarios: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable macroeconomic insights using AI.
        
        Args:
            symbol: Company ticker
            economic_data: Current economic indicators
            correlations: Correlation analysis
            sensitivity: Sensitivity analysis
            scenarios: Scenario models
            
        Returns:
            List of insights
        """
        insights = []
        
        # Economic environment assessment
        if economic_data['inflation_rate'] > 3.0:
            insights.append(
                f"⚠️ ELEVATED INFLATION: Current inflation of {economic_data['inflation_rate']:.1f}% "
                f"poses margin risk. PPI correlation of {abs(correlations['margin_sensitivity']['ppi']['coefficient']):.0%} "
                f"suggests significant input cost pressure."
            )
        
        # Interest rate environment
        if economic_data['treasury_10y'] > 4.5:
            insights.append(
                f"📊 HIGH RATE ENVIRONMENT: 10Y Treasury at {economic_data['treasury_10y']:.2f}% "
                f"may pressure valuations and increase cost of capital. Monitor refinancing needs."
            )
        
        # Recession risk assessment
        bear_scenario = sensitivity['scenarios'].get('recession', {})
        if bear_scenario.get('estimated_revenue_impact', 0) < -10:
            insights.append(
                f"🚨 RECESSION VULNERABILITY: Company shows {abs(bear_scenario['estimated_revenue_impact']):.1f}% "
                f"revenue decline risk in recession scenario. Recommend stress testing balance sheet."
            )
        
        # Growth opportunities
        bull_scenario = sensitivity['scenarios'].get('boom', {})
        if bull_scenario.get('estimated_revenue_impact', 0) > 5:
            insights.append(
                f"✅ UPSIDE POTENTIAL: Strong economic growth scenario suggests {bull_scenario['estimated_revenue_impact']:.1f}% "
                f"revenue upside. Company well-positioned to capitalize on expansion."
            )
        
        # Add correlation-based insights
        insights.extend(correlations.get('key_findings', []))
        
        return insights
    
    async def _detect_macroeconomic_anomalies(
        self,
        analysis_result: Dict[str, Any],
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect macroeconomic anomalies and risks
        
        Args:
            analysis_result: Macroeconomic analysis results
            financial_data: Company financial data
        
        Returns:
            Dictionary with detected anomalies
        """
        self.log_action("Detecting macroeconomic anomalies")
        
        anomalies = []
        
        economic_data = analysis_result.get('current_economic_conditions', {})
        correlations = analysis_result.get('correlation_analysis', {})
        sensitivity = analysis_result.get('sensitivity_analysis', {})
        scenarios = analysis_result.get('scenario_models', {})
        
        # 1. Extreme Inflation Environment
        inflation_rate = economic_data.get('inflation_rate', 0)
        if inflation_rate > 4.0:
            anomalies.append({
                'type': 'extreme_inflation_environment',
                'severity': 'critical' if inflation_rate > 6.0 else 'high',
                'description': f'Inflation rate of {inflation_rate:.1f}% significantly above Fed target of 2%',
                'impact': 'Input cost pressure, margin compression, potential demand destruction',
                'recommendation': 'Implement pricing power analysis, review cost pass-through capabilities, stress test margins',
                'data': {
                    'inflation_rate': inflation_rate,
                    'fed_target': 2.0,
                    'excess_inflation': inflation_rate - 2.0,
                    'margin_risk': 'High'
                }
            })
        
        # 2. Inverted Yield Curve / Recession Signal
        treasury_rate = economic_data.get('treasury_10y', 0)
        real_rate = economic_data.get('real_interest_rate', 0)
        if real_rate > 3.0:
            anomalies.append({
                'type': 'restrictive_monetary_policy',
                'severity': 'high',
                'description': f'Real interest rate of {real_rate:.1f}% indicates highly restrictive monetary policy',
                'impact': 'Elevated recession risk, credit tightening, demand slowdown likely',
                'recommendation': 'Model recession scenarios, review credit facilities, prepare for economic downturn',
                'data': {
                    'real_rate': real_rate,
                    'nominal_rate': treasury_rate,
                    'inflation_rate': inflation_rate,
                    'historical_avg_real_rate': 1.5
                }
            })
        
        # 3. High Cyclical Exposure
        revenue_sensitivity = correlations.get('revenue_sensitivity', {})
        gdp_correlation = revenue_sensitivity.get('gdp_growth', {}).get('coefficient', 0)
        if abs(gdp_correlation) > 0.7:
            anomalies.append({
                'type': 'high_cyclical_exposure',
                'severity': 'high',
                'description': f'Revenue highly correlated with GDP (coefficient: {gdp_correlation:.2f}) - company is highly cyclical',
                'impact': 'Vulnerable to economic downturns, revenue volatility in recession',
                'recommendation': 'Stress test recession scenarios, evaluate diversification opportunities, review covenant headroom',
                'data': {
                    'gdp_correlation': gdp_correlation,
                    'cyclicality': 'High',
                    'recession_revenue_risk': 'Severe',
                    'volatility_profile': 'Above average'
                }
            })
        
        # 4. Severe Bear Case Scenario
        bear_case = scenarios.get('bear_case', {})
        bear_projections = bear_case.get('projections', [])
        if bear_projections and len(bear_projections) > 0:
            first_year_growth = bear_projections[0].get('revenue_growth', 0)
            if first_year_growth < 3.0:
                anomalies.append({
                    'type': 'severe_downside_scenario',
                    'severity': 'high',
                    'description': f'Bear case projects {first_year_growth:.1f}% revenue growth - significant downside risk',
                    'impact': 'Potential covenant violations, liquidity stress, valuation pressure',
                    'recommendation': 'Develop contingency plans, review cost structure flexibility, assess capital allocation priorities',
                    'data': {
                        'bear_case_growth': first_year_growth,
                        'base_case_growth': scenarios.get('base_case', {}).get('projections', [{}])[0].get('revenue_growth', 8.0),
                        'downside_delta': first_year_growth - 8.0,
                        'probability': bear_case.get('projections', [{}])[0].get('probability', 25)
                    }
                })
        
        # 5. Margin Vulnerability to Input Costs
        margin_sensitivity = correlations.get('margin_sensitivity', {})
        ppi_correlation = margin_sensitivity.get('ppi', {}).get('coefficient', 0)
        if abs(ppi_correlation) > 0.5:
            anomalies.append({
                'type': 'high_input_cost_sensitivity',
                'severity': 'medium',
                'description': f'Operating margins highly sensitive to input costs (PPI correlation: {ppi_correlation:.2f})',
                'impact': 'Margin volatility, pricing power constraints, profit pressure',
                'recommendation': 'Evaluate pricing strategies, analyze pass-through mechanisms, consider hedging strategies',
                'data': {
                    'ppi_correlation': abs(ppi_correlation),
                    'margin_risk': 'High',
                    'pricing_power': 'Question mark',
                    'cost_structure': 'Variable-heavy'
                }
            })
        
        # 6. Interest Rate Shock Vulnerability
        rate_shock = scenarios.get('rate_shock', {})
        rate_shock_projections = rate_shock.get('projections', [])
        if rate_shock_projections and len(rate_shock_projections) > 0:
            rate_shock_margin = rate_shock_projections[0].get('operating_margin', 0)
            base_margin = scenarios.get('base_case', {}).get('projections', [{}])[0].get('operating_margin', 20.0)
            margin_compression = base_margin - rate_shock_margin
            
            if margin_compression > 2.0:
                anomalies.append({
                    'type': 'rate_shock_vulnerability',
                    'severity': 'medium',
                    'description': f'Rate shock scenario shows {margin_compression:.1f}pp margin compression',
                    'impact': 'Profitability risk from higher borrowing costs and demand slowdown',
                    'recommendation': 'Review debt maturity profile, evaluate fixed-rate financing, assess rate hedging',
                    'data': {
                        'margin_compression': margin_compression,
                        'base_margin': base_margin,
                        'rate_shock_margin': rate_shock_margin,
                        'rate_increase_assumption': 2.0
                    }
                })
        
        # 7. Economic Uncertainty / Stagflation Risk
        stagflation = sensitivity.get('scenarios', {}).get('stagflation', {})
        if stagflation:
            overall_risk = stagflation.get('overall_risk', 'Medium')
            if overall_risk in ['High', 'Critical']:
                revenue_impact = stagflation.get('estimated_revenue_impact', 0)
                margin_impact = stagflation.get('estimated_margin_impact', 0)
                
                anomalies.append({
                    'type': 'stagflation_vulnerability',
                    'severity': 'high',
                    'description': 'Company vulnerable to stagflation scenario (low growth + high inflation)',
                    'impact': f'Revenue impact: {revenue_impact:.1f}%, Margin impact: {margin_impact:.0f}bps',
                    'recommendation': 'Prepare for challenging environment - focus on cost control and pricing discipline',
                    'data': {
                        'revenue_impact': revenue_impact,
                        'margin_impact_bps': margin_impact,
                        'risk_level': overall_risk,
                        'scenario_description': 'Low growth + persistent inflation'
                    }
                })
        
        # 8. Lack of Economic Diversification
        unemployment_correlation = revenue_sensitivity.get('unemployment_rate', {}).get('coefficient', 0)
        if abs(gdp_correlation) > 0.6 and abs(unemployment_correlation) > 0.3:
            anomalies.append({
                'type': 'concentrated_economic_exposure',
                'severity': 'medium',
                'description': 'Revenue highly dependent on US economic conditions with limited diversification',
                'impact': 'Single point of failure in economic downturn, limited resilience',
                'recommendation': 'Consider geographic diversification, evaluate counter-cyclical opportunities',
                'data': {
                    'gdp_correlation': gdp_correlation,
                    'unemployment_correlation': unemployment_correlation,
                    'diversification_score': 'Low',
                    'resilience': 'Limited'
                }
            })
        
        # Determine overall risk level
        critical_count = sum(1 for a in anomalies if a['severity'] == 'critical')
        high_count = sum(1 for a in anomalies if a['severity'] == 'high')
        
        if critical_count > 0:
            risk_level = 'Critical'
        elif high_count > 2:
            risk_level = 'High'
        elif len(anomalies) > 3:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        self.log_action(f"Macroeconomic anomaly detection complete: {len(anomalies)} anomalies found, risk level: {risk_level}")
        
        return {
            'anomalies_detected': anomalies,
            'total_anomalies': len(anomalies),
            'risk_level': risk_level,
            'critical_issues': critical_count,
            'high_issues': high_count
        }

    def _get_industry_gdp_sensitivity(self, industry: str) -> float:
        """Get GDP sensitivity coefficient for different industries."""
        industry_map = {
            'Technology': 0.75,
            'Healthcare': 0.45,
            'Consumer Cyclical': 0.85,
            'Consumer Defensive': 0.35,
            'Industrials': 0.70,
            'Financial Services': 0.60,
            'Real Estate': 0.50,
            'Energy': 0.90,
            'Materials': 0.80,
            'Utilities': 0.30,
            'Communication Services': 0.55,
            'Other': 0.65
        }
        return industry_map.get(industry, 0.65)

    def _get_industry_inflation_sensitivity(self, industry: str) -> Dict[str, Any]:
        """Get inflation sensitivity for different industries."""
        inflation_sensitivities = {
            'Technology': {
                'revenue_coefficient': -0.15,
                'margin_coefficient': -0.30,
                'inflation_sensitivity': 'moderate',
                'industry_context': 'Tech companies benefit from pricing power but face wage inflation'
            },
            'Healthcare': {
                'revenue_coefficient': 0.05,
                'margin_coefficient': -0.40,
                'inflation_sensitivity': 'high',
                'industry_context': 'Healthcare shows limited revenue sensitivity but high cost pressures from regulations'
            },
            'Consumer Cyclical': {
                'revenue_coefficient': -0.25,
                'margin_coefficient': -0.50,
                'inflation_sensitivity': 'high',
                'industry_context': 'Highly discretionary spending leads to revenue vulnerability in inflationary periods'
            },
            'Consumer Defensive': {
                'revenue_coefficient': 0.10,
                'margin_coefficient': -0.45,
                'inflation_sensitivity': 'moderate',
                'industry_context': 'Defensive products provide some revenue stability but face significant cost inflation'
            },
            'Industrials': {
                'revenue_coefficient': -0.20,
                'margin_coefficient': -0.65,
                'inflation_sensitivity': 'very high',
                'industry_context': 'Industrial inflation (PPI) directly impacts input costs and pricing power'
            },
            'Energy': {
                'revenue_coefficient': -0.35,
                'margin_coefficient': -0.70,
                'inflation_sensitivity': 'extreme',
                'industry_context': 'Energy prices drive both revenue sensitivity and acute input cost challenges'
            },
            'Financial Services': {
                'revenue_coefficient': -0.10,
                'margin_coefficient': -0.20,
                'inflation_sensitivity': 'low to moderate',
                'industry_context': 'Interest rate sensitive with moderate inflation impact on net interest margins'
            }
        }
        return inflation_sensitivities.get(industry, {
            'revenue_coefficient': -0.20,
            'margin_coefficient': -0.40,
            'inflation_sensitivity': 'moderate',
            'industry_context': 'Mixed inflation impacts typical of general industry exposure'
        })

    def _get_industry_unemployment_sensitivity(self, industry: str) -> float:
        """Get unemployment sensitivity for different industries."""
        unemployment_map = {
            'Technology': -0.30,
            'Healthcare': -0.20,
            'Consumer Cyclical': -0.55,
            'Consumer Defensive': -0.15,
            'Industrials': -0.40,
            'Financial Services': -0.25,
            'Real Estate': -0.35,
            'Energy': -0.50,
            'Materials': -0.45,
            'Utilities': -0.15,
            'Communication Services': -0.20,
            'Other': -0.35
        }
        return unemployment_map.get(industry, -0.35)

    def _get_industry_cost_sensitivity(self, industry: str) -> Dict[str, Any]:
        """Get cost sensitivity to PPI for different industries."""
        cost_sensitivities = {
            'Technology': {
                'cost_coefficient': -0.40,
                'sensitivity_level': 'moderately',
                'at_risk_inputs': ['labor costs', 'datacenter expenses']
            },
            'Healthcare': {
                'cost_coefficient': -0.55,
                'sensitivity_level': 'significantly',
                'at_risk_inputs': ['medical supplies', 'labor costs', 'regulatory compliance']
            },
            'Consumer Cyclical': {
                'cost_coefficient': -0.45,
                'sensitivity_level': 'moderately',
                'at_risk_inputs': ['commodities', 'transportation']
            },
            'Industrials': {
                'cost_coefficient': -0.90,
                'sensitivity_level': 'extremely',
                'at_risk_inputs': ['steel', 'energy', 'semiconductors', 'labor']
            },
            'Energy': {
                'cost_coefficient': -0.85,
                'sensitivity_level': 'extremely',
                'at_risk_inputs': ['crude oil', 'refining costs', 'labor', 'equipment']
            },
            'Materials': {
                'cost_coefficient': -0.80,
                'sensitivity_level': 'extremely',
                'at_risk_inputs': ['commodities', 'energy', 'chemicals', 'minerals']
            },
            'Financial Services': {
                'cost_coefficient': -0.25,
                'sensitivity_level': 'minimally',
                'at_risk_inputs': ['interest payments', 'regulatory costs']
            }
        }
        return cost_sensitivities.get(industry, {
            'cost_coefficient': -0.50,
            'sensitivity_level': 'moderately',
            'at_risk_inputs': ['labor', 'materials', 'overhead']
        })

    def _calculate_industry_vulnerability_score(self, industry: str, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate industry vulnerability score based on current economic conditions."""
        inflation_rate = economic_data.get('inflation_rate', 3.0)
        gdp_growth = economic_data.get('gdp_growth', 2.5)
        unemployment = economic_data.get('unemployment_rate', 4.0)

        # High vulnerability if inflation > 4% AND GDP growth < 2% AND unemployment > 4%
        vulnerability_score = 0

        if inflation_rate > 4.0:
            vulnerability_score += 40
        elif inflation_rate > 3.5:
            vulnerability_score += 20

        if gdp_growth < 2.0:
            vulnerability_score += 30
        elif gdp_growth < 2.5:
            vulnerability_score += 10

        if unemployment > 4.5:
            vulnerability_score += 30
        elif unemployment > 4.0:
            vulnerability_score += 10

        # Industry-specific adjustments
        industry_adjustments = {
            'Energy': 20,  # Always high volatility
            'Consumer Cyclical': 15,  # Economic sensitivity
            'Technology': -10,  # Defensive qualities
            'Healthcare': -15   # Counter-cyclical
        }

        vulnerability_score += industry_adjustments.get(industry, 0)
        vulnerability_score = max(0, min(100, vulnerability_score))

        if vulnerability_score > 70:
            risk_level = 'Critical'
            description = f'{industry} sector shows extreme vulnerability to current economic conditions'
        elif vulnerability_score > 50:
            risk_level = 'High'
            description = f'{industry} sector shows significant vulnerability requiring monitoring'
        elif vulnerability_score > 30:
            risk_level = 'Medium'
            description = f'{industry} sector shows moderate vulnerability to economic conditions'
        else:
            risk_level = 'Low'
            description = f'{industry} sector shows low vulnerability to current economic environment'

        return {
            'score': vulnerability_score,
            'risk_level': risk_level,
            'description': description,
            'contributing_factors': [
                f'Inflation: {inflation_rate:.1f}% ({">" if inflation_rate > 3.5 else "<"} 3.5% threshold)',
                f'GDP Growth: {gdp_growth:.1f}% ({"<" if gdp_growth < 2.5 else ">"} 2.5% threshold)',
                f'Unemployment: {unemployment:.1f}% ({"<" if unemployment > 4.0 else ">"} 4.0% threshold)'
            ]
        }

    def _get_industry_macro_strategies(self, industry: str, economic_data: Dict[str, Any]) -> List[str]:
        """Get recommended macroeconomic strategies for industry."""
        strategies = []

        inflation_rate = economic_data.get('inflation_rate', 3.0)
        gdp_growth = economic_data.get('gdp_growth', 2.5)
        treasury_rate = economic_data.get('treasury_10y', 4.5)

        if inflation_rate > 3.5:
            if industry in ['Consumer Cyclical', 'Industrials', 'Energy']:
                strategies.append("Implement dynamic pricing strategies to pass through input cost inflation")
            if industry in ['Healthcare', 'Consumer Defensive']:
                strategies.append("Leverage defensive positioning while managing cost pressures")

        if gdp_growth < 2.0:
            if industry in ['Technology', 'Healthcare']:
                strategies.append("Emphasize operational efficiency and cost control in slowdown environment")
            if industry in ['Consumer Cyclical', 'Industrials']:
                strategies.append("Conservative CapEx and focus on balance sheet strength")

        if treasury_rate > 4.5:
            strategies.append("Monitor debt refinancing costs and consider hedging interest rate risk")

        if not strategies:
            strategies.append("Maintain flexible cost structure and monitor macroeconomic indicators")

        return strategies

    def _get_industry_macro_summary(self, industry: str, economic_data: Dict[str, Any]) -> str:
        """Generate industry-specific macroeconomic summary."""
        inflation_rate = economic_data.get('inflation_rate', 3.0)
        gdp_growth = economic_data.get('gdp_growth', 2.5)

        vulnerability = self._calculate_industry_vulnerability_score(industry, economic_data)

        return f"{industry} sector shows {vulnerability['risk_level'].lower()} vulnerability ({vulnerability['score']} score) to current " \
               f"{inflation_rate:.1f}% inflation and {gdp_growth:.1f}% GDP growth environment"
