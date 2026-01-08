"""Project API routes."""
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, status
from prisma.models import User

from app.api.models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)
from app.api.dependencies import get_current_user
from app.db.prisma import get_prisma
from app.utils.errors import DatabaseError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
) -> ProjectResponse:
    """Create a new project.

    Args:
        project_data: Project creation data
        current_user: Current authenticated user

    Returns:
        Created project

    Raises:
        DatabaseError: If project creation fails
    """
    db = await get_prisma()
    
    try:
        project = await db.project.create(
            data={
                "userId": current_user.id,
                "name": project_data.name,
                "description": project_data.description
            }
        )
        logger.info("Project created", project_id=project.id, user_id=current_user.id)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        logger.error("Failed to create project", error=str(e))
        raise DatabaseError(f"Failed to create project: {str(e)}")


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    take: int = Query(50, ge=1, le=100, description="Number of records to return"),
    current_user: User = Depends(get_current_user)
) -> ProjectListResponse:
    """List current user's projects with pagination.

    Args:
        skip: Number of records to skip
        take: Number of records to return
        current_user: Current authenticated user

    Returns:
        Paginated project list
    """
    db = await get_prisma()
    
    try:
        projects = await db.project.find_many(
            where={"userId": current_user.id},
            skip=skip,
            take=take,
            order={"createdAt": "desc"}
        )
        
        total = await db.project.count(where={"userId": current_user.id})
        
        return ProjectListResponse(
            projects=[ProjectResponse.model_validate(project) for project in projects],
            total=total,
            skip=skip,
            take=take
        )
    except Exception as e:
        logger.error("Failed to list projects", error=str(e))
        raise DatabaseError(f"Failed to list projects: {str(e)}")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> ProjectResponse:
    """Get project by ID.

    Args:
        project_id: Project ID
        current_user: Current authenticated user

    Returns:
        Project details

    Raises:
        HTTPException: If project not found or user doesn't have access
    """
    db = await get_prisma()
    
    project = await db.project.find_unique(where={"id": project_id})
    
    if not project:
        logger.warning("Project not found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user owns the project
    if project.userId != current_user.id:
        logger.warning(
            "Unauthorized project access attempt",
            project_id=project_id,
            user_id=current_user.id,
            owner_id=project.userId
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user)
) -> ProjectResponse:
    """Update project.

    Args:
        project_id: Project ID
        project_update: Project update data
        current_user: Current authenticated user

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or user doesn't have access
        DatabaseError: If update fails
    """
    db = await get_prisma()
    
    # Verify project exists and user owns it
    project = await db.project.find_unique(where={"id": project_id})
    
    if not project:
        logger.warning("Project not found for update", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.userId != current_user.id:
        logger.warning(
            "Unauthorized project update attempt",
            project_id=project_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Build update data (only include non-None fields)
    update_data: dict = {}
    if project_update.name is not None:
        update_data["name"] = project_update.name
    if project_update.description is not None:
        update_data["description"] = project_update.description
    
    try:
        updated_project = await db.project.update(
            where={"id": project_id},
            data=update_data
        )
        logger.info("Project updated", project_id=project_id, user_id=current_user.id)
        return ProjectResponse.model_validate(updated_project)
    except Exception as e:
        logger.error("Failed to update project", project_id=project_id, error=str(e))
        raise DatabaseError(f"Failed to update project: {str(e)}")


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete project.

    Args:
        project_id: Project ID
        current_user: Current authenticated user

    Raises:
        HTTPException: If project not found or user doesn't have access
        DatabaseError: If deletion fails
    """
    db = await get_prisma()
    
    # Verify project exists and user owns it
    project = await db.project.find_unique(where={"id": project_id})
    
    if not project:
        logger.warning("Project not found for deletion", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.userId != current_user.id:
        logger.warning(
            "Unauthorized project deletion attempt",
            project_id=project_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    try:
        await db.project.delete(where={"id": project_id})
        logger.info("Project deleted", project_id=project_id, user_id=current_user.id)
    except Exception as e:
        logger.error("Failed to delete project", project_id=project_id, error=str(e))
        raise DatabaseError(f"Failed to delete project: {str(e)}")
