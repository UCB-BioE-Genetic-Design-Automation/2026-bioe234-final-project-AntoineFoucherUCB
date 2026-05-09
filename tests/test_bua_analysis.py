"""Tests for `modules.biosafety.tools.bua_analysis` (IBC-style audit + ABSA enrichment)."""

from __future__ import annotations

import pytest

from modules.biosafety.tools import bua_analysis
from modules.biosafety.data.BUA_data_structure import BiologicalAgent, BUAForm, current_bua_state


def test_bua_analysis_enriches_agents(monkeypatch: pytest.MonkeyPatch):
    saved = BiologicalAgent(scientific_name="Escherichia coli BL21")
    prior_agents = list(current_bua_state.biological_agents)
    prior_title = current_bua_state.project_title

    current_bua_state.biological_agents = [saved.model_copy(deep=True)]

    def fake_absa(name: str, top_k: int = 5):
        return {
            "status": "success",
            "matches": [{"agent_type": "Bacterial — example RG classification"}],
        }

    monkeypatch.setattr(bua_analysis, "get_absa_data", fake_absa)
    try:
        out = bua_analysis.doc_analysis(focus_area="agents")
        assert out["status"] == "success"
        assert "instructions" in out
        agents = out["current_bua_data"]["biological_agents"]
        assert len(agents) == 1
        assert agents[0]["absa_risk_group"] == "Bacterial — example RG classification"
        assert "agents" in out["instructions"].lower()
        assert isinstance(out["campus_biosafety_practices"], str)
    finally:
        current_bua_state.biological_agents = prior_agents
        current_bua_state.project_title = prior_title
