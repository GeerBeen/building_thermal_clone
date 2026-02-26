import pytest
import uuid
from bulding_compounds.wall import Wall, Material, Opening


class TestWallInitialization:

    def test_create_valid_wall(self):
        """Тест створення коректної стіни."""
        wall = Wall(start_x=0, start_y=0, end_x=10, end_y=0, height=3.0)

        assert wall.start_x == 0
        assert wall.end_x == 10
        assert wall.height == 3.0
        assert wall.length == 10.0
        assert isinstance(wall.id, str)
        assert len(wall.id) == 8

    def test_default_id_generation(self):
        """Тест, що ID генеруються унікальними."""
        wall1 = Wall(start_x=0, start_y=0, end_x=1, end_y=1)
        wall2 = Wall(start_x=0, start_y=0, end_x=1, end_y=1)
        assert wall1.id != wall2.id

    def test_wall_with_coordinates_negative(self):
        """Тест, що координати можуть бути від'ємними (головне, щоб була довжина)."""
        # Стіна від (-5, -5) до (-5, 0)
        wall = Wall(start_x=-5, start_y=-5, end_x=-5, end_y=0)
        assert wall.length == 5.0

    def test_wall_with_material_and_openings(self):
        """Тест передачі матеріалів та отворів."""
        mat = Material(name="Brick")
        op = Opening()
        wall = Wall(start_x=0, start_y=0, end_x=5, end_y=0, base_material=mat, openings=[op])

        assert wall.base_material == mat
        assert len(wall.openings) == 1
        assert wall.openings[0] == op


class TestWallValidation:

    def test_height_zero_raises_error(self):
        """Стіна з висотою 0 має викликати помилку."""
        with pytest.raises(ValueError, match="Height must be greater than 0"):
            Wall(start_x=0, start_y=0, end_x=10, end_y=0, height=0)

    def test_height_negative_raises_error(self):
        """Стіна з від'ємною висотою має викликати помилку."""
        with pytest.raises(ValueError, match="Height must be greater than 0"):
            Wall(start_x=0, start_y=0, end_x=10, end_y=0, height=-2.5)

    def test_zero_length_raises_error(self):
        """Стіна, де початок і кінець збігаються, має викликати помилку."""
        with pytest.raises(ValueError, match="Wall length cannot be 0"):
            Wall(start_x=5.5, start_y=5.5, end_x=5.5, end_y=5.5)

    def test_very_small_length_is_valid(self):
        """Дуже коротка стіна (але > 0) має бути допустимою."""
        wall = Wall(start_x=0, start_y=0, end_x=0.001, end_y=0)
        assert wall.length > 0