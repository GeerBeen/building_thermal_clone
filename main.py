import streamlit as st
from building import Building
from custom_pages.planning import make_planning
from custom_pages.materials_list import make_materials
from custom_pages.opening_list import make_openings
from custom_pages.make_simulation import make_simulation
from custom_pages.save_load import render_save_load_controls
from custom_pages.help import make_help

st.set_page_config(
    page_title="Цифровий двійник будівлі",
    page_icon="house",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "building" not in st.session_state:
    st.session_state.building = Building()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Планування"

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/home.png", width=100)
    st.title("Цифровий двійник")
    st.markdown("---")

    st.radio(
        "Навігація",
        [
            "Планування",
            "Матеріали",
            "Вікна та двері",
            "Симуляція",
            "Імпорт та Експорт",
            "Довідка"
        ],
        key="navigation_radio",
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("Курсова робота 2025")
    st.caption("ТВ-32 Михайленко Роман")


page = st.session_state.navigation_radio

st.markdown(f"# {page}")

match page:
    case "Планування":
        make_planning()
    case "Матеріали":
        make_materials()
    case "Вікна та двері":
        make_openings()
    case "Симуляція":
        make_simulation()
    case "Імпорт та Експорт":
        render_save_load_controls()
    case "Довідка":
        make_help()
    case _:
        st.error("Невідомий тип сторінки, оберіть одну з запропонованих сторінок!")
