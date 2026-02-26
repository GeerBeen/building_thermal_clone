import pytest
from streamlit.testing.v1 import AppTest


def test_sidebar_layout(app_path):
    """
    Перевіряє статичні елементи сайдбару
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    # Перевіряємо заголовок
    assert len(at.sidebar.title) > 0
    assert "Цифровий двійник" in at.sidebar.title[0].value

    # Перевіряємо наявність меню
    assert at.sidebar.radio("navigation_radio") is not None


@pytest.mark.parametrize("page_name, expected_text", [
    ("Планування", "Створення основи будинку"),
    ("Матеріали", "Бібліотека матеріалів"),
    ("Вікна та двері", "Каталог вікон"),
    ("Симуляція", "Симуляція та Економіка"),
    ("Довідка", "Довідка користувача")
])
def test_navigation_pages(app_path, page_name, expected_text):
    """
    Перевіряє перехід на конкретну сторінку.
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    # Перемикаємо радіо
    at.sidebar.radio("navigation_radio").set_value(page_name).run()

    # Перевіряємо чи стан оновився
    assert at.session_state.navigation_radio == page_name

    # Перевіряємо чи  на сторінці з'явився унікальний контент
    all_text = []
    for elem in at.markdown: all_text.append(elem.value)
    for elem in at.header: all_text.append(elem.value)
    for elem in at.subheader: all_text.append(elem.value)

    # Перетворюємо все в один великий рядок для пошуку
    full_text = " ".join(all_text)

    assert expected_text in full_text, f"Текст '{expected_text}' не знайдено на сторінці '{page_name}'"
