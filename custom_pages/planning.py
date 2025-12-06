import streamlit as st
from bulding_compounds.material import MATERIALS
from building import Building
from bulding_compounds.custom_errors import *
from bulding_compounds.opening import Opening, OpeningCategory, OpeningTech, OPENING_TYPES
from bulding_compounds.hvac import HVACDevice, HVAC_CATALOG, HVACType
from bulding_compounds.material import MATERIALS


def make_planning():
    """
    Головна функція-контролер.
    Визначає стан програми та викликає відповідні view-функції.
    """
    _ensure_state()
    building = st.session_state.building

    st.divider()
    # Головна розвилка логіки
    if len(building.rooms) > 0:
        _render_main_workspace(building)
    else:
        _render_initial_setup(building)


# ==============================================================================
# ДОПОМІЖНІ ФУНКЦІЇ (PRIVATE FUNCTIONS)
# ==============================================================================

def _ensure_state():
    """Ініціалізація стану, якщо він відсутній"""
    if "building" not in st.session_state:
        st.session_state.building = Building()


def _render_initial_setup(building):
    """
    Відображає форму створення першої кімнати (фундаменту).
    Викликається, коли building.rooms порожній.
    """
    st.subheader("Створення основи будинку")
    st.markdown("Створіть першу кімнату, яка задасть систему координат для всього будинку.")

    with st.form("create_initial_room_form"):
        c1, c2 = st.columns(2)
        with c1:
            room_name = st.text_input("Назва кімнати", value="Вітальня")

            # Використовуємо глобальний словник MATERIALS (або WALL_MATERIALS)
            # Переконайтесь, що він доступний у цьому скоупі
            material_options = list(MATERIALS.keys())

            def format_func(key):
                mat = MATERIALS[key]
                return f"{mat.name} (U={mat.U})"

            selected_mat_key = st.selectbox(
                "Матеріал зовнішніх стін",
                options=material_options,
                format_func=format_func
            )

        with c2:
            width = st.number_input("Ширина (X), м", min_value=1.0, value=5.0, step=0.1)
            length = st.number_input("Довжина (Y), м", min_value=1.0, value=4.0, step=0.1)
            height = st.number_input("Висота стелі (H), м", min_value=2.0, value=2.8, step=0.1)

        st.caption(f"Площа: {width * length:.2f} м² | Об'єм: {width * length * height:.2f} м³")

        if st.form_submit_button("Створити фундамент та першу кімнату"):
            try:
                chosen_material = MATERIALS[selected_mat_key]
                new_room = building.create_initial_room(
                    x_len=width, y_len=length, height=height,
                    material=chosen_material, name=room_name
                )
                st.success(f"Кімнату '{new_room.name}' успішно створено!")
                st.rerun()
            except Exception as e:
                st.error(f"Помилка створення: {e}")


def _render_main_workspace(building):
    """
    Відображає основний робочий простір: Графік + Інспектор.
    Викликається, коли в будинку є кімнати.
    """
    col_ctrl, col_plot = st.columns([1, 2])

    # 1. Спочатку малюємо графік і отримуємо подію (Event)
    with col_plot:
        selection_event = _render_plot(building)

    # 2. Передаємо подію в інспектор для обробки
    with col_ctrl:
        _render_inspector_panel(building, selection_event)


def _render_plot(building):
    """Відповідає виключно за рендеринг Plotly графіка"""
    fig = building.get_building_plan()
    event = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode="points",
        use_container_width=True,
        key="room_selector"
    )
    return event


def _render_inspector_panel(building, event):
    """
    Ліва панель управління.
    Визначає, що показати: загальні кнопки або деталі вибраної кімнати.
    """
    # Логіка визначення вибору
    selected_room = _parse_selection(building, event)

    if selected_room:
        _render_room_details(building, selected_room)
    else:
        st.info("Натисніть на кімнату на плані, щоб побачити деталі та список стін.")

        # Глобальні дії
        if st.button("Видалити все", type="primary", use_container_width=True):
            st.session_state.building = Building()
            st.rerun()


def _parse_selection(building, event):
    """Парсить подію Plotly і повертає об'єкт Room або None"""
    if event and event.selection and event.selection["points"]:
        point = event.selection["points"][0]
        if "customdata" in point:
            obj_id, obj_type = point["customdata"]
            if obj_type == "room":
                return building.rooms.get(obj_id)
    return None


