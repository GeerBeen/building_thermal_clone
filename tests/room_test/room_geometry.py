import pytest
from bulding_compounds.room import Room
from bulding_compounds.wall import Wall
from building import Building


# --- Fixtures ---

@pytest.fixture
def empty_building():
    return Building()


@pytest.fixture
def square_room_walls():
    """Створює набір стін для кімнати 10x10 з центром в (5, 5)."""
    # Стіни йдуть по периметру: (0,0) -> (10,0) -> (10,10) -> (0,10) -> (0,0)
    w1 = Wall(start_x=0, start_y=0, end_x=10, end_y=0, id="w1")
    w2 = Wall(start_x=10, start_y=0, end_x=10, end_y=10, id="w2")
    w3 = Wall(start_x=10, start_y=10, end_x=0, end_y=10, id="w3")
    w4 = Wall(start_x=0, start_y=10, end_x=0, end_y=0, id="w4")
    return {"w1": w1, "w2": w2, "w3": w3, "w4": w4}

class TestRoomCenterCalculation:

    def test_center_square_room(self, empty_building, square_room_walls):
        """
        Ідеальний квадрат 10x10.
        Координати кутів: (0,0), (10,0), (10,10), (0,10).
        Очікуваний центр: (5, 5).
        """
        # Наповнюємо будівлю стінами
        empty_building.walls = square_room_walls

        # Створюємо кімнату, прив'язуємо ID стін
        room = Room(name="Hall", width=10, length=10, height=3, x=0, y=0,
                    wall_ids=["w1", "w2", "w3", "w4"])

        center_x, center_y = room.get_center(empty_building)

        assert center_x == 5.0
        assert center_y == 5.0

    def test_center_rectangular_offset_room(self, empty_building):
        """
        Прямокутна кімната, зміщена від початку координат.
        Прямокутник від (10, 10) до (20, 15).
        Розмір 10x5. Центр має бути в (15, 12.5).
        """
        w1 = Wall(start_x=10, start_y=10, end_x=20, end_y=10, id="w1")  # Низ
        w2 = Wall(start_x=20, start_y=10, end_x=20, end_y=15, id="w2")  # Право
        w3 = Wall(start_x=20, start_y=15, end_x=10, end_y=15, id="w3")  # Верх
        w4 = Wall(start_x=10, start_y=15, end_x=10, end_y=10, id="w4")  # Ліво

        empty_building.walls = {"w1": w1, "w2": w2, "w3": w3, "w4": w4}
        room = Room("Offset", 10, 5, 3, 10, 10, wall_ids=["w1", "w2", "w3", "w4"])

        cx, cy = room.get_center(empty_building)
        assert cx == 15.0
        assert cy == 12.5

    def test_center_ignores_missing_walls(self, empty_building, square_room_walls):
        """
        Якщо в списку wall_ids є ID, якого немає в building.walls,
        він має бути проігнорований, а центр розрахований по решті.
        """
        empty_building.walls = square_room_walls
        # Додаємо "fake_id", якого немає в словнику walls
        room = Room("Hall", 10, 10, 3, 0, 0,
                    wall_ids=["w1", "w2", "w3", "w4", "fake_id"])

        # Результат має бути все ще (5, 5)
        assert room.get_center(empty_building) == (5.0, 5.0)

    # така кімната не може існувати
    # def test_center_based_on_single_wall(self, empty_building):
    #     """
    #     Граничний випадок: кімната складається з однієї стіни (наприклад, незамкнутий контур).
    #     Центр має бути серединою цієї стіни.
    #     """
    #     w1 = Wall(start_x=0, start_y=0, end_x=10, end_y=0, id="w1")
    #     empty_building.walls = {"w1": w1}
    #
    #     room = Room("Line", 10, 0, 3, 0, 0, wall_ids=["w1"])
    #
    #     # Середина відрізка (0,0)-(10,0) -> (5,0)
    #     assert room.get_center(empty_building) == (5.0, 0.0)

    def test_no_valid_walls_raises_error(self, empty_building):
        """Якщо у кімнати немає жодної дійсної стіни в будівлі -> помилка."""
        room = Room("Ghost", 5, 5, 3, 0, 0, wall_ids=["ghost_1", "ghost_2"])

        # building.walls порожній
        with pytest.raises(ValueError, match="Кімната не має валідних стін"):
            room.get_center(empty_building)

    def test_center_priority_over_room_coordinates(self, empty_building):
        """
        Перевірка, що метод рахує саме по СТІНАХ, а не бере room.x/room.y.
        """
        # Стіна стоїть на координатах 100-110
        w1 = Wall(start_x=100, start_y=100, end_x=110, end_y=100, id="w1")
        empty_building.walls = {"w1": w1}

        # А в об'єкті Room записано x=0, y=0 (старі дані)
        room = Room("Moved Room", 10, 10, 3, x=0, y=0, wall_ids=["w1"])

        cx, cy = room.get_center(empty_building)

        # Очікуємо 105 (середина стіни), а не 0 (координата кімнати)
        assert cx == 105.0
        assert cy == 100.0
