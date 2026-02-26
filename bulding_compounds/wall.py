from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from bulding_compounds.material import Material
from bulding_compounds.opening import Opening
from shapely.geometry import LineString
import math


# Стіна
@dataclass
class Wall:
    start_x: float = 0
    start_y: float = 0
    end_x: float = 1
    end_y: float = 1
    height: float = 2.8
    base_material: Optional[Material] = None
    openings: List[Opening] = field(default_factory=list)
    room_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        """Валідація параметрів стіни після ініціалізації."""
        # Перевірка висоти
        if self.height <= 0:
            raise ValueError(f"Height must be greater than 0. Got: {self.height}")

        # Перевірка довжини стіни (стіна не може бути точкою)
        length = math.hypot(self.end_x - self.start_x, self.end_y - self.start_y)
        if length == 0:
            raise ValueError(
                f"Wall length cannot be 0. Start and End points coincide: ({self.start_x}, {self.start_y})")

    def add_room_id(self, id_: str):
        if len(self.room_ids) >= 2:
            raise Exception("Кількість кімнат для стіни не може бути більше 2")
        self.room_ids.append(id_)

    @property
    def length(self) -> float:
        """Допоміжна властивість для обчислення довжини"""
        return math.hypot(self.end_x - self.start_x, self.end_y - self.start_y)

    def is_equeal_wall(self, wall2) -> bool:
        line1 = LineString([(self.start_x, self.start_y), (self.end_x, self.end_y)])
        line2 = LineString([(wall2.start_x, wall2.start_y), (wall2.end_x, wall2.end_y)])
        return line1.equals(line2)

    @property
    def area_gross(self) -> float:
        """Загальна площа стіни (без вирізів)"""
        return self.length * self.height

    @property
    def area_openings(self) -> float:
        """Сумарна площа всіх отворів"""
        return sum(op.area for op in self.openings)

    @property
    def area_net(self) -> float:
        """Чиста площа стіни (матеріалу)"""
        return max(0.0, self.area_gross - self.area_openings)

    def add_opening(self, opening: Opening):
        """
        Додає отвір. Перевіряє тільки сумарні габарити.
        Позиціонування не враховується (воно автоматичне).
        """
        # 1. Перевірка висоти
        if opening.height > self.height:
            raise ValueError(f"Висота отвору ({opening.height}м) більша за висоту стіни ({self.height}м)!")

        # 2. Перевірка ширини (чи влізе це НОВЕ вікно разом зі старими)
        current_openings_width = sum(op.width for op in self.openings)
        if current_openings_width + opening.width > self.length:
            raise ValueError(f"Сумарна ширина отворів перевищує довжину стіни! (Стіна: {self.length:.2f}м)")

        self.openings.append(opening)


def walls_intersect_properly(wall1: Wall, wall2: Wall) -> bool:
    line1 = LineString([(wall1.start_x, wall1.start_y), (wall1.end_x, wall1.end_y)])
    line2 = LineString([(wall2.start_x, wall2.start_y), (wall2.end_x, wall2.end_y)])

    if line1.equals(line2):
        return True  # однакові стіни — ок

    if not line1.intersects(line2):
        return True  # не перетинаються — ок

    # Є перетин — перевіряємо, чи він у кінцевих точках
    intersection = line1.intersection(line2)

    # intersection може бути Point або MultiPoint
    if intersection.geom_type == "Point":
        px, py = intersection.x, intersection.y
        # Перевіряємо, чи це одна з 4 кінцевих точок
        ends1 = [(wall1.start_x, wall1.start_y), (wall1.end_x, wall1.end_y)]
        ends2 = [(wall2.start_x, wall2.start_y), (wall2.end_x, wall2.end_y)]
        return (px, py) in ends1 or (px, py) in ends2
    else:
        return False  # перетин не точка (наприклад, накладання) — погано


if __name__ == '__main__':
    wall1 = Wall(-1, 0, 1, 0, 1, Material())
    wall2 = Wall(0, 0, 0, 1, 1, Material())
    print(walls_intersect_properly(wall1, wall2))
