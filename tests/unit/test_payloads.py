from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

from calisero._internal import schedule
from calisero._internal.schedule import format_schedule_at, romania_time_by_rule
from calisero._payloads import (
    create_message_payload,
    create_verification_payload,
    opt_out_payload,
    verification_check_payload,
)
from tests.support.fixtures import PHONE

UTC = timezone.utc


def utc(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0
) -> datetime:
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=UTC)


class TestCreateMessagePayload:
    def test_sends_the_recipient_and_the_body_of_a_minimal_request(self) -> None:
        assert create_message_payload(recipient=PHONE, body="Hello!") == {"recipient": PHONE, "body": "Hello!"}

    def test_sends_every_option_under_its_api_name_in_the_documented_order(self) -> None:
        payload = create_message_payload(
            recipient=PHONE,
            body="Your code is 123456",
            visible_body="Your code is ******",
            validity=24,
            schedule_at="2026-12-25 10:00:00",
            callback_url="https://yourapp.com/webhooks/calisero",
            sender="Calisero",
            shorten_urls=True,
        )

        assert payload == {
            "recipient": PHONE,
            "body": "Your code is 123456",
            "visible_body": "Your code is ******",
            "validity": 24,
            "schedule_at": "2026-12-25 10:00:00",
            "callback_url": "https://yourapp.com/webhooks/calisero",
            "sender": "Calisero",
            "shorten_urls": True,
        }
        assert list(payload) == [
            "recipient",
            "body",
            "visible_body",
            "validity",
            "schedule_at",
            "callback_url",
            "sender",
            "shorten_urls",
        ]

    def test_leaves_out_the_options_that_are_none(self) -> None:
        payload = create_message_payload(
            recipient=PHONE,
            body="Hello!",
            visible_body=None,
            validity=None,
            schedule_at=None,
            callback_url=None,
            sender=None,
            shorten_urls=None,
        )

        assert payload == {"recipient": PHONE, "body": "Hello!"}

    def test_keeps_the_options_set_to_false_or_0(self) -> None:
        payload = create_message_payload(recipient=PHONE, body="Hello!", shorten_urls=False, validity=0)

        assert payload == {"recipient": PHONE, "body": "Hello!", "validity": 0, "shorten_urls": False}

    def test_sends_a_datetime_to_schedule_at_in_romania_time(self) -> None:
        payload = create_message_payload(recipient=PHONE, body="Hello!", schedule_at=utc(2026, 7, 15, 9, 30))

        assert payload["schedule_at"] == "2026-07-15 12:30:00"


