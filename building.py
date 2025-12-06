from bulding_compounds.opening import Opening, OpeningTech, OPENING_TYPES, OpeningCategory
from bulding_compounds.material import Material, MATERIALS
from bulding_compounds.room import Room
from bulding_compounds.wall import Wall, walls_intersect_properly
from typing import Dict
from icecream import ic
import plotly.graph_objects as go
from typing import Optional
import math
from bulding_compounds.custom_errors import *
from dataclasses import dataclass, field


@dataclass
class Building:
    walls: Dict[str, Wall] = field(default_factory=dict)
    rooms: Dict[str, Room] = field(default_factory=dict)

    def create_initial_room(self, x_len: float, y_len: float, height: float, material: Material,
                            name: str = "Room") -> Room:
        if x_len <= 0 or y_len <= 0 or height <= 0:
            raise ValueError("Розміри мають бути > 0")
        # створюю кімнату і додаю її до будівлі
        room = Room(name=name, x=0.0, y=0.0, width=x_len, length=y_len, height=height)
        self.rooms[room.id] = room

        # вершини кімнати проти годинникової стрілки, починаючи з лівого нижнього
        x1, y1 = 0.0, 0.0  # нижній лівий
        x2, y2 = x_len, 0.0  # нижній правий
        x3, y3 = x_len, y_len  # верхній правий
        x4, y4 = 0.0, y_len  # верхній лівий

        # Створюємо стіни з чіткими координатами
        walls = [
            Wall(start_x=x1, start_y=y1, end_x=x2, end_y=y2, height=height,  # південь
                 base_material=material, room_ids=[room.id]),
            Wall(start_x=x2, start_y=y2, end_x=x3, end_y=y3, height=height,  # схід
                 base_material=material, room_ids=[room.id]),
            Wall(start_x=x3, start_y=y3, end_x=x4, end_y=y4, height=height,  # північ
                 base_material=material, room_ids=[room.id]),
            Wall(start_x=x4, start_y=y4, end_x=x1, end_y=y1, height=height,  # захід
                 base_material=material, room_ids=[room.id]),
        ]

        # додаємо стіни в будівлю
        for wall in walls:
            self.walls[wall.id] = wall

        # зберігаємо ід стін у кімнаті S, E, N, W
        room.wall_ids = [wall.id for wall in walls]
        return room

    def get_building_plan(self) -> go.Figure:
        fig = go.Figure()

        # --- 1. КІМНАТИ (ПІДЛОГА) ---
        for room in self.rooms.values():
            room_walls = [self.walls[wid] for wid in room.wall_ids if wid in self.walls]
            if len(room_walls) < 3: continue

            # --- Геометрія кімнати ---
            vertices = set()
            for w in room_walls:
                vertices.add((round(w.start_x, 4), round(w.start_y, 4)))
                vertices.add((round(w.end_x, 4), round(w.end_y, 4)))
            unique_points = list(vertices)
            if len(unique_points) < 3: continue

            # Центр кімнати
            center_x = sum(p[0] for p in unique_points) / len(unique_points)
            center_y = sum(p[1] for p in unique_points) / len(unique_points)

            # Сортування вершин
            unique_points.sort(key=lambda p: math.atan2(p[1] - center_y, p[0] - center_x))
            x_coords = [p[0] for p in unique_points] + [unique_points[0][0]]
            y_coords = [p[1] for p in unique_points] + [unique_points[0][1]]

            # А. Візуальна заливка (не для кліку)
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                fill="toself",
                fillcolor="rgba(173, 216, 230, 0.5)",
                line=dict(width=0),
                mode="none",
                hoverinfo="skip",  # Ігноруємо ховер на заливці, щоб не заважав
                showlegend=False
            ))

            label_text = room.name
            # Якщо є девайси, додаємо іконку
            if room.hvac_devices:
                has_heat = any(d.power_heating > 0 for d in room.hvac_devices)
                has_cool = any(d.power_cooling > 0 for d in room.hvac_devices)

                if has_heat and has_cool:
                    label_text += " 🌡️"
                elif has_heat:
                    label_text += " 🔥"
                elif has_cool:
                    label_text += " ❄️"

            # Б. Текст назви кімнати (Головна точка кліку для кімнати)
            fig.add_trace(go.Scatter(
                x=[center_x],
                y=[center_y],
                mode="text+markers",  # Маркер невидимий, але розширює зону кліку
                marker=dict(size=20, opacity=0),  # Невидимий великий маркер під текстом
                text=[label_text],
                textfont=dict(size=14, color="black", weight="bold"),
                # === ID Кімнати прив'язаний до тексту ===
                customdata=[[room.id, "room"]],
                hovertemplate=f"🏠 Кімната: {room.name}<extra></extra>",
                showlegend=False
            ))

            # --- 2. СТІНИ ТА ОТВОРИ ---
            for wall in self.walls.values():
                is_external = len(wall.room_ids) == 1
                color = getattr(wall.base_material, "color", "#555555")
                # Зовнішні стіни малюємо товщими
                width_px = 8 if is_external else 4

                # А. Малюємо саму стіну (суцільна лінія)
                # Ми малюємо її повною довжиною, вікна будуть просто накладені зверху іншим кольором
                fig.add_trace(go.Scatter(
                    x=[wall.start_x, wall.end_x],
                    y=[wall.start_y, wall.end_y],
                    mode="lines",
                    line=dict(color=color, width=width_px),
                    hoverinfo="skip",
                    showlegend=False
                ))

                # Б. Малюємо отвори (якщо є)
                if wall.openings:
                    # Вектор стіни
                    wx = wall.end_x - wall.start_x
                    wy = wall.end_y - wall.start_y
                    wall_len = wall.length

                    # Нормалізований вектор напрямку стіни
                    ux = wx / wall_len
                    uy = wy / wall_len

                    # Алгоритм рівномірного розподілу:
                    # [GAP] [WIN1] [GAP] [WIN2] [GAP]
                    total_openings_width = sum(op.width for op in wall.openings)
                    total_gap = wall_len - total_openings_width
                    gap_size = total_gap / (len(wall.openings) + 1)

                    current_dist = 0.0  # Поточна відстань від start_x

                    for op in wall.openings:
                        # Початок вікна = (поточна + відступ)
                        current_dist += gap_size
                        win_start_x = wall.start_x + ux * current_dist
                        win_start_y = wall.start_y + uy * current_dist

                        # Кінець вікна = (початок + ширина)
                        win_end_x = win_start_x + ux * op.width
                        win_end_y = win_start_y + uy * op.width

                        # Малюємо вікно поверх стіни
                        # Воно має бути трохи вужчим або світлішим, щоб виділятися
                        fig.add_trace(go.Scatter(
                            x=[win_start_x, win_end_x],
                            y=[win_start_y, win_end_y],
                            mode="lines",
                            line=dict(color=op.tech.color, width=width_px),  # Трохи тонше за стіну
                            hoverinfo="text",
                            hovertext=f"{op.tech.category}: {op.tech.name}<br>{op.width}x{op.height}м",
                            showlegend=False
                        ))

                        # Зсуваємо "курсор" на ширину вікна
                        current_dist += op.width

                # В. Невидимий Хідбокс стіни (для кліку)
                # (Без змін, як було раніше)
                fig.add_trace(go.Scatter(
                    x=[wall.start_x, wall.end_x],
                    y=[wall.start_y, wall.end_y],
                    mode="lines",
                    line=dict(color="rgba(0,0,0,0)", width=20),
                    customdata=[[wall.id, "wall"], [wall.id, "wall"]],  # Дублюємо для двох точок
                    hovertemplate=f"🧱 Стіна: {getattr(wall.base_material, 'name', 'Стіна')}<extra></extra>",
                    showlegend=False
                ))

        # --- 3. НАЛАШТУВАННЯ ---
        fig.update_layout(
            title="План поверху",
            # uirevision='constant' - МАГІЯ, яка забороняє графіку скакати при кліку
            uirevision='constant',
            xaxis=dict(title="X", showgrid=True, zeroline=True, scaleanchor="y", scaleratio=1),
            yaxis=dict(title="Y", showgrid=True, zeroline=True),
            height=600,
            hovermode="closest",
            clickmode="event+select",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )

        # Вимикаємо ефект затемнення при виділенні (щоб написи не зникали)
        fig.update_traces(selectedpoints=None)

        return fig

    # def get_building_plan(self) -> go.Figure:
    #     fig = go.Figure()
    #
    #     # 1. Малюємо всі стіни (єдиний джерело правди)
    #     for wall in self.walls.values():
    #         is_external = len(wall.room_ids) == 1
    #         color = getattr(wall.base_material, "color", "#888888")
    #         width = 5 if is_external else 2
    #
    #         fig.add_trace(go.Scatter(
    #             x=[wall.start_x, wall.end_x],
    #             y=[wall.start_y, wall.end_y],
    #             mode="lines",
    #             line=dict(color=color, width=width),
    #             hoverinfo="text",
    #             hovertext=(
    #                 f"Стіна {wall.id[:6]}<br>"
    #                 f"Матеріал: {getattr(wall.base_material, 'name', '—')}<br>"
    #                 f"Довжина: {wall.length:.2f} м<br>"
    #                 f"Тип: {'Зовнішня' if is_external else 'Внутрішня'}"
    #             ),
    #             showlegend=False
    #         ))
    #
    #     # 2. Реконструюємо і малюємо кімнати з їхніх стін
    #     for room in self.rooms.values():
    #         # Беремо всі стіни кімнати
    #         room_walls: List[Wall] = []
    #         for wid in room.wall_ids:
    #             if wid in self.walls:
    #                 room_walls.append(self.walls[wid])
    #
    #         if len(room_walls) < 3:
    #             continue  # пошкоджена кімната
    #
    #         # Збираємо всі унікальні вершини
    #         vertices = set()
    #         for w in room_walls:
    #             vertices.add((round(w.start_x, 6), round(w.start_y, 6)))
    #             vertices.add((round(w.end_x, 6), round(w.end_y, 6)))
    #
    #         if len(vertices) != 4:
    #             # не прямокутник — пропускаємо або можна попередити
    #             continue
    #
    #         # Сортуємо вершини по годинниковій стрілці (від нижньої лівої)
    #         xs, ys = zip(*vertices)
    #         center_x = sum(xs) / 4
    #         center_y = sum(ys) / 4
    #
    #         sorted_vertices = sorted(vertices,
    #                                  key=lambda p: (
    #                                      -1 if p[0] < center_x else (1 if p[0] > center_x else 0),
    #                                      p[1] - center_y if p[0] <= center_x else center_y - p[1]
    #                                  ))
    #
    #         # Замикаємо контур
    #         x_coords = [p[0] for p in sorted_vertices] + [sorted_vertices[0][0]]
    #         y_coords = [p[1] for p in sorted_vertices] + [sorted_vertices[0][1]]
    #
    #         fig.add_trace(go.Scatter(
    #             x=x_coords,
    #             y=y_coords,
    #             fill="toself",
    #             fillcolor="lightblue",
    #             line=dict(width=0),
    #             opacity=0.25,
    #             text=room.name,
    #             hoverinfo="text",
    #             hovertext=f"Кімната: {room.name}<br>Стіни: {len(room_walls)}",
    #             showlegend=False
    #         ))
    #
    #     # 3. Красиве оформлення
    #     fig.update_layout(
    #         title="План будівлі — геометрія з стін (єдина правда)",
    #         xaxis=dict(title="X, м", showgrid=True, zeroline=False),
    #         yaxis=dict(title="Y, м", scaleanchor="x", scaleratio=1, showgrid=True, zeroline=False),
    #         hovermode="closest",
    #         plot_bgcolor="white",
    #         height=750,
    #         margin=dict(l=40, r=40, t=60, b=40)
    #     )
    #
    #     return fig

    # def get_room_center(self, room_id: str) -> tuple[float, float]:
    #     """Повертає координати центру кімнати"""
    #     room = self.rooms[room_id]
    #     center_x = room.x + room.width / 2
    #     center_y = room.y + room.length / 2
    #     return center_x, center_y

    def get_wall_direction(self, wall_id: str, room_id: str) -> str:
        """
        Повертає сторону світу, на яку виходить стіна відносно кімнати room_id
        Повертає: "N", "E", "S", "W"
        """
        wall = self.walls[wall_id]
        ic(wall.room_ids, room_id)
        if room_id not in wall.room_ids:
            raise ValueError("Ця кімната не належить до стіни")
        room = self.rooms[room_id]
        cx, cy = room.get_center(self)
        # ic(cx,cy)
        # Вектор від початку стіни до її середини
        mid_x = (wall.start_x + wall.end_x) / 2
        mid_y = (wall.start_y + wall.end_y) / 2

        vec_x = mid_x - cx
        vec_y = mid_y - cy

        # Визначаємо домінуючу вісь
        if abs(vec_x) > abs(vec_y):
            # горизонтальний зсув → стіна вертикальна (E або W)
            return "E" if vec_x > 0 else "W"
        else:
            # вертикальний зсув → стіна горизонтальна (N або S)
            return "N" if vec_y > 0 else "S"

    def find_wall_with_geometry(self, other_wall: Wall) -> Optional[Wall]:
        """
        Шукає стіну з точно такими ж координатами (в будь-якому напрямку)
        """
        for wall in self.walls.values():
            if wall.is_equeal_wall(other_wall):
                return wall
        return None

    def calculate_room_dimensions(self, room_id: str) -> tuple[float, float]:
        """
        Вираховує актуальні розміри кімнати на основі координат її стін.
        Повертає: (width_x, length_y)
        """
        if room_id not in self.rooms:
            return 0.0, 0.0

        room = self.rooms[room_id]

        # Збираємо всі координати точок, що належать цій кімнаті
        x_coords = []
        y_coords = []

        for wid in room.wall_ids:
            if wid in self.walls:
                wall = self.walls[wid]
                x_coords.extend([wall.start_x, wall.end_x])
                y_coords.extend([wall.start_y, wall.end_y])

        if not x_coords or not y_coords:
            return 0.0, 0.0

        # Ширина = різниця між крайніми точками по X
        # Довжина = різниця між крайніми точками по Y
        current_width = max(x_coords) - min(x_coords)
        current_length = max(y_coords) - min(y_coords)

        return current_width, current_length

    def check_if_walls_intersection_right(self, wall_to_check: Wall) -> bool:
        """
        Перевіряє надану стіну на правильність перетину з усіма існуючими
        """
        for wall in self.walls.values():
            if not walls_intersect_properly(wall, wall_to_check):
                return False
        return True

    def add_room_to_wall(self, wall_id: str, depth: float, name: str = "Нова кімната"):
        existing_wall = self.walls[wall_id]
        if len(existing_wall.room_ids) == 2:
            raise ValueError("Стіна вже має дві кімнати!")
        material = existing_wall.base_material
        height = existing_wall.height
        # отримую кімнату існуючої стіни
        existing_wall_room = self.rooms[existing_wall.room_ids[0]]
        # отримую направлення стіни відносно кімнати, щоб знати куди будувати далі
        direction = self.get_wall_direction(existing_wall.id, existing_wall_room.id)
        # Todo тут маю визначити координати майбутніх трьох стін в залежності від направлення
        # префікс "p" для координати буде позначати перпендикулярну сторону (perpendicular)
        # префікс "o" буде позначати протилежну сторону (opposite)
        x_start, y_start = existing_wall.start_x, existing_wall.start_y
        x_end, y_end = existing_wall.end_x, existing_wall.end_y
        width, length = None, None
        ox_start, oy_start, ox_end, oy_end = None, None, None, None
        match direction:
            case "N":
                width = x_end - x_start
                length = depth

                ox_start = x_start
                oy_start = y_start + depth
                ox_end = x_end
                oy_end = y_end + depth

                px1_start = x_start
                py1_start = y_start
                px1_end = x_start
                py1_end = y_start + depth

                px2_start = x_end
                py2_start = y_end
                px2_end = x_end
                py2_end = y_end + depth
            case "S":
                width = x_end - x_start
                length = depth

                ox_start = x_start
                oy_start = y_start - depth
                ox_end = x_end
                oy_end = y_end - depth

                px1_start = x_start
                py1_start = y_start
                px1_end = x_start
                py1_end = y_start - depth

                px2_start = x_end
                py2_start = y_end
                px2_end = x_end
                py2_end = y_end - depth

            case "E":
                width = depth
                length = y_end - y_start

                ox_start = x_start + depth
                oy_start = y_start
                ox_end = x_end + depth
                oy_end = y_end

                px1_start = x_start
                py1_start = y_start
                px1_end = x_start + depth
                py1_end = y_start

                px2_start = x_end
                py2_start = y_end
                px2_end = x_end + depth
                py2_end = y_end
            case "W":
                width = depth
                length = y_end - y_start

                ox_start = x_start - depth
                oy_start = y_start
                ox_end = x_end - depth
                oy_end = y_end

                px1_start = x_start
                py1_start = y_start
                px1_end = x_start - depth
                py1_end = y_start

                px2_start = x_end
                py2_start = y_end
                px2_end = x_end - depth
                py2_end = y_end
            case _:
                raise ValueError(f"Неправильний тип напрямку стіни: '{direction}'")
        # створюю стіни
        owall = Wall(ox_start, oy_start, ox_end, oy_end, height, material)
        p1wall = Wall(px1_start, py1_start, px1_end, py1_end, height, material)
        p2wall = Wall(px2_start, py2_start, px2_end, py2_end, height, material)
        # TODO перед додаванням стін треба зробити перевірку накладання стін одне на одну. Для цього

        room_ = Room(name, width, length, height, 0, 0, wall_ids=[])
        check_walls = [owall, p1wall, p2wall]
        # в циклі ми зберігаємо стіни окремо,
        # а додамо їх до кімнати і будинку тільки якщо всі вони правильні
        # таким чином забезпечуючи чистоту, ніколи не додаємо зайві стіни
        right_walls = [existing_wall]
        for new_wall in check_walls:
            if old_wall := self.find_wall_with_geometry(new_wall):
                new_wall = old_wall
                print("При побудові кімнати, знайдено стіну, яку можна не створювати, а взяти існуючу")

            if self.check_if_walls_intersection_right(new_wall):
                # якщо перетини вірні, то зберігаємо стіну,
                # якщо ця кімната вже була додана, то відпрацює правильно
                right_walls.append(new_wall)
            else:
                raise RoomOverlapError(
                    "Неможливо створити кімнату: обрані параметри не відповідають вимогам!"
                )
        # тепер коли отримали правильні стіни, зберігаємо їх
        for wall in right_walls:
            # додаємо айді кімнати
            wall.add_room_id(room_.id)
            # зберігаємо в будівлю стіну
            self.walls[wall.id] = wall

        room_.wall_ids = [wall.id for wall in right_walls]
        self.rooms[room_.id] = room_
        return room_

    def delete_room(self, room_id: str):
        """
        Видаляє кімнату та оновлює пов'язані стіни.
        Якщо стіна належала тільки цій кімнаті — вона видаляється.
        Якщо стіна була спільною — вона залишається, але перестає бути внутрішньою.
        """
        if room_id not in self.rooms:
            raise ValueError(f"Кімната {room_id} не знайдена")

        room = self.rooms[room_id]

        # Ітеруємося по копії списку стін, бо ми можемо видаляти їх з self.walls
        for wall_id in room.wall_ids:
            if wall_id in self.walls:
                wall = self.walls[wall_id]

                # Логіка видалення посилань
                if room_id in wall.room_ids:
                    wall.room_ids.remove(room_id)

                # Перевірка: чи залишились у стіни прив'язані кімнати?
                if len(wall.room_ids) == 0:
                    # Стіна "осиротіла" (була зовнішньою для цієї кімнати), видаляємо
                    del self.walls[wall_id]

                # Якщо len > 0 (наприклад, 1), стіна залишається,
                # але тепер вона стане зовнішньою стіною для сусідньої кімнати

        # Нарешті видаляємо саму кімнату
        del self.rooms[room_id]


