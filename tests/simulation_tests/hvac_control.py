import pytest
from simulation.thermal_sim import ThermalSimulation, Building, Room
from bulding_compounds.hvac import HVACDevice, HVACType
from simulation.controls import RoomControlProfile, ControlMode



# --- Fixtures ---

@pytest.fixture
def hvac_setup():
    """Сеттап: 1 кімната, 1 обігрівач (1 кВт), 1 кондиціонер (1 кВт)."""
    b = Building()

    heater = HVACDevice("Heater", HVACType.HEATER, power_heating=1000)
    cooler = HVACDevice("AC", HVACType.COOLER, power_cooling=1000)

    room = Room("R1", 10, 10, 3, 0, 0, id="r1", hvac_devices=[heater, cooler])
    b.rooms["r1"] = room

    sim = ThermalSimulation(b)
    # Початковий час 0
    sim.current_time_sec = 0

    return sim, room


# --- Tests ---

class TestHVACLogic:

    def test_always_off(self, hvac_setup):
        """Режим ALWAYS_OFF нічого не вмикає."""
        sim, room = hvac_setup
        profile = RoomControlProfile(mode=ControlMode.ALWAYS_OFF)
        sim.control_profiles[room.id] = profile

        # Перевіряємо при будь-якій температурі
        assert sim._calculate_hvac_power(room, -50) == 0.0
        assert sim._calculate_hvac_power(room, 50) == 0.0

    def test_always_on_heating_priority(self, hvac_setup):
        """
        Режим ALWAYS_ON.
        Ми видалимо кондиціонер з кімнати для цього тесту,
        щоб перевірити саме нагрів.
        """
        sim, room = hvac_setup

        # Залишаємо тільки Хітер
        room.hvac_devices = [d for d in room.hvac_devices if d.device_type == HVACType.HEATER]

        profile = RoomControlProfile(mode=ControlMode.ALWAYS_ON)
        sim.control_profiles[room.id] = profile

        power = sim._calculate_hvac_power(room, 20.0)
        assert power == 1000.0

    def test_always_on_cooling(self, hvac_setup):
        """Додатковий тест: Always On для кондиціонера."""
        sim, room = hvac_setup

        # Залишаємо тільки Кулер
        room.hvac_devices = [d for d in room.hvac_devices if d.device_type == HVACType.COOLER]

        profile = RoomControlProfile(mode=ControlMode.ALWAYS_ON)
        sim.control_profiles[room.id] = profile

        power = sim._calculate_hvac_power(room, 20.0)
        assert power == -1000.0

    def test_thermostat_heating(self, hvac_setup):
        """
        Термостат: Цільова 21. Поточна 20. (Холодно).
        Має увімкнутись нагрів (+1000).
        """
        sim, room = hvac_setup
        # Target 21
        profile = RoomControlProfile(mode=ControlMode.THERMOSTAT, target_temp=21.0)
        sim.control_profiles[room.id] = profile

        # 20 < 21 - 0.5 (умова: current < target - 0.5 -> 20 < 20.5 -> True)
        power = sim._calculate_hvac_power(room, 20.0)
        assert power == 1000.0

    def test_thermostat_cooling(self, hvac_setup):
        """
        Термостат: Цільова 21. Поточна 25. (Жарко).
        Має увімкнутись охолодження (-1000).
        """
        sim, room = hvac_setup
        profile = RoomControlProfile(mode=ControlMode.THERMOSTAT, target_temp=21.0)
        sim.control_profiles[room.id] = profile

        # 25 > 21 -> True для гілки охолодження
        power = sim._calculate_hvac_power(room, 25.0)
        assert power == -1000.0

    def test_thermostat_deadzone(self, hvac_setup):
        """
        Термостат: Цільова 21. Поточна 21.0 (Норма).
        Нічого не має працювати (мертва зона).
        """
        sim, room = hvac_setup
        profile = RoomControlProfile(mode=ControlMode.THERMOSTAT, target_temp=21.0)
        sim.control_profiles[room.id] = profile

        # 21 не менше 20.5 і не більше 21 (умова current > target)
        # У твоєму коді: elif current > target (без +0.5).
        # Перевіримо точну рівність: 21 > 21 -> False.
        power = sim._calculate_hvac_power(room, 21.0)
        assert power == 0.0

    def test_cyclic_mode_timing(self, hvac_setup):
        """
        Цикл: 1 година ВКЛ, 1 година ВИКЛ.
        ВИПРАВЛЕННЯ: Залишаємо тільки обігрівач, щоб уникнути конфлікту (+1000 -1000 = 0).
        """
        sim, room = hvac_setup
        # --- FIX START ---
        room.hvac_devices = [d for d in room.hvac_devices if d.device_type == HVACType.HEATER]
        # --- FIX END ---

        profile = RoomControlProfile(
            mode=ControlMode.CYCLIC,
            cycle_on_hours=1,
            cycle_off_hours=1,
            time_offset_hours=0
        )
        sim.control_profiles[room.id] = profile

        # 1. Початок (00:00) -> ON -> +1000
        sim.current_time_sec = 0
        assert sim._calculate_hvac_power(room, 20) == 1000.0

        # 2. 30 хвилин (00:30) -> ON -> +1000
        sim.current_time_sec = 1800
        assert sim._calculate_hvac_power(room, 20) == 1000.0

        # 3. 1 година 1 хвилина (01:01) -> OFF -> 0
        sim.current_time_sec = 3660
        assert sim._calculate_hvac_power(room, 20) == 0.0

        # 4. 2 години 1 хвилина (02:01) -> Новий цикл ON -> +1000
        sim.current_time_sec = 7260
        assert sim._calculate_hvac_power(room, 20) == 1000.0

    def test_cyclic_mode_offset(self, hvac_setup):
        """
        Цикл з offset.
        ВИПРАВЛЕННЯ: Також прибираємо кондиціонер.
        """
        sim, room = hvac_setup
        # --- FIX START ---
        room.hvac_devices = [d for d in room.hvac_devices if d.device_type == HVACType.HEATER]
        # --- FIX END ---

        profile = RoomControlProfile(
            mode=ControlMode.CYCLIC,
            cycle_on_hours=1,
            cycle_off_hours=1,
            time_offset_hours=0.5
        )
        sim.control_profiles[room.id] = profile

        # t=0. Effective time = 0.5h. ON
        sim.current_time_sec = 0
        assert sim._calculate_hvac_power(room, 20) == 1000.0

        # t=0.6h (36 min). Effective time = 1.1h. OFF
        sim.current_time_sec = int(0.6 * 3600)
        assert sim._calculate_hvac_power(room, 20) == 0.0