from pydantic import BaseModel
from typing import List, Optional, Literal


class UserProfile(BaseModel):
    role: str
    year: str
    program: str


class FacultyMember(BaseModel):
    name: str
    department: str
    expertise: str
    imageUrl: str
    bio: Optional[str]


class InvokeRequest(BaseModel):
    grantId: int
    grantName: str
    matchCriteria: str
    eligibility: str
    userProfile: UserProfile
    facultyList: List[FacultyMember]


class Collaborator(BaseModel):
    name: str
    department: str
    expertise: str
    relevanceScore: float


class ComplianceItem(BaseModel):
    task: str
    category: Literal["RAMP", "COI", "IRB", "Policy"]
    status: Literal["green", "yellow", "red"]


class ResultPayload(BaseModel):
    proposalDraft: str
    collaborators: List[Collaborator]
    matchScore: float
    matchJustification: str
    complianceChecklist: List[ComplianceItem]


class JSONLine(BaseModel):
    agent: str
    step: str
    output: Optional[dict]
    done: bool
