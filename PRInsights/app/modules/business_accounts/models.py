from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class Repository(Base):
    """
    GitHub Repository (Business Account).
    This is your "business unit" - each repo is tracked separately.
    Each repo has its own webhook_secret for signature verification.
    """
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    github_repo_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    full_name = Column(String, nullable=False, index=True)  # owner/name
    description = Column(String, nullable=True)
    
    # GitHub webhook secret for this repo (set when registering)
    webhook_secret = Column(String, nullable=True)
    
    # Is this repo actively tracked?
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pull_requests = relationship("PullRequest", back_populates="repository")
    
    def __repr__(self):
        return f"<Repository {self.full_name}>"
