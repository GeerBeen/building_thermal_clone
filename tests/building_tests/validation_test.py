import pytest
from building import Building
from bulding_compounds.wall import Wall, walls_intersect_properly


# Helper для імітації методу is_equeal_wall (якщо його немає в класі Wall при запуску тестів)
# Ти можеш видалити цей блок, якщо метод точно є в твоєму класі Wall.
def mock_is_equal(self, other):
    # Порівнюємо координати (ігноруючи напрямок)
    same_dir = (self.start_x == other.start_x and self.start_y == other.start_y and
                self.end_x == other.end_x and self.end_y == other.end_y)
    rev_dir = (self.start_x == other.end_x and self.start_y == other.end_y and
               self.end_x == other.start_x and self.end_y == other.start_y)
    return same_dir or rev_dir


# Патчимо клас Wall для тестів
Wall.is_equeal_wall = mock_is_equal


class TestBuildingValidation:

    @pytest.fixture
    def simple_building(self):
        b = Building()
        # Стіна від (0,0) до (10,0)
        w1 = Wall(0, 0, 10, 0, id="w1")
        b.walls["w1"] = w1
        return b

    def test_find_wall_with_geometry_exact_match(self, simple_building):
        """Знаходить стіну, якщо координати ідентичні."""
        # Створюємо нову стіну-копію (інший ID, ті самі координати)
        duplicate = Wall(0, 0, 10, 0, id="new")

        found = simple_building.find_wall_with_geometry(duplicate)
        assert found is not None
        assert found.id == "w1"  # Знайшло оригінал

    def test_find_wall_with_geometry_reversed(self, simple_building):
        """Знаходить стіну, навіть якщо точки задані задом наперед."""
        # (10,0) -> (0,0) це та сама стіна фізично
        reversed_wall = Wall(10, 0, 0, 0, id="rev")

        found = simple_building.find_wall_with_geometry(reversed_wall)
        assert found is not None
        assert found.id == "w1"

    def test_find_wall_fails_on_different(self, simple_building):
        """Не знаходить, якщо координати відрізняються."""
        other = Wall(0, 1, 10, 1, id="other")  # Зсув по Y
        found = simple_building.find_wall_with_geometry(other)
        assert found is None

    def test_intersection_check_valid(self, simple_building):
        """Перевірка правильного перетину (L-з'єднання)."""
        # Нова стіна примикає до кінця існуючої: (10,0) -> (10,10)
        new_wall = Wall(10, 0, 10, 10)

        is_ok = simple_building.check_if_walls_intersection_right(new_wall)
        assert is_ok is True

    def test_intersection_check_invalid_crossing(self, simple_building):
        """Перевірка неправильного перетину (X-перетин)."""
        # Існуюча: (0,0)->(10,0). Нова: (5,-5)->(5,5). Перетин у (5,0).
        bad_wall = Wall(5, -5, 5, 5)

        is_ok = simple_building.check_if_walls_intersection_right(bad_wall)
        assert is_ok is False

    def test_intersection_check_invalid_overlap(self, simple_building):
        """Перевірка накладання стін."""
        # Існуюча: (0,0)->(10,0). Нова: (2,0)->(8,0).
        overlap_wall = Wall(2, 0, 8, 0)

        is_ok = simple_building.check_if_walls_intersection_right(overlap_wall)
        assert is_ok is False
