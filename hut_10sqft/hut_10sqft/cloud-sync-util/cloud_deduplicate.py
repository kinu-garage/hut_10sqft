#!/usr/bin/env python3
# Licensed under Apache 2

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# IMPROVED REGEX:
# (.+?) -> Base filename (non-greedy)
# \s* -> ZERO or more spaces (Crucial for files like: Name(conflicted copy).ext)
# \( -> Literal parenthesis
# [^)]*conflicted copy[^)]* -> Match anything containing 'conflicted copy'
# \) -> Literal closing parenthesis
# (\.[^.]+$|$) -> File extension or end of string
REGEX_CONFLICT_DEFAULT = r"(.+?)\s*\([^)]*conflicted copy[^)]*\)(\.[^.]+$|$)"
QUERY_DEFAULT = "*(*conflict*copy*)*"

def get_dropbox_conflict_rename(file_path, pattern):
    filename = file_path.name
    match = re.search(pattern, filename, re.IGNORECASE)
    
    if match:
        # Strip trailing whitespace and fix accidental double-spaces
        clean_base = match.group(1).strip()
        clean_base = re.sub(r'\s+', ' ', clean_base)
        
        target_name = f"{clean_base}{match.group(2)}"
        target_path = file_path.parent / target_name
        
        # Only rename if the clean version doesn't exist yet
        if not target_path.exists():
            return target_path
    return None

def get_google_numbered_deletion(file_path):
    filename = file_path.name
    # Matches 'Name (1).ext'
    pattern = r"(.+?)\s*\(\d+\)(\.[^.]+$|$)"
    match = re.match(pattern, filename)
    
    if match:
        clean_base = match.group(1).strip()
        clean_base = re.sub(r'\s+', ' ', clean_base)
        master_path = file_path.parent / f"{clean_base}{match.group(2)}"
        if master_path.exists():
            return True
    return False

def run_deduplicator(base_path, query, conflict_regex, dry_run=False):
    start_time = time.time()
    root_path = Path(base_path).resolve()
    
    deleted_log = []
    renamed_log = []
    skipped_log = []

    if dry_run:
        print("\n" + "!"*45)
        print("!!! DRY RUN MODE: SIMULATING ACTIONS ONLY !!!")
        print("!"*45)

    for pass_num in [1, 2]:
        label = "Pass 1: Strip Conflicts" if pass_num == 1 else "Pass 2: Delete Numbered Duplicates"
        print(f"\n--- {label} ---")
        
        # Pass 1: Targeted search; Pass 2: Wider search for remaining (1), (2) files
        current_query = query if pass_num == 1 else "*(*)*"
        try:
            all_matches = list(root_path.rglob(current_query))
        except Exception as e:
            print(f"Search Error: {e}"); sys.exit(1)

        actions = []
        for f_path in all_matches:
            if not f_path.is_file(): continue

            if pass_num == 1:
                new_path = get_dropbox_conflict_rename(f_path, conflict_regex)
                if new_path:
                    actions.append((f_path, "RENAME", new_path))
            else:
                # Avoid processing files we just renamed or deleted
                if str(f_path) not in [r.split(" -> ")[0] for r in renamed_log]:
                    if get_google_numbered_deletion(f_path):
                        actions.append((f_path, "DELETE", None))

        if not actions:
            print("No matching files for this pass.")
            continue

        print(f"Found {len(actions)} potential actions.")
        
        if dry_run:
            print("SIMULATING (Dry Run):")
            for target, action, extra in actions:
                if action == "RENAME":
                    renamed_log.append(f"{target.name} -> {extra.name}")
                    print(f"  [R] {target.name} -> {extra.name}")
                else:
                    deleted_log.append(str(target))
                    print(f"  [-] {target.name}")
        else:
            confirm = input(f"Proceed with Pass {pass_num} changes? (y/N): ")
            if confirm.lower() == 'y':
                for target, action, extra in actions:
                    try:
                        if action == "RENAME":
                            os.rename(target, extra)
                            renamed_log.append(f"{target.name} -> {extra.name}")
                            print(f"  [R] {target.name} -> {extra.name}")
                        elif action == "DELETE":
                            os.remove(target)
                            deleted_log.append(str(target))
                            print(f"  [-] {target.name}")
                    except Exception as e:
                        skipped_log.append(f"{target.name} (Error: {e})")
            else:
                print("Pass skipped by user.")

    # Logging
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = "dryrun" if dry_run else "summary"
    log_path = root_path / f"dedup_{mode}_{ts}.txt"
    
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"CLOUD DEDUPLICATION {mode.upper()} - {ts}\nRegex: {conflict_regex}\n" + "="*60 + "\n")
        log.write(f"RENAMED ({len(renamed_log)}):\n" + "\n".join([f" [R] {x}" for x in renamed_log]) + "\n")
        log.write(f"DELETED ({len(deleted_log)}):\n" + "\n".join([f" [-] {x}" for x in deleted_log]) + "\n")
        log.write(f"SKIPPED ({len(skipped_log)}):\n" + "\n".join([f" [!] {x}" for x in skipped_log]) + "\n")

    print(f"\nProcessing Complete. Log file saved to: {log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-pass Cloud Sync Cleaner")
    parser.add_argument("path", nargs="?", default=".", help="Root directory")
    parser.add_argument("--query", default=QUERY_DEFAULT, help="Search glob")
    parser.add_argument("--regex", default=REGEX_CONFLICT_DEFAULT, help="Conflict regex")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only")
    args = parser.parse_args()
    run_deduplicator(args.path, args.query, args.regex, dry_run=args.dry_run)