import pytest
from bulding_compounds.opening import Opening, OpeningTech, OpeningCategory


@pytest.fixture
def standard_window_tech():
    return OpeningTech(
        name="Standard Glass",
        U=1.2,
        g=0.6,
        category=OpeningCategory.WINDOW
    )


@pytest.fixture
def standard_door_tech():
    return OpeningTech(
        name="Wood Door",
        U=2.0,
        g=0.0,
        category=OpeningCategory.DOOR
    )


# --- Tests for OpeningTech ---

class TestOpeningTech:

    def test_valid_tech(self, standard_window_tech):
        assert standard_window_tech.name == "Standard Glass"
        assert standard_window_tech.U == 1.2

    def test_u_value_negative_raises_error(self):
        with pytest.raises(ValueError, match="U-value cannot be negative"):
            OpeningTech(name="Bad", U=-0.5, g=0.5, category=OpeningCategory.WINDOW)

    @pytest.mark.parametrize("invalid_g", [-0.1, 1.1, 5.0])
    def test_g_factor_out_of_bounds(self, invalid_g):
        """Перевірка граничних значень для g (має бути 0-1)."""
        with pytest.raises(ValueError, match="Solar factor"):
            OpeningTech(name="Bad G", U=1.0, g=invalid_g, category=OpeningCategory.WINDOW)

    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            OpeningTech(name="", U=1.0, g=0.5, category=OpeningCategory.WINDOW)


# --- Tests for Opening ---

class TestOpening:

    def test_create_valid_opening(self, standard_window_tech):
        op = Opening(tech=standard_window_tech, width=2.0, height=1.5)

        assert op.width == 2.0
        assert op.height == 1.5
        assert op.area == 3.0  # 2.0 * 1.5
        assert len(op.id) == 8

    def test_heat_loss_calculation(self, standard_window_tech):
        """Перевірка формули тепловтрат: U * Area."""
        # U=1.2, Area=2*1=2.0 -> HeatLoss = 2.4
        op = Opening(tech=standard_window_tech, width=2.0, height=1.0)

        # Використовуємо pytest.approx для порівняння float
        assert op.heat_loss_coefficient == pytest.approx(2.4)

    def test_opening_dimensions_zero_or_negative(self, standard_window_tech):
        """Негативні тести на розміри."""
        with pytest.raises(ValueError, match="Width must be greater than 0"):
            Opening(tech=standard_window_tech, width=0, height=1)

        with pytest.raises(ValueError, match="Height must be greater than 0"):
            Opening(tech=standard_window_tech, width=1, height=-1)

    def test_invalid_tech_type(self):
        """Тест на той самий баг, де передавали Enum замість класу."""
        with pytest.raises(TypeError, match="tech must be an instance of OpeningTech"):
            # Передаємо Enum замість об'єкта OpeningTech
            Opening(tech=OpeningCategory.WINDOW, width=1, height=1)

    def test_changing_dimensions_updates_area(self, standard_window_tech):
        """Перевірка, що властивості динамічно оновлюються."""
        op = Opening(tech=standard_window_tech, width=1, height=1)
        assert op.area == 1.0

        op.width = 2
        assert op.area == 2.0
        assert op.heat_loss_coefficient == standard_window_tech.U * 2.0