import json
import dataclasses
from typing import Dict, Any
from building import Building
from bulding_compounds.material import Material
from bulding_compounds.opening import Opening, OpeningTech, OpeningCategory
from bulding_compounds.hvac import HVACDevice, HVACType
from bulding_compounds.wall import Wall
from bulding_compounds.room import Room


class BuildingSerializer:
    @staticmethod
    def to_json(building: Building) -> str:
        """Конвертує об'єкт Building у JSON-рядок."""
        # dataclasses.asdict рекурсивно перетворює все у словники
        # StrEnum (OpeningCategory, HVACType) автоматично стають рядками
        return json.dumps(dataclasses.asdict(building), indent=2, ensure_ascii=False)

    @staticmethod
    def from_json(json_str: str) -> Building:
        """Відтворює об'єкт Building з JSON-рядка."""
        data = json.loads(json_str)
        new_building = Building()

        # Відновлюємо стіни
        # Нам треба пройтися по словнику data['walls']
        walls_data = data.get('walls', {})

        for w_id, w_info in walls_data.items():
            # А. Відновлюємо Матеріал
            mat_data = w_info['base_material']
            material = Material(**mat_data)

            #  Відновлюємо Отвори
            openings = []
            for op_data in w_info.get('openings', []):
                # Відновлюємо OpeningTech
                tech_data = op_data['tech']
                # Важливо: конвертуємо рядок категорії назад в Enum
                tech_data['category'] = OpeningCategory(tech_data['category'])
                tech = OpeningTech(**tech_data)

                # Створюємо Opening
                # Видаляємо tech з op_data, щоб передати його об'єктом, а не словником
                op_params = {k: v for k, v in op_data.items() if k != 'tech'}
                openings.append(Opening(tech=tech, **op_params))

            # Створюємо Стіну
            # Прибираємо вкладені структури, які ми вже відновили
            wall_params = {k: v for k, v in w_info.items()
                           if k not in ['base_material', 'openings']}

            wall = Wall(
                base_material=material,
                openings=openings,
                **wall_params
            )
            new_building.walls[w_id] = wall

        #  Відновлюємо кімнати
        rooms_data = data.get('rooms', {})

        for r_id, r_info in rooms_data.items():
            # Відновлюємо HVAC
            hvacs = []
            for h_data in r_info.get('hvac_devices', []):
                # Конвертуємо тип назад в Enum
                h_data['device_type'] = HVACType(h_data['device_type'])
                hvacs.append(HVACDevice(**h_data))

            # Створюємо Кімнату
            room_params = {k: v for k, v in r_info.items() if k != 'hvac_devices'}

            room = Room(hvac_devices=hvacs, **room_params)
            new_building.rooms[r_id] = room

        return new_building


if __name__ == '__main__':
    from bulding_compounds.material import MATERIALS

    b = Building()
    b.create_initial_room(4, 3, 2, list(MATERIALS.values())[0], "aboba")
    js = BuildingSerializer.to_json(b)
    print(js)
    b2 = BuildingSerializer.from_json(js)
    fig = b2.get_building_plan()
    fig.show()

