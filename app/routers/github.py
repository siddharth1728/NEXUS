from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.dependencies.auth import get_current_user
from app.schemas.project import GitHubRepository
from app.services import github_service
from app.models.user import User

router = APIRouter(prefix="/github", tags=["github"])

@router.get("/repositories", response_model=List[GitHubRepository])
async def get_repositories(current_user: User = Depends(get_current_user)):
    if not current_user.profile or not current_user.profile.github_username:
        raise HTTPException(status_code=400, detail="GitHub username not set in profile")
    
    try:
        repos_data = await github_service.get_user_repositories(current_user.profile.github_username)
        repos = []
        for repo in repos_data:
            repos.append(GitHubRepository(
                id=repo["id"],
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                default_branch=repo.get("default_branch", "main"),
                html_url=repo["html_url"]
            ))
        return repos
    except github_service.GitHubRateLimitException as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch GitHub repositories")
