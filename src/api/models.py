"""
Pydantic models for API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DealType(str, Enum):
    """Deal type enumeration"""
    FINANCIAL = "financial"
    STRATEGIC = "strategic"


class AgentStatusEnum(str, Enum):
    """Agent status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"


# Authentication Models
class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


# Analysis Models
class AnalysisRequest(BaseModel):
    """Request to start a new analysis"""
    project_name: str = Field(..., description="User-friendly project name")
    acquirer_ticker: Optional[str] = Field(None, description="Acquirer company ticker")
    target_ticker: str = Field(..., description="Target company ticker")
    deal_type: DealType = Field(..., description="Type of deal")
    deal_value: Optional[float] = Field(None, description="Deal value in USD")
    investment_thesis: Optional[str] = Field(None, description="Investment thesis")
    strategic_rationale: Optional[str] = Field(None, description="Strategic rationale")


class AnalysisResponse(BaseModel):
    """Response when analysis is created"""
    job_id: str
    project_name: str
    status: str
    created_at: datetime


class AgentStatus(BaseModel):
    """Individual agent status"""
    agent_name: str
    status: AgentStatusEnum
    current_task: Optional[str] = None
    progress_percentage: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisProgress(BaseModel):
    """Overall analysis progress"""
    job_id: str
    project_name: str
    overall_status: str
    progress_percentage: int
    current_agent: Optional[str] = None
    current_task: Optional[str] = None
    agents: List[AgentStatus]
    started_at: datetime
    estimated_completion: Optional[datetime] = None


class AnalysisResult(BaseModel):
    """Analysis results summary"""
    job_id: str
    project_name: str
    status: str
    valuation_range: Optional[Dict[str, float]] = None
    top_risks: List[str] = Field(default_factory=list)
    top_opportunities: List[str] = Field(default_factory=list)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None
    reports: Dict[str, str] = Field(default_factory=dict)  # report_type -> file_path


class AnalysisList(BaseModel):
    """List of analyses"""
    analyses: List[AnalysisResponse]
    total: int


# WebSocket Models
class WSMessage(BaseModel):
    """WebSocket message"""
    type: str  # status_update, error, completion
    job_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusUpdate(BaseModel):
    """Status update message"""
    agent_name: str
    status: AgentStatusEnum
    message: str
    details: Optional[List[str]] = None
    progress_percentage: int = 0
