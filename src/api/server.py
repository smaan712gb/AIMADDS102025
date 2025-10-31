"""
FastAPI server for M&A Diligence Swarm
"""
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import asyncio
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.api.models import (
    UserCreate, UserLogin, Token, UserResponse,
    AnalysisRequest, AnalysisResponse, AnalysisProgress,
    AnalysisResult, AnalysisList, WSMessage, StatusUpdate,
    AgentStatusEnum
)
from src.api.auth import AuthService
from src.api.job_manager import get_job_manager
from src.api.orchestrator import AnalysisOrchestrator
from src.api.copilot_service_enhanced import get_enhanced_copilot_service

# Initialize FastAPI app
app = FastAPI(
    title="M&A Diligence Swarm API",
    description="AI-powered M&A due diligence platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
auth_service = AuthService()
job_manager = get_job_manager()
orchestrator = AnalysisOrchestrator()
copilot_service = get_enhanced_copilot_service()


# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token_data


# Dependency for admin-only routes
async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, tags=["auth"])
async def register_user(user_data: UserCreate, admin: dict = Depends(require_admin)):
    """Register a new user (admin only)"""
    try:
        user = auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            role=user_data.role.value
        )
        return UserResponse(
            id=user['id'],
            email=user['email'],
            role=user['role'],
            created_at=datetime.fromisoformat(user['created_at'])
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login", response_model=Token, tags=["auth"])
async def login(credentials: UserLogin):
    """Login and get access token"""
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(user)
    return Token(access_token=access_token)


@app.get("/api/auth/me", response_model=UserResponse, tags=["auth"])
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user information"""
    user_data = auth_service.get_user_by_email(user['sub'])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user_data['id'],
        email=user_data['email'],
        role=user_data['role'],
        created_at=datetime.fromisoformat(user_data['created_at'])
    )


@app.get("/api/auth/users", response_model=list[UserResponse], tags=["auth"])
async def list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    try:
        users = auth_service.list_all_users()
        return [
            UserResponse(
                id=user['id'],
                email=user['email'],
                role=user['role'],
                created_at=datetime.fromisoformat(user['created_at'])
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/auth/users/{user_id}", tags=["auth"])
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Delete a user (admin only)"""
    try:
        # Prevent admin from deleting themselves
        if user_id == admin['user_id']:
            raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
        
        success = auth_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYSIS ROUTES
# ============================================================================

@app.post("/api/analysis/start", response_model=AnalysisResponse, tags=["analysis"])
async def start_analysis(request: AnalysisRequest, user: dict = Depends(get_current_user)):
    """Start a new analysis"""
    try:
        # Create job
        job = job_manager.create_job(
            project_name=request.project_name,
            target_ticker=request.target_ticker,
            deal_type=request.deal_type.value,
            acquirer_ticker=request.acquirer_ticker,
            deal_value=request.deal_value,
            investment_thesis=request.investment_thesis,
            strategic_rationale=request.strategic_rationale,
            user_id=user['user_id']
        )
        
        # Start orchestration in background
        asyncio.create_task(orchestrator.run_analysis(job['job_id']))
        
        return AnalysisResponse(
            job_id=job['job_id'],
            project_name=job['project_name'],
            status=job['status'],
            created_at=job['created_at']
        )
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{job_id}/progress", response_model=AnalysisProgress, tags=["analysis"])
async def get_analysis_progress(job_id: str, user: dict = Depends(get_current_user)):
    """Get analysis progress"""
    progress = job_manager.get_job_progress(job_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisProgress(**progress)


@app.get("/api/analysis/{job_id}/result", response_model=AnalysisResult, tags=["analysis"])
async def get_analysis_result(job_id: str, user: dict = Depends(get_current_user)):
    """Get analysis result"""
    result = job_manager.get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResult(**result)


@app.get("/api/analysis/list", response_model=AnalysisList, tags=["analysis"])
async def list_analyses(user: dict = Depends(get_current_user)):
    """List all analyses for current user"""
    # Admin can see all, regular users only see their own
    user_id = None if user.get('role') == 'admin' else user['user_id']
    
    analyses = job_manager.list_jobs(user_id)
    
    return AnalysisList(
        analyses=[
            AnalysisResponse(**a)
            for a in analyses
        ],
        total=len(analyses)
    )


@app.get("/api/analysis/{job_id}/download/{file_type}", tags=["analysis"])
async def download_report(
    job_id: str,
    file_type: str,
    user: dict = Depends(get_current_user)
):
    """Download analysis report"""
    result = job_manager.get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Map frontend file types to backend keys
    file_type_map = {
        'pdf': 'pdf_full',  # Full PDF report
        'pptx': 'ppt',  # PowerPoint deck
        'excel': 'excel'  # Excel workbook
    }
    
    backend_key = file_type_map.get(file_type, file_type)
    
    # Get file path
    file_path = result['reports'].get(backend_key)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Report type '{file_type}' not found")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Determine media type
    media_types = {
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    media_type = media_types.get(file_type, 'application/octet-stream')
    
    # Create proper filename with extension
    extensions = {
        'pdf': '.pdf',
        'excel': '.xlsx',
        'pptx': '.pptx'
    }
    
    # Use project name from result for filename
    project_name = result.get('project_name', 'Analysis').replace(' ', '_')
    filename = f"{project_name}_Report{extensions.get(file_type, '')}"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


# ============================================================================
# COPILOT ROUTES
# ============================================================================

@app.get("/api/v1/copilot/{job_id}/init", tags=["copilot"])
async def initialize_copilot(job_id: str, user: dict = Depends(get_current_user)):
    """Initialize copilot chat session for an analysis"""
    try:
        init_data = await copilot_service.initialize_chat(job_id)
        
        if "error" in init_data:
            raise HTTPException(status_code=404, detail=init_data["error"])
        
        return init_data
    except Exception as e:
        logger.error(f"Error initializing copilot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/copilot/{job_id}/chat", tags=["copilot"])
async def chat_with_copilot(
    job_id: str,
    request: dict,
    user: dict = Depends(get_current_user)
):
    """
    Send a message to the copilot and get streaming response.
    
    Request body:
    {
        "message": "User's question",
        "conversation_history": [...]  // Optional
    }
    """
    from fastapi.responses import StreamingResponse
    
    try:
        message = request.get("message")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        conversation_history = request.get("conversation_history", [])
        
        async def generate_response():
            """Generator for streaming response"""
            async for chunk in copilot_service.process_message(
                job_id, message, conversation_history
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error in copilot chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/copilot/{job_id}/export", tags=["copilot"])
async def export_copilot_conversation(job_id: str, user: dict = Depends(get_current_user)):
    """Export conversation history to JSON"""
    try:
        file_path = await copilot_service.export_conversation(job_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="No conversation history found")
        
        return FileResponse(
            path=file_path,
            media_type="application/json",
            filename=f"conversation_{job_id}.json"
        )
    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ROUTES
# ============================================================================

@app.websocket("/ws/analysis/{job_id}")
async def websocket_analysis(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time analysis updates"""
    await websocket.accept()
    
    # Add WebSocket to job manager
    job_manager.add_websocket(job_id, websocket)
    
    try:
        # Send initial status
        progress = job_manager.get_job_progress(job_id)
        if progress:
            await websocket.send_json({
                "type": "status_update",
                "job_id": job_id,
                "data": progress,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (ping/pong)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove WebSocket from job manager
        job_manager.remove_websocket(job_id, websocket)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health", tags=["system"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🚀 M&A Diligence Swarm API starting...")
    
    # Initialize database in production
    import os
    if os.getenv("ENVIRONMENT") == "production":
        try:
            from src.database import init_db, check_db_connection
            logger.info("Initializing production database...")
            
            # Check connection first
            if check_db_connection():
                logger.info("✓ Database connection successful")
                init_db()
                logger.info("✓ Database initialized")
            else:
                logger.warning("⚠️  Database connection failed - will retry on first request")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            logger.warning("Continuing without database - file-based storage will be used")
    
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down M&A Diligence Swarm API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
