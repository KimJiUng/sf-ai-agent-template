#!/usr/bin/env python3
"""Create a local backup and target-org snapshot before AI work starts."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from deploy_org_check import file_to_metadata, get_api_version


def slugify(label: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", label.strip())
    return value.strip("-") or "work"


def copy_local_files(root: Path, session_dir: Path, files: list[str]) -> None:
    backup_root = session_dir / "local-backup"
    for rel in files:
        source = root / rel
        if not source.exists():
            continue
        target = backup_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def retrieve_org_snapshot(root: Path, session_dir: Path, target_org: str, metadata_items: set[str]) -> bool:
    org_root = session_dir / "org-start"
    (org_root / "force-app" / "main" / "default").mkdir(parents=True, exist_ok=True)
    sfdx_cfg = {
        "packageDirectories": [{"path": "force-app", "default": True}],
        "sourceApiVersion": get_api_version(root),
    }
    (org_root / "sfdx-project.json").write_text(json.dumps(sfdx_cfg, indent=2), encoding="utf-8")

    if not metadata_items:
        return True

    cmd = ["sf", "project", "retrieve", "start", "--target-org", target_org]
    for item in sorted(metadata_items):
        cmd.extend(["--metadata", item])

    result = subprocess.run(cmd, cwd=org_root, text=True)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Create local backup and org-start snapshot.")
    parser.add_argument("--target-org", required=True)
    parser.add_argument("--label", default="work")
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = sorted({f.replace("\\", "/").lstrip("/") for f in args.files})
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_rel = Path("backups") / f"{timestamp}-{slugify(args.label)}"
    session_dir = root / session_rel
    session_dir.mkdir(parents=True, exist_ok=False)

    copy_local_files(root, session_dir, files)

    metadata_items = {file_to_metadata(rel) for rel in files}
    metadata_items = {item for item in metadata_items if item}
    if not retrieve_org_snapshot(root, session_dir, args.target_org, metadata_items):
        print("Org snapshot retrieve failed. Work snapshot was not completed.", file=sys.stderr)
        sys.exit(2)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "label": args.label,
        "target_org": args.target_org,
        "files": files,
        "metadata_items": sorted(metadata_items),
        "policy": {
            "local_backup": "reference-only; AI must not edit or delete backup files",
            "org_snapshot": "deployment baseline for 3-way merge",
        },
    }
    (session_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    latest = root / "backups" / "latest-session.json"
    latest.write_text(
        json.dumps({"session_dir": session_rel.as_posix()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Work snapshot created: {session_rel.as_posix()}")
    print(f"Tracked files: {len(files)}")
    print(f"Metadata items: {len(metadata_items)}")


if __name__ == "__main__":
    main()
