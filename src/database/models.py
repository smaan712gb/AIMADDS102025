"""
Database models for PostgreSQL
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, default=lambda: f"user-{uuid.uuid4().hex[:12]}")
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # 'admin' or 'user'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }


class Analysis(Base):
    """Analysis job model"""
    __tablename__ = "analyses"
    
    job_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    target_ticker = Column(String(10), nullable=False)
    deal_type = Column(String(50), nullable=False)
    acquirer_ticker = Column(String(10), nullable=True)
    deal_value = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    
    # Analysis data (stored as JSON)
    state_data = Column(JSON, nullable=True)
    progress_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "project_name": self.project_name,
            "target_ticker": self.target_ticker,
            "deal_type": self.deal_type,
            "acquirer_ticker": self.acquirer_ticker,
            "deal_value": self.deal_value,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ConversationHistory(Base):
    """Copilot conversation history"""
    __tablename__ = "conversations"
    
    id = Column(String(50), primary_key=True, default=lambda: f"conv-{uuid.uuid4().hex[:12]}")
    job_id = Column(String(50), ForeignKey("analyses.job_id"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    
    # Message data
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata
    tokens_used = Column(Integer, nullable=True)
    model = Column(String(50), nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "tokens_used": self.tokens_used,
            "model": self.model
        }
