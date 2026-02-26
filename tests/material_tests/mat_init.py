import pytest
from bulding_compounds.material import Material  # Заміни на правильний імпорт


class TestMaterialPhysics:

    def test_concrete_calculation(self):
        """
        Тест розрахунку для бетону.
        Параметри:
        - Товщина: 0.2 м
        - Лямбда: 2.0 Вт/(м·К)

        R_layer = 0.2 / 2.0 = 0.1
        R_total = 0.1 + 0.17 = 0.27
        U = 1 / 0.27 ≈ 3.7037... -> округлюємо до 3.704
        """
        concrete = Material(
            name="Concrete",
            thickness=0.2,
            conductivity=2.0,
            density=2400,
            specific_heat=1000
        )

        # Перевіряємо U
        assert concrete.U == 3.704

        # Перевіряємо теплову масу (2400 * 0.2 * 1000 = 480,000)
        assert concrete.thermal_mass == 480_000

    def test_insulation_calculation(self):
        """
        Тест для утеплювача (мінвата).
        - Товщина: 0.1 м
        - Лямбда: 0.04 Вт/(м·К)

        R_layer = 0.1 / 0.04 = 2.5
        R_total = 2.5 + 0.17 = 2.67
        U = 1 / 2.67 ≈ 0.3745... -> 0.375
        """
        wool = Material(name="Rockwool", thickness=0.1, conductivity=0.04)
        assert wool.U == 0.375

    def test_default_values(self):
        """Перевірка дефолтного матеріалу."""
        mat = Material()
        # R = 1/1 = 1; R_tot = 1.17; U = 1/1.17 = 0.855
        assert mat.U == 0.855
        assert mat.thickness == 1.0


class TestMaterialValidation:

    def test_zero_thickness_raises_error(self):
        with pytest.raises(ValueError, match="Thickness must be > 0"):
            Material(thickness=0)

    def test_negative_conductivity_raises_error(self):
        with pytest.raises(ValueError, match="Conductivity must be > 0"):
            Material(conductivity=-0.5)

    def test_zero_conductivity_raises_error(self):
        with pytest.raises(ValueError, match="Conductivity must be > 0"):
            Material(conductivity=0)

    @pytest.mark.parametrize("invalid_val", [0, -100])
    def test_density_invalid(self, invalid_val):
        with pytest.raises(ValueError, match="Density must be > 0"):
            Material(density=invalid_val)

    @pytest.mark.parametrize("invalid_val", [0, -500])
    def test_specific_heat_invalid(self, invalid_val):
        with pytest.raises(ValueError, match="Specific heat must be > 0"):
            Material(specific_heat=invalid_val)

    def test_empty_name(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Material(name="")


class TestMaterialBehavior:

    def test_unique_ids(self):
        m1 = Material()
        m2 = Material()
        assert m1.id != m2.id

    def test_property_updates(self):
        """Якщо змінити товщину, U має перерахуватися."""
        mat = Material(thickness=0.1, conductivity=0.1)
        # R=1, Rtot=1.17, U=0.855
        assert mat.U == 0.855

        # Змінюємо товщину на дуже велику
        mat.thickness = 10.0
        # R=100, Rtot=100.17, U ~ 0.01
        assert mat.U < 0.1
