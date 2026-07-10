#!/usr/bin/env python3
# Licensed under Apache 2

import argparse
import hashlib
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Regex logic for Dropbox/Google Drive patterns
REGEX_CONFLICT_DEFAULT = r"(.+?)\s*\([^)]*conflicted copy[^)]*\)(\.[^.]+$|$)"
QUERY_DEFAULT = "*(*conflict*copy*)*"

def get_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def get_dropbox_conflict_rename(file_path, pattern):
    filename = file_path.name
    match = re.search(pattern, filename, re.IGNORECASE)
    if match:
        clean_base = re.sub(r'\s+', ' ', match.group(1).strip())
        target_name = f"{clean_base}{match.group(2)}"
        target_path = file_path.parent / target_name
        if not target_path.exists():
            return target_path
    return None

def get_google_numbered_deletion(file_path):
    filename = file_path.name
    pattern = r"(.+?)\s*\(\d+\)(\.[^.]+$|$)"
    match = re.match(pattern, filename)
    if match:
        clean_base = re.sub(r'\s+', ' ', match.group(1).strip())
        master_path = file_path.parent / f"{clean_base}{match.group(2)}"
        if master_path.exists():
            return True
    return False

def run_deduplicator(base_path, query, conflict_regex, priority_dir=None, dry_run=False):
    start_time = time.time()
    root_path = Path(base_path).resolve()
    priority_path = Path(priority_dir).resolve() if priority_dir else None
    
    deleted_log = []
    renamed_log = []
    skipped_log = []

    if dry_run:
        print("\n" + "!"*45 + "\n!!! DRY RUN MODE: SIMULATING ACTIONS ONLY !!!\n" + "!"*45)

    # Three-pass approach
    passes = [
        (1, "Pass 1: Strip Dropbox Conflicts"),
        (2, "Pass 2: Delete Google Numbered Duplicates"),
        (3, "Pass 3: Global Hash Deduplication (MD5)")
    ]

    for pass_num, label in passes:
        if pass_num == 3 and not priority_path:
            continue  # Skip Pass 3 if no priority dir is provided

        print(f"\n--- {label} ---")
        actions = []

        if pass_num == 3:
            # Hash Deduplication Logic
            hash_map = {} # {md5: [list_of_paths]}
            print("Calculating hashes for all files...")
            for f_path in root_path.rglob("*"):
                if f_path.is_file() and str(f_path) not in deleted_log:
                    f_hash = get_md5(f_path)
                    if f_hash:
                        hash_map.setdefault(f_hash, []).append(f_path)
            
            for f_hash, paths in hash_map.items():
                if len(paths) > 1:
                    # Find if any version exists in the priority directory
                    prio_files = [p for p in paths if str(p).startswith(str(priority_path))]
                    
                    if prio_files:
                        keep_file = prio_files[0]
                        for p in paths:
                            if p != keep_file:
                                actions.append((p, "DELETE", None))
        else:
            # Patterns logic (Pass 1 & 2)
            current_query = query if pass_num == 1 else "*(*)*"
            try:
                all_matches = list(root_path.rglob(current_query))
            except Exception as e:
                print(f"Search Error: {e}"); sys.exit(1)

            for f_path in all_matches:
                if not f_path.is_file(): continue
                if pass_num == 1:
                    new_path = get_dropbox_conflict_rename(f_path, conflict_regex)
                    if new_path: actions.append((f_path, "RENAME", new_path))
                elif pass_num == 2:
                    if str(f_path) not in [r.split(" -> ")[0] for r in renamed_log]:
                        if get_google_numbered_deletion(f_path):
                            actions.append((f_path, "DELETE", None))

        if not actions:
            print("No matching files for this pass.")
            continue

        print(f"Found {len(actions)} potential actions.")
        
        if dry_run:
            for target, action, extra in actions:
                if action == "RENAME":
                    renamed_log.append(f"{target} -> {extra.name}")
                    print(f"  [R] {target.name} -> {extra.name}")
                else:
                    deleted_log.append(str(target))
                    print(f"  [-] {target}")
        else:
            confirm = input(f"Proceed with Pass {pass_num}? (y/N): ")
            if confirm.lower() == 'y':
                for target, action, extra in actions:
                    try:
                        if action == "RENAME":
                            os.rename(target, extra)
                            renamed_log.append(f"{target} -> {extra.name}")
                        elif action == "DELETE":
                            os.remove(target)
                            deleted_log.append(str(target))
                            print(f"  [-] {target}")
                    except Exception as e:
                        skipped_log.append(f"{target} (Error: {e})")
            else:
                print("Pass skipped by user.")

    # Logging
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = "dryrun" if dry_run else "summary"
    log_path = root_path / f"dedup_{mode}_{ts}.txt"
    
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"CLOUD DEDUPLICATION {mode.upper()} - {ts}\n")
        if priority_path: log.write(f"Priority Directory: {priority_path}\n")
        log.write("-" * 60 + "\n")
        log.write(f"RENAMED ({len(renamed_log)}):\n" + "\n".join(renamed_log) + "\n\n")
        log.write(f"DELETED ({len(deleted_log)}):\n" + "\n".join(deleted_log) + "\n\n")
        log.write(f"SKIPPED/FAILED ({len(skipped_log)}):\n" + "\n".join(skipped_log) + "\n")

    print(f"\nProcessing Complete. Log file: {log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-pass Cloud Sync Cleaner with MD5 Deduplication")
    parser.add_argument("path", nargs="?", default=".", help="Root directory")
    parser.add_argument("--query", default=QUERY_DEFAULT, help="Search glob")
    parser.add_argument("--regex", default=REGEX_CONFLICT_DEFAULT, help="Conflict regex")
    parser.add_argument("--priority-dir", help="Folder to keep files in if MD5 matches across different names")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only")
    args = parser.parse_args()
    run_deduplicator(args.path, args.query, args.regex, args.priority_dir, dry_run=args.dry_run)
