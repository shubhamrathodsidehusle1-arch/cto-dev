"""Project API models."""
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


class ProjectUpdate(BaseModel):
    """Project update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


class ProjectResponse(BaseModel):
    """Project response model."""
    id: str
    userId: str
    name: str
    description: Optional[str]
    createdAt: str
    updatedAt: str
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Project list response."""
    projects: list[ProjectResponse]
    total: int
    skip: int
    take: int
