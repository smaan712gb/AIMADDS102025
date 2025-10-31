"""
Job manager for handling analysis jobs
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from uuid import uuid4
from loguru import logger

from src.core.state import create_initial_state, DiligenceState, AgentStatus as StateAgentStatus
from src.api.models import AgentStatusEnum


class JobManager:
    """Manages analysis jobs"""
    
    def __init__(self, jobs_dir: str = "data/jobs"):
        """Initialize job manager
        
        Args:
            jobs_dir: Directory to store job data
        """
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Active jobs and their states
        self.active_jobs: Dict[str, DiligenceState] = {}
        self.job_tasks: Dict[str, asyncio.Task] = {}
        
        # WebSocket connections for each job
        self.job_websockets: Dict[str, List] = {}
    
    def create_job(
        self,
        project_name: str,
        target_ticker: str,
        deal_type: str,
        acquirer_ticker: Optional[str] = None,
        deal_value: Optional[float] = None,
        investment_thesis: Optional[str] = None,
        strategic_rationale: Optional[str] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Create a new analysis job
        
        Args:
            project_name: User-friendly project name
            target_ticker: Target company ticker
            deal_type: Type of deal (financial/strategic)
            acquirer_ticker: Acquirer company ticker
            deal_value: Deal value
            investment_thesis: Investment thesis
            strategic_rationale: Strategic rationale
            user_id: User ID who created the job
        
        Returns:
            Job data
        """
        job_id = str(uuid4())
        deal_id = f"DEAL-{datetime.utcnow().strftime('%Y%m%d')}-{job_id[:8].upper()}"
        
        # Create initial state
        state = create_initial_state(
            deal_id=deal_id,
            target_company=target_ticker,  # Will be resolved to company name later
            target_ticker=target_ticker,
            acquirer_company=acquirer_ticker,  # Company name (will be resolved to name later)
            acquirer_ticker=acquirer_ticker,  # CRITICAL FIX: Pass ticker explicitly
            deal_type=deal_type,
            deal_value=deal_value,
            investment_thesis=investment_thesis or "Comprehensive due diligence analysis",
            strategic_rationale=strategic_rationale or "Strategic acquisition evaluation",
            currency="USD"
        )
        
        # Add metadata
        state['metadata']['job_id'] = job_id
        state['metadata']['project_name'] = project_name
        state['metadata']['user_id'] = user_id
        state['metadata']['status'] = 'pending'
        
        # Store state
        self.active_jobs[job_id] = state
        self._save_job(job_id, state)
        
        logger.info(f"Created job {job_id}: {project_name}")
        
        return {
            "job_id": job_id,
            "deal_id": deal_id,
            "project_name": project_name,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
    
    def get_job(self, job_id: str) -> Optional[DiligenceState]:
        """Get job state
        
        Args:
            job_id: Job ID
        
        Returns:
            Job state if found
        """
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Try to load from disk
        return self._load_job(job_id)
    
    def get_job_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job progress
        
        Args:
            job_id: Job ID
        
        Returns:
            Progress data
        """
        state = self.get_job(job_id)
        if not state:
            return None
        
        # Convert agent statuses
        agents = []
        for agent_name, status in state['agent_statuses'].items():
            agents.append({
                "agent_name": agent_name.replace('_', ' ').title(),
                "status": self._convert_agent_status(status),
                "current_task": None,
                "progress_percentage": 0
            })
        
        return {
            "job_id": job_id,
            "project_name": state['metadata'].get('project_name', 'Unknown'),
            "overall_status": state['metadata'].get('status', 'pending'),
            "progress_percentage": state['progress_percentage'],
            "current_agent": state.get('current_agent'),
            "current_task": None,
            "agents": agents,
            "started_at": state['workflow_started'],  # Already ISO format string
            "estimated_completion": None
        }
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result
        
        Args:
            job_id: Job ID
        
        Returns:
            Result data
        """
        state = self.get_job(job_id)
        if not state:
            return None
        
        # Extract key information
        valuation_models = state.get('valuation_models', {})
        dcf = valuation_models.get('dcf', {})
        
        # Get valuation range
        valuation_range = None
        if dcf and 'enterprise_value' in dcf:
            ev = dcf['enterprise_value']
            valuation_range = {
                "low": ev * 0.9,
                "mid": ev,
                "high": ev * 1.1
            }
        
        # Extract risks and opportunities
        risks = [r['description'] for r in state.get('critical_risks', [])[:3]]
        opportunities = state.get('recommendations', [])[:3]
        
        # Get financial metrics
        metrics = state.get('financial_metrics') or {}
        
        # Get output files
        reports = state.get('output_files', {})
        
        return {
            "job_id": job_id,
            "project_name": state['metadata'].get('project_name', 'Unknown'),
            "status": state['metadata'].get('status', 'pending'),
            "valuation_range": valuation_range,
            "top_risks": risks,
            "top_opportunities": opportunities,
            "key_metrics": metrics,
            "completed_at": datetime.fromisoformat(state['workflow_completed']) if state['workflow_completed'] else None,
            "reports": reports
        }
    
    def list_jobs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all jobs
        
        Args:
            user_id: Filter by user ID
        
        Returns:
            List of jobs
        """
        jobs = []
        
        # Get all job files
        for job_file in self.jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    state = json.load(f)
                
                # Filter by user if specified
                if user_id and state['metadata'].get('user_id') != user_id:
                    continue
                
                jobs.append({
                    "job_id": state['metadata']['job_id'],
                    "project_name": state['metadata'].get('project_name', 'Unknown'),
                    "status": state['metadata'].get('status', 'pending'),
                    "created_at": datetime.fromisoformat(state['workflow_started'])
                })
            except Exception as e:
                logger.error(f"Error loading job {job_file}: {e}")
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jobs
    
    def add_websocket(self, job_id: str, websocket):
        """Add WebSocket connection for job updates
        
        Args:
            job_id: Job ID
            websocket: WebSocket connection
        """
        if job_id not in self.job_websockets:
            self.job_websockets[job_id] = []
        self.job_websockets[job_id].append(websocket)
    
    def remove_websocket(self, job_id: str, websocket):
        """Remove WebSocket connection
        
        Args:
            job_id: Job ID
            websocket: WebSocket connection
        """
        if job_id in self.job_websockets:
            try:
                self.job_websockets[job_id].remove(websocket)
            except ValueError:
                pass
    
    async def broadcast_update(self, job_id: str, message: Dict[str, Any]):
        """Broadcast update to all WebSocket connections for a job
        
        Args:
            job_id: Job ID
            message: Message to broadcast
        """
        if job_id not in self.job_websockets:
            return
        
        dead_connections = []
        for ws in self.job_websockets[job_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                dead_connections.append(ws)
        
        # Remove dead connections
        for ws in dead_connections:
            self.remove_websocket(job_id, ws)
    
    def _save_job(self, job_id: str, state: DiligenceState):
        """Save job to disk
        
        Args:
            job_id: Job ID
            state: Job state
        """
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_job(self, job_id: str) -> Optional[DiligenceState]:
        """Load job from disk
        
        Args:
            job_id: Job ID
        
        Returns:
            Job state if found
        """
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    def _convert_agent_status(self, status: StateAgentStatus) -> AgentStatusEnum:
        """Convert internal agent status to API status
        
        Args:
            status: Internal status
        
        Returns:
            API status enum
        """
        status_map = {
            StateAgentStatus.PENDING: AgentStatusEnum.PENDING,
            StateAgentStatus.RUNNING: AgentStatusEnum.RUNNING,
            StateAgentStatus.COMPLETED: AgentStatusEnum.COMPLETED,
            StateAgentStatus.FAILED: AgentStatusEnum.FAILED,
            StateAgentStatus.SKIPPED: AgentStatusEnum.COMPLETED  # Treat skipped as completed
        }
        return status_map.get(status, AgentStatusEnum.PENDING)


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
