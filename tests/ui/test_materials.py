from streamlit.testing.v1 import AppTest


def test_materials_page_filter(app_path):
    at = AppTest.from_file(app_path)
    at.run()

    at.sidebar.radio("navigation_radio").set_value("Матеріали").run()

    assert len(at.dataframe) > 0
    initial_count = len(at.dataframe[0].value)
    assert initial_count > 0
    assert not at.exception
