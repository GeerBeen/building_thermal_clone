import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List


class HVACType(StrEnum):
    HEATER = "Обігрівач"  # Додає тепло
    COOLER = "Кондиціонер"  # Забирає тепло (охолодження)
    AC_INVERTER = "Клімат-контроль"  # Може і гріти, і охолоджувати


@dataclass
class HVACDevice:
    name: str
    device_type: HVACType
    power_heating: float = 0.0  # Вт (Максимальна потужність нагріву)
    power_cooling: float = 0.0  # Вт (Максимальна потужність охолодження)
    efficiency: float = 1.0  # COP/ККД (для розрахунку витрат електрики, поки можна 1.0)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

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
