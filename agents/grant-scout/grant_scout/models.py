"""Data models shared by the search and drafting steps."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class Grant(BaseModel):
    name: str
    organization: str
    url: str = Field(description="Official page for the grant or its application")
    deadline: Optional[str] = Field(
        description="Next application deadline as YYYY-MM-DD, or null if rolling/unknown"
    )
    deadline_is_rolling: bool = Field(description="True if applications are accepted on a rolling basis")
    award_amount: Optional[str] = Field(description="Award amount as stated, e.g. '$10,000'")
    eligibility: str = Field(description="Who can apply: location, career stage, citizenship, etc.")
    focus: str = Field(description="What the grant funds, e.g. emerging designers, sustainability")
    application_questions: List[str] = Field(
        description="Questions or required sections of the application, as published. Empty if not found."
    )
    required_materials: List[str] = Field(
        description="Attachments required, e.g. portfolio, budget, CV, lookbook"
    )

    def deadline_date(self) -> Optional[date]:
        if not self.deadline:
            return None
        try:
            return date.fromisoformat(self.deadline[:10])
        except ValueError:
            return None


class GrantList(BaseModel):
    grants: List[Grant]


class Answer(BaseModel):
    question: str
    answer: str


class ApplicationDraft(BaseModel):
    grant_name: str
    eligibility_assessment: str = Field(
        description="Whether the applicant appears eligible, based only on the profile, and any doubts"
    )
    answers: List[Answer]
    missing_information: List[str] = Field(
        description="Facts the applicant must supply before submitting"
    )
    materials_checklist: List[str]
