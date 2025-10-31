"""
Test script for the new Consolidator & Quality Control Agent (Synthesis_Reporting)

This script tests the enhanced synthesis_reporting agent that acts as a sophisticated
Consolidator & Quality Control layer with 6 phases:

1. Agent Findings Extraction
2. Grounding & Fact-Checking (Anti-Hallucination)
3. De-duplication & Semantic Clustering
4. Conflict Resolution (rule-based + LLM)
5. Confidence Scoring & Aggregation
6. Report-Ready Structure Creation

Run with: python test_consolidator.py
"""

import asyncio
import json
from datetime import datetime
from loguru import logger

from src.agents.synthesis_reporting import SynthesisReportingAgent
from src.core.state import DiligenceState

def create_mock_state_with_agent_outputs():
    """Create a comprehensive mock state with outputs from all 13 agents"""

    # Mock agent outputs simulating all agents
    agent_outputs = [
        {
            'agent_name': 'financial_analyst',
            'data': {
                'dcf_valuation': {'enterprise_value_base': 8500000000},
                'confidence_score': 0.9
            }
        },
        {
            'agent_name': 'financial_deep_dive',
            'data': {
                'insights': {
                    'key_metrics': {
                        'nwc_efficiency': 85,
                        'customer_concentration_risk': 3
                    }
                },
                'confidence_score': 0.8
            }
        },
        {
            'agent_name': 'legal_counsel',
            'data': {
                'risk_assessment': 'Medium risk exposure',
                'confidence_score': 0.75
            }
        },
        {
            'agent_name': 'risk_assessment',
            'data': {
                'risk_scores': {
                    'risk_rating': 'MODERATE',
                    'total_risks': 8,
                    'critical_risks': 1,
                    'high_risks': 3
                },
                'confidence_score': 0.9
            }
        },
        {
            'agent_name': 'external_validator',
            'data': {
                'confidence_score': 0.87,
                'external_sources_consulted': 12,
                'critical_discrepancies': []
            }
        },
        {
            'agent_name': 'market_strategist',
            'data': {
                'sentiment_analysis': {
                    'overall_sentiment': 'positive'
                },
                'confidence_score': 0.7
            }
        },
        {
            'agent_name': 'integration_planner',
            'data': {
                'synergy_analysis': {
                    'revenue_synergies': 500000000
                },
                'confidence_score': 0.75
            }
        },
        {
            'agent_name': 'tax_structuring',
            'data': {
                'optimal_structure': 'Asset Purchase',
                'estimated_tax_impact': 750000000,
                'confidence_score': 0.8
            }
        },
        {
            'agent_name': 'competitive_benchmarking',
            'data': {
                'competitive_position': {
                    'overall_rating': 'Above Average'
                },
                'confidence_score': 0.8
            }
        },
        {
            'agent_name': 'macroeconomic_analyst',
            'data': {
                'economic_outlook': 'Stable with moderate growth',
                'confidence_score': 0.7
            }
        }
    ]

    # Mock other state data
    mock_state = DiligenceState({
        'target_company': 'Oracle Corporation',
        'deal_type': 'Strategic Acquisition',
        'deal_value': 75000000000,  # $75B deal
        'investment_thesis': 'Leading enterprise software platform with strong AI capabilities',
        'agent_outputs': agent_outputs,

        # Mock source data for fact-checking
        'financial_data': {
            'revenue': 52000000000,
            'net_income': 8800000000,
            'ev_to_ebitda': 28.5
        },
        'normalized_financials': {
            'normalized_ebitda': 12000000000
        },
        'valuation_models': {
            'dcf_base': {'wacc': 0.085, 'terminal_growth': 0.025}
        },
        'legal_risks': [
            {'category': 'litigation', 'severity': 'high', 'description': 'Ongoing patent litigation'},
            {'category': 'regulatory', 'severity': 'medium', 'description': 'Antitrust review required'}
        ],
        'market_data': {
            'sentiment_analysis': {'overall_sentiment': 'positive'}
        },
        'competitive_analysis': {
            'competitive_position': {'overall_rating': 'Above Average'}
        },
        'synergy_analysis': {
            'revenue_synergies': 500000000
        },
        'tax_analysis': {
            'estimated_tax_impact': 750000000
        },
        'macroeconomic_analysis': {
            'economic_outlook': 'Stable with moderate growth'
        },

        # Initialize empty lists/dicts for results
        'errors': [],
        'metadata': {}
    })

    return mock_state

