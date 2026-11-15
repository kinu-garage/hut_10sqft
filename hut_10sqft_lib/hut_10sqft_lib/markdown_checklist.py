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
    """Insert or append bullet lines under the specified section header."""
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
