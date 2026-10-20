import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from estadisticas import rated_mean, sort_books
from sincronizar_locales import sync


class LocaleTests(unittest.TestCase):
    def test_sync_preserves_data_and_translations_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = {
                "es.json": {"title": "Título", "new": "Nuevo", "months": ["Enero"]},
                "en.json": {"title": "Existing translation", "obsolete": "Keep me"},
                "author_genders.json": {"Author": "H"},
                "author_countries.json": {"Author": "Argentina"},
                "unknown.json": {"custom": "Untouched"},
            }
            for name, data in fixtures.items():
                (root / name).write_text(json.dumps(data), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            with contextlib.redirect_stdout(io.StringIO()):
                sync(directory)
            for name in fixtures.keys() - {"en.json"}:
                self.assertEqual(before[name], (root / name).read_bytes())
            target = json.loads((root / "en.json").read_text(encoding="utf-8"))
            self.assertEqual(target, {
                "title": "Existing translation", "new": "[TRADUCIR]: Nuevo",
                "months": ["[TRADUCIR]: Enero"], "obsolete": "Keep me",
            })
            after = {p.name: p.read_bytes() for p in root.iterdir()}
            with contextlib.redirect_stdout(io.StringIO()):
                sync(directory)
            self.assertEqual(after, {p.name: p.read_bytes() for p in root.iterdir()})


class StatisticsTests(unittest.TestCase):
    def test_unrated_books_do_not_lower_average_or_reduce_totals(self):
        books = pd.DataFrame({"author": ["A"] * 3, "rating": [5, 4, 0], "pages": [100, 200, 300]})
        result = books.groupby("author").agg(rating=("rating", rated_mean), books=("rating", "size"), pages=("pages", "sum"))
        self.assertEqual(result.loc["A"].to_dict(), {"rating": 4.5, "books": 3, "pages": 600})

    def test_no_rating_has_no_numeric_average(self):
        for ratings in ([0, 0], [None, 0], []):
            self.assertTrue(pd.isna(rated_mean(pd.Series(ratings, dtype=float))))

    def test_longest_and_recent_have_independent_order(self):
        books = pd.DataFrame({"pages": [700, 1200, 900], "date_read": pd.to_datetime(["2026-03-01", "2026-01-01", "2026-02-01"])})
        self.assertEqual(sort_books(books, "pages")["pages"].tolist(), [1200, 900, 700])
        self.assertEqual(sort_books(books)["pages"].tolist(), [700, 900, 1200])
        self.assertEqual(sort_books(books, "pages", True)["pages"].tolist(), [700, 900, 1200])


if __name__ == "__main__":
    unittest.main()