# def test():
#     from bulding_compounds.wall import walls_intersect_properly
#     building = Building()
#     wall1 = Wall(0, 0, 0, 3, 1, Material())
#     wall2 = Wall(0, 0, 0, 1, 1, Material())
#     building.walls[wall1.id] = wall1
#     building.walls[wall2.id] = wall2
#     plan = building.get_building_plan()
#     plan.show()
#
#     print(walls_intersect_properly(wall1, wall2))


if __name__ == '__main__':
    # test()
    building = Building()
    room = building.create_initial_room(6, 8, 3, Material(0, 0, 0, 0, 0), "Вітальня")
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "E":
            room = building.add_room_to_wall(w_id, 4, "Кухня")
            break
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "N":
            room = building.add_room_to_wall(w_id, 4, "Кухня2")
            break
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "W":
            room = building.add_room_to_wall(w_id, 6, "Кухня3")
            break
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "W":
            room = building.add_room_to_wall(w_id, 6, "Кухня3")
            break
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "W":
            room = building.add_room_to_wall(w_id, 6, "Кухня3")
            break
    for w_id in room.wall_ids:
        if building.get_wall_direction(w_id, room.id) == "N":
            room = building.add_room_to_wall(w_id, 6, "Кухня3")
            break
    # for w_id in room.wall_ids:
    #     if building.get_wall_direction(w_id, room.id) == "E":
    #         room = building.add_room_to_wall(w_id, 4, "Кухня4")
    #         break
    # for w_id in room.wall_ids:
    #     if building.get_wall_direction(w_id, room.id) == "S":
    #         room = building.add_room_to_wall(w_id, 4, "Кухня5")
    #         break

    # ic(building.get_room_center(room.id))
    # east_wall_id = building.rooms[room.id].wall_ids[1]  # індекс 1 = схід
    # for wall_id in room.wall_ids:
    #     ic(building.get_wall_direction(wall_id, room.id))
    #     ic(building.walls[wall_id])
    ic(len(building.walls))
    fig = building.get_building_plan()
    fig.show()
