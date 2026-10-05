from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bolsa_finder.funding import FundingOpportunity
from bolsa_finder.profile import TARGET_LEVEL_DESCRIPTIONS
from bolsa_finder.web import routes
from bolsa_finder.web.app import create_app

FIXTURE_XML = Path(__file__).parent / "fixtures" / "lattes_sample.xml"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _opportunity(name: str, target_levels: list[str]) -> FundingOpportunity:
    return FundingOpportunity(
        name=name,
        agency="Test",
        country_or_region="Testland",
        target_levels=target_levels,
        amount="unknown",
        deadline="unknown",
        url="https://example.com/x",
        consulted_at=date(2026, 1, 1),
        eligibility_brazilian="confirmed",
        eligibility_evidence="quote",
    )


@pytest.fixture
def fixed_sources(monkeypatch) -> None:
    sources = [
        _opportunity("Sandwich A", ["sanduiche"]),
        _opportunity("Pleno B", ["pleno"]),
        _opportunity("Pos C", ["posdoc"]),
    ]
    monkeypatch.setattr(routes, "_fetch_automated_sources", lambda: sources)


def _profile_payload(target_level: str = "sanduiche") -> dict:
    return {
        "research_areas": ["applied statistics"],
        "methods": ["mixed models"],
        "cv_summary": "PhD candidate.",
        "academic_stage": {"program_started": "2022-03-01"},
        "target_level": target_level,
        "languages": [{"language": "english", "proficiency": "avancado"}],
        "nationality": "brazilian",
        "geographic_restrictions": [],
        "funding_required": True,
        "time_window": {"earliest_start": "2026-06-01"},
    }


def test_target_levels_lists_every_option(client: TestClient) -> None:
    response = client.get("/api/target-levels")

    assert response.status_code == 200
    values = {item["value"] for item in response.json()}
    assert values == set(TARGET_LEVEL_DESCRIPTIONS.keys())


def test_parse_xml_returns_extract_and_no_pdf_warning(client: TestClient) -> None:
    with FIXTURE_XML.open("rb") as handle:
        response = client.post(
            "/api/lattes/parse",
            files={"file": ("lattes.xml", handle, "application/xml")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["extract"]["full_name"] == "Fulana de Tal"
    assert body["extract"]["source_format"] == "xml"
    assert body["reliability_warning"] is None
    assert body["staleness_warning"] is not None  # fixture is older than 6 months


def test_parse_response_contains_no_pii(client: TestClient) -> None:
    with FIXTURE_XML.open("rb") as handle:
        response = client.post(
            "/api/lattes/parse",
            files={"file": ("lattes.xml", handle, "application/xml")},
        )

    text = response.text
    for leaked in ["000.000.000-00", "Rua Ficticia", "(00) 00000-0000", "01011995"]:
        assert leaked not in text


def test_parse_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/api/lattes/parse",
        files={"file": ("lattes.docx", b"irrelevant", "application/octet-stream")},
    )

    assert response.status_code == 415


def test_parse_rejects_oversized_upload(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 100)

    response = client.post(
        "/api/lattes/parse",
        files={"file": ("lattes.xml", b"x" * 500, "application/xml")},
    )

    assert response.status_code == 413


def test_parse_returns_422_for_unreadable_file(client: TestClient) -> None:
    response = client.post(
        "/api/lattes/parse",
        files={"file": ("lattes.xml", b"<not-closed", "application/xml")},
    )

    assert response.status_code == 422


def test_parse_removes_temporary_file_after_request(client: TestClient, monkeypatch) -> None:
    created: list[str] = []
    real_mkstemp = routes.tempfile.mkstemp

    def recording_mkstemp(*args, **kwargs):
        fd, path = real_mkstemp(*args, **kwargs)
        created.append(path)
        return fd, path

    monkeypatch.setattr(routes.tempfile, "mkstemp", recording_mkstemp)

    with FIXTURE_XML.open("rb") as handle:
        client.post("/api/lattes/parse", files={"file": ("lattes.xml", handle, "application/xml")})

    assert len(created) == 1
    assert not Path(created[0]).exists()


def test_parse_removes_temporary_file_even_when_parsing_fails(client: TestClient, monkeypatch) -> None:
    created: list[str] = []
    real_mkstemp = routes.tempfile.mkstemp

    def recording_mkstemp(*args, **kwargs):
        fd, path = real_mkstemp(*args, **kwargs)
        created.append(path)
        return fd, path

    monkeypatch.setattr(routes.tempfile, "mkstemp", recording_mkstemp)

    client.post("/api/lattes/parse", files={"file": ("lattes.xml", b"<not-closed", "application/xml")})

    assert len(created) == 1
    assert not Path(created[0]).exists()


def test_applicable_funding_filters_by_target_level(client: TestClient, fixed_sources) -> None:
    response = client.post("/api/funding/applicable", json={"target_level": "sanduiche"})

    assert response.status_code == 200
    names = [o["name"] for o in response.json()["opportunities"]]
    assert names == ["Sandwich A"]


def test_applicable_funding_empty_for_uncovered_level(client: TestClient, fixed_sources) -> None:
    response = client.post("/api/funding/applicable", json={"target_level": "mestrado"})

    assert response.status_code == 200
    assert response.json()["opportunities"] == []


def test_applicable_funding_rejects_unknown_level(client: TestClient, fixed_sources) -> None:
    response = client.post("/api/funding/applicable", json={"target_level": "graduacao"})

    assert response.status_code == 422


def test_report_contains_only_opportunities_for_profile_level(client: TestClient, fixed_sources) -> None:
    response = client.post("/api/report", json={"profile": _profile_payload("pleno")})

    assert response.status_code == 200
    body = response.json()
    assert "Pleno B" in body["markdown"]
    assert "Sandwich A" not in body["markdown"]
    assert body["json_report"]["funding_opportunities"][0]["name"] == "Pleno B"


def test_report_rejects_invalid_profile(client: TestClient, fixed_sources) -> None:
    payload = _profile_payload()
    payload["research_areas"] = [""]

    response = client.post("/api/report", json={"profile": payload})

    assert response.status_code == 422
