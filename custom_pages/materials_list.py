# materials.py
import streamlit as st
from bulding_compounds.material import MATERIALS
import pandas as pd


def make_materials():
    st.subheader("Бібліотека матеріалів")
    st.markdown("""
    База даних будівельних матеріалів з розрахованими теплофізичними характеристиками.
    """)

    # 1. ПІДГОТОВКА ДАНИХ (Data Preparation)
    # Перетворюємо словник об'єктів у список словників для DataFrame
    data = []

    # Визначаємо категорії енергоефективності
    def get_level(u_val):
        if u_val <= 0.15: return "Пасивний дім (Passive House)"
        if u_val <= 0.25: return "Енергоефективний (Сучасний)"
        if u_val <= 0.50: return "Нормативний (ДБН)"
        if u_val <= 1.00: return "Стандартний (Старий фонд)"
        return "Без утеплення (Холодний)"

    for key, mat in MATERIALS.items():
        data.append({
            "ID": key,  # Технічний ключ
            "Назва": mat.name,
            "Товщина (мм)": int(mat.thickness * 1000),  # м -> мм
            "U-значення": mat.U,
            "Лямбда": mat.conductivity,
            "Щільність": int(mat.density),
            "Теплоємність": int(mat.specific_heat),
            "Колір": mat.color,
            "Рівень": get_level(mat.U)
        })

    df_original = pd.DataFrame(data)

    # Визначаємо межі для слайдерів динамічно (щоб не хардкодити числа)
    min_u, max_u = df_original["U-значення"].min(), df_original["U-значення"].max()
    min_rho, max_rho = df_original["Щільність"].min(), df_original["Щільність"].max()

    # 2. ПАНЕЛЬ ФІЛЬТРІВ (Filters UI)
    with st.expander("Фільтри та налаштування пошуку", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_u_range = st.slider(
                "Діапазон U-значення (Вт/м²·К)",
                min_value=float(min_u),
                max_value=float(max_u),
                value=(float(min_u), float(max_u)),
                step=0.05,
                key="filter_u"
            )

        with col2:
            filter_density_range = st.slider(
                "Діапазон щільності (кг/м³)",
                min_value=int(min_rho),
                max_value=int(max_rho),
                value=(int(min_rho), int(max_rho)),
                step=50,
                key="filter_rho"
            )

        with col3:
            available_levels = sorted(df_original["Рівень"].unique())
            filter_levels = st.multiselect(
                "Клас енергоефективності",
                options=available_levels,
                default=[],
                placeholder="Оберіть рівні (пусто = всі)",
                key="filter_levels"
            )

        col_search, col_reset = st.columns([3, 1])
        with col_search:
            filter_search = st.text_input(
                "Пошук за назвою матеріалу",
                "",
                placeholder="Наприклад: Газобетон",
                key="filter_search"
            )

        with col_reset:
            st.markdown("<br>", unsafe_allow_html=True)

            # --- ФУНКЦІЯ СКИДАННЯ (Callback) ---
            def reset_filters_callback():
                # Змінюємо стан ПЕРЕД перезавантаженням
                st.session_state.filter_u = (float(min_u), float(max_u))
                st.session_state.filter_rho = (int(min_rho), int(max_rho))
                st.session_state.filter_levels = []
                st.session_state.filter_search = ""

            # Кнопка тепер просто викликає функцію, а не містить логіку всередині if
            st.button("Скинути фільтри", on_click=reset_filters_callback, use_container_width=True)

    # 3. ЛОГІКА ФІЛЬТРАЦІЇ (Filtering Logic)
    df = df_original.copy()

    # Фільтр U (діапазон)
    df = df[(df["U-значення"] >= filter_u_range[0]) & (df["U-значення"] <= filter_u_range[1])]

    # Фільтр Щільності (діапазон)
    df = df[(df["Щільність"] >= filter_density_range[0]) & (df["Щільність"] <= filter_density_range[1])]

    # Фільтр Рівня (якщо щось обрано)
    if filter_levels:
        df = df[df["Рівень"].isin(filter_levels)]

    # Текстовий пошук
    if filter_search.strip():
        df = df[df["Назва"].str.lower().str.contains(filter_search.lower())]

    # 4. ВІДОБРАЖЕННЯ ТАБЛИЦІ (Table Display)
    st.markdown(f"#### Знайдено матеріалів: **{len(df)}**")

    if df.empty:
        st.warning("За вашими критеріями не знайдено жодного матеріалу. Спробуйте змінити фільтри.")
    else:
        st.dataframe(
            df[[
                "Назва", "Рівень", "Товщина (мм)", "U-значення",
                "Лямбда", "Щільність", "Теплоємність", "Колір"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Назва": st.column_config.TextColumn("Матеріал", width="medium"),
                "Рівень": st.column_config.TextColumn("Клас", width="medium"),
                "Товщина (мм)": st.column_config.NumberColumn("d, мм", format="%d"),
                "U-значення": st.column_config.NumberColumn("U, Вт/м²К", format="%.3f"),
                "Лямбда": st.column_config.NumberColumn("λ, Вт/мК", format="%.3f"),
                "Щільність": st.column_config.ProgressColumn(
                    "ρ, кг/м³",
                    format="%d",
                    min_value=0,
                    max_value=2500
                ),
                "Теплоємність": st.column_config.NumberColumn("C, Дж/кгК", format="%d"),
                "Колір": st.column_config.TextColumn("Колір", width="small"),
            }
        )

        # 5. СЕКЦІЯ КОЛЬОРІВ (Color Preview)
        st.markdown("---")
        st.markdown("### Палітра матеріалів")

        # Перемикач режимів
        col_ctrl1, col_ctrl2 = st.columns([1, 3])
        with col_ctrl1:
            color_mode = st.radio(
                "Режим відображення:",
                ["Тільки унікальні", "Всі відфільтровані"],
                horizontal=False
            )

        with col_ctrl2:
            st.info(
                "Відображаються кольори для матеріалів, що залишилися у таблиці вище."
                if color_mode == "Всі відфільтровані"
                else "Групування однакових кольорів (наприклад, всі червоні цегли як один колір)."
            )

        # Логіка вибору даних для кольорів
        if color_mode == "Тільки унікальні":
            df_colors = df.drop_duplicates(subset=["Колір"]).sort_values("U-значення")
        else:
            df_colors = df.sort_values("U-значення")

        # Grid для карток кольорів
        if not df_colors.empty:
            cols_per_row = 6
            cols = st.columns(cols_per_row)

            for idx, (index, row) in enumerate(df_colors.iterrows()):
                col_idx = idx % cols_per_row
                with cols[col_idx]:
                    with st.container(border=True):
                        # Відображення кольору через color_picker (найчистіший UI варіант)
                        st.color_picker(
                            label=f"Color_{row['ID']}",  # Унікальний ключ
                            value=row["Колір"],
                            disabled=True,
                            label_visibility="collapsed"
                        )

                        # Підпис
                        short_name = row['Назва'].split('(')[0].strip()  # Скорочуємо довгі назви
                        st.markdown(f"**{short_name}**")

                        # Деталі
                        st.caption(f"U: **{row['U-значення']:.2f}**")
                        if color_mode == "Всі відфільтровані":
                            pass
                            # st.caption(f"d: {row['Товщина (мм)']}мм")
        else:
            st.write("Немає даних для відображення кольорів.")

# def make_materials():
#     st.subheader("Бібліотека матеріалів та конструкцій стін")
#     st.markdown("""
#     Тут представлені найпоширеніші стінові конструкції, що відповідають
#     **ДБН В.2.6-31:2016 «Теплова ізоляція будівель»** та реальним проєктам 2024–2025 рр.
#     """)
#
#     # Перетворюємо словник у DataFrame
#     data = []
#     for material in MATERIALS.values():
#         data.append({
#             "Назва конструкції": material.name,
#             "U-значення, Вт/(м²·К)": round(material.U, 3),
#             "Щільність, кг/м³": int(material.density),
#             "Питома теплоємність, Дж/(кг·К)": int(material.specific_heat),
#             "Колір (HEX)": material.color,  # Просто HEX як текст
#             "Рівень теплоізоляції":
#                 "Пасивний дім" if material.U <= 0.15 else
#                 "Енергоефективний" if material.U <= 0.25 else
#                 "Сучасний" if material.U <= 0.50 else
#                 "Стандартний" if material.U <= 1.0 else
#                 "Без утеплення"
#         })
#
#     df = pd.DataFrame(data)
#
#     # Гарна інтерактивна таблиця з виправленим column_config
#     st.dataframe(
#         df[["Назва конструкції", "U-значення, Вт/(м²·К)", "Рівень теплоізоляції",
#             "Щільність, кг/м³", "Питома теплоємність, Дж/(кг·К)", "Колір (HEX)"]],
#         use_container_width=True,
#         hide_index=True,
#         column_config={
#             "Колір (HEX)": st.column_config.Column("Колір", width="medium"),  # Виправлено: Column замість HtmlColumn
#             "U-значення, Вт/(м²·К)": st.column_config.NumberColumn(format="%.3f"),
#             "Рівень теплоізоляції": st.column_config.SelectboxColumn("Рівень", options=list(df["Рівень теплоізоляції"].unique()))
#         }
#     )
#
#     # Візуалізація кольорів нижче таблиці (як картки)
#     st.markdown("### Попередній перегляд кольорів")
#     cols = st.columns(3)
#     for idx, material in enumerate(list(MATERIALS.values())[:9]):  # Перші 9 для прикладу
#         with cols[idx % 3]:
#             with st.container(border=True):
#                 st.markdown(f"""
#                 <div style="background:{material.color}; height:20px; border-radius:4px; border:1px solid #ccc;"></div>
#                 """, unsafe_allow_html=True)
#                 st.caption(f"**{material.name}** — U={material.U:.3f}")
#
#     # Фільтри (як раніше)
#     st.markdown("---")
#     col1, col2 = st.columns(2)
#     with col1:
#         max_u = st.slider("Максимальне U-значення", 0.1, 3.5, 1.0, 0.05)
#     with col2:
#         level = st.multiselect("Рівень теплоізоляції",
#             ["Пасивний дім", "Енергоефективний", "Сучасний", "Стандартний", "Без утеплення"],
#             default=["Енергоефективний", "Пасивний дім"])
#
#     filtered = df[df["U-значення, Вт/(м²·К)"] <= max_u]
#     if level:
#         filtered = filtered[filtered["Рівень теплоізоляції"].isin(level)]
#
#     if len(filtered) < len(df):
#         st.success(f"Знайдено {len(filtered)} відповідних конструкцій")
#         st.dataframe(filtered, use_container_width=True, hide_index=True)

# # materials.py — альтернатива
# def make_materials():
#     st.subheader("Конструкції стін")
#
#     cols = st.columns(3)
#     for idx, material in enumerate(MATERIALS.values()):
#         with cols[idx % 3]:
#             u_level = "Пасивний" if material.U <= 0.15 else "Енергоефективний" if material.U <= 0.25 else "Звичайний"
#             with st.container(border=True):
#                 st.markdown(f"""
#                 <div style="background:{material.color};height:12px;border-radius:4px;"></div>
#                 """, unsafe_allow_html=True)
#                 st.markdown(f"**{material.name}**")
#                 st.caption(f"U = {material.U:.3f} Вт/(м²·К) ← {u_level}")
#                 st.caption(f"ρ = {material.density:.0f} кг/м³  •  c = {material.specific_heat:.0f} Дж/(кг·К)")
