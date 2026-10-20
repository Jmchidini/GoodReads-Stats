"""Prueba de integración con CSV sintético, sin red ni datos personales."""
import unittest
from streamlit.testing.v1 import AppTest


APP = '''
import io
import runpy
from unittest.mock import patch
csv = """Title,Author,My Rating,Number of Pages,Year Published,Original Publication Year,Date Read,Date Added,Bookshelves,Exclusive Shelf
First,Author A,5,700,2000,1999,2025/03/01,2024/01/01,fantasy,read
Second,Author A,4,1200,2001,2000,2024/01/01,2023/01/01,fantasy,read
Third,Author A,0,900,2002,2001,2025/02/01,2024/01/01,manga,read
Fourth,Author B,0,100,2003,2002,2024/02/01,2023/01/01,fiction,read
Unread,Author C,0,200,2004,2003,,2023/01/01,fiction,to-read
"""
with patch("streamlit.file_uploader", return_value=io.StringIO(csv)):
    runpy.run_path("goodreads_explorer.py", run_name="__main__")
'''


class AppTests(unittest.TestCase):
    def test_upload_languages_filters_and_tables(self):
        app = AppTest.from_string(APP, default_timeout=30).run()
        self.assertEqual(list(app.exception), [])
        # Author summary excludes zero ratings but retains all three books.
        tables = [item.value for item in app.dataframe]
        summary = tables[1]
        self.assertIn("4.50", summary.astype(str).values)
        self.assertIn("Sin puntuación", summary.astype(str).values)
        self.assertEqual(tables[-3]["pages"].tolist(), [1200, 900, 700, 100])
        app.selectbox(key="lang_selector").set_value("English").run()
        self.assertEqual(list(app.exception), [])
        app.checkbox[0].check().run()
        self.assertEqual(list(app.exception), [])
        app.multiselect[1].set_value([5]).run()
        self.assertEqual(list(app.exception), [])


if __name__ == "__main__":
    unittest.main()
