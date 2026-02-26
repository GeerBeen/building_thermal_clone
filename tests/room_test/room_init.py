import pytest
from bulding_compounds.room import Room
from bulding_compounds.hvac import HVACDevice, HVACType


class TestRoomInitialization:

    def test_create_valid_room(self):
        """Створення стандартної кімнати."""
        room = Room(
            name="Living Room",
            width=5.0,
            length=4.0,
            height=3.0,
            x=0, y=0
        )
        assert room.width == 5.0
        assert len(room.wall_ids) == 4  # Перевірка дефолтного значення
        assert len(room.id) == 8

    def test_room_negative_coordinates_ok(self):
        """Координати розташування можуть бути мінусовими."""
        room = Room("Basement", width=3, length=3, height=2.5, x=-10, y=-5)
        assert room.x == -10
        assert room.y == -5


class TestRoomValidation:

    def test_empty_name(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Room("", 4, 4, 3, 0, 0)

    @pytest.mark.parametrize("invalid_dim", [0, -5])
    def test_invalid_width(self, invalid_dim):
        with pytest.raises(ValueError, match="width must be > 0"):
            Room("Bad Room", width=invalid_dim, length=4, height=3, x=0, y=0)

    @pytest.mark.parametrize("invalid_dim", [0, -1])
    def test_invalid_length(self, invalid_dim):
        with pytest.raises(ValueError, match="length must be > 0"):
            Room("Bad Room", width=4, length=invalid_dim, height=3, x=0, y=0)

    def test_invalid_height(self):
        with pytest.raises(ValueError, match="height must be > 0"):
            Room("Bad Room", width=4, length=4, height=0, x=0, y=0)


class TestRoomHVACIntegration:

    @pytest.fixture
    def heater(self):
        return HVACDevice("Heater 1", HVACType.HEATER, power_heating=1000)

    def test_add_hvac_device(self, heater):
        """Тест додавання пристрою до кімнати."""
        room = Room("Bedroom", 4, 4, 3, 0, 0)
        assert len(room.hvac_devices) == 0

        room.add_hvac(heater)

        assert len(room.hvac_devices) == 1
        assert room.hvac_devices[0].name == "Heater 1"

    def test_initial_devices_list(self, heater):
        """Можна передати список девайсів одразу при створенні."""
        room = Room("Kitchen", 3, 3, 3, 0, 0, hvac_devices=[heater])
        assert len(room.hvac_devices) == 1
        assert room.hvac_devices[0] == heater
