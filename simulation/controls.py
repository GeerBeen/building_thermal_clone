from enum import StrEnum
from dataclasses import dataclass


class ControlMode(StrEnum):
    THERMOSTAT = "Термостат (Авто)"  # Підтримувати задану температуру
    ALWAYS_ON = "Завжди ВКЛ"  # Гріти/Студити на макс
    ALWAYS_OFF = "Завжди ВИКЛ"  # Не вмикати нічого
    CYCLIC = "Циклічний (Таймер)"  # Робота по колу (X годин вкл, Y викл)


@dataclass
class RoomControlProfile:
    """Налаштування поведінки HVAC для конкретної кімнати"""
    mode: ControlMode = ControlMode.THERMOSTAT
    target_temp: float = 21.0  # Для режиму THERMOSTAT

    # Для режиму CYCLIC
    cycle_on_hours: float = 0.0  # Скільки годин працює
    cycle_off_hours: float = 0.0  # Скільки годин відпочиває

    # Початковий зсув (наприклад, щоб кімнати вмикались не одночасно)
    time_offset_hours: float = 0.0

    def __post_init__(self):
        if not (-50 <= self.target_temp <= 100):
            raise ValueError(f"Target temperature {self.target_temp} is out of realistic range (-50 to +100)")

        if self.cycle_on_hours < 0 or self.cycle_off_hours < 0:
            raise ValueError("Cycle hours cannot be negative")

        if self.time_offset_hours < 0:
            raise ValueError("Time offset cannot be negative")

        if self.mode == ControlMode.CYCLIC:
            total_cycle = self.cycle_on_hours + self.cycle_off_hours
            if total_cycle <= 0:
                raise ValueError(
                    "For CYCLIC mode, total cycle duration (on + off) must be > 0. "
                    "Cannot loop with zero duration."
                )

