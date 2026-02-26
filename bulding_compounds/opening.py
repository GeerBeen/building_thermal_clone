import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Dict


class OpeningCategory(StrEnum):
    WINDOW = "Вікно"
    DOOR = "Двері"


@dataclass
class OpeningTech:
    """
    Технологія виготовлення отвору.
    """
    name: str = "Default Tech"
    U: float = 1  # Вт/(м²·К)
    g: float = 1  # 0.0 - 1.0
    category: OpeningCategory = OpeningCategory.WINDOW
    color: str = "#A0C4FF"

    def __post_init__(self):
        if self.U < 0:
            raise ValueError(f"U-value cannot be negative. Got: {self.U}")
        if not (0.0 <= self.g <= 1.0):
            raise ValueError(f"Solar factor (g) must be between 0 and 1. Got: {self.g}")
        if not self.name:
            raise ValueError("Name cannot be empty")


@dataclass
class Opening:
    """
    Конкретний екземпляр отвору.
    """
    tech: OpeningTech
    width: float = 1.0
    height: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        # Валідація розмірів
        if self.width <= 0:
            raise ValueError(f"Width must be greater than 0. Got: {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be greater than 0. Got: {self.height}")

        # Валідація типу технології (щоб не передали випадково Enum замість об'єкта)
        if not isinstance(self.tech, OpeningTech):
            raise TypeError(f"tech must be an instance of OpeningTech, got {type(self.tech)}")

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def heat_loss_coefficient(self) -> float:
        """H_t (W/K) = U * Area"""
        return self.tech.U * self.area


OPENING_TYPES = {
    "Win_Standard": OpeningTech("Металопластик (1-кам)", U=1.4, g=0.65, category=OpeningCategory.WINDOW,
                                color="#B0E0E6"),
    "Win_Energy": OpeningTech("Енергоефективне (2-кам)", U=0.9, g=0.50, category=OpeningCategory.WINDOW,
                              color="#E0FFFF"),
    "Win_Old": OpeningTech("Старе дерев'яне", U=2.5, g=0.75, category=OpeningCategory.WINDOW, color="#87CEEB"),
    "Door_Metal": OpeningTech("Двері металеві", U=2.0, g=0.0, category=OpeningCategory.DOOR, color="#708090"),
    "Door_Wood": OpeningTech("Двері дерев'яні", U=1.8, g=0.0, category=OpeningCategory.DOOR, color="#DEB887"),
}
