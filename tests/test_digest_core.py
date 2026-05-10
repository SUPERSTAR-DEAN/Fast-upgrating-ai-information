import unittest
from datetime import datetime, timezone

from src.models import NewsItem
from src.processors import deduplicate_items, filter_items_by_date, weekly_window
from src.render import build_subject
from src.utils import normalize_url


class DigestCoreTests(unittest.TestCase):
    def test_normalize_url_removes_tracking_query_and_fragment(self):
        url = "https://example.com/a/b/?utm_source=x&id=2#section"
        normalized = normalize_url(url)
        self.assertEqual(normalized, "https://example.com/a/b?id=2")

    def test_deduplicate_items_removes_duplicate_signature(self):
        now = datetime.now(timezone.utc)
        item1 = NewsItem("Title", "https://example.com/path/?utm_source=x", "s1", "c1", now, "d")
        item2 = NewsItem("Title", "https://example.com/path", "s1", "c1", now, "d")
        deduped = deduplicate_items([item1, item2])
        self.assertEqual(len(deduped), 1)

    def test_filter_and_subject_window(self):
        start, end = weekly_window(datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(start.strftime("%Y-%m-%d"), "2026-05-04")
        self.assertEqual(end.strftime("%Y-%m-%d"), "2026-05-10")

        inside = NewsItem("In", "https://a.com", "s", "c", datetime(2026, 5, 9, tzinfo=timezone.utc), "")
        outside = NewsItem("Out", "https://b.com", "s", "c", datetime(2026, 5, 1, tzinfo=timezone.utc), "")
        filtered = filter_items_by_date([inside, outside], start, end)
        self.assertEqual([i.title for i in filtered], ["In"])

        subject = build_subject(start, end)
        self.assertEqual(subject, "AI Weekly Digest (2026-05-04 ~ 2026-05-10)")


if __name__ == "__main__":
    unittest.main()
