import streamlit as st
import pandas as pd
from simulation.controls import RoomControlProfile, ControlMode
from simulation.thermal_simulation import ThermalSimulation
import json

# Припускаємо наявність класів Building, RoomControlProfile, ControlMode, ThermalSimulation

def make_simulation():
    """
    Головний контролер сторінки симуляції.
    """
    st.header("Симуляція та Економіка")

    if "building" not in st.session_state or not st.session_state.building.rooms:
        st.warning("Спочатку створіть будівлю та кімнати!")
        return

    building = st.session_state.building

    # 1. Збір параметрів
    params = _render_simulation_params()
    profiles = _render_room_settings(building)

    st.divider()

    # 2. Запуск
    if st.button("ЗАПУСТИТИ", type="primary", width='stretch'):
        _run_simulation_process(building, params, profiles)


# ==============================================================================
# 1. UI: НАЛАШТУВАННЯ (View Components)
# ==============================================================================

def _render_simulation_params():
    """Відображає віджети для глобальних налаштувань (погода, тариф, час)."""
    with st.container(border=True):
        st.subheader("Умови середовища")
        c1, c2, c3 = st.columns(3)
        with c1:
            t_min, t_max = st.slider(
                "Температура вулиці (Ніч / День)",
                min_value=-30.0, max_value=40.0, value=(-5.0, 2.0), step=1.0
            )
        with c2:
            tariff = st.number_input("Тариф (грн/кВт·год)", value=4.32, step=0.1)
        with c3:
            internal_gain = st.number_input(
                "Побутове тепло (Вт/кімнату)",
                value=200.0, help="Люди, техніка, освітлення"
            )

    c_dur, c_start = st.columns(2)
    with c_dur:
        duration = st.number_input("Тривалість (годин)", value=24, min_value=1)
    with c_start:
        start_t = st.number_input("Початкова температура в домі", value=19.0)

    return {
        "t_min": t_min, "t_max": t_max, "tariff": tariff,
        "internal_gain": internal_gain, "duration": duration, "start_t": start_t
    }


def _render_room_settings(building):
    """Відображає налаштування HVAC для кожної кімнати."""
    st.subheader(" Налаштування кімнат")
    profiles = {}

    for room_id, room in building.rooms.items():
        with st.expander(f"Налаштування: {room.name}", expanded=True):
            profiles[room_id] = _get_profile_for_room(room, room_id)

    return profiles


def _get_profile_for_room(room, room_id):
    """Допоміжна функція для створення профілю однієї кімнати."""
    has_hvac = len(room.hvac_devices) > 0

    if not has_hvac:
        st.caption("У кімнаті немає пристроїв обігріву. Вона буде пасивною.")
        return RoomControlProfile(mode=ControlMode.ALWAYS_OFF)

    c_mode = st.selectbox(
        f"Режим роботи ({room.name})",
        options=[e.value for e in ControlMode],
        key=f"mode_{room_id}"
    )

    selected_mode = ControlMode(c_mode)
    profile = RoomControlProfile(mode=selected_mode)

    if selected_mode == ControlMode.THERMOSTAT:
        profile.target_temp = st.slider(
            f"Цільова температура ({room.name})",
            10.0, 30.0, 21.0, key=f"t_{room_id}"
        )
    elif selected_mode == ControlMode.CYCLIC:
        c1, c2 = st.columns(2)
        with c1:
            profile.cycle_on_hours = st.number_input(
                f"Годин ВКЛ ({room.name})",
                1, 24, 5, key=f"on_{room_id}"
            )
        with c2:
            profile.cycle_off_hours = st.number_input(
                f"Годин ВИКЛ ({room.name})",
                1, 24, 3, key=f"off_{room_id}"
            )
        st.caption(f"Цикл: {profile.cycle_on_hours}год гріє -> {profile.cycle_off_hours}год пауза.")

    return profile


# ==============================================================================
# 2. LOGIC: ЗАПУСК ПРОЦЕСУ (Controller)
# ==============================================================================

def _run_simulation_process(building, params, profiles):
    """Виконує симуляцію, оновлює прогрес і викликає рендер результатів."""

    sim = ThermalSimulation(building)
    sim.initialize(
        start_temp=params["start_t"],
        profiles=profiles,
        t_min=params["t_min"],
        t_max=params["t_max"],
        internal_gain=params["internal_gain"]
    )

    # UI для прогресу
    progress_bar = st.progress(0)
    status_text = st.empty()

    # === ВИПРАВЛЕНА ЛОГІКА ЦИКЛУ ===
    # Ми хочемо симулювати загалом `duration` годин.
    # Розіб'ємо цей час на 10 кроків для анімації прогресу.
    # Кожен крок симулює duration / 10 годин.

    total_hours = params["duration"]
    chunk_hours = total_hours / 10.0

    for i in range(10):
        # 1. Рахуємо шматок фізики
        status_text.text(f"Обрахунок... {int((i + 1) * 10)}%")

        # УВАГА: run_simulation просто додає нові дані до існуючих (append),
        # тому ми викликаємо його 10 разів з меншим часом.
        sim.run_simulation(duration_hours=chunk_hours, dt_seconds=60)

        # 2. Оновлюємо бар
        progress_bar.progress((i + 1) * 10)

    status_text.text("Симуляцію завершено успішно!")

    # === ВІДОБРАЖЕННЯ РЕЗУЛЬТАТІВ (Тільки один раз в кінці) ===
    _render_results(sim, building, params["tariff"])


