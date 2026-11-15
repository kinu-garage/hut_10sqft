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
import urllib.request
import zoneinfo
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil import rrule


def fetch_ical_content(url_or_path: str, timeout: float = 10.0) -> str:
    """Fetch iCal content from HTTP(S) URL or local file path."""
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        req = urllib.request.Request(
            url_or_path, headers={"User-Agent": "Hut10sqftCalendarSync/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    with open(url_or_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_ical_vevents(ics_text: str, cal_name: str = "") -> List[Dict[str, Any]]:
    """Parse RFC 5545 iCalendar text into a list of VEVENT dictionaries.

    Handles line unfolding and multi-value fields (EXDATE).
    """
    lines: List[str] = []
    for raw_line in ics_text.splitlines():
        if raw_line.startswith(" ") or raw_line.startswith("\t"):
            if lines:
                lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)

    events: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None
    depth = 0

    for line in lines:
        upper_line = line.upper()
        if upper_line == "BEGIN:VEVENT":
            cur = {"cal_name": cal_name, "_exdates": []}
            depth = 1
        elif upper_line.startswith("BEGIN:") and cur is not None:
            depth += 1
        elif upper_line.startswith("END:") and cur is not None:
            depth -= 1
            if depth <= 0:
                events.append(cur)
                cur = None
                depth = 0
        elif cur is not None and depth == 1 and ":" in line:
            k, v = line.split(":", 1)
            k_upper = k.upper()
            k_clean = k_upper.split(";")[0]
            if k_clean == "EXDATE":
                cur["_exdates"].append((k, v))
            else:
                cur[k_upper] = v
                if k_clean not in cur:
                    cur[k_clean] = v
            if ";" in k:
                cur[k_clean + "_PARAMS"] = k.split(";")[1:]
    return events


def parse_datetime_val(
    dt_str: str,
    tz_id: Optional[str] = None,
    target_tz: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("America/New_York"),
) -> Union[datetime, date]:
    """Parse date-time or date string from iCalendar into target timezone."""
    dt_str = dt_str.strip()
    if "T" in dt_str:
        if dt_str.endswith("Z"):
            naive = datetime.strptime(dt_str[:-1], "%Y%m%dT%H%M%S")
            return naive.replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone(target_tz)
        naive = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
        if tz_id:
            return naive.replace(tzinfo=zoneinfo.ZoneInfo(tz_id)).astimezone(target_tz)
        return naive.replace(tzinfo=target_tz)
    return datetime.strptime(dt_str, "%Y%m%d").date()


def parse_duration_val(dur_str: str) -> Optional[timedelta]:
    """Parse RFC 5545 DURATION string into timedelta."""
    pattern = r"^([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
    m = re.match(pattern, dur_str.strip())
    if not m:
        return None
    sign = -1 if m.group(1) == "-" else 1
    weeks = int(m.group(2) or 0)
    days = int(m.group(3) or 0)
    hours = int(m.group(4) or 0)
    minutes = int(m.group(5) or 0)
    seconds = int(m.group(6) or 0)
    return timedelta(
        days=weeks * 7 + days, hours=hours, minutes=minutes, seconds=seconds
    ) * sign


def format_time_slug(dt: datetime) -> str:
    """Format datetime into standard schedule format: e.g. 545p or 6p."""
    minute = dt.strftime("%M")
    hour = dt.strftime("%-I")
    ampm = dt.strftime("%p").lower()[0]
    if minute == "00":
        return f"{hour}{ampm}"
    return f"{hour}{minute}{ampm}"


def extract_occurrences_in_window(
    events: List[Dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
    target_tz: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("America/New_York"),
) -> List[Dict[str, Any]]:
    """Expand and window VEVENTs.

    Correctly overrides base RRULE occurrences when a RECURRENCE-ID exception exists.
    """
    occurrences: List[Dict[str, Any]] = []

    # Map overrides by UID and recurrence-id (datetime or date) to suppress duplicates
    recurrence_overrides: Dict[str, Dict[Union[datetime, date], Dict[str, Any]]] = {}
    for ev in events:
        if "RECURRENCE-ID" in ev:
            uid = ev.get("UID", "")
            rec_id_raw = ev["RECURRENCE-ID"]
            rec_tz = None
            for p in ev.get("RECURRENCE-ID_PARAMS", []):
                if p.upper().startswith("TZID="):
                    rec_tz = p.split("=", 1)[1]
            rec_val = parse_datetime_val(rec_id_raw, rec_tz, target_tz)
            if uid not in recurrence_overrides:
                recurrence_overrides[uid] = {}
            recurrence_overrides[uid][rec_val] = ev

    for ev in events:
        if ev.get("STATUS", "").upper() == "CANCELLED":
            continue
        summary = (
            ev.get("SUMMARY", "").replace("\\,", ",").replace("\\;", ";").strip()
        )
        uid = ev.get("UID", "")
        dtstart_raw = None
        tz_id = None
        for k in ev:
            if k.startswith("DTSTART"):
                dtstart_raw = ev[k]
                for p in ev.get("DTSTART_PARAMS", []):
                    if p.upper().startswith("TZID="):
                        tz_id = p.split("=", 1)[1]
                break
        if not dtstart_raw:
            continue

        dtend_raw = None
        end_tz_id = None
        for k in ev:
            if k.startswith("DTEND"):
                dtend_raw = ev[k]
                for p in ev.get("DTEND_PARAMS", []):
                    if p.upper().startswith("TZID="):
                        end_tz_id = p.split("=", 1)[1]
                break

        duration = None
        is_nominal_day = False
        if "DURATION" in ev:
            duration = parse_duration_val(ev["DURATION"])
            dur_str = ev["DURATION"].strip()
            is_nominal_day = bool(re.match(r"^[+-]?P(?:(\d+)W)?(?:(\d+)D)?$", dur_str))

        is_all_day = "T" not in dtstart_raw
        start_val = parse_datetime_val(dtstart_raw, tz_id, target_tz)
        if is_all_day:
            start_dt = datetime.combine(start_val, time(0, 0), tzinfo=target_tz)
            if dtend_raw:
                end_val = parse_datetime_val(dtend_raw, end_tz_id or tz_id, target_tz)
                duration = timedelta(days=(end_val - start_val).days)
            elif duration is None:
                duration = timedelta(days=1)
        else:
            start_dt = start_val
            if dtend_raw:
                end_dt = parse_datetime_val(dtend_raw, end_tz_id or tz_id, target_tz)
                duration = end_dt - start_dt
            elif duration is None:
                duration = timedelta(0)

        rrule_str = ev.get("RRULE")
        exdates = set()
        for k, v in ev.get("_exdates", []):
            ex_tz = tz_id
            for p in k.split(";")[1:]:
                if p.upper().startswith("TZID="):
                    ex_tz = p.split("=", 1)[1]
            for ex in v.split(","):
                ex_val = parse_datetime_val(ex, ex_tz, target_tz)
                exdates.add(ex_val)

        if rrule_str:
            clean_rrule = rrule_str
            m = re.search(r"UNTIL=([0-9TZ]+)", rrule_str)
            if m:
                until_val = m.group(1)
                if is_all_day and until_val.endswith("Z"):
                    clean_rrule = rrule_str.replace(f"UNTIL={until_val}", f"UNTIL={until_val[:-1]}")
                elif not is_all_day and "T" not in until_val:
                    clean_rrule = rrule_str.replace(f"UNTIL={until_val}", f"UNTIL={until_val}T235959Z")

            if is_all_day:
                rule_dtstart = datetime.combine(start_val, time(0, 0))
                w_start_rule = datetime.combine((window_start - duration).date(), time(0, 0))
                w_end_rule = datetime.combine(window_end.date(), time(23, 59, 59))
            else:
                dt_clean = dtstart_raw.strip()
                utc_tz = zoneinfo.ZoneInfo("UTC")
                if dt_clean.endswith("Z"):
                    src_naive = datetime.strptime(dt_clean[:-1], "%Y%m%dT%H%M%S")
                    rule_dtstart = src_naive.replace(tzinfo=utc_tz)
                    w_start_rule = (window_start.astimezone(utc_tz) - duration).astimezone(rule_dtstart.tzinfo)
                    w_end_rule = window_end.astimezone(rule_dtstart.tzinfo)
                elif tz_id:
                    src_naive = datetime.strptime(dt_clean, "%Y%m%dT%H%M%S")
                    rule_dtstart = src_naive.replace(tzinfo=zoneinfo.ZoneInfo(tz_id))
                    if is_nominal_day:
                        w_start_local = window_start.astimezone(rule_dtstart.tzinfo)
                        w_start_rule = (w_start_local.replace(tzinfo=None) - duration).replace(
                            tzinfo=rule_dtstart.tzinfo, fold=0
                        )
                    else:
                        w_start_rule = (window_start.astimezone(utc_tz) - duration).astimezone(
                            rule_dtstart.tzinfo
                        )
                    w_end_rule = window_end.astimezone(rule_dtstart.tzinfo)
                else:
                    src_naive = datetime.strptime(dt_clean, "%Y%m%dT%H%M%S")
                    rule_dtstart = src_naive
                    if is_nominal_day:
                        w_start_local = window_start.astimezone(target_tz)
                        w_start_rule = w_start_local.replace(tzinfo=None) - duration
                    else:
                        w_start_rule = (
                            (window_start.astimezone(utc_tz) - duration)
                            .astimezone(target_tz)
                            .replace(tzinfo=None)
                        )
                    w_end_rule = window_end.astimezone(target_tz).replace(tzinfo=None)

            rule = rrule.rrulestr(clean_rrule, dtstart=rule_dtstart)
            for occ in rule.between(w_start_rule, w_end_rule, inc=True):
                if is_all_day:
                    occ_tz = datetime.combine(occ.date(), time(0, 0), tzinfo=target_tz)
                    occ_end = occ_tz + duration
                elif occ.tzinfo is None:
                    occ_tz = occ.replace(tzinfo=target_tz)
                    occ_end = occ_tz + duration
                else:
                    occ_tz = occ.astimezone(target_tz)
                    if is_nominal_day:
                        occ_end_src = occ.replace(tzinfo=None) + duration
                        occ_end = occ_end_src.replace(tzinfo=occ.tzinfo).astimezone(target_tz)
                    else:
                        # Preserve exact elapsed duration in UTC across timezone transitions
                        occ_end = (occ_tz.astimezone(zoneinfo.ZoneInfo("UTC")) + duration).astimezone(target_tz)
                utc_tz = zoneinfo.ZoneInfo("UTC")
                if duration == timedelta(0):
                    if occ_end.astimezone(utc_tz) < window_start.astimezone(utc_tz):
                        continue
                else:
                    if occ_end.astimezone(utc_tz) <= window_start.astimezone(utc_tz):
                        continue
                occ_date = occ_tz.date()
                if occ_tz in exdates or occ_date in exdates:
                    continue
                # Check if this occurrence is overridden by RECURRENCE-ID
                rec_key = occ_date if is_all_day else occ_tz
                if (
                    uid in recurrence_overrides
                    and (rec_key in recurrence_overrides[uid] or occ_date in recurrence_overrides[uid])
                ):
                    continue
                occurrences.append(
                    {
                        "cal_name": ev.get("cal_name", ""),
                        "summary": summary,
                        "start": occ_tz,
                        "end": occ_end,
                        "is_all_day": is_all_day,
                        "multi_day": duration > timedelta(days=1),
                        "description": ev.get("DESCRIPTION", ""),
                    }
                )
        else:
            utc_tz = zoneinfo.ZoneInfo("UTC")
            occ_end_utc = (start_dt + duration).astimezone(utc_tz)
            window_start_utc = window_start.astimezone(utc_tz)
            window_end_utc = window_end.astimezone(utc_tz)
            overlaps_start = (
                occ_end_utc >= window_start_utc
                if duration == timedelta(0)
                else occ_end_utc > window_start_utc
            )
            if overlaps_start and start_dt.astimezone(utc_tz) <= window_end_utc:
                if start_dt not in exdates and start_dt.date() not in exdates:
                    occurrences.append(
                        {
                            "cal_name": ev.get("cal_name", ""),
                            "summary": summary,
                            "start": start_dt,
                            "end": start_dt + duration,
                            "is_all_day": is_all_day,
                            "multi_day": duration > timedelta(days=1),
                            "description": ev.get("DESCRIPTION", ""),
                        }
                    )

    occurrences.sort(key=lambda x: (x["start"], x["summary"]))
    return occurrences


def render_schedule_markdown(
    occurrences: List[Dict[str, Any]],
    start_date: date,
    end_date: date,
    cal_prefix_map: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], List[str]]:
    """Render occurrences into (notable_period_lines, daily_lines).

    - notable_period_lines: strictly multi-day events.
    - daily_lines: single-day and timed events grouped by date.
    """
    prefix_map = cal_prefix_map or {}
    notable_lines: List[str] = []
    by_day: Dict[date, List[Dict[str, Any]]] = {}

    cur_d = start_date
    while cur_d <= end_date:
        by_day[cur_d] = []
        cur_d += timedelta(days=1)

    for occ in occurrences:
        if occ.get("multi_day"):
            s_str = occ["start"].strftime("%-m/%-d %a")
            # For all-day events, end is non-inclusive midnight; display last occupied date
            if occ.get("is_all_day"):
                last_occupied = occ["end"] - timedelta(days=1)
                e_str = last_occupied.strftime("%-m/%-d %a")
            else:
                e_str = occ["end"].strftime("%-m/%-d %a")
            prefix = prefix_map.get(occ["cal_name"], "")
            title = f"{prefix}{occ['summary']}".strip()
            notable_lines.append(f"- {s_str} – {e_str} {title}")
            continue

        d = occ["start"].date()
        if d < start_date and occ.get("end") and occ["end"].date() >= start_date:
            d = start_date
        if d in by_day:
            by_day[d].append(occ)

    daily_lines: List[str] = []
    for d in sorted(by_day.keys()):
        header = d.strftime("%-m/%-d %a")
        day_items = by_day[d]
        daily_lines.append(f"- {header}")
        if not day_items:
            continue
        for ev in day_items:
            prefix = prefix_map.get(ev["cal_name"], "")
            title = f"{prefix}{ev['summary']}".strip()
            if ev.get("is_all_day"):
                daily_lines.append(f"   - [ ] {title}")
            else:
                s_t = format_time_slug(ev["start"])
                e_t = format_time_slug(ev["end"])
                utc_tz = zoneinfo.ZoneInfo("UTC")
                is_instant = (
                    ev.get("start")
                    and ev.get("end")
                    and ev["start"].astimezone(utc_tz) == ev["end"].astimezone(utc_tz)
                )
                if is_instant:
                    daily_lines.append(f"   - [ ] {s_t} {title}")
                else:
                    daily_lines.append(f"   - [ ] {s_t}-{e_t} {title}")

    return notable_lines, daily_lines
