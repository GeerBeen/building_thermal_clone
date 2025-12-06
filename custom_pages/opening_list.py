import streamlit as st
import pandas as pd
from bulding_compounds.opening import OPENING_TYPES


def make_openings():
    st.subheader("Каталог вікон та дверей")
    st.markdown("""
    База даних світлопрозорих конструкцій та дверних блоків.
    Характеристики відповідають типовим пропозиціям на ринку України.

    * **U (Heat Transfer Coefficient)** — Втрати тепла (чим менше, тим тепліше).
    * **g (Solar Factor)** — Коефіцієнт пропускання сонячної енергії (важливо для вікон).
    """)

    # 1. ПІДГОТОВКА ДАНИХ
    data = []



    for key, tech in OPENING_TYPES.items():
        data.append({
            "ID": key,
            "Назва": tech.name,
            "Категорія": tech.category.value,  # Отримуємо стрічку з Enum
            "U-значення": tech.U,
            "g-фактор": tech.g,
            "Колір": tech.color
        })

    df_original = pd.DataFrame(data)

    # Визначаємо межі для слайдерів
    min_u, max_u = df_original["U-значення"].min(), df_original["U-значення"].max()

    # 2. ПАНЕЛЬ ФІЛЬТРІВ
    with st.expander("Фільтри каталогу", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Фільтр категорій (Вікна / Двері)
            available_cats = sorted(df_original["Категорія"].unique())
            filter_cats = st.multiselect(
                "Тип конструкції",
                options=available_cats,
                default=[],
                placeholder="Всі типи",
                key="filter_op_cats"
            )

        with col2:
            # Слайдер U-value
            filter_u_range = st.slider(
                "U-значення (Вт/м²·К)",
                min_value=float(min_u),
                max_value=float(max_u),
                value=(float(min_u), float(max_u)),
                step=0.1,
                key="filter_op_u"
            )

        with col3:
            filter_search = st.text_input(
                "Пошук за назвою",
                "",
                key="filter_op_search"
            )

        # Кнопка скидання
        def reset_op_filters():
            st.session_state.filter_op_cats = []
            st.session_state.filter_op_u = (float(min_u), float(max_u))
            st.session_state.filter_op_search = ""

        st.button("Скинути фільтри", on_click=reset_op_filters, key="btn_reset_op")

    # 3. ЛОГІКА ФІЛЬТРАЦІЇ
    df = df_original.copy()

    # За категорією
    if filter_cats:
        df = df[df["Категорія"].isin(filter_cats)]

    # За U-value
    df = df[(df["U-значення"] >= filter_u_range[0]) & (df["U-значення"] <= filter_u_range[1])]

    # За пошуком
    if filter_search.strip():
        df = df[df["Назва"].str.lower().str.contains(filter_search.lower())]

    # 4. ВІДОБРАЖЕННЯ ТАБЛИЦІ
    st.markdown(f"#### Знайдено позицій: **{len(df)}**")

    if not df.empty:
        st.dataframe(
            df[["Назва", "Категорія", "U-значення", "g-фактор", "Колір"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Назва": st.column_config.TextColumn("Назва", width="large"),
                "Категорія": st.column_config.TextColumn("Тип", width="small"),
                "U-значення": st.column_config.NumberColumn(
                    "U, Вт/м²К",
                    format="%.2f",
                    help="Чим менше число, тим краща ізоляція."
                ),
                "g-фактор": st.column_config.ProgressColumn(
                    "Сонячний фактор (g)",
                    format="%.2f",
                    min_value=0,
                    max_value=1,
                    help="Відсоток сонячної енергії, що проходить крізь скло."
                ),
                "Колір": st.column_config.TextColumn("Колір на плані"),
            }
        )

        # 5. ВІЗУАЛЬНІ КАРТКИ
        st.markdown("---")
        st.markdown("### Візуалізація")

        cols = st.columns(4)
        for idx, (index, row) in enumerate(df.iterrows()):
            col_idx = idx % 4

            with cols[col_idx]:
                with st.container(border=True):
                    # Верхня частина: Колір і Назва
                    c_color, c_text = st.columns([1, 4])
                    with c_color:
                        st.color_picker(
                            f"c_{row['ID']}",
                            row["Колір"],
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    with c_text:
                        st.markdown(f"**{row['Назва']}**")

                    # Нижня частина: Характеристики
                    st.caption(f"{row['Категорія']}")

                    # Метрики в рядок
                    m1, m2 = st.columns(2)
                    with m1:
                        st.markdown(f" **U: {row['U-значення']:.1f}**")
                    with m2:
                        if row["Категорія"] == "Вікно":
                            st.markdown(f" **g: {row['g-фактор']:.2f}**")
                        else:
                            st.markdown(" **-**")

    else:
        st.info("За вашими критеріями нічого не знайдено.")
