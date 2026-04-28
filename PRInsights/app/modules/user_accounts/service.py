from sqlalchemy.orm import Session
from app.modules.user_accounts.models import User


class UserService:
    """Service for managing GitHub users"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def upsert_user(self, github_id: int, username: str, avatar_url: str = None) -> User:
        """
        Create or update a GitHub user.
        Idempotent - safe to call multiple times with same data.
        """
        user = self.db.query(User).filter(User.github_id == github_id).first()
        
        if user:
            # Update existing user info (username/avatar may change)
            user.username = username
            if avatar_url:
                user.avatar_url = avatar_url
        else:
            # Create new user
            user = User(
                github_id=github_id,
                username=username,
                avatar_url=avatar_url
            )
            self.db.add(user)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_github_id(self, github_id: int) -> User | None:
        """Get user by GitHub ID"""
        return self.db.query(User).filter(User.github_id == github_id).first()
    
    def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
