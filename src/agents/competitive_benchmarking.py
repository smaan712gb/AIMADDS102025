"""
Competitive Benchmarking Agent - "The Rival"

This agent provides superhuman competitive intelligence by analyzing the target company
in the context of its peers and industry sector. It never looks at a company in isolation,
always providing comparative context that human analysts would take weeks to compile.

Revolutionary Capabilities:
- Parallel multi-company analysis at scale
- Real-time peer performance benchmarking
- Sector-wide trend identification
- Market share and competitive position analysis
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import statistics

from .base_agent import BaseAgent
from ..integrations.fmp_client import FMPClient


class CompetitiveBenchmarkingAgent(BaseAgent):
    """
    Agent responsible for competitive intelligence and peer benchmarking.
    
    This agent transforms isolated metrics into competitive insights by comparing
    the target company against peers and sector trends in real-time.
    """
    
    def __init__(self):
        super().__init__("competitive_benchmarking")
        self.fmp_client = None
        self.peers_cache = {}
        self.sector_cache = {}
        

    
    async def run(self, state: Any) -> Dict[str, Any]:
        """
        Execute competitive benchmarking (required by BaseAgent).
        This is called when using the standard workflow.
        """
        try:
            self.log_action("Starting competitive benchmarking analysis")
            
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
            
            # Get target financial metrics using smart accessor (prioritizes normalized)
            financial_data_smart = self._get_financial_data_smart(state, prefer_normalized=True)
            
            # Extract key metrics for comparison from normalized data
            income_statement = financial_data_smart.get('income_statement', [{}])
            latest_income = income_statement[0] if income_statement else {}
            
            target_metrics = {
                'revenue': latest_income.get('revenue', 0),
                'revenue_growth': latest_income.get('revenue_growth', 0),
                'gross_margin': latest_income.get('grossProfitMargin', 0) * 100 if latest_income.get('grossProfitMargin') else 0,
                'operating_margin': latest_income.get('operatingIncomeRatio', 0) * 100 if latest_income.get('operatingIncomeRatio') else 0,
                'net_margin': latest_income.get('netIncomeRatio', 0) * 100 if latest_income.get('netIncomeRatio') else 0,
                'roe': latest_income.get('returnOnEquity', 0) * 100 if latest_income.get('returnOnEquity') else 0,
                'roic': latest_income.get('returnOnCapitalEmployed', 0) * 100 if latest_income.get('returnOnCapitalEmployed') else 0,
                'asset_turnover': latest_income.get('assetTurnover', 0),
                'debt_to_equity': latest_income.get('debtEquityRatio', 0),
                'current_ratio': latest_income.get('currentRatio', 0),
                'data_source': financial_data_smart.get('source', 'raw'),
                'data_quality': financial_data_smart.get('quality_score', 'N/A')
            }
            
            # Log data source for transparency
            self.log_action(f"Using {target_metrics['data_source']} data (quality: {target_metrics['data_quality']}) for competitive benchmarking")
            
            # Perform competitive analysis
            analysis_result = await self.analyze(symbol, target_metrics)
            
            # Detect competitive anomalies
            anomalies = await self._detect_competitive_anomalies(
                symbol,
                target_metrics,
                analysis_result
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
            state['competitive_analysis'] = analysis_result
            
            self.log_action("Competitive benchmarking analysis complete")
            
            return {
                "data": analysis_result,
                "errors": [],
                "warnings": [],
                "recommendations": analysis_result.get('strategic_insights', []),
                "anomalies_detected": anomalies.get('anomalies_detected', []),
                "anomaly_count": len(anomalies.get('anomalies_detected', []))
            }
            
        except Exception as e:
            self.log_action(f"Error in competitive benchmarking: {str(e)}", level="error")
            return {
                "data": {},
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
        
    async def analyze(self, symbol: str, target_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive competitive benchmarking analysis.
        
        Args:
            symbol: Target company ticker symbol
            target_metrics: Financial metrics of the target company
            
        Returns:
            Comprehensive competitive analysis with peer comparisons
        """
        self.log_action(f"Starting competitive benchmarking for {symbol}")
        
        try:
            # Step 1: Identify true peers
            peers = await self._identify_peers(symbol)
            self.log_action(f"Identified {len(peers)} peer companies")
            
            # Step 2: Parallel analysis of all peers
            peer_metrics = await self._analyze_peers_parallel(peers)
            self.log_action(f"Completed parallel analysis of {len(peer_metrics)} peers")
            
            # Step 3: Sector-wide analysis
            sector_data = await self._analyze_sector_performance(symbol)
            self.log_action("Completed sector-wide analysis")
            
            # Step 3.5: Extract M&A activity context (NEW)
            ma_context = {}
            try:
                from ..integrations.sec_client import SECClient
                sec_client = SECClient()
                
                self.log_action(f"Checking M&A activity for strategic context...")
                ma_activity = await sec_client.extract_ma_activity(symbol)
                
                if 'error' not in ma_activity and ma_activity.get('has_recent_ma_activity'):
                    ma_context = {
                        'prior_ma_activity': True,
                        'filings_count': ma_activity.get('ma_filings_found', 0),
                        'ma_details': ma_activity.get('ma_activity', []),
                        'strategic_note': 'Company has prior M&A activity - review for strategic patterns and integration capability'
                    }
                    self.log_action(f"✓ M&A activity found: {ma_context['filings_count']} filings")
                else:
                    ma_context = {'prior_ma_activity': False}
                    self.log_action("No recent M&A activity detected")
            except Exception as e:
                self.log_action(f"Error extracting M&A activity: {e}", level="warning")
                ma_context = {'error': str(e)}
            
            # Step 4: Generate competitive insights (with M&A context)
            competitive_analysis = self._generate_competitive_insights(
                symbol, target_metrics, peer_metrics, sector_data
            )
            
            # Add M&A context to analysis
            competitive_analysis['ma_activity_context'] = ma_context
            
            # Store in state
            self.update_state({
                'competitive_benchmarking': competitive_analysis,
                'peers_analyzed': peers,
                'timestamp': datetime.now().isoformat()
            })
            
            self.log_action("Competitive benchmarking analysis complete")
            return competitive_analysis
            
        except Exception as e:
            self.log_action(f"Error in competitive benchmarking: {str(e)}", level="error")
            raise
            
    async def _identify_peers(self, symbol: str) -> List[str]:
        """
        Identify true peer companies using FMP API for ANY company in ANY sector.
        
        Enhanced with peers-bulk endpoint for better peer discovery.
        
        Args:
            symbol: Target company ticker
            
        Returns:
            List of peer ticker symbols
        """
        try:
            async with FMPClient() as client:
                # Method 1: Try FMP peers-bulk endpoint (most comprehensive)
                try:
                    peers_bulk = await client._make_request('peers-bulk')
                    
                    if peers_bulk and isinstance(peers_bulk, list):
                        # Find our symbol in the bulk data
                        for item in peers_bulk:
                            if item.get('symbol') == symbol:
                                peers_list = item.get('peersList', [])
                                if peers_list:
                                    self.log_action(f"Found {len(peers_list)} peers from FMP peers-bulk API")
                                    self.peers_cache[symbol] = peers_list[:10]  # Top 10
                                    return peers_list[:10]
                    
                    self.log_action("peers-bulk returned but symbol not found, trying stock-peers")
                except Exception as bulk_error:
                    self.log_action(f"peers-bulk endpoint failed: {bulk_error}, trying stock-peers")
                
                # Method 2: Try FMP stock-peers endpoint  
                peers_response = await client.get_stock_peers(symbol)
                
                if peers_response and 'peersList' in peers_response:
                    peers_list = peers_response.get('peersList', [])
                    if isinstance(peers_list, list) and len(peers_list) > 0:
                        self.log_action(f"Found {len(peers_list)} peers from FMP stock-peers API")
                        self.peers_cache[symbol] = peers_list
                        return peers_list
                
                # Method 3: Use sector + industry screening as last resort
                self.log_action("Both peers-bulk and stock-peers returned empty, using sector/industry screening")
                profile = await client.get_company_profile(symbol)
                
                if not profile:
                    self.log_action(f"Could not get profile for {symbol}", level="warning")
                    return []
                
                sector = profile.get('sector', '')
                industry = profile.get('industry', '')
                market_cap = profile.get('mktCap', 0)
                
                self.log_action(f"Company: {symbol}, Sector: {sector}, Industry: {industry}, Market Cap: ${market_cap/1e9:.1f}B")
                
                # Screen by sector AND industry for best peer matches
                # Use broader filters to find more peers
                screening_criteria = {
                    'limit': 30,  # Increased from 20
                    'marketCapMoreThan': max(market_cap * 0.05, 100000000) if market_cap > 0 else 100000000,  # More permissive: 5% of cap or $100M
                    'marketCapLowerThan': market_cap * 50 if market_cap > 0 else 10000000000000,  # Up to 50x target cap
                    'isActivelyTrading': 'true'
                }
                
                # Prioritize industry match
                if industry:
                    screening_criteria['industry'] = industry
                    self.log_action(f"Screening by industry: {industry} (broader filters)")
                elif sector:
                    screening_criteria['sector'] = sector
                    self.log_action(f"Screening by sector: {sector} (broader filters)")
                
                try:
                    screened_companies = await client.get_stock_screener(**screening_criteria)
                    
                    if screened_companies and isinstance(screened_companies, list):
                        # Filter out the target company itself
                        peers = [
                            comp.get('symbol')
                            for comp in screened_companies
                            if comp.get('symbol') and comp.get('symbol') != symbol
                        ][:10]  # Limit to top 10 peers
                        
                        if peers:
                            self.log_action(f"Found {len(peers)} peers from sector/industry screening: {', '.join(peers)}")
                            self.peers_cache[symbol] = peers
                            return peers
                
                except Exception as screen_error:
                    self.log_action(f"Sector screening failed: {screen_error}", level="warning")
                
                # Last resort: Try sector-only screening without industry filter
                if sector:
                    try:
                        self.log_action(f"Trying broader sector-only screening for {sector}")
                        sector_companies = await client.get_stock_screener(
                            sector=sector,
                            marketCapMoreThan=500000000,
                            limit=15
                        )
                        
                        if sector_companies:
                            peers = [
                                comp.get('symbol')
                                for comp in sector_companies
                                if comp.get('symbol') and comp.get('symbol') != symbol
                            ][:10]
                            
                            if peers:
                                self.log_action(f"Found {len(peers)} peers from broad sector screening")
                                self.peers_cache[symbol] = peers
                                return peers
                    except Exception as e:
                        self.log_action(f"Broad sector screening failed: {e}", level="warning")
            
            # No peers found
            self.log_action(f"Unable to find peers for {symbol} - will skip competitive analysis", level="warning")
            return []
            
        except Exception as e:
            self.log_action(f"Error identifying peers: {str(e)}", level="error")
            return []
            
    async def _analyze_peers_parallel(self, peers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all peer companies in parallel for maximum speed.
        
        Args:
            peers: List of peer ticker symbols
            
        Returns:
            Dictionary mapping ticker to financial metrics
        """
        async def analyze_single_peer(ticker: str) -> tuple[str, Dict[str, Any]]:
            """Analyze a single peer company."""
            try:
                # Fetch key financial data with async context
                async with FMPClient() as client:
                    income_stmt = await client.get_income_statement(ticker, period='annual', limit=3)
                    balance_sheet = await client.get_balance_sheet(ticker, period='annual', limit=3)
                    ratios = await client.get_financial_ratios(ticker, period='annual', limit=3)
                
                # Calculate key metrics
                metrics = self._calculate_peer_metrics(income_stmt, balance_sheet, ratios)
                return ticker, metrics
                
            except Exception as e:
                self.log_action(f"Error analyzing peer {ticker}: {str(e)}", level="warning")
                return ticker, {}
        
        # Execute all peer analyses in parallel
        tasks = [analyze_single_peer(peer) for peer in peers[:10]]  # Limit to top 10 peers
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and build results dictionary
        peer_metrics = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                ticker, metrics = result
                if metrics:
                    peer_metrics[ticker] = metrics
                    
        return peer_metrics
        
    def _calculate_peer_metrics(
        self, 
        income_stmt: List[Dict], 
        balance_sheet: List[Dict], 
        ratios: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate standardized metrics for a peer company.
        
        Args:
            income_stmt: Income statement data
            balance_sheet: Balance sheet data
            ratios: Financial ratios
            
        Returns:
            Dictionary of calculated metrics
        """
        if not income_stmt or not balance_sheet or not ratios:
            return {}
            
        latest_income = income_stmt[0]
        latest_balance = balance_sheet[0]
        latest_ratios = ratios[0]
        
        metrics = {
            # Revenue metrics
            'revenue': latest_income.get('revenue', 0),
            'revenue_growth': self._calculate_growth_rate(
                [stmt.get('revenue', 0) for stmt in income_stmt]
            ),
            
            # Profitability metrics
            'gross_margin': latest_ratios.get('grossProfitMargin', 0) * 100,
            'operating_margin': latest_ratios.get('operatingProfitMargin', 0) * 100,
            'net_margin': latest_ratios.get('netProfitMargin', 0) * 100,
            'roe': latest_ratios.get('returnOnEquity', 0) * 100,
            'roic': latest_ratios.get('returnOnCapitalEmployed', 0) * 100,
            
            # Efficiency metrics
            'asset_turnover': latest_ratios.get('assetTurnover', 0),
            'inventory_turnover': latest_ratios.get('inventoryTurnover', 0),
            
            # Leverage metrics
            'debt_to_equity': latest_ratios.get('debtEquityRatio', 0),
            'interest_coverage': latest_ratios.get('interestCoverage', 0),
            
            # Liquidity metrics
            'current_ratio': latest_ratios.get('currentRatio', 0),
            'quick_ratio': latest_ratios.get('quickRatio', 0),
            
            # Market metrics
            'market_cap': latest_balance.get('marketCap', 0),
        }
        
        return metrics
        
    def _calculate_growth_rate(self, values: List[float]) -> float:
        """Calculate CAGR from a list of values."""
        if len(values) < 2 or values[0] == 0 or values[-1] == 0:
            return 0.0
            
        n_periods = len(values) - 1
        cagr = ((values[-1] / values[0]) ** (1 / n_periods)) - 1
        return cagr * 100
        
    async def _analyze_sector_performance(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze sector-wide performance trends.
        
        Args:
            symbol: Target company ticker
            
        Returns:
            Sector performance data
        """
        try:
            # Get company profile to determine sector with async context
            async with FMPClient() as client:
                profile = await client.get_company_profile(symbol)
                sector = profile.get('sector', 'Unknown') if profile else 'Unknown'
                
                # Get sector performance data
                sector_perf = await client.get_sector_performance()
                
                sector_data = {
                    'sector': sector,
                    'sector_performance': {},
                    'industry_trends': {}
                }
                
                if sector_perf:
                    for item in sector_perf:
                        if item.get('sector') == sector:
                            sector_data['sector_performance'] = {
                                'day_change': item.get('changesPercentage', 0),
                                'ytd_change': item.get('ytdChange', 0),
                                'year_change': item.get('yearChange', 0),
                            }
                            break
                
                return sector_data
            
        except Exception as e:
            self.log_action(f"Error analyzing sector performance: {str(e)}", level="error")
            return {'sector': 'Unknown', 'sector_performance': {}, 'industry_trends': {}}
            
    def _generate_competitive_insights(
        self,
        symbol: str,
        target_metrics: Dict[str, Any],
        peer_metrics: Dict[str, Dict[str, Any]],
        sector_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate superhuman competitive insights by comparing target to peers and sector.
        
        This is where the revolutionary transformation happens - turning isolated metrics
        into competitive intelligence that reveals market position, performance gaps, and
        strategic opportunities.
        
        Args:
            symbol: Target company ticker
            target_metrics: Target company financial metrics
            peer_metrics: Peer company metrics
            sector_data: Sector performance data
            
        Returns:
            Comprehensive competitive analysis
        """
        analysis = {
            'summary': {},
            'relative_performance': {},
            'competitive_position': {},
            'strategic_insights': [],
            'market_share_analysis': self._calculate_market_share_analysis(target_metrics, peer_metrics),
            'peer_rankings': {}
        }
        
        if not peer_metrics:
            analysis['summary'] = {
                'message': 'Insufficient peer data for competitive analysis',
                'recommendation': 'Unable to provide competitive benchmarking'
            }
            return analysis
        
        # Calculate peer averages for benchmarking
        peer_averages = self._calculate_peer_averages(peer_metrics)
        
        # Analyze each key metric
        metric_comparisons = {}
        
        # Revenue growth comparison
        target_revenue_growth = target_metrics.get('revenue_growth', 0)
        peer_avg_revenue_growth = peer_averages.get('revenue_growth', 0)
        sector_growth = sector_data.get('sector_performance', {}).get('year_change', 0)
        
        metric_comparisons['revenue_growth'] = {
            'target': target_revenue_growth,
            'peer_average': peer_avg_revenue_growth,
            'sector_average': sector_growth,
            'vs_peers': target_revenue_growth - peer_avg_revenue_growth,
            'vs_sector': target_revenue_growth - sector_growth,
            'interpretation': self._interpret_growth_comparison(
                target_revenue_growth, peer_avg_revenue_growth, sector_growth
            )
        }
        
        # Margin analysis
        for margin_type in ['gross_margin', 'operating_margin', 'net_margin']:
            target_margin = target_metrics.get(margin_type, 0)
            peer_avg_margin = peer_averages.get(margin_type, 0)
            
            metric_comparisons[margin_type] = {
                'target': target_margin,
                'peer_average': peer_avg_margin,
                'difference': target_margin - peer_avg_margin,
                'percentile': self._calculate_percentile(
                    target_margin, 
                    [m.get(margin_type, 0) for m in peer_metrics.values()]
                ),
                'interpretation': self._interpret_margin_comparison(
                    target_margin, peer_avg_margin, margin_type
                )
            }
        
        # Return metrics analysis
        for return_metric in ['roe', 'roic']:
            target_return = target_metrics.get(return_metric, 0)
            peer_avg_return = peer_averages.get(return_metric, 0)
            
            metric_comparisons[return_metric] = {
                'target': target_return,
                'peer_average': peer_avg_return,
                'difference': target_return - peer_avg_return,
                'percentile': self._calculate_percentile(
                    target_return,
                    [m.get(return_metric, 0) for m in peer_metrics.values()]
                ),
                'interpretation': self._interpret_return_comparison(
                    target_return, peer_avg_return, return_metric
                )
            }
        
        analysis['relative_performance'] = metric_comparisons
        
        # Generate competitive position summary
        analysis['competitive_position'] = self._assess_competitive_position(
            metric_comparisons, peer_metrics
        )
        
        # Generate strategic insights
        analysis['strategic_insights'] = self._generate_strategic_insights(
            symbol, metric_comparisons, sector_data
        )
        
        # Peer rankings
        analysis['peer_rankings'] = self._create_peer_rankings(
            symbol, target_metrics, peer_metrics
        )
        
        # Overall summary
        analysis['summary'] = self._create_executive_summary(
            symbol, analysis, sector_data
        )
        
        return analysis
        
    def _calculate_peer_averages(self, peer_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average metrics across all peers."""
        if not peer_metrics:
            return {}
            
        averages = {}
        metric_keys = set()
        
        # Collect all metric keys
        for metrics in peer_metrics.values():
            metric_keys.update(metrics.keys())
        
        # Calculate averages
        for key in metric_keys:
            values = [m.get(key, 0) for m in peer_metrics.values() if m.get(key) is not None]
            if values:
                averages[key] = statistics.mean(values)
            else:
                averages[key] = 0
                
        return averages
        
    def _calculate_percentile(self, value: float, peer_values: List[float]) -> float:
        """
        Calculate percentile ranking vs peers
        
        CRITICAL FIX: Correct percentile calculation
        Higher percentile = better performance for margins/returns
        
        Example: If 8 out of 10 peers have lower gross margin, you're in 80th percentile (top 20%)
        """
        if not peer_values or value is None:
            return 50.0
            
        peer_values = [v for v in peer_values if v is not None]
        if not peer_values:
            return 50.0
            
        # Count how many peers are BELOW this value
        below_count = sum(1 for v in peer_values if v < value)
        
        # Percentile = (count below / total) * 100
        # 80th percentile = better than 80% of peers
        percentile = (below_count / len(peer_values)) * 100
        
        # VALIDATION: Log if margin is flagged as weakness despite high percentile
        if percentile > 75 and value > 0.50:  # Top quartile with >50% margin
            self.log_action(
                f"⚠️ COMPETITIVE ANALYSIS VALIDATION: Metric value {value:.1%} is in {percentile:.0f}th "
                f"percentile (TOP {100-percentile:.0f}%). This is a STRENGTH, not a weakness.",
                level="warning"
            )
        
        return round(percentile, 1)
        
    def _interpret_growth_comparison(
        self, 
        target: float, 
        peer_avg: float, 
        sector_avg: float
    ) -> str:
        """Generate human-readable interpretation of growth comparison."""
        if target > peer_avg and target > sector_avg:
            return f"OUTPERFORMING: Growing {target:.1f}% vs peer avg {peer_avg:.1f}% and sector avg {sector_avg:.1f}%. Company is gaining market share."
        elif target < peer_avg and target < sector_avg:
            return f"UNDERPERFORMING: Growing {target:.1f}% vs peer avg {peer_avg:.1f}% and sector avg {sector_avg:.1f}%. Company is losing market share."
        elif target > peer_avg:
            return f"MIXED PERFORMANCE: Growing {target:.1f}%, above peer avg {peer_avg:.1f}% but below sector avg {sector_avg:.1f}%."
        else:
            return f"MIXED PERFORMANCE: Growing {target:.1f}%, below peer avg {peer_avg:.1f}% but above sector avg {sector_avg:.1f}%."
            
    def _interpret_margin_comparison(
        self, 
        target: float, 
        peer_avg: float, 
        margin_type: str
    ) -> str:
        """Generate interpretation of margin comparison."""
        margin_name = margin_type.replace('_', ' ').title()
        diff = abs(target - peer_avg)
        
        if diff < 100:  # Less than 1% difference
            return f"{margin_name} of {target:.1f}% is in line with peer average of {peer_avg:.1f}%."
        elif target > peer_avg:
            return f"{margin_name} of {target:.1f}% is {diff:.1f}bps ABOVE peer average of {peer_avg:.1f}%. Strong operational efficiency."
        else:
            return f"{margin_name} of {target:.1f}% is {diff:.1f}bps BELOW peer average of {peer_avg:.1f}%. Potential efficiency gap."
            
    def _interpret_return_comparison(
        self, 
        target: float, 
        peer_avg: float, 
        return_metric: str
    ) -> str:
        """Generate interpretation of return metric comparison."""
        metric_name = return_metric.upper()
        diff = target - peer_avg
        
        if abs(diff) < 2:  # Less than 2% difference
            return f"{metric_name} of {target:.1f}% is comparable to peer average of {peer_avg:.1f}%."
        elif target > peer_avg:
            return f"{metric_name} of {target:.1f}% is {diff:.1f}% ABOVE peer average. Superior capital efficiency."
        else:
            return f"{metric_name} of {target:.1f}% is {abs(diff):.1f}% BELOW peer average. Capital efficiency gap identified."
            
    def _assess_competitive_position(
        self, 
        metric_comparisons: Dict[str, Dict], 
        peer_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess overall competitive position."""
        position = {
            'overall_rating': 'Unknown',
            'strengths': [],
            'weaknesses': [],
            'peer_count': len(peer_metrics)
        }
        
        # Count metrics where target outperforms peers
        outperforming_count = 0
        underperforming_count = 0
        
        for metric, data in metric_comparisons.items():
            if 'percentile' in data:
                percentile = data['percentile']
                # CRITICAL FIX: Correct percentile interpretation
                # Percentile = % of peers BELOW you (higher percentile = better performance)
                # 75th percentile = better than 75% of peers = top 25% performer
                if percentile >= 75:  # Top 25% of performers (better than 75% of peers)
                    position['strengths'].append(f"✓ {metric.replace('_', ' ').title()} (Top 25%)")
                    outperforming_count += 1
                elif percentile <= 25:  # Bottom 25% of performers (worse than 75% of peers)
                    position['weaknesses'].append(f"⚠ {metric.replace('_', ' ').title()} (Bottom 25%)")
                    underperforming_count += 1
        
        # Determine overall rating
        if outperforming_count > underperforming_count * 2:
            position['overall_rating'] = 'MARKET LEADER'
        elif outperforming_count > underperforming_count:
            position['overall_rating'] = 'ABOVE AVERAGE'
        elif outperforming_count == underperforming_count:
            position['overall_rating'] = 'AVERAGE'
        else:
            position['overall_rating'] = 'BELOW AVERAGE'
            
        return position
        
    def _generate_strategic_insights(
        self,
        symbol: str,
        metric_comparisons: Dict[str, Dict],
        sector_data: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable strategic insights."""
        insights = []
        
        # Revenue growth insights
        revenue_comp = metric_comparisons.get('revenue_growth', {})
        if revenue_comp.get('vs_peers', 0) < -500:  # 5% below peers
            insights.append(
                f"⚠️ CRITICAL: {symbol} is significantly underperforming peers in revenue growth. "
                f"Market share loss of approximately {abs(revenue_comp['vs_peers']):.1f}% annually. "
                f"Recommend immediate review of go-to-market strategy."
            )
        
        # Margin insights
        net_margin_comp = metric_comparisons.get('net_margin', {})
        if net_margin_comp.get('difference', 0) < -300:  # 3% below peers
            insights.append(
                f"💡 OPPORTUNITY: Net margin is {abs(net_margin_comp['difference']):.1f}bps below peers. "
                f"Cost optimization initiative could unlock significant value."
            )
        
        # Return metric insights
        roic_comp = metric_comparisons.get('roic', {})
        if roic_comp.get('difference', 0) > 5:  # 5% above peers
            insights.append(
                f"✅ STRENGTH: ROIC significantly outperforms peers by {roic_comp['difference']:.1f}%. "
                f"Company demonstrates superior capital allocation capabilities."
            )
        
        return insights
        
    def _create_peer_rankings(
        self,
        symbol: str,
        target_metrics: Dict[str, Any],
        peer_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Create rankings of target vs peers across key metrics."""
        rankings = {}
        
        key_metrics = ['revenue_growth', 'net_margin', 'roe', 'roic']
        
        for metric in key_metrics:
            # Combine target and peer data
            all_companies = {symbol: target_metrics}
            all_companies.update(peer_metrics)
            
            # Sort by metric value
            sorted_companies = sorted(
                all_companies.items(),
                key=lambda x: x[1].get(metric, 0),
                reverse=True
            )
            
            # Create ranking list
            rankings[metric] = [
                {
                    'rank': idx + 1,
                    'ticker': ticker,
                    'value': metrics.get(metric, 0),
                    'is_target': ticker == symbol
                }
                for idx, (ticker, metrics) in enumerate(sorted_companies)
            ]
        
        return rankings
        
    def _create_executive_summary(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        sector_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create executive summary of competitive position."""
        position = analysis.get('competitive_position', {})
        
        summary = {
            'competitive_position': position.get('overall_rating', 'Unknown'),
            'sector': sector_data.get('sector', 'Unknown'),
            'peers_analyzed': position.get('peer_count', 0),
            'key_strengths': position.get('strengths', [])[:3],  # Top 3
            'key_weaknesses': position.get('weaknesses', [])[:3],  # Top 3
            'strategic_priority': self._determine_strategic_priority(analysis),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
        
    def _determine_strategic_priority(self, analysis: Dict[str, Any]) -> str:
        """Determine the highest strategic priority based on analysis."""
        insights = analysis.get('strategic_insights', [])

        if any('CRITICAL' in insight for insight in insights):
            return 'IMMEDIATE ACTION REQUIRED'
        elif any('OPPORTUNITY' in insight for insight in insights):
            return 'OPTIMIZATION RECOMMENDED'
        elif analysis.get('competitive_position', {}).get('overall_rating') == 'MARKET LEADER':
            return 'MAINTAIN LEADERSHIP POSITION'
        else:
            return 'MONITOR AND ADJUST'

    def _calculate_market_share_analysis(
        self,
        target_metrics: Dict[str, Any],
        peer_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate market share analysis based on revenue vs peers.

        Args:
            target_metrics: Target company metrics
            peer_metrics: Peer company metrics

        Returns:
            Market share analysis
        """
        if not peer_metrics:
            return {
                'estimated_market_share': 0,
                'peer_revenue_distribution': {},
                'market_position': 'Unknown',
                'competitive_momentum': 'Neutral',
                'share_gain_loss': 0.0,
                'insights': ['Insufficient peer data for market share analysis']
            }

        # Calculate total measured market size
        target_revenue = target_metrics.get('revenue', 0)
        peer_revenues = [peer.get('revenue', 0) for peer in peer_metrics.values()]

        # Add target to peer list for total market calculation
        all_revenues = peer_revenues + [target_revenue]
        total_measured_market = sum(all_revenues)

        if total_measured_market == 0:
            return {
                'estimated_market_share': 0,
                'peer_revenue_distribution': {},
                'market_position': 'Unknown',
                'competitive_momentum': 'Neutral',
                'share_gain_loss': 0.0,
                'insights': ['No revenue data available for market share calculation']
            }

        # Calculate market share
        estimated_market_share = (target_revenue / total_measured_market) * 100

        # Peer revenue distribution
        peer_revenue_distribution = {}
        sorted_peers = sorted(peer_metrics.items(),
                            key=lambda x: x[1].get('revenue', 0), reverse=True)

        for i, (ticker, metrics) in enumerate(sorted_peers):
            peer_revenue_distribution[ticker] = {
                'revenue': metrics.get('revenue', 0),
                'market_share': (metrics.get('revenue', 0) / total_measured_market) * 100,
                'rank': i + 1,
                'growth_rate': metrics.get('revenue_growth', 0)
            }

        # Market position
        if estimated_market_share >= 20:
            market_position = 'Dominant'
        elif estimated_market_share >= 10:
            market_position = 'Major Player'
        elif estimated_market_share >= 5:
            market_position = 'Significant Player'
        elif estimated_market_share >= 1:
            market_position = 'Niche Player'
        else:
            market_position = 'Small Player'

        # Competitive momentum based on growth comparison
        target_growth = target_metrics.get('revenue_growth', 0)
        peer_avg_growth = statistics.mean([p.get('revenue_growth', 0) for p in peer_metrics.values()])

        growth_diff = target_growth - peer_avg_growth
        if growth_diff > 5:
            competitive_momentum = 'Strong Gainer'
        elif growth_diff > 2:
            competitive_momentum = 'Moderate Gainer'
        elif growth_diff > -2:
            competitive_momentum = 'Stable'
        elif growth_diff > -5:
            competitive_momentum = 'Moderate Loser'
        else:
            competitive_momentum = 'Strong Loser'

        # Share gain/loss estimation
        share_gain_loss = growth_diff * 0.1  # Rough estimate based on growth differential

        # Generate insights
        insights = []
        if estimated_market_share < 5:
            insights.append(f"Small market presence ({estimated_market_share:.1f}%) - focus on niche or acquisition strategy")
        elif market_position == 'Dominant':
            insights.append(f"Dominant position ({estimated_market_share:.1f}%) - leverage scale advantages")

        if competitive_momentum.startswith('Strong'):
            direction = 'gaining' if 'Gainer' in competitive_momentum else 'losing'
            insights.append(f"Strong competitive momentum - company is {direction} market share")

        if len(peer_revenue_distribution) > 1:
            top_peer_share = max([p['market_share'] for p in peer_revenue_distribution.values()])
            if estimated_market_share > top_peer_share:
                insights.append("Market leader in measured peer group")
            elif estimated_market_share < top_peer_share * 0.5:
                insights.append("Substantial market share gap to closest competitor")

        return {
            'estimated_market_share': round(estimated_market_share, 2),
            'peer_revenue_distribution': peer_revenue_distribution,
            'market_position': market_position,
            'competitive_momentum': competitive_momentum,
            'share_gain_loss': round(share_gain_loss, 2),
            'total_measured_market': total_measured_market,
            'target_revenue': target_revenue,
            'insights': insights
        }
    
    async def _detect_competitive_anomalies(
        self,
        symbol: str,
        target_metrics: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect competitive anomalies and weaknesses
        
        Args:
            symbol: Company ticker
            target_metrics: Company financial metrics
            analysis_result: Competitive analysis results
        
        Returns:
            Dictionary with detected anomalies
        """
        self.log_action("Detecting competitive anomalies")
        
        anomalies = []
        
        relative_performance = analysis_result.get('relative_performance', {})
        competitive_position = analysis_result.get('competitive_position', {})
        peer_rankings = analysis_result.get('peer_rankings', {})
        
        # 1. Severe Revenue Growth Underperformance
        revenue_growth_data = relative_performance.get('revenue_growth', {})
        vs_peers = revenue_growth_data.get('vs_peers', 0)
        if vs_peers < -5.0:  # More than 5% below peers
            anomalies.append({
                'type': 'severe_growth_underperformance',
                'severity': 'critical',
                'description': f'Revenue growth of {revenue_growth_data.get("target", 0):.1f}% is {abs(vs_peers):.1f}pp below peer average',
                'impact': 'Losing market share rapidly, competitive position deteriorating',
                'recommendation': 'Immediate strategic review required - assess product/market fit, pricing strategy, and go-to-market effectiveness',
                'data': {
                    'target_growth': revenue_growth_data.get('target', 0),
                    'peer_average': revenue_growth_data.get('peer_average', 0),
                    'gap': vs_peers,
                    'market_share_trend': 'Declining'
                }
            })
        elif vs_peers < -3.0:  # 3-5% below peers
            anomalies.append({
                'type': 'growth_underperformance',
                'severity': 'high',
                'description': f'Revenue growth lagging peers by {abs(vs_peers):.1f}pp',
                'impact': 'Market share erosion, competitive pressure mounting',
                'recommendation': 'Review growth strategies, benchmark against best-in-class competitors',
                'data': {
                    'target_growth': revenue_growth_data.get('target', 0),
                    'peer_average': revenue_growth_data.get('peer_average', 0),
                    'gap': vs_peers
                }
            })
        
        # 2. Margin Compression vs Peers
        margin_gaps = []
        for margin_type in ['gross_margin', 'operating_margin', 'net_margin']:
            margin_data = relative_performance.get(margin_type, {})
            difference = margin_data.get('difference', 0)
            if difference < -300:  # More than 3% below peers
                margin_gaps.append((margin_type, difference))
        
        if margin_gaps:
            worst_margin = min(margin_gaps, key=lambda x: x[1])
            margin_name = worst_margin[0].replace('_', ' ').title()
            gap_bps = abs(worst_margin[1])
            
            anomalies.append({
                'type': 'significant_margin_gap',
                'severity': 'high' if gap_bps > 500 else 'medium',
                'description': f'{margin_name} is {gap_bps:.0f}bps below peer average',
                'impact': 'Profitability disadvantage, operational efficiency concerns',
                'recommendation': 'Conduct detailed cost structure analysis, benchmark operational processes, identify margin improvement opportunities',
                'data': {
                    'affected_margins': [m[0] for m in margin_gaps],
                    'worst_gap_bps': gap_bps,
                    'competitiveness': 'Below average'
                }
            })
        
        # 3. Poor Capital Efficiency
        roic_data = relative_performance.get('roic', {})
        roe_data = relative_performance.get('roe', {})
        roic_diff = roic_data.get('difference', 0)
        roe_diff = roe_data.get('difference', 0)
        
        if roic_diff < -5.0 or roe_diff < -5.0:
            anomalies.append({
                'type': 'capital_efficiency_gap',
                'severity': 'high',
                'description': f'Returns significantly below peers - ROIC gap: {roic_diff:.1f}%, ROE gap: {roe_diff:.1f}%',
                'impact': 'Inferior capital allocation, value destruction vs peers',
                'recommendation': 'Review capital allocation decisions, asset base efficiency, and working capital management',
                'data': {
                    'roic_gap': roic_diff,
                    'roe_gap': roe_diff,
                    'roic_percentile': roic_data.get('percentile', 50),
                    'roe_percentile': roe_data.get('percentile', 50)
                }
            })
        
        # 4. Bottom Quartile Rankings
        bottom_quartile_metrics = []
        for metric, rankings in peer_rankings.items():
            for rank_data in rankings:
                if rank_data.get('is_target') and rank_data.get('rank', 0) > len(rankings) * 0.75:
                    bottom_quartile_metrics.append(metric)
                    break
        
        if len(bottom_quartile_metrics) >= 3:
            anomalies.append({
                'type': 'weak_competitive_position',
                'severity': 'high',
                'description': f'Bottom quartile performance in {len(bottom_quartile_metrics)} key metrics',
                'impact': 'Broad-based competitive disadvantage, multiple operational weaknesses',
                'recommendation': 'Comprehensive operational review needed across growth, profitability, and returns',
                'data': {
                    'weak_metrics': bottom_quartile_metrics,
                    'count': len(bottom_quartile_metrics),
                    'overall_position': 'Weak'
                }
            })
        
        # 5. Overall Competitive Position
        overall_rating = competitive_position.get('overall_rating', 'Unknown')
        if overall_rating == 'BELOW AVERAGE':
            weaknesses = competitive_position.get('weaknesses', [])
            anomalies.append({
                'type': 'below_average_competitive_position',
                'severity': 'medium',
                'description': f'Overall competitive position rated as {overall_rating}',
                'impact': 'Challenging competitive environment, multiple improvement areas needed',
                'recommendation': 'Focus on addressing key weaknesses while leveraging any existing strengths',
                'data': {
                    'rating': overall_rating,
                    'weakness_count': len(weaknesses),
                    'weaknesses': weaknesses
                }
            })
        
        # 6. Market Share Loss Indicators
        target_growth = revenue_growth_data.get('target', 0)
        sector_growth = revenue_growth_data.get('sector_average', 0)
        if target_growth < sector_growth - 5.0:
            anomalies.append({
                'type': 'market_share_loss',
                'severity': 'critical',
                'description': f'Growing {target_growth:.1f}% while sector grows {sector_growth:.1f}% - losing market share',
                'impact': 'Competitive position erosion, potential strategic threat',
                'recommendation': 'Urgent review of competitive strategy, product positioning, and market dynamics',
                'data': {
                    'company_growth': target_growth,
                    'sector_growth': sector_growth,
                    'implied_share_loss': target_growth - sector_growth,
                    'urgency': 'High'
                }
            })
        
        # 7. No Competitive Strengths Identified
        strengths = competitive_position.get('strengths', [])
        weaknesses = competitive_position.get('weaknesses', [])
        if len(strengths) == 0 and len(weaknesses) > 0:
            anomalies.append({
                'type': 'lack_of_competitive_advantages',
                'severity': 'high',
                'description': 'No areas of competitive strength identified vs peers',
                'impact': 'No differentiation, commoditized position, vulnerable to competition',
                'recommendation': 'Identify and develop sustainable competitive advantages - cost leadership or differentiation',
                'data': {
                    'strengths_count': 0,
                    'weaknesses_count': len(weaknesses),
                    'competitive_moat': 'Absent'
                }
            })
        
        # 8. Peer Analysis Coverage Issue
        peer_count = competitive_position.get('peer_count', 0)
        if peer_count < 3:
            anomalies.append({
                'type': 'limited_peer_analysis',
                'severity': 'medium',
                'description': f'Only {peer_count} peers analyzed - competitive analysis may be incomplete',
                'impact': 'Competitive benchmarking lacks statistical significance',
                'recommendation': 'Expand peer set or use alternative benchmarking methods',
                'data': {
                    'peers_analyzed': peer_count,
                    'minimum_recommended': 5,
                    'data_quality': 'Limited'
                }
            })
        
        # 9. Ranking Consistency Issues
        consistent_bottom_half = 0
        for metric, rankings in peer_rankings.items():
            for rank_data in rankings:
                if rank_data.get('is_target'):
                    total_companies = len(rankings)
                    if rank_data.get('rank', 0) > total_companies / 2:
                        consistent_bottom_half += 1
                    break
        
        if consistent_bottom_half >= 3:
            anomalies.append({
                'type': 'consistent_underperformance',
                'severity': 'high',
                'description': f'Bottom-half rankings in {consistent_bottom_half} of {len(peer_rankings)} metrics',
                'impact': 'Persistent competitive disadvantage across multiple dimensions',
                'recommendation': 'Comprehensive turnaround strategy may be required',
                'data': {
                    'bottom_half_count': consistent_bottom_half,
                    'metrics_analyzed': len(peer_rankings),
                    'pattern': 'Consistent underperformance'
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
        
        self.log_action(f"Competitive anomaly detection complete: {len(anomalies)} anomalies found, risk level: {risk_level}")
        
        return {
            'anomalies_detected': anomalies,
            'total_anomalies': len(anomalies),
            'risk_level': risk_level,
            'critical_issues': critical_count,
            'high_issues': high_count
        }
