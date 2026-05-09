"""Tests for example tools in `modules.seq_basics.tools` (not biosafety-specific)."""

from __future__ import annotations

import pytest


def test_translate_basic():
    from modules.seq_basics.tools.translate import translate

    assert translate("ATGGCT") == "MA"


def test_translate_invalid_frame_raises():
    from modules.seq_basics.tools.translate import translate

    with pytest.raises(ValueError):
        translate("ATG", frame=0)


def test_reverse_complement_basic():
    from modules.seq_basics.tools.reverse_complement import reverse_complement

    assert reverse_complement("ATGC") == "GCAT"


def test_reverse_complement_invalid_base():
    from modules.seq_basics.tools.reverse_complement import reverse_complement

    with pytest.raises(ValueError):
        reverse_complement("ATGZ")
