from __future__ import annotations

from pydantic import BaseModel

from bolsa_finder.lattes import LattesExtract


class TargetLevelOption(BaseModel):
    value: str
    description: str


class LattesParseResponse(BaseModel):
    extract: LattesExtract
    staleness_warning: str | None
    reliability_warning: str | None