def _render_room_details(building, room):
    """
    Відображає детальну інформацію про конкретну кімнату.
    """
    st.markdown(f"### {room.name}")

    # === ВИКОРИСТОВУЄМО НОВИЙ МЕТОД ===
    # Вираховуємо розміри "на льоту"
    actual_width, actual_length = building.calculate_room_dimensions(room.id)

    # Метрики
    c1, c2 = st.columns(2)
    with c1:
        # Площа = X * Y
        area = actual_width * actual_length
        st.metric("Площа", f"{area:.2f} м²")
        st.caption(f"Розміри: {actual_width:.2f} x {actual_length:.2f} м")
    with c2:
        # Периметр = 2 * (X + Y)
        perimeter = (actual_width + actual_length) * 2
        st.metric("Периметр", f"{perimeter:.2f} м")
        st.caption(f"Висота: {room.height:.2f} м")

    st.markdown("#### Стіни кімнати")

    # Виклик функції рендерингу списку стін
    _render_walls_list(building, room)

    st.markdown("#### Клімат-контроль")

    # 1. Список активних пристроїв
    if room.hvac_devices:
        for device in room.hvac_devices:
            with st.container(border=True):
                c_name, c_btn = st.columns([4, 1])
                with c_name:
                    st.markdown(f"**{device.name}**")
                    st.caption(device.description)
                with c_btn:
                    if st.button("❌", key=f"rm_hvac_{device.id}"):
                        room.remove_hvac(device.id)
                        st.rerun()
    else:
        st.caption("Немає встановлених пристроїв (кімната пасивна)")

    # 2. Додавання нового пристрою
    with st.expander("Встановити обладнання"):
        with st.form(key=f"add_hvac_form_{room.id}"):
            hvac_options = list(HVAC_CATALOG.keys())

            def format_hvac(key):
                d = HVAC_CATALOG[key]
                return f"{d.name} [{d.description}]"

            selected_hvac_key = st.selectbox(
                "Оберіть пристрій",
                options=hvac_options,
                format_func=format_hvac
            )

            if st.form_submit_button("Встановити"):
                # Створюємо КОПІЮ об'єкта з каталогу, щоб у кожного був свій ID
                template = HVAC_CATALOG[selected_hvac_key]
                new_device = HVACDevice(
                    name=template.name,
                    device_type=template.device_type,
                    power_heating=template.power_heating,
                    power_cooling=template.power_cooling,
                    efficiency=template.efficiency
                )

                room.add_hvac(new_device)
                st.success("Пристрій встановлено!")
                st.rerun()

    # === БЛОК ВИДАЛЕННЯ ===
    st.divider()

    if st.button("Видалити цю кімнату", key=f"del_btn_{room.id}", type="primary", use_container_width=True):
        try:
            building.delete_room(room.id)
            st.success(f"Кімнату '{room.name}' видалено!")
            st.rerun()
        except Exception as e:
            st.error(f"Помилка видалення: {e}")


def _render_walls_list(building, room):
    """
    Логіка підготовки даних та відображення списку стін.
    """
    dir_icons = {"N": "⬆️", "S": "⬇️", "E": "➡️", "W": "⬅️"}
    sort_order = {"N": 1, "E": 2, "S": 3, "W": 4}

    # Підготовка даних
    walls_data = []
    for wid in room.wall_ids:
        if wid in building.walls:
            wall = building.walls[wid]
            direction = building.get_wall_direction(wid, room.id)
            is_ext = len(wall.room_ids) == 1
            walls_data.append({
                "obj": wall,
                "dir": direction,
                "is_ext": is_ext
            })

    # Сортування
    walls_data.sort(key=lambda x: sort_order.get(x["dir"], 99))

    # Рендеринг карток
    for item in walls_data:
        _render_wall_card(building, room, item, dir_icons)


