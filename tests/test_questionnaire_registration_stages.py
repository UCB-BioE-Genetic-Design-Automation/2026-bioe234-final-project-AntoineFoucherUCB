"""Two-step header vs PI saves for questionnaire_parsing."""

import json
from pathlib import Path

import pytest

from modules.biosafety.tools import questionnaire_parsing as qp_module


@pytest.fixture
def isolated_parser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    snap = tmp_path / "bua_state_snapshot.json"
    monkeypatch.setattr(qp_module, "_state_file", lambda: snap)
    qp_module._reset_state()
    return qp_module.questionnaire_parsing


def test_project_registration_ignores_pi_fields(isolated_parser):
    r = isolated_parser(
        "project_registration",
        json.dumps(
            {
                "university": "UC Berkeley",
                "state": "CA",
                "bua_number": "BUA-1",
                "project_title": "Test project",
                "pi_name": "Should not persist",
                "pi_info": {"name": "Also should not persist"},
            }
        ),
    )
    assert r["status"] == "success"
    assert r["next_stage_to_fetch"] == "project_and_pi"
    pi = (r.get("current_state") or {}).get("pi_info") or {}
    assert pi.get("name", "") == ""


def test_project_and_pi_after_registration_keeps_header(isolated_parser):
    isolated_parser(
        "project_registration",
        json.dumps(
            {
                "university": "UC Berkeley",
                "state": "CA",
                "bua_number": "BUA-1",
                "project_title": "Test project",
            }
        ),
    )
    r2 = isolated_parser(
        "project_and_pi",
        json.dumps(
            {
                "pi_info": {
                    "name": "Dr. Example",
                    "title": "Professor",
                    "department": "BioE",
                    "building": "Stanley",
                    "room": "100",
                    "phone": "555-0000",
                    "email_address": "pi@berkeley.edu",
                    "fax": "",
                }
            }
        ),
    )
    assert r2["status"] == "success"
    st = r2.get("current_state") or {}
    assert st.get("university") == "UC Berkeley"
    assert st.get("project_title") == "Test project"
    assert (st.get("pi_info") or {}).get("name") == "Dr. Example"


def test_lab_contact_only_additional_contacts_fills_pi_too(isolated_parser):
    """When the LLM saves only lab_contact row, PI section should mirror it (same person)."""
    isolated_parser(
        "project_registration",
        json.dumps({"university": "State U", "state": "AL", "bua_number": "", "project_title": "T"}),
    )
    isolated_parser("project_and_pi", json.dumps({}))
    r = isolated_parser(
        "additional_contacts",
        json.dumps(
            {
                "co_investigator_info": {},
                "lab_contact_info": {
                    "name": "Taylor Example",
                    "title": "",
                    "department": "BioE",
                    "building": "",
                    "room": "",
                    "phone": "",
                    "email_address": "t@univ.edu",
                    "fax": "",
                },
            }
        ),
    )
    assert r["status"] == "success"
    st = r.get("current_state") or {}
    assert (st.get("pi_info") or {}).get("name") == "Taylor Example"
    assert (st.get("lab_contact_info") or {}).get("name") == "Taylor Example"
    assert (st.get("pi_info") or {}).get("department") == "BioE"


def test_project_and_pi_pi_only_payload_does_not_wipe_university(isolated_parser):
    isolated_parser(
        "project_registration",
        json.dumps(
            {
                "university": "MIT",
                "state": "MA",
                "bua_number": "",
                "project_title": "RNA work",
            }
        ),
    )
    r = isolated_parser(
        "project_and_pi",
        json.dumps(
            {
                "pi_info": {
                    "name": "Dr. Only Pi Key",
                    "title": "",
                    "department": "",
                    "building": "",
                    "room": "",
                    "phone": "",
                    "email_address": "",
                    "fax": "",
                }
            }
        ),
    )
    assert r["status"] == "success"
    st = r.get("current_state") or {}
    assert st.get("university") == "MIT"
    assert (st.get("pi_info") or {}).get("name") == "Dr. Only Pi Key"


def test_empty_repeat_project_and_pi_keeps_prior_pi(isolated_parser):
    """Stale/empty questionnaire_parsing retries must not wipe a previously saved PI row."""
    isolated_parser(
        "project_registration",
        json.dumps(
            {
                "university": "U",
                "state": "TX",
                "bua_number": "",
                "project_title": "P",
            }
        ),
    )
    isolated_parser(
        "project_and_pi",
        json.dumps({"pi_info": {"name": "Dr. Keen", "title": "", "department": "", "building": "", "room": "", "phone": "", "email_address": "k@x.edu", "fax": ""}}),
    )
    r2 = isolated_parser("project_and_pi", json.dumps({"pi_info": {}}))
    assert (r2.get("current_state") or {}).get("pi_info", {}).get("name") == "Dr. Keen"

