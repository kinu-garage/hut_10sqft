# Copyright 2026 Kinu Garage Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for parsing and updating structured Markdown checklist documents.

Primary intended use case:
    Automating recurring planning documents (e.g., weekly or sprint tracking GitHub
    issue bodies) that combine:
      1. Milestone / focused task checklists referencing GitHub issues
         (carried over across periods or synced with GitHub Projects).
      2. Notable multi-day events / spans for the period.
      3. Daily schedules grouped under ``- M/D <Day>`` date bullets with nested
         ``- [ ]`` / ``- [x]`` checklist items (e.g., populated from iCalendar feeds
         via ``calendar_util`` while preserving manual edits and completed items).

Example target Markdown format (anonymized)::

    ## Key milestone/focused areas
    - [ ] #2495 2026 Annual project planning
      Additional indented notes for this item
    - [x] org-name/repo-name#1479 Account configuration

    ## Notable period
    - 11/16 Mon – 11/17 Tue Fall Camp

    ## Daily
    - 11/16 Mon
       - [x] 9a-10a Sprint planning
       - [ ] 545p-615p Wiley swimming
    - 11/17 Tue
    - 11/21 Sat
       - [ ] 7a-8a @40z: Portland half
"""

import re
from typing import List, Optional, Set, Tuple


def extract_section_bounds(
    lines: List[str], section_header_regex: str
) -> Tuple[Optional[int], Optional[int]]:
    """Return (start_line_idx, end_line_idx) of a markdown section matching header regex.

    The section bounds extend until the next markdown header (H1-H6) or HTML comment.
    """
    sec_idx = None
    for idx, line in enumerate(lines):
        if re.match(r"^\s*#{1,6}\s+", line) and re.search(
            section_header_regex, line, re.IGNORECASE
        ):
            sec_idx = idx
            break
    if sec_idx is None:
        return None, None

    end_idx = len(lines)
    for idx in range(sec_idx + 1, len(lines)):
        if re.match(r"^\s*#{1,6}\s+\S", lines[idx]) or re.match(r"^\s*<!--", lines[idx]):
            end_idx = idx
            break
    return sec_idx, end_idx


def extract_checklist_items(
    body: str, section_header_regex: str, unchecked_only: bool = False
) -> List[str]:
    """Extract `- [ ]` or `- [x]` items from the specified section."""
    if not body:
        return []
    lines = body.splitlines()
    sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)
    if sec_idx is None:
        return []

    pattern = (
        r"^\s*[-*+]\s+\[\s\]\s+\S+"
        if unchecked_only
        else r"^\s*[-*+]\s+\[[ xX]\]\s+\S+"
    )
    items = []
    for line in lines[sec_idx + 1 : end_idx]:
        if re.match(pattern, line):
            items.append(line.rstrip())
    return items


def filter_missing_items(
    target_body: str,
    candidate_lines: List[str],
    section_header_regex: Optional[str] = None,
) -> List[str]:
    """Filter candidate lines that are not already present in the target body/section."""
    if not candidate_lines:
        return []
    lines = (target_body or "").splitlines()
    if section_header_regex:
        sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)
        if sec_idx is not None:
            existing_lines = {
                line.strip() for line in lines[sec_idx + 1 : end_idx] if line.strip()
            }
        else:
            existing_lines = {line.strip() for line in lines if line.strip()}
    else:
        existing_lines = {line.strip() for line in lines if line.strip()}

    missing = []
    seen = set()
    for line in candidate_lines:
        norm = line.strip()
        if norm and norm not in existing_lines and norm not in seen:
            missing.append(line)
            seen.add(norm)
    return missing


def update_section_body(
    original_body: str,
    new_bullet_lines: List[str],
    section_header_regex: str,
    default_header: Optional[str] = None,
) -> str:
    """Insert or append bullet lines under the specified section header.

    Cleans empty placeholder bullets (`- [ ] `), preserves multi-line continuations
    under existing bullets, and prepends a new section using `default_header` if no
    matching header exists in `original_body`.

    Args:
        original_body: Existing markdown document text. Example:

            ## Key milestone/focused areas
            - [ ] #101 Existing task
              Indented details for #101
            - [ ] 

            ## Daily
            - 11/16 Mon
        new_bullet_lines: List of markdown bullet lines to append into the section. Example:

            ["- [ ] #102 Newly added task"]
        section_header_regex: Regex pattern matching the target markdown header.
        default_header: Header line (e.g. `## Key milestone/focused areas`) to create
            if no section matching `section_header_regex` is found.

    Returns:
        Updated markdown document string. Example:

            ## Key milestone/focused areas
            - [ ] #101 Existing task
              Indented details for #101
            - [ ] #102 Newly added task

            ## Daily
            - 11/16 Mon
    """
    if not new_bullet_lines:
        return original_body or ""
    if not original_body or not original_body.strip():
        header = default_header or "## Items"
        return f"{header}\n\n" + "\n".join(new_bullet_lines) + "\n"

    lines = original_body.splitlines()
    sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)

    if sec_idx is not None:
        # Clean empty placeholder bullet '- [ ] '
        cleaned_section = []
        for line in lines[sec_idx + 1 : end_idx]:
            if re.match(r"^\s*[-*+]\s+\[\s\]\s*$", line):
                continue
            cleaned_section.append(line)
        lines = lines[: sec_idx + 1] + cleaned_section + lines[end_idx:]
        sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)

        last_bullet_idx = None
        for idx in range(sec_idx + 1, end_idx):
            if re.match(r"^\s*[-*+]\s+", lines[idx]):
                last_bullet_idx = idx

        if last_bullet_idx is not None:
            bullet_match = re.match(r"^(\s*)[-*+]\s+", lines[last_bullet_idx])
            bullet_indent = len(bullet_match.group(1)) if bullet_match else 0
            insert_at = last_bullet_idx + 1
            while insert_at < end_idx:
                curr_line = lines[insert_at]
                if re.match(r"^\s*[-*+]\s+", curr_line):
                    break
                if re.match(r"^\s*#{1,6}\s+", curr_line):
                    break
                fence_match = re.match(r"^(\s*)(`{3,}|~{3,})", curr_line)
                if fence_match:
                    fence_indent = len(fence_match.group(1))
                    if fence_indent > bullet_indent:
                        # Contained code fence within list item: skip past closing fence
                        fence_char = fence_match.group(2)[0]
                        fence_len = len(fence_match.group(2))
                        close_regex = rf"^\s*{fence_char}{{{fence_len},}}\s*$"
                        scan_idx = insert_at + 1
                        while scan_idx < end_idx:
                            if re.match(close_regex, lines[scan_idx]):
                                insert_at = scan_idx + 1
                                break
                            scan_idx += 1
                        else:
                            insert_at = scan_idx
                        continue
                    else:
                        # External code fence: stop before opening fence
                        break
                if not curr_line.strip():
                    next_idx = insert_at + 1
                    while next_idx < end_idx and not lines[next_idx].strip():
                        next_idx += 1
                    if next_idx < end_idx:
                        next_line = lines[next_idx]
                        if (
                            next_line.startswith(" ") or next_line.startswith("\t")
                        ) and not re.match(r"^\s*[-*+]\s+", next_line):
                            insert_at = next_idx
                            continue
                    break
                insert_at += 1
        else:
            insert_at = sec_idx + 1
        updated_lines = lines[:insert_at] + list(new_bullet_lines) + lines[insert_at:]
        res = "\n".join(updated_lines)
        if original_body.endswith("\n") and not res.endswith("\n"):
            res += "\n"
        return res

    header = default_header or "## Items"
    return (
        f"{header}\n\n"
        + "\n".join(new_bullet_lines)
        + "\n\n"
        + original_body.lstrip("\r\n")
    )


def normalize_checklist_text(
    line: str, managed_tag: Optional[str] = None
) -> str:
    """Normalize a markdown bullet/checklist line for duplicate comparison."""
    text = line.strip()
    if managed_tag:
        text = text.replace(managed_tag, "").strip()
    stripped = re.sub(r"^\s*[-*+]\s+(?:\[[ xX]\]\s+)?", "", text)
    return " ".join(stripped.split())


def _tag_line(line: str, managed_tag: Optional[str]) -> str:
    """Append ``managed_tag`` to ``line`` if provided and not already present."""
    if not managed_tag or managed_tag in line:
        return line
    return f"{line} {managed_tag}"


def _parse_daily_blocks(
    daily_lines: List[str],
) -> List[Tuple[str, str, List[str]]]:
    """Group rendered daily lines into [(date_key, header_line, item_lines), ...].

    Uses regex to detect top-level date bullet headers.
    Non-matching non-empty lines following a date header are collected as its ``item_lines``.
    Args:
        daily_lines (List[str]): The list of markdown lines representing the daily schedule.
           Example input ``daily_lines``::
               [
                   "- 11/16 Mon",
                   "   - [ ] 545p-615p Wiley swimming",
                   "- 11/17 Tue",
                   "- 11/21 Sat",
                   "   - [ ] 7a-8a @40z: Portland half",
                   "   - [ ] 9a-1230p: 2ndary school",
               ]

    Returns:
        List[Tuple[str, str, List[str]]]: A list of tuples containing the date key, header line, and item lines for each date.
            Example:

                Returns::
                    [
                        ("11/16", "- 11/16 Mon", ["   - [ ] 545p-615p Wiley swimming"]),
                        ("11/17", "- 11/17 Tue", []),
                        ("11/21", "- 11/21 Sat", ["   - [ ] 7a-8a @40z: Portland half", "   - [ ] 9a-1230p: 2ndary school"]),
                    ]    
    """
    blocks: List[Tuple[str, str, List[str]]] = []
    date_re = re.compile(r"^\s*[-*+]\s+(\d{1,2}/\d{1,2})\b")
    for line in daily_lines:
        m = date_re.match(line)
        if m:
            blocks.append((m.group(1), line, []))
        elif blocks and line.strip():
            blocks[-1][2].append(line)
    return blocks


def merge_daily_section(
    original_body: str,
    daily_lines: List[str],
    section_header_regex: str = r"Daily",
    default_header: str = "## Daily",
    managed_tag: Optional[str] = None,
) -> str:
    """Merge date-grouped daily schedule lines into a markdown section without duplicates.

    Preserves existing checked (`- [x]`) items and manual entries under each date,
    inserts only missing items under matching `- M/D` headers, and appends any
    dates not yet present in the section.

    When `managed_tag` (e.g. `<!-- gcal -->`) is provided:
    - Newly added items are suffixed with `managed_tag`.
    - Existing lines containing `managed_tag` under a synced date that are no
      longer present in `daily_lines` for that date are pruned, while untagged
      (manual) lines are always preserved.

    Args:
        original_body: Full markdown document text to update.
        daily_lines: Rendered date headers and checklist items to merge.
            Example input ``daily_lines``::
               [
                   "- 11/16 Mon",
                   "   - [ ] 545p-615p Wiley swimming",
                   "- 11/17 Tue",
                   "- 11/21 Sat",
                   "   - [ ] 7a-8a @40z: Portland half",
                   "   - [ ] 9a-1230p: 2ndary school",
               ]
        section_header_regex: Regex to identify the target section header.
        default_header: Default header to create if the section is not found.
        managed_tag: Optional tag to mark and prune managed lines.

    Returns:
        Updated markdown document string.
    """
    if not daily_lines:
        return original_body or ""
    tagged_all = [_tag_line(l, managed_tag) if re.match(r"^\s+[-*+]\s+", l) else l for l in daily_lines]
    if not original_body or not original_body.strip():
        return update_section_body(
            original_body,
            tagged_all,
            section_header_regex,
            default_header=default_header,
        )

    lines = original_body.splitlines()
    sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)
    if sec_idx is None:
        return update_section_body(
            original_body,
            tagged_all,
            section_header_regex,
            default_header=default_header,
        )

    date_re = re.compile(r"^\s*[-*+]\s+(\d{1,2}/\d{1,2})\b")
    section_lines = lines[sec_idx + 1 : end_idx]

    date_starts: List[Tuple[str, int]] = []
    for idx, line in enumerate(section_lines):
        m = date_re.match(line)
        if m:
            date_starts.append((m.group(1), idx))

    date_spans = {}
    for i, (dk, start_i) in enumerate(date_starts):
        end_i = date_starts[i + 1][1] if i + 1 < len(date_starts) else len(section_lines)
        date_spans[dk] = (start_i, end_i)

    missing_date_lines: List[str] = []
    # Track per-span replacements/insertions: (start_i, end_i, new_block_lines)
    span_updates: List[Tuple[int, int, List[str]]] = []
    for dk, header_line, cal_items in _parse_daily_blocks(daily_lines):
        if dk not in date_spans:
            missing_date_lines.append(header_line)
            missing_date_lines.extend(_tag_line(item, managed_tag) for item in cal_items)
            continue

        start_i, end_i = date_spans[dk]
        block_body = section_lines[start_i + 1 : end_i]
        cal_norms = {
            normalize_checklist_text(item, managed_tag=managed_tag)
            for item in cal_items
        }
        if managed_tag:
            block_body = [
                l
                for l in block_body
                if managed_tag not in l
                or normalize_checklist_text(l, managed_tag=managed_tag) in cal_norms
            ]

        existing_norms = {
            normalize_checklist_text(l, managed_tag=managed_tag)
            for l in block_body
            if l.strip()
        }
        to_add: List[str] = []
        for item in cal_items:
            norm = normalize_checklist_text(item, managed_tag=managed_tag)
            if norm and norm not in existing_norms:
                to_add.append(_tag_line(item, managed_tag))
                existing_norms.add(norm)

        if to_add:
            ins_i = len(block_body)
            while ins_i > 0 and not block_body[ins_i - 1].strip():
                ins_i -= 1
            block_body = block_body[:ins_i] + to_add + block_body[ins_i:]

        if block_body != section_lines[start_i + 1 : end_i]:
            span_updates.append((start_i + 1, end_i, block_body))

    for s_i, e_i, new_block in sorted(span_updates, key=lambda x: x[0], reverse=True):
        section_lines = section_lines[:s_i] + new_block + section_lines[e_i:]

    merged_body = "\n".join(lines[: sec_idx + 1] + section_lines + lines[end_idx:])
    if original_body.endswith("\n") and not merged_body.endswith("\n"):
        merged_body += "\n"

    if missing_date_lines:
        merged_body = update_section_body(
            merged_body,
            missing_date_lines,
            section_header_regex,
            default_header=default_header,
        )
    return merged_body


def merge_section_unique_lines(
    original_body: str,
    candidate_lines: List[str],
    section_header_regex: str,
    default_header: Optional[str] = None,
    managed_tag: Optional[str] = None,
) -> str:
    """Append candidate bullet lines to a section, skipping lines already present.

    When ``managed_tag`` is provided, newly appended lines are suffixed with
    ``managed_tag`` and existing ``managed_tag`` lines in the section that are
    no longer in ``candidate_lines`` are pruned.
    """
    if not candidate_lines and not managed_tag:
        return original_body or ""
    lines = (original_body or "").splitlines()
    sec_idx, end_idx = extract_section_bounds(lines, section_header_regex)
    if sec_idx is None:
        if not candidate_lines:
            return original_body or ""
        tagged = [_tag_line(l, managed_tag) for l in candidate_lines]
        return update_section_body(
            original_body,
            tagged,
            section_header_regex,
            default_header=default_header,
        )

    section_lines = lines[sec_idx + 1 : end_idx]
    cand_norms = {
        normalize_checklist_text(l, managed_tag=managed_tag)
        for l in candidate_lines
    }
    if managed_tag:
        pruned_section = [
            l
            for l in section_lines
            if managed_tag not in l
            or normalize_checklist_text(l, managed_tag=managed_tag) in cand_norms
        ]
    else:
        pruned_section = section_lines

    working_body = original_body
    if pruned_section != section_lines:
        working_body = "\n".join(
            lines[: sec_idx + 1] + pruned_section + lines[end_idx:]
        )
        if original_body.endswith("\n") and not working_body.endswith("\n"):
            working_body += "\n"

    existing_norms = {
        normalize_checklist_text(l, managed_tag=managed_tag)
        for l in pruned_section
        if l.strip()
    }
    missing = [
        _tag_line(l, managed_tag)
        for l in candidate_lines
        if normalize_checklist_text(l, managed_tag=managed_tag) not in existing_norms
    ]
    if not missing:
        return working_body
    return update_section_body(
        working_body,
        missing,
        section_header_regex,
        default_header=default_header,
    )


def extract_issue_keys_from_bullet(
    line: str, default_repo: Optional[str] = None
) -> List[str]:
    """Extract repository issue references (e.g. repo#123) from a bullet line."""
    if not re.match(r"^\s*[-*+]\s+", line):
        return []
    if re.match(r"^\s*[-*+]\s+\[\s\]\s*$", line):
        return []

    keys = []
    seen = set()
    for repo, num in re.findall(
        r"https?://github\.com/[\w.-]+/([\w.-]+)/issues/(\d+)", line
    ):
        k = f"{repo}#{num}"
        if k not in seen:
            keys.append(k)
            seen.add(k)

    line_no_urls = re.sub(r"https?://\S+", "", line)
    for repo, num in re.findall(
        r"(?<![/\w.-])(?:[\w.-]+/)?([\w.-]+)#(\d+)\b", line_no_urls
    ):
        k = f"{repo}#{num}"
        if k not in seen:
            keys.append(k)
            seen.add(k)
    if default_repo:
        for num in re.findall(r"(?<![/\w.-])#(\d+)\b", line_no_urls):
            k = f"{default_repo}#{num}"
            if k not in seen:
                keys.append(k)
                seen.add(k)
    return keys