class TestFormatScheduleAt:
    def test_converts_a_date_in_summer_time(self) -> None:
        assert format_schedule_at(utc(2026, 7, 15, 9, 30)) == "2026-07-15 12:30:00"

    def test_converts_a_date_in_winter_time(self) -> None:
        assert format_schedule_at(utc(2026, 1, 15, 9, 30, 5)) == "2026-01-15 11:30:05"

    def test_writes_midnight_as_00_on_the_next_day_in_romania(self) -> None:
        assert format_schedule_at(utc(2026, 3, 1, 22)) == "2026-03-02 00:00:00"

    def test_follows_the_switch_to_summer_time(self) -> None:
        # On 2026-03-29 the clocks go from 03:00 to 04:00 in Romania
        assert format_schedule_at(utc(2026, 3, 29, 0, 59, 59)) == "2026-03-29 02:59:59"
        assert format_schedule_at(utc(2026, 3, 29, 1)) == "2026-03-29 04:00:00"

    def test_follows_the_switch_to_winter_time(self) -> None:
        # On 2026-10-25 the clocks go from 04:00 back to 03:00 in Romania
        assert format_schedule_at(utc(2026, 10, 25, 0, 59, 59)) == "2026-10-25 03:59:59"
        assert format_schedule_at(utc(2026, 10, 25, 1)) == "2026-10-25 03:00:00"

    def test_converts_a_datetime_of_any_time_zone(self) -> None:
        tokyo = datetime(2026, 7, 15, 18, 30, tzinfo=ZoneInfo("Asia/Tokyo"))
        offset = datetime(2026, 1, 15, 9, 30, tzinfo=timezone(timedelta(hours=-5)))

        assert format_schedule_at(tokyo) == "2026-07-15 12:30:00"
        assert format_schedule_at(offset) == "2026-01-15 16:30:00"

    def test_drops_the_microseconds(self) -> None:
        assert format_schedule_at(utc(2026, 7, 15, 9, 30, 0, 999999)) == "2026-07-15 12:30:00"

    def test_passes_a_string_as_is(self) -> None:
        assert format_schedule_at("2026-12-25 10:00:00") == "2026-12-25 10:00:00"

    def test_refuses_a_naive_datetime_whose_time_zone_cannot_be_known(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware datetime"):
            format_schedule_at(datetime(2026, 7, 15, 9, 30))

    @pytest.mark.parametrize("value", [1_790_000_000, date(2026, 7, 15), None])
    def test_refuses_what_is_neither_a_datetime_nor_a_string(self, value: object) -> None:
        with pytest.raises(TypeError, match="timezone-aware datetime"):
            format_schedule_at(value)  # type: ignore[arg-type]


class TestRomaniaTimeWithoutATimeZoneDatabase:
    def test_formats_the_same_by_the_european_rule(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(schedule, "_romania_zone", lambda: None)

        assert format_schedule_at(utc(2026, 7, 15, 9, 30)) == "2026-07-15 12:30:00"
        assert format_schedule_at(utc(2026, 1, 15, 9, 30, 5)) == "2026-01-15 11:30:05"
        assert format_schedule_at(utc(2026, 3, 29, 1)) == "2026-03-29 04:00:00"
        assert format_schedule_at(utc(2026, 10, 25, 1)) == "2026-10-25 03:00:00"

    def test_falls_back_to_the_rule_when_the_zone_is_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def missing(key: str) -> ZoneInfo:
            raise ZoneInfoNotFoundError(key)

        monkeypatch.setattr(schedule, "ZoneInfo", missing)

        assert schedule._romania_zone.__wrapped__() is None

    def test_the_rule_agrees_with_the_time_zone_database(self) -> None:
        bucharest = ZoneInfo("Europe/Bucharest")
        instants: list[datetime] = []

        for year in range(1997, 2041):
            instants += [utc(year, 1, 1), utc(year, 7, 1), utc(year, 12, 31, 23, 59, 59)]

            # Every half hour around the two switches of the year
            for month in (3, 10):
                last_day = utc(year, month, 31, 1)
                switch = last_day - timedelta(days=(last_day.weekday() + 1) % 7)
                instants += [switch + timedelta(minutes=30 * step) for step in range(-6, 7)]
                instants += [switch - timedelta(seconds=1)]

        for instant in instants:
            by_rule = romania_time_by_rule(instant)
            by_database = instant.astimezone(bucharest)

            assert (by_rule.replace(tzinfo=None), by_rule.utcoffset()) == (
                by_database.replace(tzinfo=None),
                by_database.utcoffset(),
            ), instant


class TestOptOutPayload:
    def test_sends_the_phone_and_the_reason(self) -> None:
        assert opt_out_payload(phone=PHONE, reason="Asked to stop") == {"phone": PHONE, "reason": "Asked to stop"}

    def test_leaves_out_a_missing_reason(self) -> None:
        assert opt_out_payload(phone=PHONE) == {"phone": PHONE}
        assert opt_out_payload(phone=PHONE, reason=None) == {"phone": PHONE}


class TestCreateVerificationPayload:
    def test_sends_the_phone_and_the_brand(self) -> None:
        assert create_verification_payload(phone=PHONE, brand="Calisero") == {"phone": PHONE, "brand": "Calisero"}

    def test_sends_a_template_and_the_expiry_under_their_api_names(self) -> None:
        payload = create_verification_payload(phone=PHONE, template="Your code: {code}", expires_in=10, brand=None)

        assert payload == {"phone": PHONE, "template": "Your code: {code}", "expires_in": 10}


class TestVerificationCheckPayload:
    def test_sends_the_phone_and_the_code(self) -> None:
        assert verification_check_payload(phone=PHONE, code="ABC123") == {"phone": PHONE, "code": "ABC123"}
