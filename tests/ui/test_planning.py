import pytest
from streamlit.testing.v1 import AppTest


def test_planning_defaults(app_path):
    """
    Перевірка "За замовчуванням": Чи заповнена форма правильними стартовими даними?
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    at.sidebar.radio("navigation_radio").set_value("Планування").run()

    # Перевіряємо, що поля існують і мають правильні значення
    assert at.text_input("plan_room_name").value == "Вітальня"
    assert at.number_input("plan_room_width").value == 5.0
    assert at.number_input("plan_room_length").value == 4.0
    assert at.number_input("plan_room_height").value == 2.8

    # Перевіряємо, що кнопка має правильний напис
    assert "Створити фундамент" in at.button("plan_create_submit").label


def test_planning_create_success(app_path):
    """
     Вводимо дані -> Тиснемо -> Отримуємо успіх
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    # Вводимо свої дані
    at.text_input("plan_room_name").set_value("Test Bedroom").run()
    at.number_input("plan_room_width").set_value(6.0).run()

    # Натискаємо кнопку
    at.button("plan_create_submit").click().run()

    assert not at.exception

    assert len(at.success) > 0
    assert "успішно створено" in at.success[0].value

    building = at.session_state["building"]
    assert len(building.rooms) == 1
    assert list(building.rooms.values())[0].name == "Test Bedroom"


def test_planning_validation_logic(app_path):
    """
     Пробуємо ввести мінус -> Тиснемо -> Отримуємо помилку.
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    # Вводимо некоректну ширину
    at.number_input("plan_room_width").set_value(-5.0).run()

    # Натискаємо кнопку
    at.button("plan_create_submit").click().run()

    assert len(at.error) > 0

    assert "Розміри мають бути > 0" in at.error[0].value

    # Кімната не створилася
    assert len(at.session_state["building"].rooms) == 0
