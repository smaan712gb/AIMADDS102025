"""
Revolutionary M&A Analysis System - Second-Order Insights Demo

This demo showcases the system's ability to connect disparate information
across agents to generate insights humans would miss - focusing on the "how"
and consequences, not just the "what".

Example of Second-Order Insight:
- First-Order: "Revenue grew 12%"
- Second-Order: "Revenue grew 12%, BUT competitive analysis shows peers at 18%,
  macro analysis reveals sector tailwinds of 15%, AND anomaly detection flags
  inventory up 40% - suggesting the company is LOSING market share despite
  favorable conditions and potentially building obsolete inventory. This
  indicates fundamental competitive weakness requiring immediate strategic review."
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import get_config
from src.core.state import create_initial_state
from src.core.llm_factory import get_llm
from src.integrations.fmp_client import FMPClient
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.competitive_benchmarking import CompetitiveBenchmarkingAgent
from src.agents.macroeconomic_analyst import MacroeconomicAnalystAgent
from src.agents.conversational_synthesis import ConversationalSynthesisAgent
from src.utils.anomaly_detection import AnomalyDetector


class SecondOrderInsightEngine:
    """
    Engine that connects insights across agents to generate second-order insights
    that reveal consequences humans would miss.
    """
    
    def __init__(self):
        self.insights_log = []
        
    def connect_insights(
        self,
        financial_analysis: Dict[str, Any],
        competitive_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any],
        anomaly_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Connect insights across all agents to generate second-order intelligence.
        
        This is where the magic happens - we don't just report facts, we reveal
        the consequences and interconnections that humans would miss.
        """
        print("\n" + "="*80)
        print("🧠 SECOND-ORDER INSIGHT ENGINE - CONNECTING THE DOTS")
        print("="*80 + "\n")
        
        second_order_insights = {
            'critical_connections': [],
            'hidden_risks': [],
            'strategic_opportunities': [],
            'consequence_chains': []
        }
        
        # INSIGHT CONNECTION 1: Revenue Growth + Competitive Position + Macro Environment
        self._analyze_revenue_in_context(
            financial_analysis,
            competitive_analysis,
            macro_analysis,
            second_order_insights
        )
        
        # INSIGHT CONNECTION 2: Inventory Anomalies + Revenue Performance + Competition
        self._analyze_inventory_revenue_dynamics(
            financial_analysis,
            anomaly_analysis,
            competitive_analysis,
            second_order_insights
        )
        
        # INSIGHT CONNECTION 3: Margin Pressure + Macro Sensitivity + Competitive Gaps
        self._analyze_margin_vulnerability(
            financial_analysis,
            competitive_analysis,
            macro_analysis,
            second_order_insights
        )
        
        # INSIGHT CONNECTION 4: Anomalies + Competitive Position + Strategic Implications
        self._analyze_operational_anomalies_strategic_impact(
            anomaly_analysis,
            competitive_analysis,
            financial_analysis,
            second_order_insights
        )
        
        return second_order_insights
        
    def _analyze_revenue_in_context(
        self,
        financial: Dict,
        competitive: Dict,
        macro: Dict,
        insights: Dict
    ):
        """
        First-Order: "Revenue grew X%"
        Second-Order: Connect revenue to competitive position, macro environment,
                     and strategic implications
        """
        print("🔗 CONNECTION 1: Revenue Growth in Full Context")
        print("-" * 80)
        
        # Extract data
        fin_metrics = financial.get('ratio_analysis', {}).get('growth_metrics', {})
        revenue_growth = fin_metrics.get('revenue_cagr_3y', 0)
        
        comp_perf = competitive.get('relative_performance', {}).get('revenue_growth', {})
        peer_avg = comp_perf.get('peer_average', 0)
        sector_avg = comp_perf.get('sector_average', 0)
        percentile = comp_perf.get('percentile', 50)
        
        macro_corr = macro.get('correlation_analysis', {})
        
        # Generate second-order insight
        if revenue_growth > 0 and revenue_growth < peer_avg and revenue_growth < sector_avg:
            insight = {
                'type': 'critical_market_share_loss',
                'first_order': f"Revenue grew {revenue_growth:.1f}%",
                'second_order': (
                    f"Revenue grew {revenue_growth:.1f}%, BUT this UNDERPERFORMS peer average "
                    f"of {peer_avg:.1f}% AND sector growth of {sector_avg:.1f}%. "
                    f"\n\n📊 CONSEQUENCE: Company is in {percentile:.0f}th percentile - actively "
                    f"LOSING MARKET SHARE despite favorable sector tailwinds. "
                    f"\n\n🎯 STRATEGIC IMPLICATION: This suggests fundamental competitive weakness. "
                    f"Macro analysis shows sector growth at {sector_avg:.1f}%, meaning favorable "
                    f"external conditions exist. The company's inability to capture this growth "
                    f"indicates either: (1) inferior product positioning, (2) pricing disadvantage, "
                    f"(3) distribution channel weakness, or (4) brand deterioration. "
                    f"\n\n⚠️ ACTION REQUIRED: Immediate strategic review needed. Recommend deep-dive "
                    f"into customer churn analysis, competitive win/loss analysis, and pricing "
                    f"elasticity studies."
                ),
                'severity': 'CRITICAL',
                'cross_agent_evidence': {
                    'financial': f'{revenue_growth:.1f}% growth',
                    'competitive': f'Bottom {100-percentile:.0f}% performer',
                    'macro': f'{sector_avg:.1f}% sector tailwinds available'
                }
            }
            
            insights['critical_connections'].append(insight)
            
            print(f"❌ FIRST-ORDER: {insight['first_order']}")
            print(f"\n✅ SECOND-ORDER INSIGHT:")
            print(insight['second_order'])
            print()
        
    def _analyze_inventory_revenue_dynamics(
        self,
        financial: Dict,
        anomaly: Dict,
        competitive: Dict,
        insights: Dict
    ):
        """
        First-Order: "Inventory increased 40%"
        Second-Order: Connect inventory anomaly to revenue performance,
                     competitive context, and cash flow implications
        """
        print("🔗 CONNECTION 2: Inventory Anomalies + Revenue Dynamics")
        print("-" * 80)
        
        anomalies_detected = anomaly.get('anomalies_detected', [])
        inventory_anomaly = next(
            (a for a in anomalies_detected if a.get('metric') == 'inventory'),
            None
        )
        
        if inventory_anomaly and inventory_anomaly.get('severity') == 'High':
            # Get revenue performance
            comp_perf = competitive.get('relative_performance', {}).get('revenue_growth', {})
            revenue_vs_peers = comp_perf.get('vs_peers', 0)
            
            # Generate second-order insight
            insight = {
                'type': 'inventory_revenue_mismatch',
                'first_order': f"Inventory is {inventory_anomaly.get('interpretation', 'elevated')}",
                'second_order': (
                    f"Inventory anomaly detected: {inventory_anomaly.get('current_value', 0)/1e6:.1f}M "
                    f"vs expected {inventory_anomaly.get('expected_mean', 0)/1e6:.1f}M "
                    f"(z-score: {inventory_anomaly.get('z_score', 0):.1f}). "
                    f"\n\n📊 CONSEQUENCE CHAIN:"
                    f"\n1. OPERATIONAL: Inventory build suggests demand forecasting error or product transition issues"
                    f"\n2. COMPETITIVE: Revenue underperforms peers by {abs(revenue_vs_peers):.1f}%, indicating "
                    f"   inventory is building BECAUSE customers are choosing competitors"
                    f"\n3. FINANCIAL: High inventory = cash trapped in working capital, reducing financial flexibility"
                    f"\n4. STRATEGIC RISK: If inventory is obsolete (likely given sales underperformance), "
                    f"   expect future write-downs of {inventory_anomaly.get('current_value', 0) * 0.15/1e6:.1f}M-"
                    f"{inventory_anomaly.get('current_value', 0) * 0.30/1e6:.1f}M (15-30% haircut)"
                    f"\n\n🎯 HIDDEN INSIGHT: The combination of rising inventory + declining competitive position "
                    f"is a classic 'death spiral' indicator. Competitors are winning, forcing aggressive discounting, "
                    f"which further erodes margin and brand perception. "
                    f"\n\n⚠️ URGENT ACTION: Immediate inventory audit, SKU-level analysis, and pricing review required."
                ),
                'severity': 'CRITICAL',
                'cross_agent_evidence': {
                    'anomaly': f'Inventory {(inventory_anomaly.get("current_value", 0) / inventory_anomaly.get("expected_mean", 1) - 1) * 100:.0f}% above normal',
                    'competitive': f'Revenue {abs(revenue_vs_peers):.1f}% below peers',
                    'financial': 'Working capital deterioration'
                }
            }
            
            insights['hidden_risks'].append(insight)
            
            print(f"❌ FIRST-ORDER: {insight['first_order']}")
            print(f"\n✅ SECOND-ORDER INSIGHT:")
            print(insight['second_order'])
            print()
        
    def _analyze_margin_vulnerability(
        self,
        financial: Dict,
        competitive: Dict,
        macro: Dict,
        insights: Dict
    ):
        """
        First-Order: "Net margin is 18%"
        Second-Order: Connect margin to competitive gaps, macro sensitivities,
                     and future risk scenarios
        """
        print("🔗 CONNECTION 3: Margin Vulnerability Analysis")
        print("-" * 80)
        
        # Extract data
        comp_margins = competitive.get('relative_performance', {}).get('net_margin', {})
        margin_gap = comp_margins.get('difference', 0)
        
        macro_sensitivity = macro.get('correlation_analysis', {}).get('margin_sensitivity', {})
        ppi_impact = macro_sensitivity.get('ppi', {}).get('coefficient', 0)
        
        current_inflation = macro.get('current_economic_conditions', {}).get('inflation_rate', 0)
        
        if margin_gap < -200:  # More than 200bps below peers
            insight = {
                'type': 'margin_competitive_vulnerability',
                'first_order': f"Net margin {abs(margin_gap):.0f}bps below peers",
                'second_order': (
                    f"Margin analysis reveals structural disadvantage: {abs(margin_gap):.0f} basis points "
                    f"BELOW peer average. "
                    f"\n\n📊 CONSEQUENCE CHAIN:"
                    f"\n1. COMPETITIVE: {abs(margin_gap):.0f}bps gap means competitors have MORE pricing power "
                    f"   OR lower cost structure - sustainable competitive advantage"
                    f"\n2. MACRO SENSITIVITY: Company's margins are {abs(ppi_impact):.0%} sensitive to PPI. "
                    f"   With current {current_inflation:.1f}% inflation, this is {abs(ppi_impact * current_inflation * 100):.0f}bps "
                    f"   of additional pressure"
                    f"\n3. STRATEGIC VULNERABILITY: In recession scenario, this company will face margin "
                    f"   compression from BOTH competitive discounting AND input costs, while peers "
                    f"   have cushion to absorb shocks"
                    f"\n4. VALUATION IMPACT: Structural margin disadvantage warrants 15-20% valuation discount "
                    f"   vs. peers due to higher business risk"
                    f"\n\n🎯 ROOT CAUSE HYPOTHESIS: The margin gap likely stems from:"
                    f"\n   • Scale disadvantage (lower volumes = higher unit costs)"
                    f"\n   • Inferior supplier relationships"
                    f"\n   • Legacy cost structure from older facilities"
                    f"\n   • Product mix skewed toward lower-margin offerings"
                    f"\n\n⚠️ STRATEGIC IMPERATIVE: Cost transformation program required. Recommend benchmarking "
                    f"peer COGS structure, evaluating manufacturing footprint consolidation, and supplier renegotiation."
                ),
                'severity': 'HIGH',
                'cross_agent_evidence': {
                    'competitive': f'{abs(margin_gap):.0f}bps structural disadvantage',
                    'macro': f'{abs(ppi_impact):.0%} sensitivity to inflation',
                    'financial': 'Limited pricing power'
                }
            }
            
            insights['strategic_opportunities'].append(insight)
            
            print(f"❌ FIRST-ORDER: {insight['first_order']}")
            print(f"\n✅ SECOND-ORDER INSIGHT:")
            print(insight['second_order'])
            print()
        
    def _analyze_operational_anomalies_strategic_impact(
        self,
        anomaly: Dict,
        competitive: Dict,
        financial: Dict,
        insights: Dict
    ):
        """
        First-Order: "AR increased 25%"
        Second-Order: Connect AR anomaly to competitive dynamics and strategic risks
        """
        print("🔗 CONNECTION 4: Operational Anomalies → Strategic Impact")
        print("-" * 80)
        
        anomalies = anomaly.get('anomalies_detected', [])
        ar_anomaly = next(
            (a for a in anomalies if a.get('metric') == 'accounts_receivable'),
            None
        )
        
        if ar_anomaly and ar_anomaly.get('severity') == 'High':
            comp_position = competitive.get('competitive_position', {}).get('overall_rating', 'Unknown')
            
            insight = {
                'type': 'ar_strategic_weakness',
                'first_order': "Accounts receivable elevated",
                'second_order': (
                    f"AR anomaly: {ar_anomaly.get('current_value', 0)/1e6:.1f}M vs expected "
                    f"{ar_anomaly.get('expected_mean', 0)/1e6:.1f}M (z-score: {ar_anomaly.get('z_score', 0):.1f}). "
                    f"\n\n📊 CONSEQUENCE CHAIN:"
                    f"\n1. OPERATIONAL: Rising AR suggests customers delaying payment - sign of dissatisfaction"
                    f"\n2. COMPETITIVE: Combined with '{comp_position}' competitive position, this indicates "
                    f"   CUSTOMERS HAVE LEVERAGE. They know switching options exist."
                    f"\n3. STRATEGIC RISK: High AR in weak competitive position creates vicious cycle:"
                    f"   → Extended payment terms to retain customers"
                    f"   → Reduces cash generation"
                    f"   → Forces cost cuts that further weaken competitive position"
                    f"   → More customer churn"
                    f"\n4. HIDDEN RISK: Some of this AR may be UNCOLLECTIBLE. If 10-15% proves bad, "
                    f"   that's {ar_anomaly.get('current_value', 0) * 0.125/1e6:.1f}M write-off risk"
                    f"\n\n🎯 STRATEGIC IMPLICATION: This is NOT just a collections issue. It's a symptom of "
                    f"weak negotiating position with customers. The company is being forced to finance "
                    f"customer operations because their product is not differentiated enough to command "
                    f"normal payment terms."
                    f"\n\n⚠️ CRITICAL ACTION: Customer concentration analysis + AR aging + credit quality review. "
                    f"Also evaluate product differentiation strategy to improve negotiating leverage."
                ),
                'severity': 'HIGH',
                'cross_agent_evidence': {
                    'anomaly': f'AR {(ar_anomaly.get("current_value", 0) / ar_anomaly.get("expected_mean", 1) - 1) * 100:.0f}% above normal',
                    'competitive': f'{comp_position} position = low leverage',
                    'financial': 'Cash conversion cycle deteriorating'
                }
            }
            
            insights['hidden_risks'].append(insight)
            
            print(f"❌ FIRST-ORDER: {insight['first_order']}")
            print(f"\n✅ SECOND-ORDER INSIGHT:")
            print(insight['second_order'])
            print()
        
    def print_insight_summary(self, insights: Dict[str, Any]):
        """Print executive summary of all second-order insights."""
        print("\n" + "="*80)
        print("📋 SECOND-ORDER INSIGHTS - EXECUTIVE SUMMARY")
        print("="*80 + "\n")
        
        all_insights = (
            insights.get('critical_connections', []) +
            insights.get('hidden_risks', []) +
            insights.get('strategic_opportunities', []) +
            insights.get('consequence_chains', [])
        )
        
        if not all_insights:
            print("✅ No critical second-order insights identified - company performing within normal parameters")
            return
        
        critical_count = len([i for i in all_insights if i.get('severity') == 'CRITICAL'])
        high_count = len([i for i in all_insights if i.get('severity') == 'HIGH'])
        
        print(f"🚨 CRITICAL INSIGHTS: {critical_count}")
        print(f"⚠️  HIGH PRIORITY: {high_count}")
        print(f"📊 TOTAL CONNECTIONS: {len(all_insights)}\n")
        
        print("KEY TAKEAWAYS:")
        for idx, insight in enumerate(all_insights, 1):
            print(f"\n{idx}. [{insight.get('severity')}] {insight.get('type').replace('_', ' ').title()}")
            print(f"   First-Order: {insight.get('first_order')}")
            print(f"   Second-Order Impact: {insight.get('second_order', '')[:200]}...")


