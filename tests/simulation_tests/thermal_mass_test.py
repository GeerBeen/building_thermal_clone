import pytest
from simulation.thermal_sim import ThermalSimulation, Building, Room, AIR_DENSITY, AIR_SPECIFIC_HEAT
from bulding_compounds.wall import Wall, Material
from bulding_compounds.opening import Opening, OpeningTech


class TestThermalMassCalculation:

    @pytest.fixture
    def concrete(self):
        return Material(
            name="Concrete",
            thickness=0.1,  # 10 см
            density=2400,  # кг/м3
            specific_heat=1000  # Дж/кгК
        )

    @pytest.fixture
    def setup_room(self, concrete):
        """Кімната 1x1x1 (Куб) для простих розрахунків."""
        b = Building()
        # Створюємо кімнату з явними стінами, щоб розрахунки працювали
        room = Room("Box", 1, 1, 1, 0, 0, id="r1")
        b.rooms["r1"] = room

        # 4 стіни 1x1
        for i in range(4):
            w = Wall(start_x=0, start_y=0, end_x=1, end_y=0, height=1,
                     base_material=concrete, id=f"w{i}", room_ids=["r1"])
            b.walls[f"w{i}"] = w
            room.wall_ids.append(f"w{i}")

        # Патчимо calculate_room_dimensions, щоб не залежати від складної геометрії тут
        # Або просто налаштуємо стіни так, щоб геометрія рахувалась.
        # Простіше замокати calculate_room_dimensions.
        b.calculate_room_dimensions = lambda rid: (1.0, 1.0)

        sim = ThermalSimulation(b)
        return sim, room, concrete

    def test_air_thermal_mass(self, setup_room):
        """
        Перевірка внеску повітря.
        Об'єм = 1 * 1 * 1 = 1 м3.
        C_air = 1 * 1.2 * 1005 = 1206 Дж/К.
        """
        sim, room, concrete = setup_room

        # Відключаємо стіни (робимо їх невагомими)
        concrete.density = 0

        c_total = sim._calculate_room_thermal_mass(room)

        expected_air = 1 * AIR_DENSITY * AIR_SPECIFIC_HEAT
        assert c_total == pytest.approx(expected_air)

    def test_walls_thermal_mass(self, setup_room):
        """
        Перевірка внеску стін.
        Стіна: 1x1 м, товщина 0.1 м -> Об'єм 0.1 м3.
        Маса 1 стіни: 0.1 * 2400 = 240 кг.
        C 1 стіни (повної): 240 * 1000 = 240,000 Дж/К.
        Враховуючи фактор 0.5 -> 120,000 Дж/К.
        Всього 4 стіни -> 480,000 Дж/К.

        Плюс повітря (1206).
        Разом: 481,206.
        """
        sim, room, concrete = setup_room

        c_total = sim._calculate_room_thermal_mass(room)

        expected_walls = 4 * (1 * 1 * 0.1 * 2400 * 1000 * 0.5)
        expected_air = 1 * 1.2 * 1005

        assert c_total == pytest.approx(expected_walls + expected_air, rel=0.01)

    def test_openings_reduce_mass(self, setup_room):
        """
        Вікна зменшують масу стіни.
        Додаємо вікно на всю стіну (1x1).
        Ця стіна тепер має масу 0 (бетону немає).
        """
        sim, room, concrete = setup_room

        # Беремо першу стіну
        w0 = sim.building.walls["w0"]

        # Додаємо величезне вікно 1x1 (OpeningTech не важливий для маси)
        op = Opening(tech=OpeningTech(), width=1.0, height=1.0)
        w0.openings.append(op)

        # Тепер внесок стін має зменшитись на 1 стіну (120,000)
        c_total = sim._calculate_room_thermal_mass(room)

        expected_walls = 3 * (1 * 1 * 0.1 * 2400 * 1000 * 0.5)  # Тільки 3 стіни
        expected_air = 1206

        assert c_total == pytest.approx(expected_walls + expected_air, rel=0.01)

    def test_minimum_safety_limit(self, setup_room):
        """
        Перевірка запобіжника max(..., 1000.0).
        Робимо кімнату майже вакуумною.
        """
        sim, room, concrete = setup_room

        # Ставимо нульові параметри
        concrete.density = 0
        concrete.specific_heat = 0
        # Об'єм повітря дуже малий
        sim.building.calculate_room_dimensions = lambda rid: (0.001, 0.001)

        c_total = sim._calculate_room_thermal_mass(room)

        # Розрахунок дасть ~0, але функція має повернути 1000
        assert c_total == 1000.0