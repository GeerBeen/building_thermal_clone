import pytest
from simulation.thermal_sim import ThermalSimulation, Building
from bulding_compounds.wall import Wall, Material
from bulding_compounds.room import Room
from bulding_compounds.opening import Opening, OpeningTech, OpeningCategory


@pytest.fixture
def mat_brick():
    # U = 1 / (0.5/0.5 + 0.17) = 1/1.17 ~ 0.85
    # Для простоти розрахунків у тестах, ми можемо замокати властивість U
    m = Material(name="TestBrick", thickness=0.5, conductivity=0.5)
    return m


@pytest.fixture
def tech_glass():
    return OpeningTech(name="Glass", U=2.0, g=0.7, category=OpeningCategory.WINDOW)


@pytest.fixture
def simulation_setup():
    """Піднімає симуляцію з базовою будівлею."""
    b = Building()
    sim = ThermalSimulation(b)
    return sim, b


# Хелпер для динамічного додавання властивості area_net, якщо її немає в класі
def get_area_net(self):
    total_area = (self.end_x - self.start_x) * self.height  # спрощено для горизонтальної стіни
    openings_area = sum(op.area for op in self.openings)
    return total_area - openings_area


@pytest.fixture(autouse=True)
def patch_wall_area_net(monkeypatch):
    """Автоматично додає властивість area_net до класу Wall для тестів."""
    # raising=False дозволяє додавати нові атрибути, яких не було в класі
    monkeypatch.setattr(Wall, "area_net", property(get_area_net), raising=False)

    # Додаємо area
    monkeypatch.setattr(Wall, "area", property(lambda self: (self.end_x - self.start_x) * self.height), raising=False)


# --- Tests ---

class TestHeatTransmission:

    def test_external_wall_heat_loss(self, simulation_setup, mat_brick, monkeypatch):
        """
        Тест втрат тепла через одну зовнішню стіну.
        Внутр. темп: 20, Вулиця: 0. Delta T = -20.
        """
        sim, b = simulation_setup

        # --- FIX START ---
        # Замінюємо властивість U на фіксоване значення 0.5 для всіх матеріалів у цьому тесті
        monkeypatch.setattr(Material, "U", 0.5)
        # --- FIX END ---

        wall = Wall(0, 0, 10, 0, height=3.0, base_material=mat_brick, id="w1", room_ids=["r1"])
        b.walls["w1"] = wall

        room = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w1"])
        b.rooms["r1"] = room

        # Тепер U точно 0.5
        flow = sim._calculate_transmission_heat_flow(room, current_temp=20.0, outdoor_temp=0.0)

        expected_flow = 0.5 * 30.0 * (-20.0)  # -300.0

        assert flow == pytest.approx(expected_flow, rel=0.001)
        assert flow < 0

    def test_internal_wall_heat_transfer(self, simulation_setup, mat_brick):
        """
        Тест перетоку тепла між кімнатами.
        R1 (20°C) -> Стіна -> R2 (10°C).
        Для R1 це втрата тепла (потік від'ємний).
        """
        sim, b = simulation_setup

        # Спільна стіна 10x3 = 30 м2
        wall = Wall(0, 0, 10, 0, height=3.0, base_material=mat_brick, id="w_shared", room_ids=["r1", "r2"])
        b.walls["w_shared"] = wall

        room1 = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w_shared"])

        # Налаштовуємо температуру сусіда
        sim.current_temperatures["r2"] = 10.0

        flow = sim._calculate_transmission_heat_flow(room1, current_temp=20.0, outdoor_temp=-5.0)

        # Вулична температура (-5) має ігноруватися, береться темп R2 (10)
        # dT = 10 - 20 = -10
        expected_flow = mat_brick.U * 30.0 * (-10.0)

        assert flow == pytest.approx(expected_flow)

    def test_wall_with_window(self, simulation_setup, mat_brick, tech_glass):
        """
        Стіна з вікном. Потік сумується.
        Стіна: 10x3 = 30м2.
        Вікно: 2x1 = 2м2.
        Чиста стіна: 28м2.
        """
        sim, b = simulation_setup

        wall = Wall(0, 0, 10, 0, height=3.0, base_material=mat_brick, id="w1", room_ids=["r1"])

        # Додаємо вікно
        op = Opening(tech=tech_glass, width=2.0, height=1.0)
        wall.openings.append(op)

        b.walls["w1"] = wall
        room = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w1"])

        # dT = -10 (вулиця 0, дім 10)
        dT = -10.0

        flow = sim._calculate_transmission_heat_flow(room, current_temp=10.0, outdoor_temp=0.0)

        # Розрахунок компонентів
        flow_wall = mat_brick.U * 28.0 * dT  # 28 м2 цегли
        flow_window = tech_glass.U * 2.0 * dT  # 2 м2 скла

        assert flow == pytest.approx(flow_wall + flow_window)

    def test_equilibrium_zero_flow(self, simulation_setup, mat_brick):
        """Якщо температури рівні, потік має бути 0."""
        sim, b = simulation_setup
        wall = Wall(0, 0, 10, 0, height=3, base_material=mat_brick, id="w1", room_ids=["r1"])
        b.walls["w1"] = wall
        room = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w1"])

        # Temp In = Temp Out = 20
        flow = sim._calculate_transmission_heat_flow(room, current_temp=20.0, outdoor_temp=20.0)

        assert flow == 0.0

    def test_missing_neighbor_fallback(self, simulation_setup, mat_brick):
        """
        Едж-кейс: Стіна позначена як внутрішня (2 ID), але сусідньої кімнати
        немає в списку current_temperatures (наприклад, глюк ініціалізації).
        Має використатись outdoor_temp.
        """
        sim, b = simulation_setup
        wall = Wall(0, 0, 10, 0, height=3, base_material=mat_brick, id="w_sh", room_ids=["r1", "missing_r2"])
        b.walls["w_sh"] = wall
        room = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w_sh"])

        # У sim.current_temperatures пусто

        # Тімпература кімнати 20, вулиця -5.
        # Оскільки сусіда немає, dT має бути -5 - 20 = -25
        flow = sim._calculate_transmission_heat_flow(room, current_temp=20.0, outdoor_temp=-5.0)

        expected_flow = mat_brick.U * 30.0 * (-25.0)
        assert flow == pytest.approx(expected_flow)
