from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid
from bulding_compounds.hvac import HVACDevice


@dataclass
class Room:
    name: str
    width: float  # розмір по осі X
    length: float  # розмір по осі Y
    height: float
    # Координати лівого нижнього кута
    x: float
    y: float
    wall_ids: List[str] = field(default_factory=lambda: ["", "", "", ""])
    hvac_devices: List[HVACDevice] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

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