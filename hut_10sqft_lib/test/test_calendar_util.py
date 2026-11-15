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
import zoneinfo
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from hut_10sqft_lib.calendar_util import (
    extract_occurrences_in_window,
    fetch_ical_content,
    format_time_slug,
    parse_datetime_val,
    parse_ical_vevents,
    render_schedule_markdown,
)


class TestCalendarUtil(unittest.TestCase):

    def test_parse_datetime_val(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        d = parse_datetime_val("20261116", target_tz=tz)
        self.assertEqual(d, date(2026, 11, 16))

        dt_utc = parse_datetime_val("20261116T210000Z", target_tz=tz)
        self.assertEqual(dt_utc.hour, 16)  # 21 UTC is 16:00 EST

        # Valid tz_id conversion
        dt_custom_tz = parse_datetime_val(
            "20261116T180000", tz_id="America/Chicago", target_tz=tz
        )
        self.assertEqual(dt_custom_tz.hour, 19)  # 18:00 CST is 19:00 EST

        # Invalid tz_id raises zoneinfo.ZoneInfoNotFoundError or KeyError
        with self.assertRaises(Exception):
            parse_datetime_val("20261116T180000", tz_id="Invalid/Timezone", target_tz=tz)

    def test_format_time_slug(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        dt1 = datetime(2026, 11, 16, 17, 45, tzinfo=tz)
        self.assertEqual(format_time_slug(dt1), "545p")

        dt2 = datetime(2026, 11, 16, 18, 0, tzinfo=tz)
        self.assertEqual(format_time_slug(dt2), "6p")

    def test_recurrence_id_override(self):
        # Base event: every Thursday at 16:30
        # Exception event: 2026-11-19 moved to 17:00
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:math-series-1\n"
            "SUMMARY:Math Tutoring\n"
            "DTSTART;TZID=America/New_York:20261105T163000\n"
            "DTEND;TZID=America/New_York:20261105T173000\n"
            "RRULE:FREQ=WEEKLY;BYDAY=TH\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:math-series-1\n"
            "SUMMARY:Math Tutoring\n"
            "RECURRENCE-ID;TZID=America/New_York:20261119T163000\n"
            "DTSTART;TZID=America/New_York:20261119T170000\n"
            "DTEND;TZID=America/New_York:20261119T180000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = parse_ical_vevents(ics_text, cal_name="1-Kods")
        tz = zoneinfo.ZoneInfo("America/New_York")
        w_start = datetime(2026, 11, 19, 0, 0, tzinfo=tz)
        w_end = datetime(2026, 11, 19, 23, 59, tzinfo=tz)

        occs = extract_occurrences_in_window(events, w_start, w_end, target_tz=tz)
        # Should only have 1 occurrence (the override at 17:00), NOT two!
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].hour, 17)
        self.assertEqual(occs[0]["start"].minute, 0)

    def test_render_schedule_markdown(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        occs = [
            {
                "cal_name": "1-Kods",
                "summary": "Wiley swimming",
                "start": datetime(2026, 11, 16, 17, 45, tzinfo=tz),
                "end": datetime(2026, 11, 16, 18, 15, tzinfo=tz),
                "is_all_day": False,
                "multi_day": False,
            },
            {
                "cal_name": "4-Trico",
                "summary": "Portland half",
                "start": datetime(2026, 11, 21, 7, 0, tzinfo=tz),
                "end": datetime(2026, 11, 21, 8, 0, tzinfo=tz),
                "is_all_day": False,
                "multi_day": False,
            },
        ]
        prefix_map = {"4-Trico": "@40z: "}
        notable, daily = render_schedule_markdown(
            occs,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 21),
            cal_prefix_map=prefix_map,
        )
        self.assertEqual(len(notable), 0)  # No multi-day events
        daily_text = "\n".join(daily)
        self.assertIn("545p-615p Wiley swimming", daily_text)
        self.assertIn("@40z: Portland half", daily_text)

    @patch("urllib.request.urlopen")
    def test_fetch_ical_content_timeout(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"BEGIN:VCALENDAR\nEND:VCALENDAR\n"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        content = fetch_ical_content("https://example.com/calendar.ics", timeout=15.0)
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertEqual(mock_urlopen.call_args.kwargs.get("timeout"), 15.0)

    def test_valarm_nested_component_ignored(self):
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:vevent\n"
            "uid:event-with-alarm\n"
            "summary:Real Event Title\n"
            "dtstart:20261116T100000Z\n"
            "dtend:20261116T110000Z\n"
            "BEGIN:VALARM\n"
            "ACTION:DISPLAY\n"
            "summary:Alarm Reminder\n"
            "description:This is an alarm description\n"
            "TRIGGER:-PT15M\n"
            "END:VALARM\n"
            "END:vevent\n"
            "END:VCALENDAR\n"
        )
        events = parse_ical_vevents(ics_text)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["SUMMARY"], "Real Event Title")

    def test_recurrence_id_timed_event_distinction(self):
        # Two occurrences on same day (e.g. 09:00 and 10:00)
        # Override only 09:00, 10:00 should remain
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:hourly-event\n"
            "SUMMARY:Hourly Check\n"
            "DTSTART;TZID=America/New_York:20261116T090000\n"
            "DTEND;TZID=America/New_York:20261116T093000\n"
            "RRULE:FREQ=HOURLY;COUNT=2\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:hourly-event\n"
            "RECURRENCE-ID;TZID=America/New_York:20261116T090000\n"
            "SUMMARY:Hourly Check Rescheduled\n"
            "DTSTART;TZID=America/New_York:20261116T091500\n"
            "DTEND;TZID=America/New_York:20261116T094500\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        # Should have 2 occurrences: the overridden 09:15 and the untouched 10:00
        summaries = [o["summary"] for o in occs]
        self.assertIn("Hourly Check Rescheduled", summaries)
        self.assertIn("Hourly Check", summaries)
        self.assertEqual(len(occs), 2)

    def test_cancelled_override_suppresses_base_without_emitting(self):
        # Base event: daily at 10:00
        # Exception on 2026-11-17 with STATUS:CANCELLED
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:daily-cancelled\n"
            "SUMMARY:Daily Standup\n"
            "DTSTART;TZID=America/New_York:20261116T100000\n"
            "DTEND;TZID=America/New_York:20261116T103000\n"
            "RRULE:FREQ=DAILY;COUNT=3\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:daily-cancelled\n"
            "RECURRENCE-ID;TZID=America/New_York:20261117T100000\n"
            "STATUS:CANCELLED\n"
            "SUMMARY:Daily Standup\n"
            "DTSTART;TZID=America/New_York:20261117T100000\n"
            "DTEND;TZID=America/New_York:20261117T103000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 18, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        # Should have 2 occurrences (11/16 and 11/18), NOT 11/17
        occ_dates = [o["start"].date() for o in occs]
        self.assertIn(date(2026, 11, 16), occ_dates)
        self.assertIn(date(2026, 11, 18), occ_dates)
        self.assertNotIn(date(2026, 11, 17), occ_dates)
        self.assertEqual(len(occs), 2)

    def test_duration_parsing(self):
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:timed-duration\n"
            "SUMMARY:Two Hour Workshop\n"
            "DTSTART;TZID=America/New_York:20261116T140000\n"
            "DURATION:PT2H\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:allday-duration\n"
            "SUMMARY:Three Day Trip\n"
            "DTSTART:20261117\n"
            "DURATION:P3D\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 21, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 2)
        timed = next(o for o in occs if o["summary"] == "Two Hour Workshop")
        self.assertEqual(timed["end"] - timed["start"], timedelta(hours=2))

        allday = next(o for o in occs if o["summary"] == "Three Day Trip")
        self.assertTrue(allday["multi_day"])
        self.assertEqual(allday["end"] - allday["start"], timedelta(days=3))

    def test_exdate_timed_and_tzid(self):
        # Hourly rule on 2026-11-16 at 09:00 and 10:00 (EST)
        # EXDATE for 09:00 EST specified in CST (08:00 CST)
        # 10:00 EST should remain!
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:exdate-hourly\n"
            "SUMMARY:Standup Sync\n"
            "DTSTART;TZID=America/New_York:20261116T090000\n"
            "DTEND;TZID=America/New_York:20261116T093000\n"
            "RRULE:FREQ=HOURLY;COUNT=2\n"
            "EXDATE;TZID=America/Chicago:20261116T080000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].hour, 10)

    def test_dtend_distinct_tzid(self):
        # DTSTART in Chicago at 10:00 (11:00 EST)
        # DTEND in New_York at 12:00 (12:00 EST) -> Duration is 1 hour!
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:cross-tz\n"
            "SUMMARY:Cross TZ Flight\n"
            "DTSTART;TZID=America/Chicago:20261116T100000\n"
            "DTEND;TZID=America/New_York:20261116T120000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].hour, 11)
        self.assertEqual(occs[0]["end"].hour, 12)
        self.assertEqual(occs[0]["end"] - occs[0]["start"], timedelta(hours=1))

        # Case-insensitive parameter check: lowercase tzid
        ics_text_lowercase = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:cross-tz-lower\n"
            "SUMMARY:Cross TZ Flight Lower\n"
            "DTSTART;tzid=America/Chicago:20261116T100000\n"
            "DTEND;tzid=America/New_York:20261116T120000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events_lower = parse_ical_vevents(ics_text_lowercase)
        occs_lower = extract_occurrences_in_window(
            events_lower,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs_lower), 1)
        self.assertEqual(occs_lower[0]["start"].hour, 11)
        self.assertEqual(occs_lower[0]["end"].hour, 12)
        self.assertEqual(occs_lower[0]["end"] - occs_lower[0]["start"], timedelta(hours=1))

    def test_rrule_source_tz_expansion(self):
        # DTSTART: 20261116T003000Z (Monday 00:30 UTC -> Sunday 19:30 EST)
        # RRULE: FREQ=WEEKLY;BYDAY=MO
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:weekly-utc-event\n"
            "SUMMARY:Late UTC Sync\n"
            "DTSTART:20261116T003000Z\n"
            "DTEND:20261116T013000Z\n"
            "RRULE:FREQ=WEEKLY;BYDAY=MO\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 15, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 22, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        starts = [o["start"] for o in occs]
        self.assertEqual(len(starts), 2)
        self.assertEqual(starts[0], datetime(2026, 11, 15, 19, 30, tzinfo=tz))
        self.assertEqual(starts[1], datetime(2026, 11, 22, 19, 30, tzinfo=tz))

    def test_allday_rrule_with_date_until(self):
        # All-day event with UNTIL=20261118
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:allday-until\n"
            "SUMMARY:Multi-day Conference\n"
            "DTSTART:20261116\n"
            "DTEND:20261117\n"
            "RRULE:FREQ=DAILY;UNTIL=20261118\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 15, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 22, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        occ_dates = [o["start"].date() for o in occs]
        self.assertEqual(occ_dates, [date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18)])

    def test_window_start_non_inclusive_overlap(self):
        # Event that ended exactly at window_start should NOT be included
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:ended-event\n"
            "SUMMARY:Past Event\n"
            "DTSTART;TZID=America/New_York:20261115T220000\n"
            "DTEND;TZID=America/New_York:20261116T000000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 22, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 0)

    def test_allday_recurring_carry_in_overlap(self):
        # DTSTART: 20261115 (Sunday), DURATION: P3D (ends 20261118 Wednesday)
        # RRULE: FREQ=WEEKLY;COUNT=2
        # Window starts 2026-11-16 (Monday)
        # The 11/15 occurrence must be included as it overlaps 11/16!
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:weekly-3day\n"
            "SUMMARY:3-Day Conference\n"
            "DTSTART:20261115\n"
            "DURATION:P3D\n"
            "RRULE:FREQ=WEEKLY;COUNT=2\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 21, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].date(), date(2026, 11, 15))
        self.assertEqual(occs[0]["end"].date(), date(2026, 11, 18))

    def test_floating_rrule_with_floating_until(self):
        # Floating timed event (no TZID, no Z) with floating UNTIL
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:floating-rrule\n"
            "SUMMARY:Floating Meeting\n"
            "DTSTART:20261116T090000\n"
            "DTEND:20261116T093000\n"
            "RRULE:FREQ=DAILY;UNTIL=20261118T090000\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 15, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 22, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 3)
        for o in occs:
            self.assertEqual(o["start"].tzinfo, tz)
            self.assertEqual(o["start"].hour, 9)
            self.assertEqual(o["start"].minute, 0)

    def test_exact_duration_across_dst_transition(self):
        # 2020-11-01 was DST transition in America/New_York (2:00 EDT -> 1:00 EST)
        # DTSTART: 20201031T043000Z (00:30 EDT on Oct 31)
        # DTEND: 20201031T063000Z (02:30 EDT on Oct 31) -> 2 hours duration
        # RRULE: DAILY;COUNT=2
        # Second occurrence on 2020-11-01 starts at 00:30 EDT and ends at 01:30 EST (2 hours elapsed!)
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:dst-transition\n"
            "SUMMARY:Night Shift\n"
            "DTSTART:20201031T043000Z\n"
            "DTEND:20201031T063000Z\n"
            "RRULE:FREQ=DAILY;COUNT=2\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2020, 10, 31, 0, 0, tzinfo=tz),
            window_end=datetime(2020, 11, 2, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 2)
        nov1_occ = occs[1]
        self.assertEqual(nov1_occ["start"].day, 1)
        self.assertEqual(nov1_occ["end"].hour, 1)
        self.assertEqual(nov1_occ["end"].minute, 30)
        utc_tz = zoneinfo.ZoneInfo("UTC")
        elapsed = nov1_occ["end"].astimezone(utc_tz) - nov1_occ["start"].astimezone(utc_tz)
        self.assertEqual(elapsed, timedelta(hours=2))

    def test_render_schedule_allday_multiday_last_occupied_date(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        # All day event: 2026-11-16 through 2026-11-17 (exclusive endpoint 2026-11-18)
        occs = [
            {
                "cal_name": "1-Kods",
                "summary": "Fall Camp",
                "start": datetime(2026, 11, 16, 0, 0, tzinfo=tz),
                "end": datetime(2026, 11, 18, 0, 0, tzinfo=tz),
                "is_all_day": True,
                "multi_day": True,
            }
        ]
        notable, daily = render_schedule_markdown(
            occs,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 21),
        )
        self.assertEqual(len(notable), 1)
        # Should display 11/16 Mon – 11/17 Tue, NOT 11/18 Wed
        self.assertIn("11/16 Mon – 11/17 Tue Fall Camp", notable[0])

    def test_render_schedule_overnight_event_in_window(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        # Event starting Sunday 2026-11-15 at 22:00 and ending Monday 2026-11-16 at 02:00
        # Schedule rendered for 2026-11-16 through 2026-11-21
        occs = [
            {
                "cal_name": "1-Kods",
                "summary": "Late Night Hackathon",
                "start": datetime(2026, 11, 15, 22, 0, tzinfo=tz),
                "end": datetime(2026, 11, 16, 2, 0, tzinfo=tz),
                "is_all_day": False,
                "multi_day": False,
            }
        ]
        notable, daily = render_schedule_markdown(
            occs,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 21),
        )
        self.assertEqual(len(notable), 0)
        daily_text = "\n".join(daily)
        self.assertIn("11/16 Mon", daily_text)
        self.assertIn("Late Night Hackathon", daily_text)



    def test_repeated_dst_hour_window_boundary_utc_comparison(self):
        # 2020-11-01 repeated hour in NY (fall transition)
        # DTSTART: 20201031T043000Z (00:30 EDT on Oct 31)
        # DTEND: 20201031T063000Z (02:30 EDT on Oct 31) -> 2h duration
        # Nov 1 occurrence starts 00:30 EDT, ends 01:30 EST (fold=1, 06:30 UTC)
        # Window starts at 01:45 EDT (fold=0, 05:45 UTC)
        # Although wall clock 01:30 < 01:45, UTC 06:30 > 05:45, so occurrence must be included!
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:dst-repeated-hour\n"
            "SUMMARY:Night Shift\n"
            "DTSTART:20201031T043000Z\n"
            "DTEND:20201031T063000Z\n"
            "RRULE:FREQ=DAILY;COUNT=2\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        w_start = datetime(2020, 11, 1, 1, 45, fold=0, tzinfo=tz)
        w_end = datetime(2020, 11, 2, 23, 59, tzinfo=tz)
        occs = extract_occurrences_in_window(
            events,
            window_start=w_start,
            window_end=w_end,
            target_tz=tz,
        )
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].day, 1)

    def test_nominal_day_duration_across_dst_transition(self):
        # DTSTART;TZID=America/New_York:20201031T003000
        # DURATION:P1D
        # RRULE:FREQ=DAILY;COUNT=2
        # Nov 1 occurrence starts at 00:30 EDT, must end on Nov 2 at 00:30 EST (nominal day)
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:p1d-dst\n"
            "SUMMARY:Daily 24h Block\n"
            "DTSTART;TZID=America/New_York:20201031T003000\n"
            "DURATION:P1D\n"
            "RRULE:FREQ=DAILY;COUNT=2\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2020, 10, 31, 0, 0, tzinfo=tz),
            window_end=datetime(2020, 11, 3, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 2)
        nov1_occ = occs[1]
        self.assertEqual(nov1_occ["start"].day, 1)
        self.assertEqual(nov1_occ["start"].hour, 0)
        self.assertEqual(nov1_occ["start"].minute, 30)
        # End must be Nov 2 at 00:30 EST
        self.assertEqual(nov1_occ["end"].day, 2)
        self.assertEqual(nov1_occ["end"].hour, 0)
        self.assertEqual(nov1_occ["end"].minute, 30)

        # Carry-in check: window starts Nov 2 at 00:15 EST (before event ends at 00:30 EST)
        carry_in_occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2020, 11, 2, 0, 15, tzinfo=tz),
            window_end=datetime(2020, 11, 2, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(carry_in_occs), 1)
        self.assertEqual(carry_in_occs[0]["start"].day, 1)
        self.assertEqual(carry_in_occs[0]["end"].day, 2)
        self.assertEqual(carry_in_occs[0]["end"].hour, 0)
        self.assertEqual(carry_in_occs[0]["end"].minute, 30)

    def test_spring_transition_recurrence_bound_utc_subtraction(self):
        # 2026-03-08 spring transition in NY (2:00 EST -> 3:00 EDT)
        # DTSTART: 20260307T060000Z
        # DTEND: 20260307T080000Z (2 hours duration)
        # RRULE: DAILY;COUNT=2
        # Second occurrence on 2026-03-08 is 06:00 UTC - 08:00 UTC (ends at 04:00 EDT)
        # Window starts 2026-03-08 at 03:30 EDT
        # The 06:00 UTC occurrence overlaps and must be included!
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:spring-dst\n"
            "SUMMARY:Spring Transition Sync\n"
            "DTSTART:20260307T060000Z\n"
            "DTEND:20260307T080000Z\n"
            "RRULE:FREQ=DAILY;COUNT=2\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        w_start = datetime(2026, 3, 8, 3, 30, tzinfo=tz)
        w_end = datetime(2026, 3, 8, 23, 59, tzinfo=tz)
        occs = extract_occurrences_in_window(
            events,
            window_start=w_start,
            window_end=w_end,
            target_tz=tz,
        )
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["start"].astimezone(zoneinfo.ZoneInfo("UTC")).hour, 6)



    def test_default_duration_without_dtend_or_duration(self):
        # Timed event without DTEND or DURATION: default duration is 0
        # All-day event without DTEND or DURATION: default duration is 1 day
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:instant-event\n"
            "SUMMARY:Instant Alarm\n"
            "DTSTART;TZID=America/New_York:20261116T170000\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:allday-default\n"
            "SUMMARY:All Day Single\n"
            "DTSTART:20261116\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )
        self.assertEqual(len(occs), 2)
        instant = next(o for o in occs if o["summary"] == "Instant Alarm")
        self.assertEqual(instant["start"], instant["end"])
        self.assertEqual(instant["end"] - instant["start"], timedelta(0))

        allday = next(o for o in occs if o["summary"] == "All Day Single")
        self.assertFalse(allday["multi_day"])
        self.assertEqual(allday["end"] - allday["start"], timedelta(days=1))

        notable, daily = render_schedule_markdown(
            occs,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 16),
        )
        daily_text = "\n".join(daily)
        self.assertIn("5p Instant Alarm", daily_text)
        self.assertNotIn("5p-5p", daily_text)
        self.assertIn("All Day Single", daily_text)

    def test_zero_duration_window_boundary_inclusion(self):
        # Verify boundary behavior at window_start:
        # 1. Zero-duration non-recurring event at window_start must be included.
        # 2. Positive-duration non-recurring event ending at window_start must be excluded.
        # 3. Zero-duration recurring occurrence at window_start must be included.
        # 4. Positive-duration recurring occurrence ending at window_start must be excluded.
        ics_text = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:zero-dur-nonrecurring\n"
            "SUMMARY:Zero Non-Recurring at Start\n"
            "DTSTART;TZID=America/New_York:20261116T000000\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:pos-dur-nonrecurring\n"
            "SUMMARY:Positive Non-Recurring Ending at Start\n"
            "DTSTART;TZID=America/New_York:20261115T230000\n"
            "DTEND;TZID=America/New_York:20261116T000000\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:zero-dur-recurring\n"
            "SUMMARY:Zero Recurring Daily\n"
            "DTSTART;TZID=America/New_York:20261115T000000\n"
            "RRULE:FREQ=DAILY;COUNT=3\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:pos-dur-recurring\n"
            "SUMMARY:Positive Recurring Ending at Start\n"
            "DTSTART;TZID=America/New_York:20261114T230000\n"
            "DTEND;TZID=America/New_York:20261115T000000\n"
            "RRULE:FREQ=DAILY;COUNT=3\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        tz = zoneinfo.ZoneInfo("America/New_York")
        events = parse_ical_vevents(ics_text)
        occs = extract_occurrences_in_window(
            events,
            window_start=datetime(2026, 11, 16, 0, 0, tzinfo=tz),
            window_end=datetime(2026, 11, 16, 23, 59, tzinfo=tz),
            target_tz=tz,
        )

        summaries = [o["summary"] for o in occs]
        # Zero-duration non-recurring event at window_start included
        self.assertIn("Zero Non-Recurring at Start", summaries)
        # Positive-duration non-recurring event ending at window_start excluded
        self.assertNotIn("Positive Non-Recurring Ending at Start", summaries)

        # Zero-duration recurring: 11/15 excluded, 11/16 at window_start included
        zero_recurring = [o for o in occs if o["summary"] == "Zero Recurring Daily"]
        self.assertEqual(len(zero_recurring), 1)
        self.assertEqual(zero_recurring[0]["start"], datetime(2026, 11, 16, 0, 0, tzinfo=tz))

        # Positive-duration recurring:
        # 11/14 occurrence ends 11/15 00:00 (excluded)
        # 11/15 occurrence ends 11/16 00:00 (ended at window_start, exclusive end -> excluded)
        # 11/16 occurrence ends 11/17 00:00 (in window -> included)
        pos_recurring = [o for o in occs if o["summary"] == "Positive Recurring Ending at Start"]
        self.assertEqual(len(pos_recurring), 1)
        self.assertEqual(pos_recurring[0]["start"], datetime(2026, 11, 16, 23, 0, tzinfo=tz))

    def test_render_schedule_nonzero_duration_matching_slugs(self):
        tz = zoneinfo.ZoneInfo("America/New_York")
        # Nonzero-duration event where start and end have the same formatted time slug (5p)
        # e.g., 24-hour event from Nov 16 17:00 to Nov 17 17:00
        occs = [
            {
                "cal_name": "Test",
                "summary": "24h Hackathon",
                "start": datetime(2026, 11, 16, 17, 0, tzinfo=tz),
                "end": datetime(2026, 11, 17, 17, 0, tzinfo=tz),
                "is_all_day": False,
                "multi_day": False,
            },
            {
                "cal_name": "Test",
                "summary": "Zero Alarm",
                "start": datetime(2026, 11, 16, 17, 0, tzinfo=tz),
                "end": datetime(2026, 11, 16, 17, 0, tzinfo=tz),
                "is_all_day": False,
                "multi_day": False,
            },
        ]
        notable, daily = render_schedule_markdown(
            occs,
            start_date=date(2026, 11, 16),
            end_date=date(2026, 11, 17),
        )
        daily_text = "\n".join(daily)
        # Nonzero-duration event must preserve the range even when slugs match
        self.assertIn("5p-5p 24h Hackathon", daily_text)
        # True zero-duration event must suppress duplicate end slug
        self.assertIn("5p Zero Alarm", daily_text)
        self.assertNotIn("5p-5p Zero Alarm", daily_text)


if __name__ == "__main__":
    unittest.main()