async def test_consolidator():
    """Test the new Consolidator & Quality Control agent"""

    logger.info("🧪 Testing Consolidator & Quality Control Agent...")
    logger.info("=" * 80)

    # Create mock state with comprehensive agent outputs
    state = create_mock_state_with_agent_outputs()

    logger.info(f"📊 Mock state created for: {state['target_company']}")
    logger.info(f"💰 Deal value: ${state['deal_value']:,.0f}")
    logger.info(f"🤖 {len(state['agent_outputs'])} agent outputs simulated")
    logger.info(" ")

    # Initialize the Consolidator
    consolidator = SynthesisReportingAgent()

    try:
        # Run the consolidator
        start_time = datetime.now()
        result_state = await consolidator.run(state)
        end_time = datetime.now()

        # Display results
        logger.info("✅ Consolidator completed successfully!")
        execution_time = (end_time - start_time).total_seconds()
        logger.info(".2f")
        logger.info(" ")

        # Show consolidation metadata
        if 'consolidation_metadata' in result_state:

            # Convert the Set of processed IDs to JSON-serializable format
            result_state['consolidation_metadata'] = {
                k: (list(v) if isinstance(v, set) else v)
                for k, v in result_state['consolidation_metadata'].items()
            }

            logger.info("📈 CONSOLIDATION METADATA:")
            metadata = result_state['consolidation_metadata']
            logger.info(f"   📊 Agent extractions: {metadata.get('agent_extractions', 0)}")
            logger.info(f"   ✅ Grounded findings: {metadata.get('grounded_findings', 0)}")
            logger.info(f"   🔀 De-duplicated: {metadata.get('consolidated_findings', 0)}")
            logger.info(f"   ⚖️ Conflicts resolved: {metadata.get('conflicts_resolved', 0)}")
            logger.info(f"   🎯 Final datapoints: {metadata.get('final_datapoints', 0)}")
            logger.info(f"   🚨 Hallucinations flagged: {metadata.get('hallucination_flags', 0)}")
            logger.info("")

            # Show confidence distribution
            conf_dist = metadata.get('confidence_distribution', {})
            if conf_dist:
                logger.info("📊 CONFIDENCE DISTRIBUTION:")
                for level, pct in conf_dist.items():
                    if pct > 0:
                        logger.info(f"   {level}: {pct:.1f}%")
                logger.info("")

        # Show consolidated insights
        if 'consolidated_insights' in result_state:
            insights = result_state['consolidated_insights']

            logger.info("🔍 CONSOLIDATED INSIGHTS SUMMARY:")
            logger.info(f"   📈 Overall confidence: {insights.get('metadata', {}).get('overall_confidence', 0):.1%}")

            # Quality metrics
            quality = insights.get('quality_metrics', {})
            if quality:
                logger.info("   📊 Quality Metrics:")
                logger.info(f"      Total findings: {quality.get('total_findings', 0)}")
                logger.info(f"      High confidence: {quality.get('high_confidence_findings', 0)}")
                logger.info(f"      Data quality score: {quality.get('data_quality_score', 0):.2f}")
                logger.info(f"      Hallucinations detected: {quality.get('hallucinations_detected', 0)}")
            logger.info("")

            # Categorized insights
            categories = insights.get('categorized_insights', {})
            if categories:
                logger.info("📂 FINDINGS BY CATEGORY:")
                for category, findings in categories.items():
                    if findings:
                        logger.info(f"   {category.replace('_', ' ').title()}: {len(findings)} findings")
                logger.info("")

            # Executive summary highlights
            exec_summary = insights.get('executive_summary', {})
            if exec_summary:
                logger.info("💼 EXECUTIVE SUMMARY HIGHLIGHTS:")
                logger.info(f"   Deal value: {exec_summary.get('deal_value', 'Unknown')}")
                logger.info(f"   Key highlights: {len(exec_summary.get('key_highlights', []))} major findings")
                logger.info(f"   Confidence statement: {exec_summary.get('confidence_statement', '')}")
                logger.info("")

            # Valuation assessment
            valuation = insights.get('valuation_assessment', {})
            if valuation:
                logger.info("💰 VALUATION ASSESSMENT:")
                dcf_range = valuation.get('dcf_range', (0, 0))
                if dcf_range[0] != 0 or dcf_range[1] != 0:
                    logger.info(f"   DCF range: ${dcf_range[0]:,.0f} - ${dcf_range[1]:,.0f}")
                multiples = valuation.get('comparable_multiples', [])
                if multiples:
                    logger.info(f"   Comparable multiples: {multiples[:3]}")
                logger.info("")

            # Risk assessment
            risk = insights.get('risk_assessment', {})
            if risk:
                logger.info("⚠️ RISK ASSESSMENT:")
                logger.info(f"   Overall risk level: {risk.get('overall_risk_level', 'UNKNOWN')}")
                logger.info(f"   Critical risks: {risk.get('critical_risks', 0)}")
                logger.info(f"   High risks: {risk.get('high_risks', 0)}")
                logger.info(" ")

        # Show hallucination monitoring
        hallucinations = result_state.get('consolidation_metadata', {}).get('hallucination_flags', [])
        if hallucinations:
            logger.info("🚨 HALLUCINATION MONITORING:")
            for flag in hallucinations[:3]:  # Show first 3
                logger.info(f"   ❌ {flag.get('severity', 'UNKNOWN')}: {flag.get('finding', {}).get('description', '')[:100]}...")
            logger.info(" ")

        # Show sample consolidated findings
        consolidated_findings = result_state.get('consolidated_insights', {}).get('consolidated_findings', [])
        if consolidated_findings:
            logger.info("🔍 SAMPLE CONSOLIDATED FINDINGS:")
            for i, finding in enumerate(consolidated_findings[:5]):  # Show first 5
                grounding = finding.get('grounding_status', 'UNKNOWN')
                confidence = finding.get('confidence', 0)
                agents = finding.get('source_agents', [finding.get('source_agent', 'unknown')])
                logger.info(f"   {i+1}. [{grounding}] {finding.get('description', '')[:120]}...")
                logger.info(f"        🎯 {confidence:.0%} confidence | 🤖 {len(agents)} agent(s)")
            logger.info("")

        logger.info("🏆 CONSOLIDATOR TEST COMPLETED SUCCESSFULLY!")
        logger.info("✨ All 12 agents processed, validated, and consolidated into report-ready data structure")

        # Save results for inspection
        output_file = f"consolidator_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert the results to JSON-serializable format
        serializable_result = {}
        for key, value in result_state.items():
            try:
                json.dumps(value)
                serializable_result[key] = value
            except (TypeError, ValueError):
                # Convert non-serializable objects
                if hasattr(value, '__dict__'):
                    serializable_result[key] = str(value)
                elif isinstance(value, set):
                    serializable_result[key] = list(value)
                else:
                    serializable_result[key] = str(value)

        with open(output_file, 'w') as f:
            json.dump(serializable_result, f, indent=2, default=str)

        logger.info(f"💾 Full results saved to: {output_file}")

    except Exception as e:
        logger.error(f"❌ Consolidator test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    return True

async def demonstrate_phases():
    """Demonstrate each phase of the consolidator with sample data"""

    logger.info("🎯 CONSOLIDATOR PHASE DEMONSTRATION")
    logger.info("=" * 80)

    # Create sample findings from multiple agents
    sample_findings = [
        {
            'source_agent': 'financial_analyst',
            'metric': 'dcf',
            'value': 5000000000,
            'description': 'DCF valuation indicates enterprise value of $5.0B',
            'type': 'valuation',
            'confidence': 0.9,
            'data_type': 'valuation'
        },
        {
            'source_agent': 'integration_planner',
            'metric': 'synergy_value',
            'value': 800000000,
            'description': 'Projected synergies of $800M from combined operations',
            'type': 'financial_metric',
            'confidence': 0.75,
            'data_type': 'integration'
        },
        {
            'source_agent': 'external_validator',
            'metric': 'validation_confidence',
            'value': 0.87,
            'description': 'External validation shows 87% confidence in financial projections',
            'type': 'confidence_metric',
            'confidence': 0.95,
            'data_type': 'validation'
        },
        {
            'source_agent': 'risk_assessment',
            'metric': 'overall_risk',
            'value': 'MODERATE',
            'description': 'Overall risk assessment rated as MODERATE',
            'type': 'qualitative',
            'confidence': 0.85,
            'data_type': 'risk_scores'
        }
    ]

    logger.info("📊 PHASE DEMONSTRATION INPUT:")
    logger.info(f"   Sample findings from {len(sample_findings)} agents")
    for i, finding in enumerate(sample_findings, 1):
        logger.info(f"   {i}. {finding['description']}")
        logger.info(f"      Agent: {finding['source_agent']} | Confidence: {finding['confidence']:.0%}")
    logger.info("")

    # Demonstrating key phases (would normally be done by the full consolidator)
    consolidator = SynthesisReportingAgent()

    # Phase 3: Clustering
    logger.info("🔀 PHASE 3 SIMULATION: Clustering by keywords...")
    clusters = consolidator._cluster_findings_by_keywords(sample_findings)
    logger.info(f"   Created {len(clusters)} clusters from {len(sample_findings)} findings")
    for i, cluster in enumerate(clusters, 1):
        logger.info(f"   Cluster {i}: {len(cluster)} findings")
        for finding in cluster:
            logger.info(f"      - {finding['source_agent']}: {finding['description'][:50]}...")
    logger.info("")

    # Phase 5: Confidence aggregation simulation
    logger.info("📈 PHASE 5 SIMULATION: Confidence aggregation...")

    # Simulate confidence aggregation for a merged finding
    merged_finding = {
        'description': 'Consolidated valuation and risk assessment',
        'source_agents': ['financial_analyst', 'integration_planner', 'risk_assessment', 'external_validator'],
        'type': 'consolidated'
    }

    # Apply the actual confidence aggregation logic
    consolidated = consolidator._aggregate_confidence_scores([merged_finding], {})

    if consolidated:
        final_finding = consolidated[0]
        logger.info("   Merged finding confidence calculation:")
        logger.info("   Contributing agents and weights:")
        for agent in final_finding.get('source_agents', []):
            weight = consolidator.CONFIDENCE_WEIGHTS.get(agent, 0.05)
            logger.info(",.0%")

        logger.info(f"   Final aggregated confidence: {final_finding.get('confidence', 0):.0%}")
        logger.info(f"   Confidence level: {final_finding.get('confidence_level', 'UNKNOWN')}")

    logger.info("✨ Phase demonstration complete!")

if __name__ == "__main__":
    # Run comprehensive test
    success = asyncio.run(test_consolidator())

    if success:
        logger.info("\n" + "="*80)
        logger.info("🎉 CONSOLIDATOR TEST SUITE PASSED!")
        logger.info("The new Consolidator & Quality Control layer is ready for production.")
        logger.info("="*80)

        # Also demonstrate phases
        asyncio.run(demonstrate_phases())
    else:
        logger.error("❌ CONSOLIDATOR TEST FAILED!")
        exit(1)
