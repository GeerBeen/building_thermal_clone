import pytest
import time
import os
from building_serializer import BuildingSerializer
from custom_pages.make_simulation import ThermalSimulation, RoomControlProfile, ControlMode

# Визначаємо шлях до файлу з даними
# Припускаємо, що файл лежить в tests/data/complex_building.json
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
JSON_FILE_PATH = os.path.join(TEST_DATA_DIR, "complex_building.json")


def test_complex_building_simulation_performance():
    """
    Бенчмарк:
    Завантажує складну структуру будинку з JSON файлу
    Запускає симуляцію на тривалий період
    Вимірює час виконання
    """

    # Перевірка наявності файлу
    if not os.path.exists(JSON_FILE_PATH):
        pytest.skip(f"Файл {JSON_FILE_PATH} не знайдено."
                    f" Створіть складний будинок в UI і збережіть його туди.")

    # Читання та Десеріалізація
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        json_data = f.read()

    building = BuildingSerializer.from_json(json_data)

    profiles = {}
    for room_id in building.rooms:
        profiles[room_id] = RoomControlProfile(
            mode=ControlMode.THERMOSTAT,
            target_temp=21.0
        )

    sim = ThermalSimulation(building)
    sim.initialize(
        start_temp=20.0,
        profiles=profiles,
        t_min=-10.0,
        t_max=-2.0,
        internal_gain=200.0
    )

    # Симулюємо 30 днів з кроком 1 хвилина
    # Це 43 200 кроків розрахунку для кожної кімнати
    DURATION_HOURS = 720

    start_time = time.time()

    sim.run_simulation(duration_hours=DURATION_HOURS, dt_seconds=60)

    end_time = time.time()
    total_time = end_time - start_time

    # звіт
    print(f"\n" + "=" * 40)
    print(f"BENCHMARK RESULTS (Complex Building)")
    print(f"=" * 40)
    print(f"Duration Simulated: {DURATION_HOURS} hours")
    print(f"Execution Time:     {total_time:.4f} seconds")
    print(f"Speedup Factor:     {int((DURATION_HOURS * 3600) / total_time)}"
          f"x faster than real time")
    print(f"=" * 40)

    assert total_time < 5.0, f"Simulation is too slow! {total_time:.4f}s > 2.0s"
