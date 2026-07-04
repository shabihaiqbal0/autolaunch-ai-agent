from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class ProjectSpec:
    name: str
    description: str
    stack: list[str] = field(default_factory=list)
    repository_url: Optional[str] = None
    requirements: list[str] = field(default_factory=list)
