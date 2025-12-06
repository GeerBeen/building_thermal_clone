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
    Технологія виготовлення отвору (Каталог).
    Визначає фізику (тепло).
    """
    name: str
    U: float  # Вт/(м²·К) - Коефіцієнт теплопередачі
    g: float  # 0.0 - 1.0 - Сонячний фактор
    category: OpeningCategory
    color: str = "#A0C4FF"  # Колір для відображення


@dataclass
class Opening:
    """
    Конкретний екземпляр отвору на стіні.
    Визначає геометрію (розміри).
    """
    tech: OpeningTech  # Посилання на тип
    width: float  # Ширина (м)
    height: float  # Висота (м)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

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
