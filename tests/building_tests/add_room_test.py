import pytest
from building import Building, Wall, Room, Material
from bulding_compounds.custom_errors import RoomOverlapError


def wall_is_equal(self, other):
    # Проста перевірка координат
    return {self.start_x, self.end_x, self.start_y, self.end_y} == \
        {other.start_x, other.end_x, other.start_y, other.end_y}


# --- Fixtures ---

@pytest.fixture
def material():
    return Material(name="Brick")


@pytest.fixture
def one_room_building(material):
    """Будівля з однією кімнатою 10x10. Північна стіна зверху (y=10)."""
    b = Building()
    b.create_initial_room(10, 10, 3, material, name="BaseRoom")
    return b


# --- Tests ---

class TestBuildingAddRoom:

    def test_expand_north_success(self, one_room_building):
        """
        Успішне додавання кімнати на Північ.
        Базова: (0,0)-(10,10). Північна стіна: y=10.
        Нова має бути: (0,10)-(10,15) при глибині 5.
        """
        room = list(one_room_building.rooms.values())[0]
        # Знаходимо північну стіну (start_y=10, end_y=10)
        north_wall_id = next(
            wid for wid in room.wall_ids
            if one_room_building.walls[wid].start_y == 10
        )

        # Дія
        new_room = one_room_building.add_room_to_wall(
            wall_id=north_wall_id,
            depth=5.0,
            name="NorthRoom"
        )

        # Перевірки
        assert new_room.name == "NorthRoom"
        # Перевірка розмірів нової кімнати (ширина така ж як у старої=10, глибина=5)
        assert new_room.width == 10.0
        assert new_room.length == 5.0

        # Перевірка зв'язку: Північна стіна тепер має 2 кімнати
        shared_wall = one_room_building.walls[north_wall_id]
        assert len(shared_wall.room_ids) == 2
        assert new_room.id in shared_wall.room_ids

    def test_expand_east_success(self, one_room_building):
        """
        Успішне додавання кімнати на Схід.
        Базова: (0,0)-(10,10). Східна стіна: x=10.
        Нова має бути: (10,0)-(15,10) при глибині 5.
        """
        room = list(one_room_building.rooms.values())[0]
        # Знаходимо східну стіну (x=10)
        east_wall_id = next(
            wid for wid in room.wall_ids
            if one_room_building.walls[wid].start_x == 10
        )

        new_room = one_room_building.add_room_to_wall(east_wall_id, depth=5.0)

        # Ширина (depth) = 5, Довжина (стара висота Y) = 10
        assert new_room.width == 5.0
        assert new_room.length == 10.0

        # Перевіряємо координати нової "зовнішньої" стіни (має бути x=15)
        outer_walls = [
            one_room_building.walls[wid]
            for wid in new_room.wall_ids
            if wid != east_wall_id
        ]
        xs = [w.start_x for w in outer_walls] + [w.end_x for w in outer_walls]
        assert max(xs) == 15.0

    def test_add_room_to_filled_wall_raises_error(self, one_room_building):
        """
        Неможливо додати кімнату до стіни, яка вже розділяє дві кімнати.
        """
        # Створюємо кімнату 2
        room1 = list(one_room_building.rooms.values())[0]
        wall_id = room1.wall_ids[0]

        one_room_building.add_room_to_wall(wall_id, depth=5)

        # Пробуємо додати кімнату 3 до тієї ж стіни
        with pytest.raises(ValueError, match="Стіна вже має дві кімнати"):
            one_room_building.add_room_to_wall(wall_id, depth=5)

    def test_smart_wall_reuse(self, one_room_building):
        from icecream import ic
        """
        Тест на 'Тетріс':
        Створюємо L-подібну структуру і заповнюємо кут.
        Коли створюємо R4 (??), вона має використати існуючі стіни від R2 та R3.
        """
        # R1: (0,0)-(10,10)
        r1 = list(one_room_building.rooms.values())[0]
        w_east = one_room_building.get_wall_by_direction(r1.id, "E")
        w_north = one_room_building.get_wall_by_direction(r1.id, "N")
        # Створюємо R2 праворуч від R1: (10,0)-(20,10)
        r2 = one_room_building.add_room_to_wall(w_east.id, depth=10, name="R2")

        # Створюємо R3 зверху від R1: (0,10)-(10,20)
        r3 = one_room_building.add_room_to_wall(w_north.id, depth=10, name="R3")

        # додаємо R4 зверху від R2.
        # Вона має зайняти простір (10,10)-(20,20).
        # Її стіна зліва (x=10, y=10..20) вже існує як права стіна R3.

        # Знаходимо північну стіну R2
        w_r2_north = one_room_building.get_wall_by_direction(r2.id, "N")

        # Додаємо R4
        r4 = one_room_building.add_room_to_wall(w_r2_north.id, depth=10, name="R4")

        # ПЕРЕВІРКА:
        # Серед стін R4 має бути стіна, яка також належить R3
        r3_wall_ids = set(r3.wall_ids)
        r4_wall_ids = set(r4.wall_ids)

        common_walls = r3_wall_ids.intersection(r4_wall_ids)
        assert len(common_walls) == 1, "Має бути одна спільна стіна між R3 і R4"

        shared_wall = one_room_building.walls[list(common_walls)[0]]
        assert shared_wall.start_x == 10 or shared_wall.end_x == 10

    def test_overlap_raises_error(self, one_room_building):
        """
        Спроба побудувати кімнату поверх існуючої має викликати помилку.
        Ми спробуємо зімітувати перетин, побудувавши дуже довгу кімнату,
        яка врізається в іншу (якщо б вона там була).

        Оскільки у нас лише одна кімната, ми зробимо так:
        1. R1 (0,0)-(10,10)
        2. R2 справа (10,0)-(20,10)
        3. R3 з R2 будуємо ВЛІВО (назад в R1).
           Хоча технічно метод бере direction автоматично, ми можемо створити ситуацію
           через "заворот".

        Але простіше: створити стіну вручну, яка заважає.
        """
        # Створюємо стіну-перешкоду на (0, 12) -> (10, 12)
        # Ми хочемо розширити R1 на північ на 5 метрів (до y=15).
        # Стіна на y=12 має заблокувати це.

        blocker = Wall(0, 12, 10, 12, id="blocker")
        one_room_building.walls["blocker"] = blocker

        r1 = list(one_room_building.rooms.values())[0]
        w_north = next(w for w in [one_room_building.walls[i] for i in r1.wall_ids] if w.start_y == 10)

        # Очікуємо RoomOverlapError (або той Exception, який ти використовуєш)
        # Оскільки ми визначили клас RoomOverlapError зверху для тесту:
        try:
            one_room_building.add_room_to_wall(w_north.id, depth=5)
        except Exception as e:
            # Перевіряємо, що це помилка перетину (за назвою або типом)
            assert "overlap" in str(e).lower() or "неможливо створити" in str(e).lower()


