from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from bolsa_core.funding import FundingOpportunity
from bolsa_core.lattes import LattesExtract
from bolsa_core.positions import Position
from bolsa_core.profile import Profile, TargetLevel

# The keywords are forwarded to a third-party job board as a search query
# (see routes._search_positions), so both bounds are part of the trust
# boundary.
MAX_KEYWORDS = 5
MAX_KEYWORD_LENGTH = 60

Keyword = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=MAX_KEYWORD_LENGTH),
]


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


class PositionSearchRequest(BaseModel):
    keywords: list[Keyword] = Field(min_length=1, max_length=MAX_KEYWORDS)


class PositionSearchResponse(BaseModel):
    keywords: list[str]
    positions: list[Position]
    # One entry per source request that failed. Empty `positions` with an
    # empty list here means "nothing matched"; with entries, "couldn't ask".
    source_errors: list[str]
