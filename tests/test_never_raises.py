"""
test_never_raises.py — Verify extract_record() NEVER raises an exception.
Tests corrupt file, empty file, wrong MIME, missing file, and network mock.
Run: pytest tests/test_never_raises.py -v
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.models import DISCLAIMER


def _call(file_path: str, mime: str = "image/jpeg") -> dict:
    """Import and call extract_record in mock mode to avoid real LLM calls."""
    # Force mock mode for these tests
    with patch.dict(os.environ, {"USE_MOCK_AI": "true"}):
        from ai_engine import extract_record
        return extract_record(file_path, mime)


class TestNeverRaises:
    def test_missing_file(self):
        result = _call("/nonexistent/path/to/file.jpg")
        # Should return either an error record or mock record — never raise
        assert isinstance(result, dict)
        assert "record_id" in result
        assert "disclaimer" in result

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"")  # empty file
            tmp = f.name
        try:
            result = _call(tmp, "image/jpeg")
            assert isinstance(result, dict)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_corrupt_image(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"NOT_VALID_IMAGE_DATA_\x00\xff\xfe" * 100)
            tmp = f.name
        try:
            result = _call(tmp, "image/jpeg")
            assert isinstance(result, dict)
            assert "record_id" in result
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_wrong_mime_type(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"FAKE_DATA")
            tmp = f.name
        try:
            result = _call(tmp, "application/x-unknown-binary")
            assert isinstance(result, dict)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_binary_random_data(self):
        import random
        data = bytes([random.randint(0, 255) for _ in range(2048)])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(data)
            tmp = f.name
        try:
            result = _call(tmp, "application/pdf")
            assert isinstance(result, dict)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_disclaimer_always_present(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"BAD_DATA")
            tmp = f.name
        try:
            result = _call(tmp)
            assert result.get("disclaimer") == DISCLAIMER
        finally:
            Path(tmp).unlink(missing_ok=True)


class TestMockMode:
    """Verify mock mode returns valid contract dicts."""

    def test_mock_lab_report(self):
        result = _call("samples/lab1.jpg", "image/jpeg")
        assert isinstance(result, dict)
        assert result.get("doc_type") in {"lab_report", "prescription", "discharge_summary", "diagnostic_report"}
        assert result.get("disclaimer") == DISCLAIMER

    def test_mock_prescription(self):
        result = _call("samples/prescription1.jpg", "image/jpeg")
        assert isinstance(result, dict)
        assert result.get("doc_type") == "prescription"

    def test_mock_discharge(self):
        result = _call("samples/discharge1.pdf", "application/pdf")
        assert isinstance(result, dict)
        assert result.get("doc_type") == "discharge_summary"

    def test_mock_always_has_record_id(self):
        r1 = _call("samples/lab1.jpg")
        r2 = _call("samples/lab2.jpg")
        # Each call should produce a unique record_id
        assert r1["record_id"] != r2["record_id"]
