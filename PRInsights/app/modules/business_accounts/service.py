from sqlalchemy.orm import Session
from app.modules.business_accounts.models import Repository


class RepositoryService:
    """Service for managing GitHub repositories"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_business_account(
        self,
        github_repo_id: int,
        name: str,
        owner: str,
        webhook_secret: str,
        description: str = None
    ) -> Repository:
        """
        Register a new business account (repository) with its webhook secret.
        Call this when onboarding a new repo.
        """
        existing = self.db.query(Repository).filter(
            Repository.github_repo_id == github_repo_id
        ).first()
        
        if existing:
            raise ValueError(f"Repository {owner}/{name} already registered")
        
        repo = Repository(
            github_repo_id=github_repo_id,
            name=name,
            owner=owner,
            full_name=f"{owner}/{name}",
            description=description,
            webhook_secret=webhook_secret,
            is_active=True
        )
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def upsert_repository(
        self,
        github_repo_id: int,
        name: str,
        owner: str,
        description: str = None
    ) -> Repository:
        """
        Create or update a repository from webhook events.
        Does NOT set webhook_secret (that's done during registration).
        Idempotent - safe to call multiple times.
        """
        repo = self.db.query(Repository).filter(
            Repository.github_repo_id == github_repo_id
        ).first()
        
        full_name = f"{owner}/{name}"
        
        if repo:
            repo.name = name
            repo.owner = owner
            repo.full_name = full_name
            if description:
                repo.description = description
        else:
            repo = Repository(
                github_repo_id=github_repo_id,
                name=name,
                owner=owner,
                full_name=full_name,
                description=description
            )
            self.db.add(repo)
        
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def update_webhook_secret(self, repo_id: int, webhook_secret: str) -> Repository:
        """Update webhook secret for a repository"""
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")
        
        repo.webhook_secret = webhook_secret
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def get_by_github_id(self, github_repo_id: int) -> Repository | None:
        """Get repository by GitHub ID"""
        return self.db.query(Repository).filter(
            Repository.github_repo_id == github_repo_id
        ).first()
    
    def get_by_full_name(self, owner: str, name: str) -> Repository | None:
        """Get repository by owner/name"""
        full_name = f"{owner}/{name}"
        return self.db.query(Repository).filter(
            Repository.full_name == full_name
        ).first()
    
    def get_all_repositories(self, skip: int = 0, limit: int = 100) -> list[Repository]:
        """Get all repositories with pagination"""
        return self.db.query(Repository).offset(skip).limit(limit).all()
