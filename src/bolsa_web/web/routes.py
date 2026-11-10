from __future__ import annotations

import os
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, UploadFile

from bolsa_core.funding import fetch_all_automated_opportunities, opportunities_for_target_level
from bolsa_core.lattes import check_staleness, parse_lattes_pdf, parse_lattes_xml
from bolsa_core.positions import Position, fetch_sciencecareers_positions
from bolsa_core.profile import TARGET_LEVEL_DESCRIPTIONS
from bolsa_core.report import build_report, render_markdown
from bolsa_web.web.schemas import (
    ApplicableFundingRequest,
    ApplicableFundingResponse,
    LattesParseResponse,
    PositionSearchRequest,
    PositionSearchResponse,
    ReportRequest,
    ReportResponse,
    TargetLevelOption,
)

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".xml", ".pdf"}
PDF_RELIABILITY_WARNING = (
    "Extraído de PDF: menor confiabilidade que XML. Revise nome, formação, "
    "projetos e publicações antes de usar."
)

# Server-fixed, never client-supplied. Science Careers takes all keywords
# in a single search request, and each returned listing's own page is then
# fetched for its closing date and job type, so one call to this public
# endpoint triggers at most 1 + SCIENCECAREERS_LIMIT outbound requests.
#
# EURAXESS is deliberately not queried here: since 2026-11 it refuses any
# filtered or paginated search with a 403 anti-bot page (see bolsa-core's
# positions.py), leaving only its 10 newest listings regardless of the
# keywords -- about a dozen outbound requests per call for close to no
# relevant result.
SCIENCECAREERS_LIMIT = 15


@router.get("/target-levels", response_model=list[TargetLevelOption])
def list_target_levels() -> list[TargetLevelOption]:
    return [
        TargetLevelOption(value=value, description=description)
        for value, description in TARGET_LEVEL_DESCRIPTIONS.items()
    ]


@router.post("/lattes/parse", response_model=LattesParseResponse)
async def parse_lattes(file: UploadFile) -> LattesParseResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Envie um arquivo .xml ou .pdf do Lattes.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo maior que 10 MB.")

    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        if suffix == ".xml":
            extract = parse_lattes_xml(tmp_path)
            reliability_warning = None
        else:
            extract = parse_lattes_pdf(tmp_path)
            reliability_warning = PDF_RELIABILITY_WARNING
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível ler este arquivo como currículo Lattes.",
        ) from exc
    finally:
        os.unlink(tmp_path)

    return LattesParseResponse(
        extract=extract,
        staleness_warning=check_staleness(extract),
        reliability_warning=reliability_warning,
    )


def _fetch_automated_sources() -> list:
    with httpx.Client(timeout=30.0) as client:
        return fetch_all_automated_opportunities(client)


@router.post("/funding/applicable", response_model=ApplicableFundingResponse)
def applicable_funding(request: ApplicableFundingRequest) -> ApplicableFundingResponse:
    opportunities = opportunities_for_target_level(_fetch_automated_sources(), request.target_level)
    return ApplicableFundingResponse(target_level=request.target_level, opportunities=opportunities)


@router.post("/report", response_model=ReportResponse)
def build_candidate_report(request: ReportRequest) -> ReportResponse:
    opportunities = opportunities_for_target_level(
        _fetch_automated_sources(), request.profile.target_level
    )
    report = build_report(opportunities, fit_scores=[])
    return ReportResponse(
        markdown=render_markdown(report),
        json_report=report.model_dump(mode="json"),
    )


def _search_positions(keywords: list[str]) -> tuple[list[Position], list[str]]:
    """Return the listings found plus one message per source request that failed."""
    errors: list[str] = []
    with httpx.Client(timeout=30.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        positions = fetch_sciencecareers_positions(
            client,
            keywords,
            limit=SCIENCECAREERS_LIMIT,
            fetch_details=True,
            errors=errors,
        )
    return positions, errors


@router.post("/positions/search", response_model=PositionSearchResponse)
def search_positions(request: PositionSearchRequest) -> PositionSearchResponse:
    positions, source_errors = _search_positions(request.keywords)
    return PositionSearchResponse(
        keywords=request.keywords,
        positions=positions,
        source_errors=source_errors,
    )
