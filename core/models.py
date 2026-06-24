"""Core data models for Archon 3.0"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class TechStack(BaseModel):
    language: str = Field(..., description="Primary programming language")
    framework: Optional[str] = Field(None)
    database: Optional[str] = Field(None)
    frontend: Optional[str] = Field(None)

class ModuleSpec(BaseModel):
    module_id: str
    name: str
    dependencies: List[str] = Field(default_factory=list)
    files: List[str]
    description: str
    priority: str = "normal"

class Phase(BaseModel):
    phase_id: int
    name: str
    modules: List[ModuleSpec]

class IntegrationRequirements(BaseModel):
    shared_models: bool = True
    api_gateway: bool = False
    error_handling: str = "centralized"

class Deployment(BaseModel):
    containerization: str = "docker"
    orchestration: str = "docker-compose"
    ci_cd: str = "github-actions"

class DeploymentPlan(BaseModel):
    project_name: str
    tech_stack: TechStack
    phases: List[Phase]
    integration_requirements: IntegrationRequirements = Field(default_factory=IntegrationRequirements)
    deployment: Deployment = Field(default_factory=Deployment)

class ArchitectureBlueprint(BaseModel):
    project_name: str
    execution_order: List[str]
    module_specs: Dict[str, ModuleSpec]
    integration_plan: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]

class ValidationIssue(BaseModel):
    severity: str
    type: str
    description: str
    fix_suggestion: str
    line_number: Optional[int] = None

class ValidationResult(BaseModel):
    module_id: str
    passed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    retry_count: int = 0

class GeneratedModule(BaseModel):
    module_id: str
    files: Dict[str, str]
    validation_result: Optional[ValidationResult] = None

class IntegratedProject(BaseModel):
    project_name: str
    modules: List[GeneratedModule]
    integration_files: Dict[str, str]
    requirements_txt: str
    readme: str
    docker_files: Dict[str, str]
    success: bool
    execution_report: Dict[str, Any]
