import sys
import time
from datetime import datetime, timedelta

from .calendar_utils import (add_events_from_activity_list,
                             create_and_initialize_calendar,
                             get_start_and_end_dates)
from .web_scraping_utils import (exit_on_authentication_failure,
                                 get_session_token, get_soup,
                                 save_session_token_if_user_agrees)

REQUEST_INTERVAL_SEC = 1


def export_calendar() -> None:
    session_token, session_token_is_obtained_from_input = get_session_token()
    cookie = {"mytimetable_session": session_token}
    if session_token_is_obtained_from_input:
        save_session_token_if_user_agrees(session_token)

    # Exit on auth failure for some reasons (e.g. expired or invalid session token)
    soup = get_soup(cookie)
    exit_on_authentication_failure(soup)

    cal = create_and_initialize_calendar()

    start_date, end_date = get_start_and_end_dates()

    filename = input(
        "Please enter a filename for your calendar file (default: 'mycalendar'): "
    )
    if not filename:
        filename = "mytimetable"

    processing_date = start_date

    while processing_date < (end_date + timedelta(weeks=1)):
        # Print the range of currently processing week
        week_start_date = processing_date - timedelta(days=processing_date.weekday())
        week_end_date = processing_date + timedelta(
            days=(6 - processing_date.weekday())
        )

        if week_start_date < start_date:
            week_start_date = start_date
        if end_date < week_end_date:
            week_end_date = end_date

        sys.stdout.write(
            f"\rProcessing {week_start_date.strftime('%a %d %b %Y')} to {week_end_date.strftime('%a %d %b %Y')}..."
        )
        sys.stdout.flush()

        soup = get_soup(cookie, processing_date)
        day_divs = soup.find_all("div", {"class": "activity-list-group-title"})

        for day_div in day_divs:
            monday_date = day_div["id"][:10]
            day = day_div["id"][11:]
            day_int = time.strptime(day, "%A").tm_wday
            date = datetime.strptime(monday_date, "%d-%m-%Y") + timedelta(days=day_int)

            if not start_date <= date <= end_date:
                continue

            activity_list = day_div.find_next_sibling()
            add_events_from_activity_list(date, cal, activity_list)

        time.sleep(REQUEST_INTERVAL_SEC)
        processing_date += timedelta(weeks=1)

    print("\r")

    # Export the calendar in iCalendar format
    with open(f"{filename}.ics", "wb") as f:
        f.write(cal.to_ical())
    print(f"Calendar exported to '{filename}.ics' successfully.")
