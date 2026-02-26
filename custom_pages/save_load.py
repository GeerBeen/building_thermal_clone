import streamlit as st
import json
from building_serializer import BuildingSerializer


def apply_load_callback(new_building_obj):
    st.session_state.building = new_building_obj
    st.session_state.navigation_radio = "Планування"


def render_save_load_controls():
    st.header("Керування файлами проєкту")

    col_save, col_load = st.columns(2)

    with col_save:
        with st.container(border=True):
            st.subheader(" Експорт")
            if "building" in st.session_state and st.session_state.building.rooms:
                building = st.session_state.building
                st.info(f"Кімнат: {len(building.rooms)} | Стін: {len(building.walls)}")
                try:
                    json_str = BuildingSerializer.to_json(building)
                    st.download_button(
                        label="Завантажити (.json)",
                        data=json_str,
                        file_name="house_project.json",
                        mime="application/json",
                        width='stretch',
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"Помилка: {e}")
            else:
                st.warning("Проєкт порожній.")

    with col_load:
        with st.container(border=True):
            st.subheader("Імпорт")
            uploaded_file = st.file_uploader("Оберіть файл", type=["json"], label_visibility="collapsed")

            if uploaded_file is not None:
                try:
                    json_data = uploaded_file.getvalue().decode("utf-8")
                    loaded_building = BuildingSerializer.from_json(json_data)

                    st.success("Файл валідний!")
                    st.markdown(f"**Знайдено:** {len(loaded_building.rooms)} кімнат.")
                    st.divider()

                    st.button(
                        "Відкрити цей проєкт",
                        type="primary",
                        width='stretch',
                        on_click=apply_load_callback,  # Викликати цю функцію
                        args=(loaded_building,)  # Передати цей аргумент у функцію
                    )

                except Exception as e:
                    st.error(f"Помилка обробки: {e}")