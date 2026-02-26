import pytest
from building import Building, Room, Wall


class TestBuildingRoomDeletion:

    @pytest.fixture
    def building_one_room(self):
        """Будівля з однією кімнатою (4 унікальні стіни)."""
        b = Building()
        # Створюємо кімнату вручну, щоб контролювати ID
        room = Room("Solo", 10, 10, 3, 0, 0, id="r1")

        # 4 стіни, що належать тільки r1
        walls = []
        for i in range(4):
            w = Wall(id=f"w{i}", room_ids=["r1"])
            walls.append(w)
            b.walls[w.id] = w

        room.wall_ids = [w.id for w in walls]
        b.rooms["r1"] = room
        return b

    @pytest.fixture
    def building_two_rooms_shared(self):
        """
        Будівля з двома кімнатами (R1 і R2).
        Вони мають одну спільну стіну (Shared).
        Інші стіни - унікальні.
        """
        b = Building()

        # Спільна стіна
        w_shared = Wall(id="w_shared", room_ids=["r1", "r2"])
        b.walls["w_shared"] = w_shared

        # Унікальна стіна для R2 (наприклад, зовнішня)
        w_unique_r2 = Wall(id="w_r2_only", room_ids=["r2"])
        b.walls["w_r2_only"] = w_unique_r2

        # Інші стіни опустимо для спрощення, головне ці дві

        # Кімнати
        r1 = Room("R1", 10, 10, 3, 0, 0, id="r1", wall_ids=["w_shared"])
        r2 = Room("R2", 10, 10, 3, 10, 0, id="r2", wall_ids=["w_shared", "w_r2_only"])

        b.rooms["r1"] = r1
        b.rooms["r2"] = r2

        return b

    def test_delete_isolated_room(self, building_one_room):
        """
        Сценарій: Видаляємо єдину кімнату.
        Очікування: Кімната видалена, всі 4 стіни видалені (бо вони стали сиротами).
        """
        building_one_room.delete_room("r1")

        # Кімната зникла
        assert "r1" not in building_one_room.rooms
        assert len(building_one_room.rooms) == 0

        # Стіни зникли (clean up)
        assert len(building_one_room.walls) == 0

    def test_delete_room_keeps_shared_wall(self, building_two_rooms_shared):
        """
        Сценарій: Видаляємо R2, яка має спільну стіну з R1.
        Очікування:
        1. R2 видалена.
        2. Унікальна стіна R2 видалена.
        3. Спільна стіна ЗАЛИШИЛАСЬ.
        4. Спільна стіна більше не посилається на R2 (стала зовнішньою для R1).
        """
        b = building_two_rooms_shared

        b.delete_room("r2")

        # 1. R2 немає
        assert "r2" not in b.rooms
        assert "r1" in b.rooms  # R1 не зачепило

        # 2. Унікальна стіна видалена
        assert "w_r2_only" not in b.walls

        # 3. Спільна стіна існує
        assert "w_shared" in b.walls

        # 4. Перевірка посилань у спільній стіні
        shared_wall = b.walls["w_shared"]
        assert "r2" not in shared_wall.room_ids
        assert "r1" in shared_wall.room_ids
        assert len(shared_wall.room_ids) == 1  # Тепер вона належить тільки R1

    def test_delete_non_existent_room(self, building_one_room):
        """Спроба видалити неіснуючий ID викликає помилку."""
        with pytest.raises(ValueError, match="не знайдена"):
            building_one_room.delete_room("ghost_room")

    def test_data_inconsistency_resilience(self, building_one_room):
        """
        Сценарій: У кімнати в списку wall_ids є ID стіни, якої фізично немає в b.walls.
        Метод не повинен впасти з помилкою KeyError.
        """
        # Створюємо "бите" посилання
        room = building_one_room.rooms["r1"]
        room.wall_ids.append("missing_wall_id")

        # Видаляємо (має пройти успішно, ігноруючи missing_wall_id)
        building_one_room.delete_room("r1")

        assert len(building_one_room.rooms) == 0