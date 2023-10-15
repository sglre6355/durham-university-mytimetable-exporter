import getpass
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from .utils import get_bool_from_str_input, normalize_text

BASE_URL = "https://mytimetable.durham.ac.uk/weekly/activities"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"
}


def get_session_token() -> tuple[str, bool]:
    load_dotenv()
    session_token = os.getenv("MYTIMETABLE_SESSION")

    session_token_is_obtained_from_input = False

    if session_token:
        input_str = input(
            "Found your cookie token saved in .env file. Do you wish to use it? (y/n): "
        )

        should_use_saved_session_token = get_bool_from_str_input(input_str)

        if should_use_saved_session_token:
            return session_token, session_token_is_obtained_from_input

    session_token = getpass.getpass("Please input mytimetable_session cookie value: ")
    session_token_is_obtained_from_input = True

    return session_token, session_token_is_obtained_from_input


def save_session_token_if_user_agrees(session_token) -> None:
    input_str = input("Do you want to save your cookie in .env file? (y/n): ")

    should_save_session_token = get_bool_from_str_input(input_str)

    if should_save_session_token:
        with open("./.env", "w") as f:
            f.write(f"MYTIMETABLE_SESSION = {session_token}")


def exit_on_authentication_failure(soup: BeautifulSoup) -> None:
    title = soup.title.get_text()

    if title == "Sign in to your account":
        raise Exception("Authentication error: Please update the session cookie.")


def get_soup(cookie: dict, date: datetime | None = None) -> BeautifulSoup:
    if date:
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = ""

    response = requests.get(f"{BASE_URL}/{date_str}", headers=HEADERS, cookies=cookie)
    response.raise_for_status()

    return BeautifulSoup(response.content, "html.parser")


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
