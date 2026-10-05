from __future__ import annotations

from pydantic import BaseModel

from bolsa_finder.funding import FundingOpportunity
from bolsa_finder.lattes import LattesExtract
from bolsa_finder.profile import Profile, TargetLevel


class TargetLevelOption(BaseModel):
    value: str
    description: str


class LattesParseResponse(BaseModel):
    extract: LattesExtract
    staleness_warning: str | None
    reliability_warning: str | None


class ApplicableFundingRequest(BaseModel):
    target_level: TargetLevel


class ApplicableFundingResponse(BaseModel):
    target_level: TargetLevel
    opportunities: list[FundingOpportunity]


class ReportRequest(BaseModel):
    profile: Profile


class ReportResponse(BaseModel):
    markdown: str
    json_report: dict
