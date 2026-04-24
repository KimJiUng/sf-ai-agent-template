#!/usr/bin/env python3
"""
Deploy Gate — 정적 검사 (Python)
배포 전 규칙 위반을 자동 검사하는 사전 게이트
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


IGNORED_DIRS = {".git", ".sfdx", ".sf", "node_modules", "backups"}


class Violation(NamedTuple):
    rule: str
    path: str
    detail: str


def load_config(root: Path) -> dict:
    config_path = root / "config" / "deploy-gate-rules.json"
    if not config_path.exists():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def check_required_files(root: Path, config: dict) -> list[Violation]:
    """1) 필수 파일 존재 여부 검사"""
    violations = []
    for rel_path in config.get("required_files", []):
        full = root / rel_path
        if not full.exists():
            violations.append(Violation("required-file", rel_path, "Required file is missing."))
    return violations


def check_banned_patterns(root: Path, config: dict) -> list[Violation]:
    """2) 금지 패턴 검사"""
    violations = []
    for rule in config.get("banned_patterns", []):
        extensions = [ext.lower() for ext in rule.get("include_extensions", [])]
        pattern = re.compile(rule["pattern"])

        for dirpath, _, filenames in os.walk(root):
            # local tool/runtime directories are ignored
            rel_dir = os.path.relpath(dirpath, root)
            if any(part in IGNORED_DIRS for part in Path(rel_dir).parts):
                continue

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue

                filepath = Path(dirpath) / filename
                try:
                    content = filepath.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue

                if pattern.search(content):
                    # 첫 번째 매치 라인 번호 찾기
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            rel = os.path.relpath(filepath, root)
                            violations.append(Violation(
                                rule["name"], rel,
                                f"{rule['message']} (line {i})"
                            ))
                            break
    return violations


def check_markdown_links(root: Path) -> list[Violation]:
    """3) Markdown 로컬 링크 무결성 검사"""
    violations = []
    link_pattern = re.compile(r'\[[^\]]*\]\(([^)]+)\)')

    for dirpath, _, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if any(part in IGNORED_DIRS for part in Path(rel_dir).parts):
            continue

        for filename in filenames:
            if not filename.endswith(".md"):
                continue

            filepath = Path(dirpath) / filename
            try:
                content = filepath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for match in link_pattern.finditer(content):
                target = match.group(1).strip()
                # 외부 링크, 앵커, mailto 등 무시
                if re.match(r'^(https?://|mailto:|#)', target):
                    continue

                # 제목 부분 제거
                target = re.sub(r'\s+".*"$', '', target).strip('<>').strip()
                path_part = re.sub(r'#.*$', '', target)
                if not path_part:
                    continue

                resolved = (filepath.parent / path_part).resolve()
                if not resolved.exists():
                    rel = os.path.relpath(filepath, root)
                    violations.append(Violation(
                        "broken-markdown-link", rel,
                        f"Broken local markdown link: {target}"
                    ))
    return violations


def check_markdown_encoding(root: Path) -> list[Violation]:
    """3.5) Markdown UTF-8 인코딩 검사"""
    violations = []
    for dirpath, _, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if any(part in IGNORED_DIRS for part in Path(rel_dir).parts):
            continue

        for filename in filenames:
            if not filename.endswith(".md"):
                continue

            filepath = Path(dirpath) / filename
            try:
                filepath.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                rel = os.path.relpath(filepath, root)
                violations.append(Violation(
                    "encoding-check", rel,
                    "Markdown file is not valid UTF-8 encoding."
                ))
    return violations


def check_text_contracts(root: Path, config: dict) -> list[Violation]:
    """4) 텍스트 계약 문구 존재 여부 검사"""
    violations = []
    for rel_path, rule in config.get("text_contract_rules", {}).items():
        filepath = root / rel_path
        if not filepath.exists():
            violations.append(Violation(
                "text-contract-file", rel_path,
                "Contract file is missing."
            ))
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            violations.append(Violation(
                "text-contract-file", rel_path,
                "Cannot read contract file."
            ))
            continue

        for token in rule.get("must_contain", []):
            if token not in content:
                violations.append(Violation(
                    "text-contract-content", rel_path,
                    f"Required content missing: {token}"
                ))
    return violations


def check_design_artifact_index(root: Path, config: dict) -> list[Violation]:
    """5) 디자인 인덱스 문서 내 경로 실존 여부 검사"""
    violations = []
    dai = config.get("design_artifact_index")
    if not dai:
        return violations

    index_path = root / dai["path"]
    if not index_path.exists():
        violations.append(Violation(
            "design-artifact-index", dai["path"],
            "Design artifact index file is missing."
        ))
        return violations

    prefixes = dai.get("must_exist_paths_prefixes", [])
    content = index_path.read_text(encoding="utf-8")

    backtick_pattern = re.compile(r'`([^`]+)`')
    for match in backtick_pattern.finditer(content):
        candidate = match.group(1).strip()
        if not candidate or any(c in candidate for c in "{}*"):
            continue
        if not any(candidate.startswith(p) for p in prefixes):
            continue
        full = root / candidate
        if not full.exists():
            violations.append(Violation(
                "design-artifact-index", dai["path"],
                f"Index path does not exist: {candidate}"
            ))
    return violations


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    config = load_config(root)

    if not config:
        print("\033[0;31mDeploy Gate rules file is missing.\033[0m")
        sys.exit(2)

    all_violations: list[Violation] = []
    all_violations.extend(check_required_files(root, config))
    all_violations.extend(check_banned_patterns(root, config))
    all_violations.extend(check_markdown_links(root))
    all_violations.extend(check_markdown_encoding(root))
    all_violations.extend(check_text_contracts(root, config))
    all_violations.extend(check_design_artifact_index(root, config))

    if all_violations:
        print()
        print("\033[0;31mDeploy Gate check failed: deployment will be stopped.\033[0m")
        print()

        # 규칙별 그룹핑
        by_rule: dict[str, list[Violation]] = {}
        for v in all_violations:
            by_rule.setdefault(v.rule, []).append(v)

        for rule in sorted(by_rule.keys()):
            print(f"\033[1;33m[Rule] {rule}\033[0m")
            for v in by_rule[rule]:
                print(f"  - {v.path}: {v.detail}")
            print()

        sys.exit(2)
    else:
        print("\033[0;32mDeploy Gate check passed: deployment can continue.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
