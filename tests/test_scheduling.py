from datetime import datetime, time, timedelta
from unittest.mock import patch

import main
from main import PaintedDesktop, is_change_due, retry_delay

EIGHT = time(8, 0)


def test_due_when_never_set():
    assert is_change_due(None, datetime(2026, 10, 3, 7, 0), EIGHT)


def test_not_due_before_change_time_if_set_after_yesterdays():
    assert not is_change_due(datetime(2026, 10, 2, 8, 0, 5), datetime(2026, 10, 3, 7, 59), EIGHT)


def test_due_at_change_time():
    assert is_change_due(datetime(2026, 10, 2, 8, 0, 5), datetime(2026, 10, 3, 8, 0), EIGHT)


def test_not_due_at_midnight():
    assert not is_change_due(datetime(2026, 10, 2, 9, 0), datetime(2026, 10, 3, 0, 0, 1), EIGHT)


def test_catches_up_after_pc_was_off_for_days():
    assert is_change_due(datetime(2026, 6, 23, 12, 0), datetime(2026, 10, 3, 21, 37), EIGHT)


def test_manual_change_after_change_time_counts_for_today():
    assert not is_change_due(datetime(2026, 10, 3, 9, 0), datetime(2026, 10, 3, 23, 0), EIGHT)


def test_retry_backs_off_to_fifteen_minutes():
    assert [retry_delay(n) for n in (1, 2, 3, 4, 5, 9)] == [timedelta(minutes=m) for m in (1, 2, 4, 8, 15, 15)]


class FakeFetcher:
    NAME = "Fake"
    paintings = []
    fail_downloads = False

    def __init__(self, screen, mode):
        pass

    def candidates(self, style):
        return iter(self.paintings)

    def fetch_image(self, painting, cache_dir):
        return None if self.fail_downloads else str(cache_dir / f"{painting['id']}.jpg")


def make_fetcher(ids, fail=False):
    paintings = [{"id": i, "title": f"T{i}", "artist": "A", "year": "", "institution": "Fake",
                  "source_url": ""} for i in ids]
    return type("F", (FakeFetcher,), {"paintings": paintings, "fail_downloads": fail})


def make_app(tmp_path, sources):
    with patch.dict("os.environ", {"APPDATA": str(tmp_path)}):
        app = PaintedDesktop()
    return app, patch.multiple(main, SOURCES=sources, set_wallpaper=lambda path, mode: True,
                               get_monitor_resolution=lambda: (2560, 1600))


def test_skips_used_paintings_and_falls_back_to_next_source(tmp_path):
    app, patches = make_app(tmp_path, (make_fetcher(["a"], fail=True), make_fetcher(["used", "b"])))
    app.history.add_entry("Old", "A", "", "Fake", "", "", "used", "")
    with patches:
        painting = app._find_and_set()
    assert painting["id"] == "b"
    assert app.history.get_last_entry()["painting_id"] == "b"


def test_failure_when_every_source_is_down(tmp_path):
    app, patches = make_app(tmp_path, (make_fetcher([]), make_fetcher(["x"], fail=True)))
    with patches:
        assert app.change_wallpaper() is False
    assert app.history.get_last_entry() is None
