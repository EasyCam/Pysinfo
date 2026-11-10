"""A legacy Windows console (e.g. cp1252) must not crash pysinfo's output."""

import io
import sys

import pysinfo


def _cp1252_stdout(monkeypatch):
    buffer = io.BytesIO()
    fake = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", fake)
    return buffer, fake


def test_print_system_info_survives_cp1252_console(monkeypatch):
    buffer, fake = _cp1252_stdout(monkeypatch)

    pysinfo.print_system_info()

    fake.flush()
    out = buffer.getvalue().decode("utf-8")
    assert "PySinfo" in out


def test_ensure_utf8_stdout_tolerates_streams_without_reconfigure(monkeypatch):
    monkeypatch.setattr(sys, "stdout", object())

    pysinfo._ensure_utf8_stdout()
