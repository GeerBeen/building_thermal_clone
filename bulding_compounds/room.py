from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid
from bulding_compounds.hvac import HVACDevice


@dataclass
class Room:
    name: str
    width: float  # розмір по осі X (м)
    length: float  # розмір по осі Y (м)
    height: float  # висота стелі (м)
    # Координати лівого нижнього кута
    x: float
    y: float
    # За замовчуванням 4 стіни (прямокутна кімната)
    wall_ids: List[str] = field(default_factory=lambda: ["", "", "", ""])
    hvac_devices: List['HVACDevice'] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        """Валідація геометрії кімнати."""
        if not self.name:
            raise ValueError("Room name cannot be empty")

        if self.width <= 0:
            raise ValueError(f"Room width must be > 0. Got: {self.width}")

        if self.length <= 0:
            raise ValueError(f"Room length must be > 0. Got: {self.length}")

        if self.height <= 0:
            raise ValueError(f"Room height must be > 0. Got: {self.height}")

    def get_center(self, building) -> tuple[float, float]:
        """Центр кімнати — з координат стін (надійний спосіб)"""
        xs = []
        ys = []
        for wall_id in self.wall_ids:
            wall = building.walls.get(wall_id)
            if wall:
                xs.extend([wall.start_x, wall.end_x])
                ys.extend([wall.start_y, wall.end_y])

        if not xs:
            raise ValueError("Кімната не має валідних стін")

        return sum(xs) / len(xs), sum(ys) / len(ys)

    def add_hvac(self, device: HVACDevice):
        self.hvac_devices.append(device)

    def remove_hvac(self, device_id: str):
        self.hvac_devices = [d for d in self.hvac_devices if d.id != device_id]