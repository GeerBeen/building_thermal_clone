import pytest
from bulding_compounds.hvac import HVACDevice, HVACType


class TestHVACInitialization:

    def test_create_heater(self):
        """Створення коректного обігрівача."""
        heater = HVACDevice(
            name="Oil Heater",
            device_type=HVACType.HEATER,
            power_heating=2000,  # 2 кВт
            efficiency=0.95
        )
        assert heater.power_heating == 2000
        assert heater.power_cooling == 0
        assert "🔥 2.0 кВт" in heater.description

    def test_create_cooler(self):
        """Створення коректного кондиціонера (тільки холод)."""
        cooler = HVACDevice(
            name="Basic AC",
            device_type=HVACType.COOLER,
            power_cooling=3500,
            efficiency=3.0  # COP
        )
        assert cooler.power_cooling == 3500
        assert "❄️ 3.5 кВт" in cooler.description

    def test_create_inverter(self):
        """Створення інвертора (гріє і холодить)."""
        ac = HVACDevice(
            name="Split System",
            device_type=HVACType.AC_INVERTER,
            power_heating=4000,
            power_cooling=3500
        )
        desc = ac.description
        assert "🔥 4.0 кВт" in desc
        assert "❄️ 3.5 кВт" in desc
        assert " / " in desc


class TestHVACValidationLogic:

    def test_negative_power(self):
        """Негативна потужність заборонена."""
        with pytest.raises(ValueError, match="Heating power cannot be negative"):
            HVACDevice("Bad", HVACType.HEATER, power_heating=-100)

    def test_zero_efficiency(self):
        """ККД 0 або менше заборонено."""
        with pytest.raises(ValueError, match="Efficiency must be greater than 0"):
            HVACDevice("Bad", HVACType.HEATER, power_heating=1000, efficiency=0)

    def test_heater_logic_error(self):
        """Помилка: Обігрівач без потужності нагріву."""
        with pytest.raises(ValueError, match="Heater must have heating_power > 0"):
            HVACDevice("Useless Heater", HVACType.HEATER, power_heating=0)

    def test_heater_with_cooling_error(self):
        """Помилка: Обігрівач не може охолоджувати."""
        with pytest.raises(ValueError, match="Heater cannot have cooling_power"):
            HVACDevice("Strange Heater", HVACType.HEATER, power_heating=1000, power_cooling=500)

    def test_cooler_logic_error(self):
        """Помилка: Кондиціонер без потужності охолодження."""
        with pytest.raises(ValueError, match="Cooler must have cooling_power > 0"):
            HVACDevice("Fan Only", HVACType.COOLER, power_cooling=0)

    def test_cooler_with_heating_error(self):
        """Помилка: Звичайний кондиціонер (Cooler) не гріє."""
        with pytest.raises(ValueError, match="Cooler cannot have heating_power"):
            HVACDevice("Wrong Type", HVACType.COOLER, power_cooling=2000, power_heating=2000)

    def test_inverter_empty_error(self):
        """Помилка: Інвертор з нулями всюди."""
        with pytest.raises(ValueError, match="AC Inverter must have either heating or cooling"):
            HVACDevice("Broken AC", HVACType.AC_INVERTER, power_heating=0, power_cooling=0)

    def test_inverter_partial_power(self):
        """Інвертор може мати тільки нагрів (теоретично) або тільки холод, це не заборонено, але хоч щось має бути."""
        ac = HVACDevice("Heating Only AC", HVACType.AC_INVERTER, power_heating=2000, power_cooling=0)
        assert ac.power_heating == 2000