# ==============================================================================
# 3. UI: РЕЗУЛЬТАТИ (Results View)
# ==============================================================================

def _render_results(sim, building, tariff):
    """Малює графіки та таблиці."""

    # 1. Графік температур
    st.plotly_chart(sim.get_results_chart(), width='stretch')

    # 2. Економічний звіт
    st.subheader("Енерговитрати та Вартість")

    total_kwh_all = sum(sim.total_energy_kwh.values())
    total_cost = total_kwh_all * tariff
    avg_outdoor = (sim.t_min_outdoor + sim.t_max_outdoor) / 2

    # Метрики
    m1, m2, m3 = st.columns(3)
    m1.metric("Всього спожито", f"{total_kwh_all:.2f} кВт·год")
    m2.metric("Загальна вартість", f"{total_cost:.2f} грн")
    m3.metric("Середня темп. вулиці", f"{avg_outdoor:.1f} °C")

    # Таблиця
    _render_energy_table(sim, building, tariff, total_kwh_all)


def _render_energy_table(sim, building, tariff, total_kwh_all):
    """Малює детальну таблицю по кімнатах та дозволяє скачати результати."""

    # 1. Формуємо зведені дані (для таблиці)
    report_data = []

    for rid, kwh in sim.total_energy_kwh.items():
        cost = kwh * tariff
        room_name = building.rooms[rid].name

        # Середня температура
        temps = sim.history_temps.get(rid, [])
        avg_temp = sum(temps) / len(temps) if temps else 0.0

        report_data.append({
            "Кімната": room_name,
            "Споживання (кВт·год)": kwh,
            "Вартість (грн)": cost,
            "Середня T (°C)": avg_temp
        })

    if not report_data:
        st.info("Немає даних для звіту.")
        return

    # Створюємо DataFrame для відображення
    df_summary = pd.DataFrame(report_data)

    st.dataframe(
        df_summary,
        width='stretch',
        column_config={
            "Споживання (кВт·год)": st.column_config.ProgressColumn(
                "Споживання",
                format="%.2f",
                min_value=0,
                max_value=max(total_kwh_all, 1.0)
            ),
            "Вартість (грн)": st.column_config.NumberColumn("Вартість", format="%.2f грн"),
            "Середня T (°C)": st.column_config.NumberColumn("Середня T", format="%.1f °C"),
        }
    )

    # =========================================================
    # 2. БЛОК ЕКСПОРТУ (CSV, JSON)
    # =========================================================
    st.divider()
    st.subheader("Експорт результатів")

    with st.container(border=True):
        st.caption("Оберіть формат для завантаження даних:")

        # А. Готуємо Детальний DataFrame (Часовий ряд)
        # Створюємо словник: Час -> Вулиця -> Кімната 1 -> Кімната 2...
        time_series_data = {
            "Час (годин)": sim.history_time,
            "Вулиця (°C)": sim.history_outdoor
        }
        for rid, temps in sim.history_temps.items():
            r_name = building.rooms[rid].name
            time_series_data[f"{r_name} (°C)"] = temps

        df_detailed = pd.DataFrame(time_series_data)

        # Б. Кнопки завантаження
        col1, col2, col3 = st.columns(3)

        with col1:
            # 1. CSV: Зведений звіт (Те, що в таблиці)
            st.download_button(
                label="Звіт (CSV)",
                data=df_summary.to_csv(index=False).encode('utf-8'),
                file_name="simulation_summary.csv",
                mime="text/csv",
                help="Завантажити таблицю витрат та середніх температур"
            )

        with col2:
            # 2. CSV: Детальна динаміка (Для Excel)
            st.download_button(
                label="Динаміка (CSV)",
                data=df_detailed.to_csv(index=False).encode('utf-8'),
                file_name="simulation_dynamics.csv",
                mime="text/csv",
                help="Завантажити детальні зміни температури по хвилинах для Excel"
            )

        with col3:
            # 3. JSON: Повний дамп (Звіт + Динаміка)
            full_json_data = {
                "summary": report_data,
                "dynamics": time_series_data,
                "parameters": {
                    "t_min": sim.t_min_outdoor,
                    "t_max": sim.t_max_outdoor,
                    "tariff": tariff
                }
            }
            # Конвертуємо в JSON рядок
            json_str = json.dumps(full_json_data, indent=2, ensure_ascii=False)

            st.download_button(
                label="Все (JSON)",
                data=json_str,
                file_name="simulation_full.json",
                mime="application/json",
                help="Повний набір даних у форматі JSON"
            )