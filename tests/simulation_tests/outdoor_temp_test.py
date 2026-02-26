import pytest
import math
from simulation.thermal_sim import ThermalSimulation, Building


class TestWeatherSimulation:

    @pytest.fixture
    def sim(self):
        """Базова симуляція без кімнат (вони не треба для погоди)."""
        b = Building()
        s = ThermalSimulation(b)
        # Налаштовуємо діапазон температур: Ніч -10, День +10
        s.t_min_outdoor = -10.0
        s.t_max_outdoor = 10.0
        return s

    def test_temperature_bounds(self, sim):
        """
        Температура ніколи не має виходити за межі [min, max].
        Перевіряємо кожну годину доби.
        """
        for hour in range(24):
            sim.current_time_sec = hour * 3600
            temp = sim._get_current_outdoor_temp()

            # Використовуємо approx з невеликим запасом через float point arithmetic
            assert temp >= -10.0 - 0.01
            assert temp <= 10.0 + 0.01

    def test_peak_temperature_time(self, sim):
        """
        Пік (максимум) має бути близько 14:00.
        При t_max = 10.0, о 14:00 має бути 10.0.
        """
        sim.current_time_sec = 14 * 3600  # 14:00
        temp = sim._get_current_outdoor_temp()

        assert temp == pytest.approx(10.0, abs=0.1)

    def test_min_temperature_time(self, sim):
        """
        Мінімум має бути через 12 годин від піку (близько 2:00 ночі).
        При t_min = -10.0, о 2:00 має бути -10.0.
        """
        sim.current_time_sec = 2 * 3600  # 02:00
        temp = sim._get_current_outdoor_temp()

        assert temp == pytest.approx(-10.0, abs=0.1)

    def test_cyclicity_next_day(self, sim):
        """
        Температура в той самий час на наступний день має бути такою ж.
        14:00 (день 1) == 14:00 (день 2).
        """
        # День 1, 10:00
        sim.current_time_sec = 10 * 3600
        temp_day1 = sim._get_current_outdoor_temp()

        # День 2, 10:00 (10 + 24 = 34 години)
        sim.current_time_sec = 34 * 3600
        temp_day2 = sim._get_current_outdoor_temp()

        assert temp_day1 == pytest.approx(temp_day2)

    def test_constant_weather(self, sim):
        """
        Якщо t_min == t_max, температура має бути постійною.
        """
        sim.t_min_outdoor = 5.0
        sim.t_max_outdoor = 5.0

        sim.current_time_sec = 0
        assert sim._get_current_outdoor_temp() == 5.0

        sim.current_time_sec = 12 * 3600
        assert sim._get_current_outdoor_temp() == 5.0

    def test_smoothness(self, sim):
        """
        Перевірка плавності: різниця між 12:00 і 12:01 має бути малою.
        """
        sim.current_time_sec = 12 * 3600
        t1 = sim._get_current_outdoor_temp()

        sim.current_time_sec = 12 * 3600 + 60  # +1 хвилина
        t2 = sim._get_current_outdoor_temp()

        diff = abs(t1 - t2)
        assert diff < 0.1  # Зміна за хвилину не має бути різкою