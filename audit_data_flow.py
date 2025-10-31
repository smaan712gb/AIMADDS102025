"""
Comprehensive Data Flow Audit Script
Verifies end-to-end data flow from agents → synthesis → reports
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

# Import all agents to test
from src.agents.financial_analyst import FinancialAnalystAgent
from src.agents.financial_deep_dive import FinancialDeepDiveAgent
from src.agents.deal_structuring import DealStructuringAgent
from src.agents.tax_structuring import TaxStructuringAgent
from src.agents.integration_planner import IntegrationPlannerAgent
from src.agents.synthesis_reporting import SynthesisReportingAgent

# Import report generator
try:
    from src.outputs.report_generator import ReportGenerator
    REPORT_GEN_AVAILABLE = True
except ImportError:
    REPORT_GEN_AVAILABLE = False
    logger.warning("ReportGenerator not available")


class DataFlowAuditor:
    """Audits complete data flow through the system"""
    
    def __init__(self):
        self.findings = {
            'timestamp': datetime.now().isoformat(),
            'financial_analyst': {},
            'downstream_agents': {},
            'synthesis_agent': {},
            'report_generation': {},
            'issues': [],
            'recommendations': []
        }
    
    async def run_comprehensive_audit(self, test_ticker: str = 'AAPL'):
        """Run complete audit"""
        logger.info(f"=== Starting Comprehensive Data Flow Audit for {test_ticker} ===")
        
        # Phase 1: Test Financial Analyst Output
        logger.info("\n--- Phase 1: Financial Analyst Output ---")
        state = await self.audit_financial_analyst(test_ticker)
        
        # Phase 2: Test Downstream Agent Data Usage
        logger.info("\n--- Phase 2: Downstream Agent Data Usage ---")
        await self.audit_downstream_agents(state)
        
        # Phase 3: Test Synthesis Agent Mapping
        logger.info("\n--- Phase 3: Synthesis Agent Mapping ---")
        await self.audit_synthesis_mapping(state)
        
        # Phase 4: Test Report Generation
        logger.info("\n--- Phase 4: Report Generation ---")
        await self.audit_report_generation(state)
        
        # Phase 5: NEW - Test Report Fallback & Transformation
        logger.info("\n--- Phase 5: Report Fallback & Transformation ---")
        await self.audit_report_fallback_transformation(state)
        
        # Generate Report
        self.generate_audit_report()
        
        return self.findings
    
    async def audit_financial_analyst(self, ticker: str) -> Dict[str, Any]:
        """Audit financial analyst output"""
        logger.info(f"Testing financial_analyst for {ticker}...")
        
        state = {
            'target_ticker': ticker,
            'target_company': 'Test Company'
        }
        
        analyst = FinancialAnalystAgent()
        result = await analyst.run(state)
        
        # Check normalized_financials
        normalized = state.get('normalized_financials', {})
        
        findings = {
            'has_normalized_financials': 'normalized_financials' in state,
            'has_historical': 'historical' in normalized,
            'has_forecast': 'forecast' in normalized,
            'has_adjustments': 'adjustments' in normalized,
            'has_quality_score': 'quality_score' in normalized,
            'has_cagr_analysis': 'cagr_analysis' in normalized,
            'ebitda_calculated': state.get('ebitda') is not None,
            'data_keys': list(state.keys())
        }
        
        self.findings['financial_analyst'] = findings
        
        # Log issues
        if not findings['has_normalized_financials']:
            self.findings['issues'].append({
                'severity': 'CRITICAL',
                'component': 'financial_analyst',
                'issue': 'normalized_financials not created',
                'recommendation': 'Fix financial_analyst to create normalized_financials dict'
            })
        
        if not findings['ebitda_calculated']:
            self.findings['issues'].append({
                'severity': 'HIGH',
                'component': 'financial_analyst',
                'issue': 'EBITDA not calculated',
                'recommendation': 'Ensure _ensure_ebitda_calculated() is called'
            })
        
        logger.info(f"✓ Financial Analyst Output: {json.dumps(findings, indent=2)}")
        
        return state
    
    async def audit_downstream_agents(self, state: Dict[str, Any]):
        """Audit downstream agent data source usage"""
        logger.info("Testing downstream agents...")
        
        agents_to_test = [
            ('financial_deep_dive', FinancialDeepDiveAgent(), 'Should use normalized'),
            ('deal_structuring', DealStructuringAgent(), 'Should use normalized'),
            ('integration_planner', IntegrationPlannerAgent(), 'Should use normalized'),
            ('tax_structuring', TaxStructuringAgent(), 'Should use original'),
        ]
        
        for agent_name, agent_instance, expected_behavior in agents_to_test:
            logger.info(f"Testing {agent_name}...")
            
            try:
                # Run agent
                agent_result = await agent_instance.run(state)
                
                # Check what data it used (simplified check)
                agent_findings = {
                    'ran_successfully': 'error' not in agent_result.get('errors', []),
                    'expected_behavior': expected_behavior,
                    'has_output': bool(agent_result.get('data', {}))
                }
                
                self.findings['downstream_agents'][agent_name] = agent_findings
                
                if not agent_findings['ran_successfully']:
                    self.findings['issues'].append({
                        'severity': 'HIGH',
                        'component': agent_name,
                        'issue': f'{agent_name} failed to run',
                        'recommendation': f'Debug {agent_name} agent'
                    })
                
                logger.info(f"  {agent_name}: {agent_findings}")
                
            except Exception as e:
                logger.error(f"  {agent_name} ERROR: {e}")
                self.findings['issues'].append({
                    'severity': 'CRITICAL',
                    'component': agent_name,
                    'issue': f'{agent_name} crashed: {str(e)}',
                    'recommendation': f'Fix {agent_name} agent exception handling'
                })
    
    async def audit_synthesis_mapping(self, state: Dict[str, Any]):
        """Audit synthesis agent receives all agent outputs"""
        logger.info("Testing synthesis agent mapping...")
        
        # Check if all agents are in agent_outputs
        agent_outputs = state.get('agent_outputs', [])
        
        expected_agents = [
            'project_manager',
            'financial_analyst',
            'financial_deep_dive',
            'legal_counsel',
            'market_strategist',
            'competitive_benchmarking',
            'macroeconomic_analyst',
            'risk_assessment',
            'tax_structuring',
            'deal_structuring',  # NEW
            'integration_planner',
            'external_validator',
            'synthesis_reporting'
        ]
        
        present_agents = [output.get('agent_name') for output in agent_outputs]
        
        missing_agents = [agent for agent in expected_agents if agent not in present_agents]
        
        findings = {
            'expected_agent_count': len(expected_agents),
            'present_agent_count': len(present_agents),
            'present_agents': present_agents,
            'missing_agents': missing_agents,
            'all_agents_mapped': len(missing_agents) == 0
        }
        
        self.findings['synthesis_agent'] = findings
        
        if missing_agents:
            self.findings['issues'].append({
                'severity': 'CRITICAL',
                'component': 'synthesis_agent',
                'issue': f'Missing agents in synthesis: {", ".join(missing_agents)}',
                'recommendation': 'Add missing agents to synthesis agent mapping'
            })
        
        logger.info(f"✓ Synthesis Mapping: {json.dumps(findings, indent=2)}")
    
    async def audit_report_generation(self, state: Dict[str, Any]):
        """Audit report generation data flow"""
        logger.info("Testing report generation...")
        
        if not REPORT_GEN_AVAILABLE:
            self.findings['issues'].append({
                'severity': 'CRITICAL',
                'component': 'report_generation',
                'issue': 'ReportGenerator not available',
                'recommendation': 'Fix ReportGenerator import'
            })
            return
        
        generator = ReportGenerator()
        
        # Check which report methods exist
        findings = {
            'has_standard_method': hasattr(generator, 'generate_all_reports'),
            'has_revolutionary_method': hasattr(generator, 'generate_all_revolutionary_reports'),
            'methods': [m for m in dir(generator) if 'generate' in m and not m.startswith('_')]
        }
        
        self.findings['report_generation'] = findings
        
        # Check for architecture redundancy
        if findings['has_standard_method'] and findings['has_revolutionary_method']:
            self.findings['issues'].append({
                'severity': 'MEDIUM',
                'component': 'report_generation',
                'issue': 'Both standard AND revolutionary report methods exist',
                'recommendation': 'Remove standard reports, keep only revolutionary'
            })
        
        logger.info(f"✓ Report Generation: {json.dumps(findings, indent=2)}")
    
    async def audit_report_fallback_transformation(self, state: Dict[str, Any]):
        """
        NEW: Test revolutionary reports fallback & transformation logic
        Verifies reports can transform agent data even without synthesis
        """
        logger.info("Testing revolutionary reports fallback & transformation...")
        
        findings = {
            'can_access_agent_outputs': False,
            'can_transform_financial_data': False,
            'can_generate_with_fallback': False,
            'fallback_data_quality': 'unknown',
            'transformation_errors': []
        }
        
        try:
            # Test 1: Can reports access agent_outputs array?
            agent_outputs = state.get('agent_outputs', [])
            findings['can_access_agent_outputs'] = len(agent_outputs) > 0
            
            # Test 2: Can reports transform agent data?
            financial_agent_data = None
            for output in agent_outputs:
                if output.get('agent_name') == 'financial_analyst':
                    financial_agent_data = output.get('data', {})
                    break
            
            if not financial_agent_data:
                # Fallback: Try direct state access
                financial_agent_data = state.get('financial_analyst', {})
            
            if financial_agent_data:
                # Test transformation: Extract key fields reports need
                try:
                    # Reports need: normalized_financials, valuation, health, etc.
                    required_fields = {
                        'normalized_financials': financial_agent_data.get('normalized_financials'),
                        'advanced_valuation': financial_agent_data.get('advanced_valuation'),
                        'financial_health': financial_agent_data.get('financial_health'),
                        'ratio_analysis': financial_agent_data.get('ratio_analysis')
                    }
                    
                    # Check if fields are present and non-empty
                    present_fields = {k: v is not None and v != {} for k, v in required_fields.items()}
                    
                    findings['can_transform_financial_data'] = any(present_fields.values())
                    findings['transformed_fields'] = present_fields
                    findings['fallback_data_quality'] = 'good' if sum(present_fields.values()) >= 2 else 'poor'
                    
                except Exception as e:
                    findings['transformation_errors'].append(f"Transformation failed: {str(e)}")
            
            # Test 3: Simulate report generation with fallback data
            try:
                if findings['can_transform_financial_data']:
                    # Simulate what revolutionary reports do
                    mock_report_data = {
                        'source': 'agent_outputs_fallback',
                        'financial_section': {
                            'normalized_data': required_fields.get('normalized_financials', {}),
                            'valuation': required_fields.get('advanced_valuation', {}),
                            'health': required_fields.get('financial_health', {})
                        }
                    }
                    
                    # Check if report data is usable
                    is_usable = (
                        mock_report_data['financial_section']['normalized_data'] and
                        mock_report_data['financial_section']['valuation']
                    )
                    
                    findings['can_generate_with_fallback'] = is_usable
                    findings['mock_report_keys'] = list(mock_report_data['financial_section'].keys())
                
            except Exception as e:
                findings['transformation_errors'].append(f"Report generation test failed: {str(e)}")
        
        except Exception as e:
            findings['transformation_errors'].append(f"Fallback test failed: {str(e)}")
        
        self.findings['report_fallback_transformation'] = findings
        
        # Log issues
        if not findings['can_transform_financial_data']:
            self.findings['issues'].append({
                'severity': 'CRITICAL',
                'component': 'report_fallback',
                'issue': 'Revolutionary reports cannot transform agent data',
                'recommendation': 'Add transformation logic to revolutionary report generators'
            })
        
        if not findings['can_generate_with_fallback']:
            self.findings['issues'].append({
                'severity': 'HIGH',
                'component': 'report_fallback',
                'issue': 'Reports cannot generate without synthesized_data',
                'recommendation': 'Add robust fallback logic: synthesized_data → agent_outputs → state'
            })
        
        logger.info(f"✓ Report Fallback Test: {json.dumps(findings, indent=2)}")
    
    def generate_audit_report(self):
        """Generate final audit report"""
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE DATA FLOW AUDIT REPORT")
        logger.info("="*80)
        
        # Summary
        critical_issues = [i for i in self.findings['issues'] if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.findings['issues'] if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.findings['issues'] if i['severity'] == 'MEDIUM']
        
        logger.info(f"\nISSUE SUMMARY:")
        logger.info(f"  CRITICAL: {len(critical_issues)}")
        logger.info(f"  HIGH:     {len(high_issues)}")
        logger.info(f"  MEDIUM:   {len(medium_issues)}")
        logger.info(f"  TOTAL:    {len(self.findings['issues'])}")
        
        # Detailed issues
        if self.findings['issues']:
            logger.info("\nDETAILED ISSUES:")
            for i, issue in enumerate(self.findings['issues'], 1):
                logger.info(f"\n{i}. [{issue['severity']}] {issue['component']}")
                logger.info(f"   Issue: {issue['issue']}")
                logger.info(f"   Recommendation: {issue['recommendation']}")
        else:
            logger.info("\n✓ NO ISSUES FOUND - System is healthy!")
        
        # Save to file
        output_file = f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.findings, f, indent=2)
        
        logger.info(f"\n✓ Audit report saved to: {output_file}")
        logger.info("="*80)


async def main():
    """Run audit"""
    auditor = DataFlowAuditor()
    findings = await auditor.run_comprehensive_audit('AAPL')
    
    return findings


if __name__ == "__main__":
    asyncio.run(main())
