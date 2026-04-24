#!/usr/bin/env python3
"""
Org-aware pre-deploy check without repository-history dependency.

The workflow uses a work snapshot created before AI changes:

1. local-backup: local files before the AI edits them
2. org-start: the target org version at the same moment

Before deployment this script retrieves the current org version and performs a
3-way comparison:

    org-start + current local + current org

Non-overlapping changes are merged automatically. Overlapping changes stop the
deployment and must be reviewed by a human.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


RED = "\033[0;31m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

TEXT_EXTENSIONS = {
    ".cls", ".trigger", ".page", ".component",
    ".xml", ".html", ".js", ".css",
}

METADATA_TYPE_MAP = {
    "classes": "ApexClass",
    "triggers": "ApexTrigger",
    "lwc": "LightningComponentBundle",
    "aura": "AuraDefinitionBundle",
    "pages": "ApexPage",
    "components": "ApexComponent",
    "objects": "CustomObject",
    "layouts": "Layout",
    "permissionsets": "PermissionSet",
    "permissionsetGroups": "PermissionSetGroup",
    "flows": "Flow",
    "flexipages": "FlexiPage",
    "staticresources": "StaticResource",
    "customMetadata": "CustomMetadata",
    "labels": "CustomLabels",
    "tabs": "CustomTab",
}

BUNDLE_TYPES = {"lwc", "aura"}


@dataclass(frozen=True)
class Change:
    start: int
    end: int
    replacement: list[str]


@dataclass(frozen=True)
class MergeResult:
    success: bool
    content: str
    conflicts: list[str]


# ──────────────────────────────────────────────
# Metadata helpers
# ──────────────────────────────────────────────

def file_to_metadata(rel_path: str) -> str | None:
    """Convert a force-app source path to Metadata API type:name."""
    parts = Path(rel_path).parts
    if len(parts) < 5 or parts[0] != "force-app":
        return None
    type_dir = parts[3]
    meta_type = METADATA_TYPE_MAP.get(type_dir)
    if not meta_type:
        return None
    if type_dir in BUNDLE_TYPES:
        return f"{meta_type}:{parts[4]}"
    name = Path(parts[4]).stem
    if name.endswith("-meta"):
        name = name[:-5]
    return f"{meta_type}:{name}"


def get_api_version(root: Path) -> str:
    cfg = root / "sfdx-project.json"
    if cfg.exists():
        with open(cfg, encoding="utf-8") as f:
            return json.load(f).get("sourceApiVersion", "65.0")
    return "65.0"


def retrieve_from_org(
    root: Path, target_org: str, metadata_items: set[str],
) -> tuple[Path | None, bool]:
    """Retrieve metadata from the org into a temporary Salesforce project."""
    temp_dir = Path(tempfile.mkdtemp(prefix="org-retrieve-"))
    try:
        (temp_dir / "force-app" / "main" / "default").mkdir(parents=True)
        sfdx_cfg = {
            "packageDirectories": [{"path": "force-app", "default": True}],
            "sourceApiVersion": get_api_version(root),
        }
        with open(temp_dir / "sfdx-project.json", "w", encoding="utf-8") as f:
            json.dump(sfdx_cfg, f)

        cmd = ["sf", "project", "retrieve", "start", "--target-org", target_org]
        for item in sorted(metadata_items):
            cmd.extend(["--metadata", item])

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir)
        if result.returncode != 0:
            print(f"{YELLOW}  Org retrieve warning: {result.stderr.strip()}{NC}")
            return temp_dir, False
        return temp_dir, True
    except FileNotFoundError:
        print(f"{YELLOW}  sf CLI not found. Skipping org comparison.{NC}")
        return temp_dir, False


# ──────────────────────────────────────────────
# Work snapshot helpers
# ──────────────────────────────────────────────

def parse_runtime_args(args: list[str]) -> tuple[str | None, list[str]]:
    session_dir: str | None = None
    deploy_args: list[str] = []
    i = 0
    while i < len(args):
        value = args[i]
        if value == "--session-dir":
            session_dir = args[i + 1] if i + 1 < len(args) else None
            i += 2
            continue
        if value.startswith("--session-dir="):
            session_dir = value.split("=", 1)[1]
            i += 1
            continue
        deploy_args.append(value)
        i += 1
    return session_dir, deploy_args


def load_session(root: Path, requested: str | None) -> tuple[Path, dict]:
    if requested:
        session_dir = Path(requested)
        if not session_dir.is_absolute():
            session_dir = (root / session_dir).resolve()
    else:
        latest = root / "backups" / "latest-session.json"
        if not latest.exists():
            raise FileNotFoundError(
                "Work snapshot is missing. Run `npm run work:snapshot -- "
                "--target-org <ORG_ALIAS> --files <paths...>` before deployment."
            )
        pointer = json.loads(latest.read_text(encoding="utf-8"))
        session_dir = (root / pointer["session_dir"]).resolve()

    manifest_path = session_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Work snapshot manifest is missing: {manifest_path}")

    return session_dir, json.loads(manifest_path.read_text(encoding="utf-8"))


def get_tracked_files(manifest: dict) -> list[str]:
    return sorted({f.replace("\\", "/") for f in manifest.get("files", []) if f})


def read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def get_changed_files_from_snapshot(root: Path, session_dir: Path, manifest: dict) -> list[str]:
    changed: list[str] = []
    backup_root = session_dir / "local-backup"
    for rel in get_tracked_files(manifest):
        local_path = root / rel
        backup_path = backup_root / rel
        local_exists = local_path.exists()
        backup_exists = backup_path.exists()
        if local_exists != backup_exists:
            changed.append(rel)
            continue
        if not local_exists:
            continue
        if local_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if local_path.read_text(encoding="utf-8") != backup_path.read_text(encoding="utf-8"):
                changed.append(rel)
        except (UnicodeDecodeError, OSError):
            changed.append(rel)
    return changed


# ──────────────────────────────────────────────
# Encoding checks
# ──────────────────────────────────────────────

def check_utf8_encoding(root: Path, files: list[str]) -> list[str]:
    violations = []
    for rel in files:
        fp = root / rel
        if not fp.exists() or fp.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            fp.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            violations.append(f"  - {rel}: Not valid UTF-8 encoding")
    return violations


def check_korean_corruption(root: Path, files: list[str]) -> list[str]:
    violations = []
    for rel in files:
        fp = root / rel
        if not fp.exists() or fp.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "\ufffd" in content:
            violations.append(
                f"  - {rel}: Contains replacement character (possible Korean corruption)"
            )
    return violations


# ──────────────────────────────────────────────
# 3-way merge without repository-history dependency
# ──────────────────────────────────────────────

def _changes(base: list[str], changed: list[str]) -> list[Change]:
    matcher = SequenceMatcher(None, base, changed, autojunk=False)
    changes: list[Change] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        changes.append(Change(i1, i2, changed[j1:j2]))
    return changes


def _overlaps(left: Change, right: Change) -> bool:
    if left.start == left.end and right.start == right.end:
        return left.start == right.start
    if left.start == left.end:
        return right.start <= left.start < right.end
    if right.start == right.end:
        return left.start <= right.start < left.end
    return left.start < right.end and right.start < left.end


def _apply_changes(base: list[str], changes: list[Change]) -> list[str]:
    merged = list(base)
    for change in sorted(changes, key=lambda item: (item.start, item.end), reverse=True):
        merged[change.start:change.end] = change.replacement
    return merged


def merge_non_overlapping_changes(base: str, local: str, org: str) -> MergeResult:
    """Merge local and org changes when their edits touch different base ranges."""
    if local == org:
        return MergeResult(True, local, [])
    if base == org:
        return MergeResult(True, local, [])
    if base == local:
        return MergeResult(True, org, [])

    base_lines = base.splitlines(keepends=True)
    local_lines = local.splitlines(keepends=True)
    org_lines = org.splitlines(keepends=True)

    local_changes = _changes(base_lines, local_lines)
    org_changes = _changes(base_lines, org_lines)
    conflicts: list[str] = []

    for local_change in local_changes:
        for org_change in org_changes:
            if _overlaps(local_change, org_change):
                conflicts.append(
                    f"base lines {local_change.start + 1}-{max(local_change.end, local_change.start + 1)}"
                )

    if conflicts:
        return MergeResult(False, local, conflicts)

    merged_lines = _apply_changes(base_lines, local_changes + org_changes)
    return MergeResult(True, "".join(merged_lines), [])


# ──────────────────────────────────────────────
# 3-way comparison
# ──────────────────────────────────────────────

def do_three_way_check(
    root: Path, target_org: str, session_dir: Path, manifest: dict,
) -> tuple[list[str], list[str]]:
    changed_files = get_changed_files_from_snapshot(root, session_dir, manifest)
    metadata_items = {file_to_metadata(f) for f in get_tracked_files(manifest)}
    metadata_items = {item for item in metadata_items if item}

    if not metadata_items:
        return [], [f"{GREEN}No deployable metadata items found in work snapshot.{NC}"]

    print(f"{CYAN}Retrieving {len(metadata_items)} metadata item(s) from org [{target_org}]...{NC}")
    current_org_dir, ok = retrieve_from_org(root, target_org, metadata_items)
    if not ok:
        if current_org_dir:
            shutil.rmtree(current_org_dir, ignore_errors=True)
        return [f"{YELLOW}[Rule] org-retrieve{NC}", "  - Could not retrieve current org metadata."], []

    violations: list[str] = []
    summaries: list[str] = []
    auto_merged: list[str] = []
    org_only_updates: list[str] = []
    deleted_files: list[str] = []
    created_files: list[str] = []

    org_start_root = session_dir / "org-start"
    local_backup_root = session_dir / "local-backup"

    try:
        for rel in get_tracked_files(manifest):
            local_path = root / rel
            local_backup_path = local_backup_root / rel
            base_path = org_start_root / rel
            current_org_path = current_org_dir / rel

            if not local_path.exists():
                if local_backup_path.exists():
                    deleted_files.append(rel)
                    violations.append(
                        f"  - {rel}: 삭제 감지. destructive 배포는 자동 처리하지 않습니다."
                    )
                continue

            if local_path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            local_content = read_optional_text(local_path)
            base_content = read_optional_text(base_path)
            current_org_content = read_optional_text(current_org_path)
            local_backup_content = read_optional_text(local_backup_path)

            if base_content is None:
                if current_org_content is None:
                    created_files.append(rel)
                    continue
                violations.append(
                    f"  - {rel}: 로컬 신규 파일이지만 현재 Org에도 같은 메타데이터가 있습니다."
                )
                continue

            if current_org_content is None:
                violations.append(
                    f"  - {rel}: 작업 시작 후 Org에서 메타데이터가 삭제되었습니다."
                )
                continue

            if local_content == local_backup_content and current_org_content != base_content:
                local_path.write_text(current_org_content, encoding="utf-8")
                org_only_updates.append(rel)
                continue

            merge = merge_non_overlapping_changes(base_content, local_content, current_org_content)
            if merge.success:
                if merge.content != local_content:
                    local_path.write_text(merge.content, encoding="utf-8")
                    auto_merged.append(rel)
            else:
                violations.append(
                    f"  - {rel}: 로컬과 Org 변경 의도가 겹칩니다. "
                    f"충돌 위치: {', '.join(merge.conflicts)}"
                )

        if changed_files:
            summaries.append(f"{CYAN}  [local-change] {len(changed_files)}개 파일 변경 감지{NC}")
            for rel in changed_files:
                summaries.append(f"    -> {rel}")

        if created_files:
            summaries.append(f"{GREEN}  [created] {len(created_files)}개 파일 신규 생성{NC}")
            for rel in created_files:
                summaries.append(f"    -> {rel}")

        if org_only_updates:
            summaries.append(f"{CYAN}  [org-only] {len(org_only_updates)}개 파일을 Org 최신본으로 갱신{NC}")
            for rel in org_only_updates:
                summaries.append(f"    -> {rel}")

        if auto_merged:
            summaries.append(f"{GREEN}  [auto-merge] {len(auto_merged)}개 파일 자동 병합 완료{NC}")
            for rel in auto_merged:
                summaries.append(f"    -> {rel}")

        if deleted_files:
            summaries.append(f"{YELLOW}  [deleted] {len(deleted_files)}개 파일 삭제 감지{NC}")
            for rel in deleted_files:
                summaries.append(f"    -> {rel}")
    finally:
        shutil.rmtree(current_org_dir, ignore_errors=True)

    return violations, summaries


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 3:
        print(f"{RED}Usage: {sys.argv[0]} <ROOT_PATH> <TARGET_ORG> [--session-dir <DIR>] [deploy args...]{NC}")
        sys.exit(2)

    root = Path(sys.argv[1]).resolve()
    target_org = sys.argv[2]
    session_arg, _deploy_args = parse_runtime_args(sys.argv[3:])

    try:
        session_dir, manifest = load_session(root, session_arg)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"{RED}Work snapshot check failed: deployment will be stopped.{NC}")
        print(f"  - {exc}")
        sys.exit(2)

    snapshot_org = manifest.get("target_org")
    if snapshot_org and snapshot_org != target_org:
        print(f"{RED}Work snapshot target org mismatch: deployment will be stopped.{NC}")
        print(f"  - snapshot org: {snapshot_org}")
        print(f"  - deploy org: {target_org}")
        sys.exit(2)

    tracked_files = get_tracked_files(manifest)
    if not tracked_files:
        print(f"{YELLOW}Work snapshot has no tracked files. Org-aware check skipped.{NC}")
        sys.exit(0)

    print(f"{CYAN}Using work snapshot: {session_dir}{NC}")
    print(f"{CYAN}Checking {len(tracked_files)} tracked file(s)...{NC}")

    all_violations: list[str] = []

    utf8 = check_utf8_encoding(root, tracked_files)
    if utf8:
        all_violations.append(f"{YELLOW}[Rule] encoding-check{NC}")
        all_violations.extend(utf8)

    korean = check_korean_corruption(root, tracked_files)
    if korean:
        all_violations.append(f"{YELLOW}[Rule] korean-corruption{NC}")
        all_violations.extend(korean)

    three_way_violations, three_way_summaries = do_three_way_check(
        root, target_org, session_dir, manifest,
    )
    if three_way_violations:
        all_violations.append(f"{YELLOW}[Rule] org-conflict{NC}")
        all_violations.extend(three_way_violations)

    for summary in three_way_summaries:
        print(summary)

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