def _render_wall_card(building, room, item, dir_icons):
    """
    Відображає картку однієї стіни, форму додавання кімнати та форму додавання отворів.
    """
    w = item["obj"]
    d_code = item["dir"]
    is_ext = item["is_ext"]

    d_icon = dir_icons.get(d_code, "⏺")
    type_str = "Зовнішня" if is_ext else "Внутрішня"

    with st.container(border=True):
        # 1. Заголовок і Інформація
        col_info, col_visual = st.columns([4, 1])
        with col_info:
            st.markdown(f"**{d_icon} {d_code} — {type_str}**")
            st.caption(f"Матеріал: {w.base_material.name}")
            # Показуємо не тільки довжину, а й кількість отворів
            st.caption(f"Довжина: {w.length:.2f} м | Отворів: {len(w.openings)}")

        with col_visual:
            st.color_picker(
                "Колір", w.base_material.color,
                disabled=True,
                label_visibility="collapsed",
                key=f"color_{w.id}"
            )

        # 2. Блок "Додати отвір" (Доступний для ВСІХ стін)
        with st.expander(" Додати отвір (Вікно/Двері)", expanded=False):
            with st.form(key=f"add_opening_form_{w.id}"):
                # А. Вибір типу (Selectbox)
                tech_keys = list(OPENING_TYPES.keys())

                def format_tech(key):
                    t = OPENING_TYPES[key]
                    # Показуємо категорію і назву
                    return f"{t.category}: {t.name}"

                selected_tech_key = st.selectbox(
                    "Тип конструкції",
                    options=tech_keys,
                    format_func=format_tech
                )

                # Б. Розміри (Columns)
                c_w, c_h = st.columns(2)
                with c_w:
                    op_width = st.number_input("Ширина, м", min_value=0.5, value=0.9, step=0.1)
                with c_h:
                    op_height = st.number_input("Висота, м", min_value=1.0, value=2.1, step=0.1)

                submitted_op = st.form_submit_button("Додати отвір")

                if submitted_op:
                    try:
                        # 1. Отримуємо технологію з каталогу
                        tech = OPENING_TYPES[selected_tech_key]

                        # 2. Створюємо об'єкт Opening
                        # (Клас Opening має бути імпортований)
                        new_opening = Opening(
                            tech=tech,
                            width=op_width,
                            height=op_height
                        )

                        # 3. Додаємо до стіни (метод сам перевірить валідацію розмірів)
                        w.add_opening(new_opening)

                        st.success(f"{tech.category} додано!")
                        st.rerun()

                    except ValueError as e:
                        # Ловимо помилки валідації (не влізло в стіну)
                        st.error(f"{e}")
                    except Exception as e:
                        st.error(f"Помилка: {e}")

        # 3. Блок "Прибудувати кімнату" (Тільки для ЗОВНІШНІХ стін)
        if is_ext:
            with st.expander("Прибудувати кімнату", expanded=False):
                with st.form(key=f"add_room_form_{w.id}"):
                    st.markdown("Параметри нової кімнати:")

                    new_depth = st.number_input(
                        "Глибина (перпендикулярно), м",
                        min_value=1.0, value=3.0, step=0.5
                    )

                    new_name = st.text_input(
                        "Назва кімнати",
                        value=f"Кімната {d_code}"
                    )

                    submitted_room = st.form_submit_button("Створити прибудову")

                    if submitted_room:
                        try:
                            building.add_room_to_wall(
                                wall_id=w.id,
                                depth=new_depth,
                                name=new_name
                            )
                            st.success("Кімнату успішно додано!")
                            st.rerun()
                        except RoomOverlapError as e:
                            st.error(f"{e}")
                        except Exception as e:
                            st.error(f"Помилка: {e}")

        with st.expander(" Змінити матеріал", expanded=False):
            with st.form(key=f"change_mat_form_{w.id}"):
                # Отримуємо список доступних матеріалів
                # (WALL_MATERIALS має бути доступним у цьому контексті)
                mat_keys = list(MATERIALS.keys())

                def format_mat(key):
                    m = MATERIALS[key]
                    # Показуємо назву і U, щоб користувач розумів, на що міняє
                    return f"{m.name} (U={m.U})"

                # Спробуємо знайти поточний матеріал у списку, щоб зробити його дефолтним
                # Порівнюємо за назвою, бо об'єкти можуть бути різними інстансами
                current_index = 0
                for idx, k in enumerate(mat_keys):
                    if MATERIALS[k].name == w.base_material.name:
                        current_index = idx
                        break

                new_mat_key = st.selectbox(
                    "Оберіть новий матеріал",
                    options=mat_keys,
                    index=current_index,
                    format_func=format_mat
                )

                if st.form_submit_button("Застосувати"):
                    # Оновлюємо посилання на матеріал стіни
                    w.base_material = MATERIALS[new_mat_key]
                    st.success(f"Матеріал змінено на: {w.base_material.name}")
                    # Перезавантажуємо, щоб оновити колір на графіку і U-value в інфо
                    st.rerun()
