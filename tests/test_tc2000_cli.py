from __future__ import annotations

import sys
from pathlib import Path

import pytest

from swing_trading.tc2000.cli import main


def test_cli_blocks_pending_versioned_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    files = []
    for kind in ("strength20", "strength60", "strength120"):
        path = tmp_path / f"tc2000_2026-07-31_{kind}_20260731T160500-0400.txt"
        path.write_text("AAPL\n")
        files.append(path)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://127.0.0.1/unused")
    monkeypatch.setenv("RAW_IMPORT_ROOT", str(tmp_path / "raw"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "swing-import-tc2000",
            "--market-date",
            "2026-07-31",
            "--config",
            "config/strategy-v1.yaml",
            *(str(path) for path in files),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert "not operator-approved" in capsys.readouterr().err
