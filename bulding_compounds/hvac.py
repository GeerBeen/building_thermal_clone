import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List


class HVACType(StrEnum):
    HEATER = "Обігрівач"
    COOLER = "Кондиціонер"
    AC_INVERTER = "Клімат-контроль"


@dataclass
class HVACDevice:
    name: str
    device_type: HVACType
    power_heating: float = 0.0  # Вт
    power_cooling: float = 0.0  # Вт
    efficiency: float = 1.0  # COP/ККД
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        # 1. Базові перевірки значень
        if not self.name:
            raise ValueError("Device name cannot be empty")

        if self.power_heating < 0:
            raise ValueError(f"Heating power cannot be negative. Got: {self.power_heating}")

        if self.power_cooling < 0:
            raise ValueError(f"Cooling power cannot be negative. Got: {self.power_cooling}")

        if self.efficiency <= 0:
            raise ValueError(f"Efficiency must be greater than 0. Got: {self.efficiency}")

        # 2. Логічні перевірки відповідності Типу та Потужності
        if self.device_type == HVACType.HEATER:
            if self.power_heating == 0:
                raise ValueError("A Heater must have heating_power > 0")
            if self.power_cooling > 0:
                raise ValueError("A Heater cannot have cooling_power")

        elif self.device_type == HVACType.COOLER:
            if self.power_cooling == 0:
                raise ValueError("A Cooler must have cooling_power > 0")
            if self.power_heating > 0:
                raise ValueError("A Cooler cannot have heating_power")

        elif self.device_type == HVACType.AC_INVERTER:
            if self.power_heating == 0 and self.power_cooling == 0:
                raise ValueError("AC Inverter must have either heating or cooling power (or both)")

    @property
    def description(self) -> str:
        parts = []
        if self.power_heating > 0:
            parts.append(f"🔥 {self.power_heating / 1000:.1f} кВт")
        if self.power_cooling > 0:
            parts.append(f"❄️ {self.power_cooling / 1000:.1f} кВт")
        return " / ".join(parts)


HVAC_CATALOG = {
    "Radiator_1000": HVACDevice("Електрорадіатор (1 кВт)", HVACType.HEATER, power_heating=1000),
    "Radiator_2000": HVACDevice("Масляний обігрівач (2 кВт)", HVACType.HEATER, power_heating=2000),
    "AC_09": HVACDevice("Кондиціонер '09' (2.5 кВт)", HVACType.AC_INVERTER, power_heating=2800, power_cooling=2500),
    "AC_12": HVACDevice("Кондиціонер '12' (3.5 кВт)", HVACType.AC_INVERTER, power_heating=3800, power_cooling=3500),
    "UFO": HVACDevice("Інфрачервоний обігрівач (1.5 кВт)", HVACType.HEATER, power_heating=1500),
    "HeatPump_Air": HVACDevice("Тепловий насос (Повітря-Повітря)", HVACType.AC_INVERTER, power_heating=5000,
                               power_cooling=4500),
}
