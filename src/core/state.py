"""
State management for multi-agent workflow using LangGraph
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import operator


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentMetadata(TypedDict):
    """Document metadata"""
    filename: str
    file_type: str
    file_size: int
    upload_date: str
    category: str
    processed: bool


@dataclass
class Document:
    """Document data class for handling uploaded documents"""
    document_id: str
    filename: str
    filepath: str
    document_type: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FinancialMetrics(TypedDict):
    """Financial metrics data"""
    revenue: Optional[float]
    ebitda: Optional[float]
    net_income: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    equity: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    roe: Optional[float]
    roa: Optional[float]


class RiskAssessment(TypedDict):
    """Risk assessment data"""
    category: str
    severity: str  # low, medium, high, critical
    description: str
    impact: str
    mitigation: Optional[str]
    identified_by: str


class AgentOutput(TypedDict):
    """Output from individual agent"""
    agent_name: str
    status: AgentStatus
    timestamp: str
    data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


class DiligenceState(TypedDict):
    """
    Main state object for the M&A diligence workflow
    This state is passed between agents in the LangGraph
    """
    # Deal Information
    deal_id: str
    target_company: str
    target_ticker: Optional[str]
    acquirer_company: Optional[str]
    acquirer_ticker: Optional[str]  # CRITICAL: Add acquirer ticker field
    deal_type: str  # acquisition, merger, investment
    deal_value: Optional[float]
    deal_structure: Optional[str]
    expected_close_date: Optional[str]
    currency: str
    
    # Investment Thesis
    investment_thesis: str
    strategic_rationale: str
    target_synergies: Optional[float]
    
    # Document Management
    documents: Annotated[List[DocumentMetadata], operator.add]
    document_index: Dict[str, str]  # filename -> vector_id
    
    # Agent Execution Tracking
    agent_statuses: Dict[str, AgentStatus]
    agent_outputs: Annotated[List[AgentOutput], operator.add]
    current_agent: Optional[str]
    
    # Financial Analysis
    financial_data: Dict[str, Any]
    financial_metrics: Optional[FinancialMetrics]
    valuation_models: Dict[str, Dict[str, Any]]
    
    # Legal Analysis
    legal_documents: List[str]
    legal_risks: Annotated[List[RiskAssessment], operator.add]
    compliance_status: Dict[str, str]
    
    # Market Analysis
    market_data: Dict[str, Any]
    competitive_landscape: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    
    # Integration Planning
    integration_roadmap: Dict[str, Any]
    synergy_analysis: Dict[str, Any]
    organizational_design: Dict[str, Any]
    
    # Synthesis & Reporting
    executive_summary: Optional[str]
    key_findings: Annotated[List[str], operator.add]
    critical_risks: Annotated[List[RiskAssessment], operator.add]
    recommendations: Annotated[List[str], operator.add]
    
    # Workflow Control
    workflow_started: str
    workflow_completed: Optional[str]
    errors: Annotated[List[str], operator.add]
    progress_percentage: int
    
    # Output Management
    output_files: Dict[str, str]  # output_type -> file_path
    dashboard_url: Optional[str]
    
    # Additional Metadata
    metadata: Dict[str, Any]


def create_initial_state(
    deal_id: str,
    target_company: str,
    investment_thesis: str,
    strategic_rationale: str,
    target_ticker: Optional[str] = None,
    acquirer_company: Optional[str] = None,
    acquirer_ticker: Optional[str] = None,  # CRITICAL: Add acquirer ticker parameter
    deal_type: str = "acquisition",
    deal_value: Optional[float] = None,
    deal_structure: Optional[str] = None,
    expected_close_date: Optional[str] = None,
    currency: str = "USD"
) -> DiligenceState:
    """
    Create initial state for a new diligence workflow
    
    Args:
        deal_id: Unique identifier for the deal
        target_company: Name of the target company
        investment_thesis: Investment thesis for the deal
        strategic_rationale: Strategic rationale for the deal
        target_ticker: Stock ticker (if public company)
        deal_type: Type of deal (acquisition, merger, investment)
        deal_value: Deal value in specified currency
        currency: Currency code (default: USD)
    
    Returns:
        DiligenceState object with initial values
    """
    return DiligenceState(
        # Deal Information
        deal_id=deal_id,
        target_company=target_company,
        target_ticker=target_ticker,
        acquirer_company=acquirer_company,
        acquirer_ticker=acquirer_ticker,  # CRITICAL: Store acquirer ticker
        deal_type=deal_type,
        deal_value=deal_value,
        deal_structure=deal_structure,
        expected_close_date=expected_close_date,
        currency=currency,
        
        # Investment Thesis
        investment_thesis=investment_thesis,
        strategic_rationale=strategic_rationale,
        target_synergies=None,
        
        # Document Management
        documents=[],
        document_index={},
        
        # Agent Execution Tracking
        agent_statuses={
            "project_manager": AgentStatus.PENDING,
            "data_ingestion": AgentStatus.PENDING,
            "financial_analyst": AgentStatus.PENDING,
            "legal_counsel": AgentStatus.PENDING,
            "market_strategist": AgentStatus.PENDING,
            "competitive_benchmarking": AgentStatus.PENDING,
            "macroeconomic_analyst": AgentStatus.PENDING,
            "integration_planner": AgentStatus.PENDING,
            "external_validator": AgentStatus.PENDING,
            "synthesis_reporting": AgentStatus.PENDING,
            "conversational_synthesis": AgentStatus.PENDING
        },
        agent_outputs=[],
        current_agent=None,
        
        # Financial Analysis
        financial_data={},
        financial_metrics=None,
        valuation_models={},
        
        # Legal Analysis
        legal_documents=[],
        legal_risks=[],
        compliance_status={},
        
        # Market Analysis
        market_data={},
        competitive_landscape={},
        sentiment_analysis={},
        
        # Integration Planning
        integration_roadmap={},
        synergy_analysis={},
        organizational_design={},
        
        # Synthesis & Reporting
        executive_summary=None,
        key_findings=[],
        critical_risks=[],
        recommendations=[],
        
        # Workflow Control
        workflow_started=datetime.utcnow().isoformat(),
        workflow_completed=None,
        errors=[],
        progress_percentage=0,
        
        # Output Management
        output_files={},
        dashboard_url=None,
        
        # Additional Metadata
        metadata={}
    )


def update_agent_status(
    state: DiligenceState,
    agent_name: str,
    status: AgentStatus
) -> DiligenceState:
    """
    Update the status of an agent
    
    Args:
        state: Current state
        agent_name: Name of the agent
        status: New status
    
    Returns:
        Updated state
    """
    state["agent_statuses"][agent_name] = status
    state["current_agent"] = agent_name if status == AgentStatus.RUNNING else state["current_agent"]
    
    # Calculate progress
    completed = sum(1 for s in state["agent_statuses"].values() if s == AgentStatus.COMPLETED)
    total = len(state["agent_statuses"])
    state["progress_percentage"] = int((completed / total) * 100)
    
    return state


def add_agent_output(
    state: DiligenceState,
    agent_name: str,
    status: AgentStatus,
    data: Dict[str, Any],
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    recommendations: Optional[List[str]] = None
) -> DiligenceState:
    """
    Add output from an agent to the state
    
    Args:
        state: Current state
        agent_name: Name of the agent
        status: Agent execution status
        data: Agent output data
        errors: List of errors encountered
        warnings: List of warnings
        recommendations: List of recommendations
    
    Returns:
        Updated state
    """
    output = AgentOutput(
        agent_name=agent_name,
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        data=data,
        errors=errors or [],
        warnings=warnings or [],
        recommendations=recommendations or []
    )
    
    state["agent_outputs"].append(output)
    
    return state
