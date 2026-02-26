import pytest
from unittest.mock import MagicMock
from simulation.thermal_sim import ThermalSimulation, Building, Room, RoomControlProfile


class TestSimulationStep:

    @pytest.fixture
    def sim_setup(self):
        """Підготовка симуляції з 1 кімнатою."""
        b = Building()
        r = Room("TestRoom", 10, 10, 3, 0, 0, id="r1")
        b.rooms["r1"] = r

        sim = ThermalSimulation(b)
        # Ініціалізуємо базовий стан
        sim.initialize(start_temp=20.0, profiles={"r1": RoomControlProfile()}, t_min=0, t_max=0)

        return sim, r

    def test_step_physics_formula(self, sim_setup):
        """
        Перевірка головної формули: Delta T = (Q_total * dt) / C_mass
        """
        sim, room = sim_setup

        # Підміняємо складні методи на фіксовані значення
        # Тепловтрати = -100 Вт
        sim._calculate_transmission_heat_flow = MagicMock(return_value=-100.0)

        # HVAC = +500 Вт
        sim._calculate_hvac_power = MagicMock(return_value=500.0)

        # Теплоємність = 4000 Дж/К
        sim._calculate_room_thermal_mass = MagicMock(return_value=4000.0)

        # Внутрішні надходження (вимкнемо для чистоти експерименту)
        sim.internal_heat_gain = 0.0

        # Крок dt = 10 секунд
        sim.step(dt_seconds=10.0)

        # Q_total = -100 + 500 + 0 = 400 Вт
        # Delta T = 400 * 10 / 4000 = 1 Градус

        new_temp = sim.current_temperatures["r1"]
        assert new_temp == pytest.approx(20.0 + 1.0)

        # Перевіряємо, що час оновився
        assert sim.current_time_sec == 10.0

    def test_energy_consumption_accumulation(self, sim_setup):
        """
        Перевірка, що кВт*год накопичуються правильно.
        """
        sim, room = sim_setup

        # HVAC працює на 1000 Вт (1 кВт)
        sim._calculate_hvac_power = MagicMock(return_value=1000.0)
        # Решту можна не мокати, вони не впливають на лічильник енергії

        # Крок 1 година (3600 сек)
        sim.step(dt_seconds=3600.0)

        # 1 кВт * 1 год = 1 кВт*год
        assert sim.total_energy_kwh["r1"] == pytest.approx(1.0)

        # Ще крок на 30 хв (1800 сек)
        sim.step(dt_seconds=1800.0)

        # 1.0 + 0.5 = 1.5 кВт*год
        assert sim.total_energy_kwh["r1"] == pytest.approx(1.5)

    def test_cooling_consumes_energy(self, sim_setup):
        """
        Охолодження теж має споживати енергію.
        """
        sim, room = sim_setup

        # HVAC = -1000 Вт
        sim._calculate_hvac_power = MagicMock(return_value=-1000.0)
        sim.step(dt_seconds=3600.0)

        assert sim.total_energy_kwh["r1"] == pytest.approx(1.0)

    def test_history_updates(self, sim_setup):
        """
        Перевірка, що масиви історії ростуть.
        """
        sim, room = sim_setup

        initial_len = len(sim.history_temps["r1"])  # 1 (стартова точка)

        sim.step(60)
        sim.step(60)

        # Має додатися 2 точки
        assert len(sim.history_temps["r1"]) == initial_len + 2
        assert len(sim.history_time) == initial_len + 2
        assert len(sim.history_outdoor) == initial_len + 2  # +1 стартова outdoor

    def test_run_simulation_loop(self, sim_setup):
        """
        Інтеграційний тест методу run_simulation.
        Чи виконується правильна кількість кроків?
        """
        sim, room = sim_setup

        # Запускаємо на 2 години з кроком 1 година
        # Це має бути рівно 2 кроки
        sim.step = MagicMock(wraps=sim.step)  # Шпигуємо за методом step

        sim.run_simulation(duration_hours=2, dt_seconds=3600)

        assert sim.step.call_count == 2
        assert sim.current_time_sec == 2 * 3600

    def test_internal_heat_gain_influence(self, sim_setup):
        """
        Перевірка, що internal_heat_gain додається до балансу.
        """
        sim, room = sim_setup

        # Ізолюємо все інше
        sim._calculate_transmission_heat_flow = MagicMock(return_value=0)
        sim._calculate_hvac_power = MagicMock(return_value=0)
        sim._calculate_room_thermal_mass = MagicMock(return_value=1000.0)

        sim.internal_heat_gain = 200.0  # Вт

        # Крок 10 сек
        sim.step(10)

        # Q = 200. dT = (200 * 10) / 1000 = 2.0
        expected_temp = 20.0 + 2.0
        assert sim.current_temperatures["r1"] == pytest.approx(expected_temp)
