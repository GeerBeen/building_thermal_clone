import pytest
from streamlit.testing.v1 import AppTest
from building import Building
from bulding_compounds.material import MATERIALS


def test_simulation_empty_warning(app_path):
    """
    Якщо будинку немає, показуємо st.warning.
    """
    at = AppTest.from_file(app_path, default_timeout=10)
    at.run()

    # Йдемо на вкладку Симуляція
    at.sidebar.radio("navigation_radio").set_value("Симуляція").run()

    # Перевіряємо, що з'явилося жовте попередження
    assert len(at.warning) > 0
    # Перевіряємо текст (частину)
    assert "Спочатку створіть будівлю" in at.warning[0].value

    sim_buttons = [b for b in at.button if b.key == "sim_run_btn"]
    assert len(sim_buttons) == 0


def test_simulation_run_happy_path(app_path):
    """
    Якщо будинок є, все працює
    """
    at = AppTest.from_file(app_path, default_timeout=20)

    # Створюємо будинок прямо в session_state перед запуском
    if "building" not in at.session_state:
        at.session_state["building"] = Building()
    mat = list(MATERIALS.values())[0]

    at.session_state["building"].create_initial_room(5, 5, 3, mat, "Sim Room")

    at.run()

    # Йдемо на симуляцію
    at.sidebar.radio("navigation_radio").set_value("Симуляція").run()

    # Перевіряємо дефолтні значення параметрів
    assert at.number_input("sim_duration").value == 24
    assert at.number_input("sim_tariff").value == 4.32

    # Змінюємо параметри
    at.number_input("sim_duration").set_value(10).run()
    at.number_input("sim_tariff").set_value(2.5).run()

    # запускаєм
    at.button("sim_run_btn").click().run()
    assert not at.exception

    # Має з'явитися таблиця
    assert len(at.dataframe) > 0

    # Мають бути метрики
    assert len(at.metric) >= 3

