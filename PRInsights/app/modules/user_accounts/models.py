from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class User(Base):
    """
    Global GitHub user identity.
    One row per GitHub user - NOT duplicated per repo.
    Relationships to repos are implicit via PRs/comments.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    avatar_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pull_requests = relationship("PullRequest", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username} (github_id={self.github_id})>"
