"""
cli.py — Command-line interface for the AI Health Copilot engine.

Usage:
    python -m ai_engine.cli <file_path> [--mime <mime>] [--lang <en|ta|auto>]

Examples:
    python -m ai_engine.cli samples/lab1.jpg
    python -m ai_engine.cli samples/discharge1.pdf --mime application/pdf
    python -m ai_engine.cli samples/tamil_mixed1.jpg --lang ta
    python -m ai_engine.cli /bad/path/file.xyz    # → prints error JSON, exit 0
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys


def _guess_mime(file_path: str) -> str:
    mime, _ = mimetypes.guess_type(file_path)
    if mime:
        return mime
    path_lower = file_path.lower()
    if path_lower.endswith(".pdf"):
        return "application/pdf"
    if path_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if path_lower.endswith(".png"):
        return "image/png"
    if path_lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="AI Health Copilot — extract medical document to JSON"
    )
    parser.add_argument("file", help="Path to image or PDF")
    parser.add_argument(
        "--mime", default=None, help="MIME type (auto-detected if omitted)"
    )
    parser.add_argument(
        "--lang", default="auto", choices=["auto", "en", "ta"],
        help="Language hint (default: auto)"
    )
    parser.add_argument(
        "--pretty", action="store_true", default=True,
        help="Pretty-print JSON output (default: true)"
    )
    args = parser.parse_args()

    mime = args.mime or _guess_mime(args.file)

    # Import here so .env is already loaded
    from ai_engine import extract_record

    result = extract_record(args.file, mime, lang_hint=args.lang)
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))

    # Exit 0 even on error — the contract dict is always returned
    sys.exit(0)


if __name__ == "__main__":
    main()
