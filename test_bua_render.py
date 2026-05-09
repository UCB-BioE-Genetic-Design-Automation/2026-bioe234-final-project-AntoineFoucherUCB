"""Tests for `modules.biosafety.tools.bua_render`."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_bua_render_missing_template_reports_error(tmp_path: Path):
    pytest.importorskip("docxtpl", reason="bua_render requires docxtpl")
    import modules.biosafety.tools.bua_render as bua_render_module

    renderer = bua_render_module.BUARenderer()
    renderer.template_path = str(tmp_path / "missing_template.docx")
    renderer.output_dir = str(tmp_path / "out")
    Path(renderer.output_dir).mkdir(parents=True, exist_ok=True)
    out = renderer.run("nope.docx")
    assert out["status"] == "error"
    assert "Template not found" in out["message"]
