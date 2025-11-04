from datetime import date, datetime, time, timedelta

import holidays


def get_day_times(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min)  # 00:00:00
    end = datetime.combine(day, time.max)  # 23:59:59.999999
    return start, end


def get_week_times(day: date) -> tuple[datetime, datetime]:
    # Calculate days to subtract to get to Monday
    days_since_monday = day.weekday()
    week_start_date = day - timedelta(days=days_since_monday)

    # Calculate days to add to get to Sunday
    days_until_sunday = 6 - day.weekday()
    week_end_date = day + timedelta(days=days_until_sunday)

    start = datetime.combine(week_start_date, time.min)  # Monday 00:00:00
    end = datetime.combine(week_end_date, time.max)  # Sunday 23:59:59.999999

    return start, end


def get_age(birth_date, today):
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def is_workday(day: date) -> bool:
    return day.weekday() != 6


def is_in_work_hours(timepoint: time) -> bool:
    return timepoint >= time(6) and timepoint <= time(22)


def is_in_work_hours_underage(timepoint: time):
    return timepoint >= time(6) and timepoint <= time(20)


def get_holiday(
    day: date, *, country: str, subdiv: str | None, language: str | None
) -> None | str:
    h = holidays.country_holidays(country=country, subdiv=subdiv, language=language)
    return h.get(day)


def quantizise_minute(date_time: datetime) -> datetime:
    return date_time.replace(second=0, microsecond=0)
