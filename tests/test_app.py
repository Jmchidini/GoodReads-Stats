"""Prueba de integración con CSV sintético, sin red ni datos personales."""
import unittest
import json
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
    def test_decimal_ratings_labels_filter_and_chart_selection(self):
        source = APP.replace("Second,Author A,4,", "Second,Author A,4.25,").replace(
            "Third,Author A,0,", "Third,Author A,3.5,"
        )
        # Render real charts, then simulate the rating selection event returned
        # by Streamlit (AppTest does not provide a Plotly click control).
        source = source.replace('with patch("streamlit.file_uploader"', '''
import streamlit as st
from types import SimpleNamespace
original_chart = st.plotly_chart
def capture_chart(fig, *args, **kwargs):
    result = original_chart(fig, *args, **kwargs)
    if kwargs.get("key") == "chart_ratings":
        st.session_state["rating_chart_json"] = fig.to_json()
        if st.session_state.get("simulate_rating_click", False):
            return SimpleNamespace(selection={"points": [{"point_index": 1}]})
    return result
with patch("streamlit.plotly_chart", side_effect=capture_chart), patch("streamlit.file_uploader"''')
        app = AppTest.from_string(source, default_timeout=30).run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.dataframe[0].value["my_rating"].tolist(), [5, 3.5, 0, 4.25])
        self.assertIn("4.25", app.dataframe[1].value.astype(str).values)
        self.assertIn("4.25 ⭐", app.multiselect[1].options)
        self.assertIn("3.5 ⭐", app.multiselect[1].options)
        chart = json.loads(app.session_state["rating_chart_json"])
        self.assertEqual(chart["data"][0]["x"], ["3.5 ⭐", "4.25 ⭐", "5 ⭐"])
        self.assertEqual(app.dataframe[-2].value["title"].tolist(), ["First"])
        app.session_state["simulate_rating_click"] = True
        app.run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.dataframe[-4].value["title"].tolist(), ["Second"])
        app.session_state["simulate_rating_click"] = False
        app.selectbox(key="lang_selector").set_value("English").run()
        app.multiselect[1].set_value([4.25]).run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.dataframe[0].value["title"].tolist(), ["Second"])
        app.checkbox(key="show_all_ratings").check().run()
        self.assertEqual(list(app.exception), [])
        chart = json.loads(app.session_state["rating_chart_json"])
        self.assertEqual(chart["data"][0]["x"], [f"{step / 4:g} ⭐" for step in range(1, 21)])
        self.assertEqual(chart["layout"]["xaxis"]["tickmode"], "array")
        app.checkbox(key="show_all_ratings").uncheck().run()
        self.assertEqual(list(app.exception), [])
        chart = json.loads(app.session_state["rating_chart_json"])
        self.assertEqual(chart["data"][0]["x"], ["4.25 ⭐"])

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
