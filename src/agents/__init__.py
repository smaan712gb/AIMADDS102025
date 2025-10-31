# Agents module

from .base_agent import BaseAgent
from .project_manager import ProjectManagerAgent
from .data_ingestion import DataIngestionAgent
from .financial_analyst import FinancialAnalystAgent
from .legal_counsel import LegalCounselAgent
from .market_strategist import MarketStrategistAgent
from .integration_planner import IntegrationPlannerAgent
from .synthesis_reporting import SynthesisReportingAgent
from .competitive_benchmarking import CompetitiveBenchmarkingAgent
from .macroeconomic_analyst import MacroeconomicAnalystAgent
from .conversational_synthesis import ConversationalSynthesisAgent
from .external_validator import ExternalValidatorAgent
from .financial_deep_dive import FinancialDeepDiveAgent

__all__ = [
    'BaseAgent',
    'ProjectManagerAgent',
    'DataIngestionAgent',
    'FinancialAnalystAgent',
    'LegalCounselAgent',
    'MarketStrategistAgent',
    'IntegrationPlannerAgent',
    'SynthesisReportingAgent',
    'CompetitiveBenchmarkingAgent',
    'MacroeconomicAnalystAgent',
    'ConversationalSynthesisAgent',
    'ExternalValidatorAgent',
    'FinancialDeepDiveAgent',
]
