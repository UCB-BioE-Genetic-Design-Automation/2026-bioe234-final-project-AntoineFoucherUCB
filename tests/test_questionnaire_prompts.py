"""Tests for `modules.biosafety.tools.questionnaire_prompts` (stage prompts + aliases)."""

from __future__ import annotations

import modules.biosafety.data.BUA_data_structure as bua_ds
from modules.biosafety.tools.questionnaire_prompts import _normalize_stage
from modules.biosafety.tools import questionnaire_prompts as qp_prompts_module


def test_normalize_stage_aliases():
    assert _normalize_stage("submission") == "project_summary"
    assert _normalize_stage("principal_investigator") == "pi_info"
    assert _normalize_stage("lab_identity") == "project_info"


def test_questionnaire_prompts_known_stage_returns_prompt():
    out = qp_prompts_module.questionnaire_prompts("start")
    assert out["status"] == "success"
    assert "prompt_text" in out
    assert "project_info" in out["prompt_text"]


def test_questionnaire_prompts_unknown_stage_errors():
    out = qp_prompts_module.questionnaire_prompts("not_a_valid_stage_name")
    assert out["status"] == "error"
    assert "not found" in out["message"].lower()


def test_questionnaire_prompts_includes_document_notes_when_set():
    prior = bua_ds.current_document_markdown
    prior_src = bua_ds.current_document_source
    bua_ds.current_document_markdown = "PI: Dr. Smith\nbiosafety cabinet in room 101"
    bua_ds.current_document_source = "uploaded_bua.docx"
    try:
        out = qp_prompts_module.questionnaire_prompts("room_usage")
        assert out["status"] == "success"
        text = out["prompt_text"].lower()
        assert "biosafety cabinet" in text or "document" in text
    finally:
        bua_ds.current_document_markdown = prior
        bua_ds.current_document_source = prior_src
