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

import unittest

from hut_10sqft_lib.markdown_checklist import (
    extract_checklist_items,
    extract_issue_keys_from_bullet,
    extract_section_bounds,
    filter_missing_items,
    merge_daily_section,
    merge_section_unique_lines,
    update_section_body,
)


class TestMarkdownChecklist(unittest.TestCase):

    def test_extract_section_bounds(self):
        body = (
            "# Title\n\n"
            "## Key milestone/focused areas\n"
            "- [ ] #101 Task A\n"
            "- [x] #102 Task B\n\n"
            "## Daily\n"
            "- 11/16 Mo\n"
        )
        lines = body.splitlines()
        s, e = extract_section_bounds(lines, r"^\s*##\s*Key milestone")
        self.assertEqual(s, 2)
        self.assertEqual(e, 6)

    def test_extract_section_bounds_requires_header(self):
        body = (
            "- [ ] Review Section before header\n\n"
            "## Section\n"
            "- [ ] Real Item\n"
        )
        lines = body.splitlines()
        s, e = extract_section_bounds(lines, r"Section")
        self.assertEqual(s, 2)
        items = extract_checklist_items(body, r"Section")
        self.assertEqual(len(items), 1)
        self.assertIn("Real Item", items[0])

    def test_extract_checklist_items(self):
        body = (
            "## Key milestone/focused areas\n"
            "- [ ] #101 Task A\n"
            "- [x] #102 Task B\n"
            "- normal text\n"
        )
        unchecked = extract_checklist_items(body, r"Key milestone", unchecked_only=True)
        self.assertEqual(unchecked, ["- [ ] #101 Task A"])

        all_items = extract_checklist_items(body, r"Key milestone", unchecked_only=False)
        self.assertEqual(len(all_items), 2)

    def test_filter_missing_items(self):
        target = "## Section\n- [ ] #101 Existing\n"
        candidates = ["- [ ] #101 Existing", "- [ ] #102 New Task"]
        missing = filter_missing_items(target, candidates)
        self.assertEqual(missing, ["- [ ] #102 New Task"])

    def test_update_section_body(self):
        original = "## Section\n- [ ] #101 Existing\n\n## Next\nOther"
        updated = update_section_body(
            original, ["- [ ] #102 Added"], r"Section"
        )
        self.assertIn("- [ ] #101 Existing\n- [ ] #102 Added", updated)
        self.assertIn("## Next\nOther", updated)

    def test_update_section_body_with_multiline_continuation(self):
        body = (
            "## Tasks\n"
            "- [ ] Existing task\n"
            "  Details for existing task\n"
            "  More notes\n"
            "\n"
            "## Other Section\n"
        )
        updated = update_section_body(
            body,
            ["- [ ] New added task"],
            r"Tasks",
        )
        lines = updated.splitlines()
        existing_idx = lines.index("- [ ] Existing task")
        details_idx = lines.index("  Details for existing task")
        notes_idx = lines.index("  More notes")
        new_task_idx = lines.index("- [ ] New added task")

        self.assertLess(existing_idx, details_idx)
        self.assertLess(details_idx, notes_idx)
        self.assertLess(notes_idx, new_task_idx)

    def test_update_section_body_with_blank_separated_indented_continuation(self):
        body = (
            "## Tasks\n"
            "- [ ] Existing\n"
            "\n"
            "  Existing details\n"
        )
        updated = update_section_body(
            body,
            ["- [ ] New"],
            r"Tasks",
        )
        lines = updated.splitlines()
        existing_idx = lines.index("- [ ] Existing")
        details_idx = lines.index("  Existing details")
        new_idx = lines.index("- [ ] New")

        self.assertLess(existing_idx, details_idx)
        self.assertLess(details_idx, new_idx)

    def test_update_section_body_with_unindented_lazy_continuation(self):
        body = (
            "## Tasks\n"
            "- [ ] Existing\n"
            "continued description\n"
        )
        updated = update_section_body(
            body,
            ["- [ ] New"],
            r"Tasks",
        )
        lines = updated.splitlines()
        existing_idx = lines.index("- [ ] Existing")
        desc_idx = lines.index("continued description")
        new_idx = lines.index("- [ ] New")

        self.assertLess(existing_idx, desc_idx)
        self.assertLess(desc_idx, new_idx)

    def test_update_section_body_stops_before_external_fenced_code_block(self):
        body = (
            "## Tasks\n"
            "- [ ] Existing\n"
            "```\n"
            "example\n"
            "\n"
            "more\n"
            "```\n"
        )
        updated = update_section_body(
            body,
            ["- [ ] New"],
            r"Tasks",
        )
        lines = updated.splitlines()
        existing_idx = lines.index("- [ ] Existing")
        new_idx = lines.index("- [ ] New")
        fence_idx = lines.index("```")

        self.assertLess(existing_idx, new_idx)
        self.assertLess(new_idx, fence_idx)

    def test_update_section_body_preserves_contained_fenced_code_block(self):
        body = (
            "## Tasks\n"
            "- [ ] Existing task with code\n"
            "  ```bash\n"
            "  echo 'hello'\n"
            "  ```\n"
        )
        updated = update_section_body(
            body,
            ["- [ ] New"],
            r"Tasks",
        )
        lines = updated.splitlines()
        existing_idx = lines.index("- [ ] Existing task with code")
        code_idx = lines.index("  echo 'hello'")
        closing_fence_idx = lines.index("  ```")
        new_idx = lines.index("- [ ] New")

        self.assertLess(existing_idx, code_idx)
        self.assertLess(code_idx, closing_fence_idx)
        self.assertLess(closing_fence_idx, new_idx)

    def test_extract_issue_keys(self):
        line = "- [ ] #2495 2026 Annual project planning"
        keys = extract_issue_keys_from_bullet(line, default_repo="40z-life")
        self.assertEqual(keys, ["40z-life#2495"])

        line2 = "- [ ] kinu-garage/hut_10sqft#1479 Adding account"
        keys2 = extract_issue_keys_from_bullet(line2, default_repo="40z-life")
        self.assertEqual(keys2, ["hut_10sqft#1479"])

    def test_extract_multiple_issue_keys_from_bullet(self):
        line = "- [ ] repo#1 and repo#2"
        keys = extract_issue_keys_from_bullet(line, default_repo="fallback")
        self.assertEqual(keys, ["repo#1", "repo#2"])

        line2 = "- [ ] #10 and #20"
        keys2 = extract_issue_keys_from_bullet(line2, default_repo="fallback")
        self.assertEqual(keys2, ["fallback#10", "fallback#20"])

    def test_merge_daily_section_idempotent_and_preserves_checked(self):
        original_body = (
            "## Key milestone\n\n"
            "### Daily\n"
            "- 11/23 Mon\n"
            "   - [x] 430p-6p Hs basketball\n"
            "   - [ ] Manual note\n"
        )
        daily_lines = [
            "- 11/23 Mon",
            "   - [ ] 430p-6p Hs basketball",
            "   - [ ] 605p-650p Hs TKD",
            "- 11/24 Tue",
            "   - [ ] 5p-6p As Mathnasium",
        ]

        updated = merge_daily_section(original_body, daily_lines)

        self.assertEqual(updated.count("430p-6p Hs basketball"), 1)
        self.assertIn("   - [x] 430p-6p Hs basketball", updated)
        self.assertIn("   - [ ] Manual note", updated)
        self.assertIn("   - [ ] 605p-650p Hs TKD", updated)
        self.assertEqual(updated.count("- 11/23 Mon"), 1)
        self.assertIn("- 11/24 Tue\n   - [ ] 5p-6p As Mathnasium", updated)

        # Second run is a complete no-op
        self.assertEqual(merge_daily_section(updated, daily_lines), updated)

    def test_merge_section_unique_lines(self):
        original_body = (
            "### Notable period\n"
            "- 11/25 We – 11/27 Fr Thanksgiving week\n"
        )
        candidates = [
            "- 11/25 We – 11/27 Fr Thanksgiving week",
            "- 11/28 Sa – 11/29 Su Weekend trip",
        ]
        updated = merge_section_unique_lines(
            original_body,
            candidates,
            r"Notable period",
            default_header="## Notable period",
        )
        self.assertEqual(updated.count("11/25 We – 11/27 Fr Thanksgiving week"), 1)
        self.assertIn("- 11/28 Sa – 11/29 Su Weekend trip", updated)
        self.assertEqual(
            merge_section_unique_lines(
                updated, candidates, r"Notable period", default_header="## Notable period"
            ),
            updated,
        )


if __name__ == "__main__":
    unittest.main()
