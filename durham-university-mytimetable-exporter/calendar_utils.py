from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from icalendar import Calendar, Event
from icalendar.prop import vGeo

from .utils import normalize_text

if TYPE_CHECKING:
    from bs4.element import Tag


def create_and_initialize_calendar() -> Calendar:
    cal = Calendar()

    # Add some elements to be compliant with RFC 5545
    cal.add("prodid", "-//sglre6355//durham-university-mytimetable-exporter//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")

    return cal


def get_start_and_end_dates() -> tuple[datetime, datetime]:
    start_date_str = input("Please enter the start date (YYYY-MM-DD): ")
    end_date_str = input("Please enter the end date (YYYY-MM-DD): ")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    return start_date, end_date


def scrape_activity_properties(activity) -> tuple[str, str, str, str, str | None, str]:
    activity_type = normalize_text(
        activity.find("div", {"class": "activity-type-title"}).get_text()
    )

    activity_time = normalize_text(
        activity.find("div", {"class": "activity-time"}).get_text()
    )

    activity_content_labels = activity.find_all(
        "div", {"class": "activity-content-label"}
    )

    activity_title = normalize_text(
        activity_content_labels[0].find_next_sibling().get_text()
    )

    activity_location_div = activity_content_labels[1].find_next_sibling()
    activity_location_name = normalize_text(activity_location_div.get_text())
    if activity_location_div.a:
        activity_location_url = activity_location_div.a["href"]
    else:
        activity_location_url = None

    activity_staff = normalize_text(
        activity_content_labels[2].find_next_sibling().get_text()
    )

    return (
        activity_type,
        activity_time,
        activity_title,
        activity_location_name,
        activity_location_url,
        activity_staff,
    )


def convert_activity_time_to_datetime(
    activity_time: str, date: datetime
) -> tuple[datetime, datetime]:
    start_hour, start_min, end_hour, end_min = map(
        int, activity_time.replace(":", " ").replace("-", " ").split()
    )

    activity_start = date.replace(hour=start_hour, minute=start_min)
    activity_end = date.replace(hour=end_hour, minute=end_min)

    return activity_start, activity_end


def convert_activity_location_url_to_geo(activity_location_url) -> vGeo:
    geo_str_list = (
        parse_qs(urlparse(activity_location_url).query)["query"][0]
        .replace(",", " ")
        .split()
    )

    return vGeo(geo_str_list)


def create_event_and_set_properties(
    activity_type: str,
    activity_start: datetime,
    activity_end: datetime,
    activity_title: str,
    activity_location_name: str,
    activity_location_url: str | None,
    geo: vGeo | None,
    activity_staff: str,
):
    event = Event()

    # Add some elements to be compliant with RFC 5 i45
    event.add("dtstamp", datetime.now())
    event.add("uid", str(uuid.uuid4()))

    event.add("summary", f"{activity_title} ({activity_type})")

    event.add("dtstart", activity_start)
    event.add("dtend", activity_end)
    event.add("transp", "OPAQUE")

    event.add("location", activity_location_name)
    if geo:
        event.add("geo", geo)

    event.add(
        "description",
        f"With {activity_staff}\n\n<a href={activity_location_url}>View {activity_location_name} on Google Maps</a>",
    )

    return event


def add_events_from_activity_list(
    date: datetime, cal: Calendar, activity_list: Tag
) -> None:
    activities = activity_list.find_all("div", {"class": "activity"})

    for activity in activities:
        # Skip if there is no activity
        if activity.find("div", {"class": "activity-none"}):
            break

        (
            activity_type,
            activity_time,
            activity_title,
            activity_location_name,
            activity_location_url,
            activity_staff,
        ) = scrape_activity_properties(activity)

        activity_start, activity_end = convert_activity_time_to_datetime(
            activity_time, date
        )

        if activity_location_url:
            geo = convert_activity_location_url_to_geo(activity_location_url)
        else:
            geo = None

        event = create_event_and_set_properties(
            activity_type,
            activity_start,
            activity_end,
            activity_title,
            activity_location_name,
            activity_location_url,
            geo,
            activity_staff,
        )

        cal.add_component(event)