async def run_revolutionary_demo():
    """
    Run complete demo showcasing second-order insights across all agents.
    """
    print("\n" + "="*80)
    print("🚀 REVOLUTIONARY M&A ANALYSIS SYSTEM - SECOND-ORDER INSIGHTS DEMO")
    print("="*80)
    print("\nDemonstrating how the system connects disparate information")
    print("to generate insights humans would miss...")
    print()
    
    try:
        # Initialize system
        print("📦 Initializing multi-agent system...")
        config = get_config()
        state = create_initial_state(
            deal_id="DEMO-001",
            target_company="NVIDIA Corporation",
            target_ticker="NVDA",
            investment_thesis="Leading AI infrastructure provider",
            strategic_rationale="Capitalize on AI revolution"
        )
        
        # Get LLMs
        claude = get_llm('claude')
        gemini = get_llm('gemini')
        
        # Initialize FMP client
        fmp_client = FMPClient()
        
        # Initialize agents
        print("🤖 Initializing specialized agents...")
        financial_agent = FinancialAnalystAgent()
        financial_agent.set_fmp_client(fmp_client)
        
        competitive_agent = CompetitiveBenchmarkingAgent()
        competitive_agent.set_fmp_client(fmp_client)
        
        macro_agent = MacroeconomicAnalystAgent()
        macro_agent.set_fmp_client(fmp_client)
        
        conversation_agent = ConversationalSynthesisAgent()
        
        anomaly_detector = AnomalyDetector()
        
        # Initialize insight engine
        insight_engine = SecondOrderInsightEngine()
        
        # Demo symbol
        symbol = "NVDA"  # or "AAPL", "MSFT", etc.
        print(f"\n🎯 Target Company: {symbol}")
        print("="*80 + "\n")
        
        # Step 1: Financial Analysis
        print("💰 STEP 1: Running Financial Analysis...")
        print("-" * 80)
        financial_analysis = await financial_agent.analyze(symbol)
        print(f"✅ Financial health score: {financial_analysis.get('financial_health_score', 0):.1f}/100")
        print(f"✅ DCF Valuation: ${financial_analysis.get('valuation', {}).get('dcf_value_per_share', 0):.2f}/share\n")
        
        # Extract target metrics for competitive analysis
        target_metrics = {
            'revenue_growth': financial_analysis.get('ratio_analysis', {}).get('growth_metrics', {}).get('revenue_cagr_3y', 0),
            'gross_margin': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('gross_margin', 0),
            'operating_margin': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('operating_margin', 0),
            'net_margin': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('net_margin', 0),
            'roe': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('roe', 0),
            'roic': financial_analysis.get('ratio_analysis', {}).get('profitability_ratios', {}).get('roic', 0),
        }
        
        # Step 2: Competitive Benchmarking
        print("🏆 STEP 2: Running Competitive Benchmarking...")
        print("-" * 80)
        competitive_analysis = await competitive_agent.analyze(symbol, target_metrics)
        comp_position = competitive_analysis.get('summary', {}).get('competitive_position', 'Unknown')
        peers_count = competitive_analysis.get('summary', {}).get('peers_analyzed', 0)
        print(f"✅ Competitive Position: {comp_position}")
        print(f"✅ Peers Analyzed: {peers_count}\n")
        
        # Step 3: Macroeconomic Analysis
        print("🌍 STEP 3: Running Macroeconomic Analysis...")
        print("-" * 80)
        historical_financials = financial_analysis.get('historical_data', {})
        macro_analysis = await macro_agent.analyze(symbol, historical_financials)
        print(f"✅ Scenarios Generated: {len(macro_analysis.get('scenario_models', {}))}")
        print(f"✅ Economic Insights: {len(macro_analysis.get('insights', []))}\n")
        
        # Step 4: Anomaly Detection with REAL NVDA data
        print("🔍 STEP 4: Running Anomaly Detection...")
        print("-" * 80)
        
        # Use REAL historical data from NVDA balance sheets and income statements
        balance_sheets = financial_analysis.get('historical_data', {}).get('balance_sheet', [])
        income_statements = financial_analysis.get('historical_data', {}).get('income_statement', [])
        cash_flows = financial_analysis.get('historical_data', {}).get('cash_flow', [])
        
        if balance_sheets and income_statements and len(balance_sheets) >= 8:
            # Extract historical data for training (use last 8 quarters or years)
            historical_data = []
            for i in range(min(8, len(balance_sheets) - 1)):  # Leave latest for anomaly detection
                bs = balance_sheets[i + 1]  # Skip latest
                inc = income_statements[i + 1] if i + 1 < len(income_statements) else {}
                
                historical_data.append({
                    'revenue': inc.get('revenue', 0),
                    'inventory': bs.get('inventory', 0),
                    'accounts_receivable': bs.get('netReceivables', 0),
                    'cost_of_revenue': inc.get('costOfRev
        print(f"✅ Anomalies Detected: {len(anomaly_analysis.get('anomalies_detected', []))}")
        print(f"✅ Risk Level: {anomaly_analysis.get('risk_level', 'Unknown')}\n")
        
        # Step 5: SECOND-ORDER INSIGHT GENERATION
        print("\n" + "🌟"*40)
        print("GENERATING SECOND-ORDER INSIGHTS")
        print("🌟"*40 + "\n")
        
        second_order_insights = insight_engine.connect_insights(
            financial_analysis,
            competitive_analysis,
            macro_analysis,
            anomaly_analysis
        )
        
        # Print summary
        insight_engine.print_insight_summary(second_order_insights)
        
        # Step 6: Initialize Conversational Interface
        print("\n\n" + "="*80)
        print("💬 STEP 6: Initializing Conversational Interface")
        print("="*80 + "\n")
        
        complete_analysis = {
            'financial_analysis': financial_analysis,
            'competitive_benchmarking': competitive_analysis,
            'macroeconomic_analysis': macro_analysis,
            'anomaly_detection': anomaly_analysis,
            'second_order_insights': second_order_insights
        }
        
        summary = await conversation_agent.initialize_analysis(complete_analysis)
        print(summary)
        
        # Demo conversational queries
        print("\n" + "="*80)
        print("🗣️  CONVERSATIONAL QUERY DEMO")
        print("="*80 + "\n")
        
        questions = [
            "Why is the company losing market share?",
            "What are the biggest risks I should worry about?",
            "How does this compare to competitors?"
        ]
        
        for question in questions:
            print(f"\n❓ User: {question}")
            print("-" * 80)
            response = await conversation_agent.process_question(question)
            print(f"🤖 Agent: {response['answer'][:500]}...")
            print()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETE - SECOND-ORDER INSIGHTS SUCCESSFULLY DEMONSTRATED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting Revolutionary M&A Analysis Demo...")
    asyncio.run(run_revolutionary_demo())
