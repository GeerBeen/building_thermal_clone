import pytest
from building import Building, Material, Room, Wall


class TestBuildingCreateInitialRoom:

    @pytest.fixture
    def empty_building(self):
        return Building()

    @pytest.fixture
    def concrete(self):
        return Material(name="Concrete", thickness=0.2)

    def test_create_valid_room_structure(self, empty_building, concrete):
        """
        Перевірка успішного створення базової кімнати.
        Перевіряємо кількість об'єктів та їх наявність у словниках.
        """
        room = empty_building.create_initial_room(
            x_len=10.0,
            y_len=5.0,
            height=3.0,
            material=concrete,
            name="Main Hall"
        )

        #  Кімната додалась у будівлю
        assert len(empty_building.rooms) == 1
        assert room.id in empty_building.rooms
        assert empty_building.rooms[room.id] == room

        #  Створилось рівно 4 стіни
        assert len(empty_building.walls) == 4
        assert len(room.wall_ids) == 4

        #  Перевірка параметрів кімнати
        assert room.width == 10.0
        assert room.length == 5.0
        assert room.height == 3.0

    def test_wall_geometry_and_topology(self, empty_building, concrete):
        """
        Перевірка координат стін.
        Код створює стіни проти годинникової стрілки: Південь -> Схід -> Північ -> Захід.
        """
        room = empty_building.create_initial_room(10, 5, 3, concrete)
        wall_ids = room.wall_ids

        # Отримуємо об'єкти стін
        w_south = empty_building.walls[wall_ids[0]]
        w_east = empty_building.walls[wall_ids[1]]
        w_north = empty_building.walls[wall_ids[2]]
        w_west = empty_building.walls[wall_ids[3]]

        # Перевірка координат (Loop check)
        # Південь: (0,0) -> (10,0)
        assert (w_south.start_x, w_south.start_y) == (0, 0)
        assert (w_south.end_x, w_south.end_y) == (10, 0)

        # Схід: (10,0) -> (10,5)
        assert (w_east.start_x, w_east.start_y) == (10, 0)
        assert (w_east.end_x, w_east.end_y) == (10, 5)

        # Північ: (10,5) -> (0,5)
        assert (w_north.start_x, w_north.start_y) == (10, 5)
        assert (w_north.end_x, w_north.end_y) == (0, 5)

        # Захід: (0,5) -> (0,0)
        assert (w_west.start_x, w_west.start_y) == (0, 5)
        assert (w_west.end_x, w_west.end_y) == (0, 0)

    def test_relationships_linking(self, empty_building, concrete):
        """
        Перевірка двосторонніх зв'язків:
        Room -> знає про Wall IDs
        Wall -> знає про Room ID
        Wall -> має правильний матеріал
        """
        room = empty_building.create_initial_room(5, 5, 3, concrete)

        for wall_id in room.wall_ids:
            wall = empty_building.walls[wall_id]

            # Стіна має посилатися на цю кімнату
            assert room.id in wall.room_ids
            assert len(wall.room_ids) == 1

            # Матеріал має бути переданий
            assert wall.base_material == concrete

            # Висота стіни має співпадати з висотою кімнати
            assert wall.height == room.height

    @pytest.mark.parametrize("x, y, h", [
        (0, 5, 3),  # x = 0
        (5, 0, 3),  # y = 0
        (5, 5, 0),  # h = 0
        (-1, 5, 3),  # negative
    ])
    def test_invalid_dimensions_raise_error(self, empty_building, concrete, x, y, h):
        """
        Негативні сценарії: нульові або від'ємні розміри мають викликати помилку.
        """
        with pytest.raises(ValueError, match="Розміри мають бути > 0"):
            empty_building.create_initial_room(x, y, h, concrete)
