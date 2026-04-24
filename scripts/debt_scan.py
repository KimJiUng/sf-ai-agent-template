#!/usr/bin/env python3
"""Review Gate: collect technical-debt candidates from changed files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


SALESFORCE_ID_RE = re.compile(
    r"\b(?:001|003|005|006|00Q|00T|500|701|a0[A-Za-z0-9])[A-Za-z0-9]{12,15}\b"
)
REVIEW_COMMENT_RE = re.compile(
    r"(?i)(TODO|FIXME|XXX|TO-DO|pending-confirm|확인\s*필요|임시|우회|추후|나중|가정)"
)


@dataclass(frozen=True)
class DebtCandidate:
    status: str
    kind: str
    title: str
    impact: str
    path: str
    line: int
    snippet: str


def classify_review_comment(line: str) -> str:
    if re.search(r"확인|confirm|고객|담당자|정책|요구사항|pending", line, re.IGNORECASE):
        return "pending-confirm"
    if re.search(r"임시|우회|가정", line):
        return "assumption"
    return "code-debt"


def scan_text_for_candidates(path: str, content: str) -> list[DebtCandidate]:
    candidates: list[DebtCandidate] = []
    for line_no, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if REVIEW_COMMENT_RE.search(stripped):
            kind = classify_review_comment(stripped)
            candidates.append(DebtCandidate(
                status="review-needed",
                kind=kind,
                title="검토 필요 주석 발견",
                impact="배포 전 사용자 확인 필요",
                path=path,
                line=line_no,
                snippet=stripped[:120],
            ))

        if SALESFORCE_ID_RE.search(stripped):
            candidates.append(DebtCandidate(
                status="review-needed",
                kind="code-debt",
                title="하드코딩된 Salesforce ID 의심",
                impact="환경별 데이터 차이 또는 배포 실패 가능성",
                path=path,
                line=line_no,
                snippet=stripped[:120],
            ))

    return candidates


def load_latest_session_files(root: Path) -> list[str]:
    latest = root / "backups" / "latest-session.json"
    if not latest.exists():
        return []
    try:
        pointer = json.loads(latest.read_text(encoding="utf-8"))
        session_dir = (root / pointer["session_dir"]).resolve()
        manifest = json.loads((session_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, KeyError, json.JSONDecodeError):
        return []
    return sorted({f.replace("\\", "/") for f in manifest.get("files", []) if f})


def next_debt_id(register_content: str) -> str:
    existing = [int(match.group(1)) for match in re.finditer(r"\bTD-(\d{3,})\b", register_content)]
    return f"TD-{(max(existing) + 1 if existing else 1):03d}"


def candidate_exists(register_content: str, candidate: DebtCandidate) -> bool:
    location = f"{candidate.path}:{candidate.line}"
    return location in register_content and candidate.title in register_content


def format_row(candidate_id: str, candidate: DebtCandidate) -> str:
    location = f"{candidate.path}:{candidate.line}"
    today = date.today().isoformat()
    return (
        f"| {candidate_id} | {candidate.status} | {candidate.kind} | "
        f"{candidate.title} | {candidate.impact} | `{location}` | {today} | 검토 대기 |"
    )


def append_candidates(register_path: Path, candidates: list[DebtCandidate]) -> list[DebtCandidate]:
    if not candidates:
        return []

    register_content = register_path.read_text(encoding="utf-8") if register_path.exists() else ""
    inserted: list[DebtCandidate] = []
    rows: list[str] = []

    for candidate in candidates:
        if candidate_exists(register_content, candidate):
            continue
        candidate_id = next_debt_id(register_content + "\n".join(rows))
        rows.append(format_row(candidate_id, candidate))
        inserted.append(candidate)

    if not rows:
        return []

    marker = "<!-- review-needed 항목은 자동 스캔으로 누적됩니다. -->"
    if marker in register_content:
        register_content = register_content.replace(marker, "\n".join(rows) + "\n" + marker)
    else:
        register_content = register_content.rstrip() + "\n" + "\n".join(rows) + "\n"

    register_path.write_text(register_content, encoding="utf-8")
    return inserted


def scan_files(root: Path, files: list[str]) -> list[DebtCandidate]:
    candidates: list[DebtCandidate] = []
    for rel in files:
        path = root / rel
        if not path.exists() or path.suffix.lower() not in {".cls", ".trigger", ".js", ".html", ".xml", ".md"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        candidates.extend(scan_text_for_candidates(rel.replace("\\", "/"), content))
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect technical-debt review candidates.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--files", nargs="*", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = args.files if args.files is not None else load_latest_session_files(root)

    if not files:
        print("Review Gate: no work snapshot files found. Debt scan skipped.")
        sys.exit(0)

    candidates = scan_files(root, files)
    register_path = root / "docs" / "technical-debt" / "register.md"
    inserted = append_candidates(register_path, candidates)

    print(f"Review Gate: scanned {len(files)} file(s), found {len(candidates)} candidate(s).")
    print(f"Review Gate: added {len(inserted)} new review-needed item(s).")
    for candidate in inserted:
        print(f"  - {candidate.kind}: {candidate.path}:{candidate.line} {candidate.title}")


if __name__ == "__main__":
    main()
