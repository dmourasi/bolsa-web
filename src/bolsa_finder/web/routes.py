from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from bolsa_finder.lattes import check_staleness, parse_lattes_pdf, parse_lattes_xml
from bolsa_finder.profile import TARGET_LEVEL_DESCRIPTIONS
from bolsa_finder.web.schemas import LattesParseResponse, TargetLevelOption

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".xml", ".pdf"}
PDF_RELIABILITY_WARNING = (
    "Extraído de PDF: menor confiabilidade que XML. Revise nome, formação, "
    "projetos e publicações antes de usar."
)


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
