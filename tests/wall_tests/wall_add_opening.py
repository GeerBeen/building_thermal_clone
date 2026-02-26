import pytest
from bulding_compounds.wall import Wall
from bulding_compounds.opening import Opening, OpeningTech, OpeningCategory


# --- Fixtures ---
@pytest.fixture
def base_wall():
    # Стіна довжиною 10м (0->10), висота 3м
    return Wall(start_x=0, start_y=0, end_x=10, end_y=0, height=3.0)


@pytest.fixture
def simple_window():
    # Технологія-заглушка
    tech = OpeningTech(name="Glass", U=1, g=0.5, category=OpeningCategory.WINDOW)
    return Opening(tech=tech, width=2.0, height=1.5)


class TestWallAddOpening:

    def test_add_valid_opening(self, base_wall, simple_window):
        """Тест успішного додавання одного вікна."""
        base_wall.add_opening(simple_window)
        assert len(base_wall.openings) == 1
        assert base_wall.openings[0] == simple_window

    def test_add_multiple_openings_success(self, base_wall, simple_window):
        """Тест додавання декількох вікон, що влазять у стіну."""
        # Довжина стіни 10м, додаємо 4 вікна по 2м = 8м (ок)
        for _ in range(4):
            base_wall.add_opening(simple_window)

        assert len(base_wall.openings) == 4

    def test_opening_too_tall_raises_error(self, base_wall, simple_window):
        """Помилка, якщо вікно вище за стіну."""
        simple_window.height = 3.5  # Стіна 3.0
        with pytest.raises(ValueError, match="більша за висоту стіни"):
            base_wall.add_opening(simple_window)

    def test_opening_exact_height_allowed(self, base_wall, simple_window):
        """Граничне значення: висота вікна дорівнює висоті стіни (має бути ок)."""
        simple_window.height = 3.0
        base_wall.add_opening(simple_window)
        assert len(base_wall.openings) == 1

    def test_opening_too_wide_single(self, base_wall, simple_window):
        """Помилка, якщо одне вікно ширше за стіну."""
        simple_window.width = 11.0  # Стіна 10.0
        with pytest.raises(ValueError, match="перевищує довжину стіни"):
            base_wall.add_opening(simple_window)

    def test_cumulative_width_exceeded(self, base_wall, simple_window):
        """Помилка, якщо сума ширин вікон перевищує довжину стіни."""
        # 1. Додаємо вікно 5м (залишилось 5м)
        large_window = Opening(tech=simple_window.tech, width=5.0, height=1.5)
        base_wall.add_opening(large_window)

        # 2. Додаємо ще 4м (залишилось 1м)
        medium_window = Opening(tech=simple_window.tech, width=4.0, height=1.5)
        base_wall.add_opening(medium_window)

        # 3. Спробуємо додати 2м (разом буде 11м > 10м) -> Помилка
        with pytest.raises(ValueError, match="Сумарна ширина отворів перевищує"):
            base_wall.add_opening(simple_window)  # width=2.0

    def test_exact_length_filled(self, base_wall, simple_window):
        """Граничне значення: сумарна ширина вікон точно дорівнює довжині стіни."""
        w1 = Opening(tech=simple_window.tech, width=5.0, height=1.0)
        w2 = Opening(tech=simple_window.tech, width=5.0, height=1.0)

        base_wall.add_opening(w1)
        base_wall.add_opening(w2)  # Має пройти, 5+5=10
        assert len(base_wall.openings) == 2
