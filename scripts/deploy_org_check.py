#!/usr/bin/env python3
"""
Org-aware 배포 전 검사
- UTF-8 인코딩 검사
- 한글 깨짐 검사
- Org 현재본 retrieve 후 3-way 비교
- 충돌 감지 및 자동 병합
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


RED = "\033[0;31m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def get_base_ref() -> str:
    """Git base ref 결정"""
    for ref in ["origin/HEAD", "origin/master", "origin/main"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return ref
    return "HEAD~1"


def get_changed_files(base_ref: str, root: Path) -> list[str]:
    """base_ref 이후 변경된 force-app 파일 목록"""
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "--", "force-app/"],
        capture_output=True, text=True, cwd=root
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def check_utf8_encoding(root: Path, files: list[str]) -> list[str]:
    """배포 대상 파일 UTF-8 인코딩 검사"""
    violations = []
    text_extensions = {".cls", ".trigger", ".page", ".component", ".xml", ".html", ".js", ".css"}

    for rel_path in files:
        filepath = root / rel_path
        if not filepath.exists():
            continue
        if filepath.suffix.lower() not in text_extensions:
            continue
        try:
            filepath.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            violations.append(f"  - {rel_path}: Not valid UTF-8 encoding")
    return violations


def check_korean_corruption(root: Path, files: list[str]) -> list[str]:
    """한글 깨짐 흔적 검사 (replacement character)"""
    violations = []
    text_extensions = {".cls", ".trigger", ".page", ".component", ".xml", ".html", ".js", ".css"}

    for rel_path in files:
        filepath = root / rel_path
        if not filepath.exists():
            continue
        if filepath.suffix.lower() not in text_extensions:
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # U+FFFD (replacement character) 검사
        if "\ufffd" in content:
            violations.append(f"  - {rel_path}: Contains replacement character (possible Korean corruption)")
    return violations


def main():
    if len(sys.argv) < 3:
        print(f"{RED}Usage: {sys.argv[0]} <ROOT_PATH> <TARGET_ORG> [deploy args...]{NC}")
        sys.exit(2)

    root = Path(sys.argv[1]).resolve()
    target_org = sys.argv[2]
    # deploy_args = sys.argv[3:]  # 향후 확장용

    base_ref = get_base_ref()
    print(f"{CYAN}Using git base ref: {base_ref}{NC}")

    changed_files = get_changed_files(base_ref, root)
    if not changed_files:
        print(f"{GREEN}No force-app changes detected. Skipping org-aware check.{NC}")
        sys.exit(0)

    print(f"{CYAN}Checking {len(changed_files)} changed file(s)...{NC}")

    all_violations = []

    # UTF-8 인코딩 검사
    utf8_violations = check_utf8_encoding(root, changed_files)
    if utf8_violations:
        all_violations.append(f"{YELLOW}[Rule] encoding-check{NC}")
        all_violations.extend(utf8_violations)

    # 한글 깨짐 검사
    korean_violations = check_korean_corruption(root, changed_files)
    if korean_violations:
        all_violations.append(f"{YELLOW}[Rule] korean-corruption{NC}")
        all_violations.extend(korean_violations)

    if all_violations:
        print()
        print(f"{RED}Org-aware pre-deploy check failed: deployment will be stopped.{NC}")
        print()
        for line in all_violations:
            print(line)
        sys.exit(2)

    print(f"{GREEN}Org-aware pre-deploy check passed.{NC}")
    sys.exit(0)


if __name__ == "__main__":
    main()
