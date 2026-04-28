from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class PullRequest(Base):
    """
    GitHub Pull Request.
    Belongs to a Repository, authored by a User.
    """
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    github_pr_id = Column(Integer, nullable=False, index=True)
    github_pr_number = Column(Integer, nullable=False)
    
    # Foreign keys
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # PR details
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String, nullable=False, default="open")  # open, closed, merged
    
    # Timestamps from GitHub
    gh_created_at = Column(DateTime(timezone=True), nullable=False)
    gh_updated_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Our timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Raw payload for debugging/reprocessing
    raw_payload = Column(JSON, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    author = relationship("User", back_populates="pull_requests")
    comments = relationship("Comment", back_populates="pull_request")
    
    # Unique constraint: PR number is unique within a repo
    __table_args__ = (
        # Composite unique constraint
    )
    
    def __repr__(self):
        return f"<PullRequest #{self.github_pr_number} in repo_id={self.repo_id}>"


class Comment(Base):
    """
    GitHub PR Comment (issue comment or review comment).
    Belongs to a PullRequest, authored by a User.
    """
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    github_comment_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Foreign keys
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Comment details
    body = Column(Text, nullable=False)
    comment_type = Column(String, default="issue_comment")  # issue_comment, review_comment
    
    # Timestamps from GitHub
    gh_created_at = Column(DateTime(timezone=True), nullable=False)
    gh_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Our timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Raw payload for debugging
    raw_payload = Column(JSON, nullable=True)
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="comments")
    user = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment {self.github_comment_id} on PR {self.pr_id}>"
