"""Tests for `modules.biosafety.tools.questionnaire_parsing` (staged BUA JSON → state)."""

from __future__ import annotations

import json


def test_questionnaire_parsing_full_pipeline(isolated_questionnaire_parser):
    p = isolated_questionnaire_parser

    r0 = p(
        "project_info",
        json.dumps(
            {
                "university": "UC Berkeley",
                "state": "CA",
                "bua_number": "X-99",
                "project_title": "Test project",
            }
        ),
    )
    assert r0["status"] == "success"
    assert r0["next_stage_to_fetch"] == "pi_info"

    r1 = p(
        "pi_info",
        json.dumps(
            {
                "pi_info": {
                    "name": "Dr. Example",
                    "title": "",
                    "department": "BioE",
                    "building": "",
                    "room": "",
                    "phone": "",
                    "email_address": "pi@school.edu",
                    "fax": "",
                }
            }
        ),
    )
    assert r1["status"] == "success"
    pi = r1["current_state"]["pi_info"]
    assert pi["name"] == "Dr. Example"
    assert pi["department"] == "BioE"

    r2 = p(
        "personnel",
        json.dumps({"personnel": [{"name": "Student", "phone": "111"}]}),
    )
    assert r2["status"] == "success"

    r3 = p(
        "room_usage",
        json.dumps(
            {
                "irb_approval_sought": False,
                "iacuc_approval_sought": False,
                "room_usage": [
                    {
                        "building": "Stanley",
                        "room_number": "101",
                        "biosafety_level": "1",
                        "activities": [],
                        "equipment": [],
                    }
                ],
            }
        ),
    )
    assert r3["status"] == "success"
    assert r3["current_state"]["room_usage"][0]["biosafety_level"] == "BL1"

    r4 = p(
        "biological_agents",
        json.dumps(
            {
                "biological_agents": [
                    {
                        "scientific_name": "Escherichia coli",
                        "common_name": "",
                        "cdc_select_agent": False,
                    }
                ]
            }
        ),
    )
    assert r4["status"] == "success"
    assert r4["current_state"]["biological_agents"][0]["scientific_name"] == "Escherichia coli"

    r5 = p(
        "submission",
        json.dumps(
            {
                "project_summary": {
                    "project_goal": "Learn",
                    "experimental_procedure": "Grow cultures",
                    "containment": "BL1",
                    "protective_equipment": "coat",
                    "transportation_methods": "",
                    "decontamination_methods": "",
                    "waste_disposal": "",
                    "spill_emergency_procedures": "",
                }
            }
        ),
    )
    assert r5["status"] == "success"
    assert r5["next_stage_to_fetch"] == "complete"
    assert r5["current_state"]["project_summary"]["project_goal"] == "Learn"


def test_questionnaire_parsing_legacy_lab_identity_alias_maps_to_project_info(
    isolated_questionnaire_parser,
):
    r = isolated_questionnaire_parser(
        "lab_identity",
        json.dumps(
            {"university": "State U", "state": "AL", "bua_number": "", "project_title": "T"}
        ),
    )
    assert r["status"] == "success"
    assert r["next_stage_to_fetch"] == "pi_info"


def test_questionnaire_parsing_malformed_json(isolated_questionnaire_parser):
    r = isolated_questionnaire_parser("project_info", "{not json}")
    assert r["status"] == "error"


def test_questionnaire_parsing_unknown_stage(isolated_questionnaire_parser):
    r = isolated_questionnaire_parser(
        "not_a_real_stage",
        json.dumps({"university": "X"}),
    )
    assert r["status"] == "error"
    assert "Unknown stage" in r["message"]


# --- Header vs PI persistence (often confused by models) --------------------


def test_project_info_ignores_pi_fields(isolated_questionnaire_parser):
    r = isolated_questionnaire_parser(
        "project_info",
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
    assert r["next_stage_to_fetch"] == "pi_info"
    pi = (r.get("current_state") or {}).get("pi_info") or {}
    assert pi.get("name", "") == ""


def test_pi_after_project_info_keeps_header(isolated_questionnaire_parser):
    isolated_questionnaire_parser(
        "project_info",
        json.dumps(
            {
                "university": "UC Berkeley",
                "state": "CA",
                "bua_number": "BUA-1",
                "project_title": "Test project",
            }
        ),
    )
    r2 = isolated_questionnaire_parser(
        "pi_info",
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


def test_lab_contact_only_additional_contacts_fills_pi_too(isolated_questionnaire_parser):
    isolated_questionnaire_parser(
        "project_info",
        json.dumps({"university": "State U", "state": "AL", "bua_number": "", "project_title": "T"}),
    )
    isolated_questionnaire_parser("pi_info", json.dumps({"pi_info": {}}))
    r = isolated_questionnaire_parser(
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


def test_pi_only_payload_after_project_info_does_not_wipe_university(isolated_questionnaire_parser):
    isolated_questionnaire_parser(
        "project_info",
        json.dumps(
            {
                "university": "MIT",
                "state": "MA",
                "bua_number": "",
                "project_title": "RNA work",
            }
        ),
    )
    r = isolated_questionnaire_parser(
        "pi_info",
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


def test_empty_repeat_pi_info_keeps_prior_pi(isolated_questionnaire_parser):
    isolated_questionnaire_parser(
        "project_info",
        json.dumps(
            {
                "university": "U",
                "state": "TX",
                "bua_number": "",
                "project_title": "P",
            }
        ),
    )
    isolated_questionnaire_parser(
        "pi_info",
        json.dumps(
            {
                "pi_info": {
                    "name": "Dr. Keen",
                    "title": "",
                    "department": "",
                    "building": "",
                    "room": "",
                    "phone": "",
                    "email_address": "k@x.edu",
                    "fax": "",
                }
            }
        ),
    )
    r2 = isolated_questionnaire_parser("pi_info", json.dumps({"pi_info": {}}))
    assert (r2.get("current_state") or {}).get("pi_info", {}).get("name") == "Dr. Keen"
