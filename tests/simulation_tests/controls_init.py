import pytest
from simulation.controls import RoomControlProfile, ControlMode


class TestControlProfileInitialization:

    def test_default_profile(self):
        """Перевірка дефолтних значень (Термостат, 21 градус)."""
        profile = RoomControlProfile()
        assert profile.mode == ControlMode.THERMOSTAT
        assert profile.target_temp == 21.0
        assert profile.cycle_on_hours == 0
        assert profile.cycle_off_hours == 0

    def test_valid_thermostat_settings(self):
        """Зміна цільової температури в допустимих межах."""
        profile = RoomControlProfile(mode=ControlMode.THERMOSTAT, target_temp=25.5)
        assert profile.target_temp == 25.5

    def test_valid_cyclic_profile(self):
        """Створення коректного циклічного профілю."""
        # 1 година гріє, 2 години відпочиває, старт через 0.5 години
        profile = RoomControlProfile(
            mode=ControlMode.CYCLIC,
            cycle_on_hours=1.0,
            cycle_off_hours=2.0,
            time_offset_hours=0.5
        )
        assert profile.cycle_on_hours == 1.0
        assert profile.cycle_off_hours == 2.0
        assert profile.time_offset_hours == 0.5

    def test_always_modes(self):
        """Режими ALWAYS_ON/OFF не вимагають налаштувань циклу."""
        p1 = RoomControlProfile(mode=ControlMode.ALWAYS_ON)
        p2 = RoomControlProfile(mode=ControlMode.ALWAYS_OFF)
        assert p1.mode == ControlMode.ALWAYS_ON
        assert p2.mode == ControlMode.ALWAYS_OFF


class TestControlProfileValidation:

    @pytest.mark.parametrize("bad_temp", [-274, -100, 150, 500])
    def test_temperature_out_of_bounds(self, bad_temp):
        """Температура має бути в межах фізичної реальності будівлі."""
        with pytest.raises(ValueError, match="out of realistic range"):
            RoomControlProfile(target_temp=bad_temp)

    def test_negative_times_forbidden(self):
        """Час не може бути від'ємним у будь-якому режимі."""
        with pytest.raises(ValueError, match="Cycle hours cannot be negative"):
            RoomControlProfile(cycle_on_hours=-1)

        with pytest.raises(ValueError, match="Cycle hours cannot be negative"):
            RoomControlProfile(cycle_off_hours=-0.5)

        with pytest.raises(ValueError, match="Time offset cannot be negative"):
            RoomControlProfile(time_offset_hours=-10)

    def test_cyclic_mode_zero_duration_error(self):
        """
        У режимі CYCLIC сума on+off має бути > 0.
        Інакше це нескінченний цикл перемикань за 0 секунд.
        """
        with pytest.raises(ValueError, match="total cycle duration .* must be > 0"):
            RoomControlProfile(
                mode=ControlMode.CYCLIC,
                cycle_on_hours=0,
                cycle_off_hours=0
            )

    def test_cyclic_mode_partial_zero_is_ok(self):
        """
        Цикл може бути "1 година працює, 0 відпочиває" (по суті Always On),
        або "0 працює, 1 відпочиває" (Always Off). Це технічно валідно.
        """
        p1 = RoomControlProfile(mode=ControlMode.CYCLIC, cycle_on_hours=1, cycle_off_hours=0)
        assert p1.mode == ControlMode.CYCLIC

        p2 = RoomControlProfile(mode=ControlMode.CYCLIC, cycle_on_hours=0, cycle_off_hours=1)
        assert p2.mode == ControlMode.CYCLIC

    def test_non_cyclic_mode_ignores_zero_cycles(self):
        """
        Якщо режим НЕ Cyclic, то нулі в cycle_hours допустимі (вони просто не використовуються).
        """
        profile = RoomControlProfile(
            mode=ControlMode.THERMOSTAT,
            cycle_on_hours=0,
            cycle_off_hours=0
        )
        # Помилки не має бути
        assert profile.mode == ControlMode.THERMOSTAT
