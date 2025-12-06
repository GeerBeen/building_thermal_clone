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