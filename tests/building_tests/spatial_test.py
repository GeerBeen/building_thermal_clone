import pytest
from building import Building, Room, Wall


class TestBuildingSpatialAnalysis:

    @pytest.fixture
    def room_10x5(self):
        """
        Створює кімнату 10x5 (Ширина x Довжина).
        Координати: (0,0) -> (10,0) -> (10,5) -> (0,5).
        Центр: (5, 2.5).
        """
        b = Building()

        # Стіни
        w_s = Wall(0, 0, 10, 0, id="S")  # Південь (South)
        w_e = Wall(10, 0, 10, 5, id="E")  # Схід (East)
        w_n = Wall(10, 5, 0, 5, id="N")  # Північ (North)
        w_w = Wall(0, 5, 0, 0, id="W")  # Захід (West)

        b.walls = {"S": w_s, "E": w_e, "N": w_n, "W": w_w}

        # Кімната
        room = Room("Main", 10, 5, 3, 0, 0, wall_ids=["S", "E", "N", "W"])
        b.rooms[room.id] = room

        # Лінкуємо стіни до кімнати (це перевіряється в методі get_wall_direction)
        for w in b.walls.values():
            w.room_ids.append(room.id)

        return b, room.id

    def test_get_wall_direction_cardinal(self, room_10x5):
        """Перевірка визначення сторін світу (N, S, E, W)."""
        building, room_id = room_10x5

        # South: Центр стіни (5, 0). Вектор до центру (5, 2.5) -> (0, -2.5). Y < 0 -> S
        assert building.get_wall_direction("S", room_id) == "S"

        # North: Центр стіни (5, 5). Вектор (0, 2.5). Y > 0 -> N
        assert building.get_wall_direction("N", room_id) == "N"

        # East: Центр стіни (10, 2.5). Вектор (5, 0). X > 0 -> E
        assert building.get_wall_direction("E", room_id) == "E"

        # West: Центр стіни (0, 2.5). Вектор (-5, 0). X < 0 -> W
        assert building.get_wall_direction("W", room_id) == "W"

    def test_get_wall_direction_error(self, room_10x5):
        """Помилка, якщо стіна не належить кімнаті."""
        building, room_id = room_10x5

        alien_wall = Wall(100, 100, 105, 100, id="alien")
        building.walls["alien"] = alien_wall
        # Ми не додали room_id в alien_wall.room_ids

        with pytest.raises(ValueError, match="Ця кімната не належить до стіни"):
            building.get_wall_direction("alien", room_id)

    def test_calculate_room_dimensions_standard(self, room_10x5):
        """Розрахунок габаритів для прямокутної кімнати."""
        building, room_id = room_10x5

        width, length = building.calculate_room_dimensions(room_id)

        # Max X (10) - Min X (0) = 10
        assert width == 10.0
        # Max Y (5) - Min Y (0) = 5
        assert length == 5.0

    def test_calculate_room_dimensions_updated(self, room_10x5):
        """
        Якщо пересунути стіну, розміри мають перерахуватися.
        """
        building, room_id = room_10x5

        # Зміщуємо східну стіну з X=10 на X=15
        building.walls["E"].start_x = 15
        building.walls["E"].end_x = 15

        # Також треба оновити кінці суміжних стін, щоб bounding box був правильним
        building.walls["S"].end_x = 15
        building.walls["N"].start_x = 15

        width, length = building.calculate_room_dimensions(room_id)
        assert width == 15.0
        assert length == 5.0

    def test_calculate_dimensions_missing_room(self):
        """Якщо кімнати немає, повертаємо 0,0."""
        b = Building()
        w, l = b.calculate_room_dimensions("missing_id")
        assert w == 0.0
        assert l == 0.0

    def test_calculate_dimensions_no_walls(self):
        """Якщо у кімнати видалили всі стіни, розміри 0,0."""
        b = Building()
        r = Room("Empty", 10, 10, 3, 0, 0)
        b.rooms[r.id] = r
        # wall_ids порожній

        w, l = b.calculate_room_dimensions(r.id)
        assert w == 0.0
        assert l == 0.0
