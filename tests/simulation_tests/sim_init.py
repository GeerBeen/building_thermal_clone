import pytest
from simulation.thermal_sim import ThermalSimulation, Building, Room, RoomControlProfile


class TestSimulationInitialization:

    @pytest.fixture
    def simple_building(self):
        """Будівля з двома кімнатами."""
        b = Building()
        r1 = Room("Hall", 10, 10, 3, 0, 0, id="r1")
        r2 = Room("Bath", 5, 5, 3, 0, 0, id="r2")
        b.rooms["r1"] = r1
        b.rooms["r2"] = r2
        return b

    @pytest.fixture
    def default_profiles(self, simple_building):
        """Профілі для всіх кімнат."""
        return {
            "r1": RoomControlProfile(),
            "r2": RoomControlProfile()
        }

    def test_successful_initialization(self, simple_building, default_profiles):
        """Перевірка коректного старта."""
        sim = ThermalSimulation(simple_building)

        sim.initialize(
            start_temp=20.0,
            profiles=default_profiles,
            t_min=-10,
            t_max=5,
            internal_gain=150
        )

        # Перевіряємо стан
        assert sim.current_time_sec == 0.0
        assert sim.t_min_outdoor == -10
        assert sim.internal_heat_gain == 150

        # Перевіряємо кімнати
        assert sim.current_temperatures["r1"] == 20.0
        assert sim.current_temperatures["r2"] == 20.0
        assert sim.total_energy_kwh["r1"] == 0.0

        # Перевіряємо історію (має бути 1 точка - стартова)
        assert len(sim.history_time) == 1
        assert len(sim.history_temps["r1"]) == 1
        assert len(sim.history_outdoor) == 1

    def test_weather_validation_error(self, simple_building, default_profiles):
        """Помилка, якщо мін. температура вища за максимальну."""
        sim = ThermalSimulation(simple_building)
        with pytest.raises(ValueError, match="t_min .* cannot be greater than t_max"):
            sim.initialize(20, default_profiles, t_min=10, t_max=5)

    def test_missing_profiles_error(self, simple_building):
        """Помилка, якщо забули профіль для однієї з кімнат."""
        sim = ThermalSimulation(simple_building)

        incomplete_profiles = {
            "r1": RoomControlProfile()
            # r2 пропущена
        }

        with pytest.raises(ValueError, match="Missing control profiles"):
            sim.initialize(20, incomplete_profiles, -5, 0)

    def test_reinitialization_clears_history(self, simple_building, default_profiles):
        """
        Якщо викликати initialize вдруге, історія має очиститись,
        а не додаватись до старої.
        """
        sim = ThermalSimulation(simple_building)

        # 1. Перший запуск
        sim.initialize(20, default_profiles, -5, 0)
        # Імітуємо роботу (додаємо "сміття" в історію)
        sim.history_time.append(3600)
        sim.history_temps["r1"].append(21.0)
        assert len(sim.history_time) == 2

        # 2. Другий запуск (Ресет)
        sim.initialize(15, default_profiles, -10, -5)

        # Історія має знову стати довжиною 1
        assert len(sim.history_time) == 1
        assert sim.history_time[0] == 0.0
        assert len(sim.history_temps["r1"]) == 1
        assert sim.history_temps["r1"][0] == 15.0  # Нова стартова темп.

    def test_extra_profiles_ignored(self, simple_building, default_profiles):
        """
        Якщо передали профілі для неіснуючих кімнат (зайві),
        це не критично, але валідація має пропустити це (або попередити).
        В моїй реалізації це дозволено.
        """
        sim = ThermalSimulation(simple_building)
        default_profiles["ghost_room"] = RoomControlProfile()

        # Має пройти без помилок
        sim.initialize(20, default_profiles, -5, 0)
        assert len(sim.control_profiles) == 3  # r1, r2, ghost_room