from building import Building
from bulding_compounds.room import Room
import plotly.graph_objects as go
from typing import Dict, List
from simulation.controls import RoomControlProfile, ControlMode
import math
# Константи фізики
AIR_DENSITY = 1.225  # кг/м³
AIR_SPECIFIC_HEAT = 1005  # Дж/(кг·К)
WALL_MASS_FACTOR = 0.5  # Яка частина маси стіни бере участь в інерції (внутрішня половина)


class ThermalSimulation:
    def __init__(self, building):
        self.building = building

        self.t_min_outdoor = -5.0
        self.t_max_outdoor = 0.0
        self.total_energy_kwh: Dict[str, float] = {}
        self.internal_heat_gain = 200.0

        # Стан
        self.current_temperatures: Dict[str, float] = {}
        self.control_profiles: Dict[str, 'RoomControlProfile'] = {} # Типізація стрінгою
        self.current_time_sec = 0.0

        # Історія (ініціалізуємо порожніми списками для існуючих кімнат)
        self.history_temps: Dict[str, List[float]] = {rid: [] for rid in building.rooms}
        self.history_outdoor: List[float] = []
        self.history_time: List[float] = []

    def initialize(self, start_temp: float, profiles: Dict[str, 'RoomControlProfile'],
                   t_min: float, t_max: float, internal_gain: float = 200.0):

        # --- 1. ВАЛІДАЦІЯ ---
        if t_min > t_max:
            raise ValueError(f"t_min ({t_min}) cannot be greater than t_max ({t_max})")

        if internal_gain < 0:
            raise ValueError("Internal heat gain cannot be negative")

        # Перевіряємо, чи всі кімнати мають профіль
        building_room_ids = set(self.building.rooms.keys())
        provided_profile_ids = set(profiles.keys())

        # Якщо є кімнати без профілю -> помилка
        missing_rooms = building_room_ids - provided_profile_ids
        if missing_rooms:
            raise ValueError(f"Missing control profiles for rooms: {missing_rooms}")

        # --- 2. СКИДАННЯ СТАНУ ---
        self.current_time_sec = 0.0
        self.t_min_outdoor = t_min
        self.t_max_outdoor = t_max
        self.internal_heat_gain = internal_gain
        self.control_profiles = profiles

        # Обнуляємо лічильники енергії
        self.total_energy_kwh = {rid: 0.0 for rid in self.building.rooms}

        # Скидаємо історію (починаємо з чистого аркуша)
        self.history_time = [0.0]

        # Температура вулиці на старті
        initial_outdoor = self._get_current_outdoor_temp()
        self.history_outdoor = [initial_outdoor]

        # Ініціалізуємо температури кімнат
        self.current_temperatures = {}
        self.history_temps = {}

        for room_id in self.building.rooms:
            self.current_temperatures[room_id] = start_temp
            self.history_temps[room_id] = [start_temp]

    def _get_current_outdoor_temp(self) -> float:
        """
        Генерує температуру залежно від часу доби (Синусоїда).
        Припускаємо, що мінімум о 4:00 ранку, максимум о 15:00.
        """
        # Переводимо секунди в години доби (0-24)
        hour_of_day = (self.current_time_sec / 3600.0) % 24

        # Середня температура і амплітуда
        avg_temp = (self.t_max_outdoor + self.t_min_outdoor) / 2
        amplitude = (self.t_max_outdoor - self.t_min_outdoor) / 2

        # Зміщення фази, щоб пік був о 14:00-15:00
        # cos(0) = 1 (пік), cos(pi) = -1 (дно).
        # Нам треба пік о 14:00.
        # (hour - 14) * (2pi / 24)
        phase = (hour_of_day - 14.0) * (2 * math.pi / 24.0)

        return avg_temp + amplitude * math.cos(phase)

    def _calculate_room_thermal_mass(self, room: Room) -> float:
        """
        Рахує сумарну теплоємність (C) кімнати в Дж/К.
        C_total = C_air + C_walls_effective
        """
        # Теплоємність повітря
        # V = Area * Height
        w, l = self.building.calculate_room_dimensions(room.id)
        volume = w * l * room.height
        c_air = volume * AIR_DENSITY * AIR_SPECIFIC_HEAT

        # Теплоємність стін (інерція)
        c_walls = 0.0
        for wid in room.wall_ids:
            if wid in self.building.walls:
                wall = self.building.walls[wid]
                mat = wall.base_material

                # Маса стіни = Об'єм * Щільність
                # Об'єм = Довжина * Висота * Товщина (з матеріалу)
                # Треба брати чисту площу (без вікон)
                wall_volume = wall.area_net * mat.thickness
                wall_mass = wall_volume * mat.density

                # Теплоємність цієї стіни = Mass * specific_heat
                # Множимо на фактор (наприклад 0.5), бо гріється не вся стіна миттєво
                c_walls += wall_mass * mat.specific_heat * WALL_MASS_FACTOR

        total_c = c_air + c_walls
        return max(total_c, 1000.0)  # Захист від ділення на нуль

    def _calculate_transmission_heat_flow(self, room: Room, current_temp: float, outdoor_temp: float) -> float:
        heat_flow = 0.0
        for wid in room.wall_ids:
            if wid not in self.building.walls: continue
            wall = self.building.walls[wid]

            # Визначаємо сусідню температуру
            t_neighbor = outdoor_temp

            if len(wall.room_ids) == 2:
                other_id = wall.room_ids[0] if wall.room_ids[1] == room.id else wall.room_ids[1]
                t_neighbor = self.current_temperatures.get(other_id, outdoor_temp)

            dt = t_neighbor - current_temp
            heat_flow += wall.base_material.U * wall.area_net * dt
            for op in wall.openings:
                heat_flow += op.tech.U * op.area * dt
        return heat_flow

    def _calculate_hvac_power(self, room: Room, current_temp: float) -> float:
        """
        Визначає, чи увімкнений прилад в даний момент часу t, базуючись на профілі.
        """
        profile = self.control_profiles.get(room.id, RoomControlProfile())

        # Якщо режим "Завжди ВИКЛ" - повертаємо 0 одразу
        if profile.mode == ControlMode.ALWAYS_OFF:
            return 0.0

        is_active = False

        # Логіка визначення активності (is_active)
        if profile.mode == ControlMode.ALWAYS_ON:
            is_active = True

        elif profile.mode == ControlMode.THERMOSTAT:
            # Гріємо, якщо холодно (з гістерезисом)
            if current_temp < profile.target_temp - 0.5:
                is_active = True
            # Якщо режим охолодження (кондиціонер)
            # Тут треба складнішу логіку, якщо є і те і те, але поки припустимо:
            # Якщо > Target + 0.5, то active для охолодження

        elif profile.mode == ControlMode.CYCLIC:
            # Математика циклу
            cycle_duration = (profile.cycle_on_hours + profile.cycle_off_hours) * 3600
            if cycle_duration > 0:
                # Поточний час у циклі
                t_mod = (self.current_time_sec + profile.time_offset_hours * 3600) % cycle_duration
                on_duration_sec = profile.cycle_on_hours * 3600

                if t_mod < on_duration_sec:
                    is_active = True
                else:
                    is_active = False

        # Застосування активності до приладів
        total_power = 0.0

        if is_active:
            for device in room.hvac_devices:
                # Для простоти поки вважаємо, що ControlMode керує "основним" режимом.
                # Якщо THERMOSTAT і холодно -> гріємо.
                # Якщо THERMOSTAT і жарко -> студимо.

                if profile.mode == ControlMode.THERMOSTAT:
                    if device.power_heating > 0 and current_temp < profile.target_temp:
                        total_power += device.power_heating
                    elif device.power_cooling > 0 and current_temp > profile.target_temp:
                        total_power -= device.power_cooling
                else:
                    # Для ALWAYS_ON та CYCLIC вмикаємо ВСЕ (або пріоритет нагріву)
                    # Тут можна додати логіку: "Взимку вмикаємо Heater, влітку Cooler"
                    # Поки що просто додаємо нагрів (зимовий сценарій)
                    if device.power_heating > 0:
                        total_power += device.power_heating
                    # Якщо нагріву нема, але є кондюк - вмикаємо кондюк (хочемо заморозити?)
                    elif device.power_cooling > 0:
                        total_power -= device.power_cooling

        return total_power

    def step(self, dt_seconds: float):
        # Визначаємо погоду зараз
        current_outdoor = self._get_current_outdoor_temp()
        self.history_outdoor.append(current_outdoor)

        temp_changes = {}

        for room_id, room in self.building.rooms.items():
            current_t = self.current_temperatures[room_id]

            # Потоки (Втрати + HVAC + Люди)
            q_transmission = self._calculate_transmission_heat_flow(room, current_t, current_outdoor)
            q_hvac = self._calculate_hvac_power(room, current_t)

            # Power (W) * Time (h) / 1000 = kWh
            # Беремо модуль, бо охолодження теж витрачає електрику
            kwh_consumed = abs(q_hvac) * (dt_seconds / 3600.0) / 1000.0
            self.total_energy_kwh[room_id] += kwh_consumed

            # Сумарний потік: Стіни + Обігрів + Побутове тепло
            q_total = q_transmission + q_hvac + self.internal_heat_gain

            c_mass = self._calculate_room_thermal_mass(room)
            delta_t = (q_total * dt_seconds) / c_mass
            temp_changes[room_id] = delta_t

        self.current_time_sec += dt_seconds
        self.history_time.append(self.current_time_sec / 3600.0)

        for rid, change in temp_changes.items():
            self.current_temperatures[rid] += change
            self.history_temps[rid].append(self.current_temperatures[rid])

    def run_simulation(self, duration_hours: int, dt_seconds: int = 60):
        """
        Запускає цикл на заданий час.
        """
        steps = int((duration_hours * 3600) / dt_seconds)
        for _ in range(steps):
            self.step(dt_seconds)

    def get_results_chart(self) -> go.Figure:
        fig = go.Figure()

        # Нам треба масив часу такої ж довжини, як і масив температур
        fig.add_trace(go.Scatter(
            x=self.history_time,
            y=self.history_outdoor,
            mode="lines",
            name="Вулиця",
            line=dict(color="blue", dash="dash", width=2),
            opacity=0.5
        ))

        # Кімнати
        for room_id, temps in self.history_temps.items():
            room_name = self.building.rooms[room_id].name
            fig.add_trace(go.Scatter(
                x=self.history_time,
                y=temps,
                mode="lines",
                name=room_name,
                line=dict(width=3)
            ))

        #   Зони комфорту
        fig.add_hrect(
            y0=20.0, y1=22.0,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="Комфорт", annotation_position="top left"
        )

        fig.update_layout(
            title="Динаміка температурного режиму",
            xaxis_title="Час (години)",
            yaxis_title="Температура (°C)",
            hovermode="x unified",
            height=600,
            template="plotly_white",
            legend=dict(orientation="h", y=1.02, yanchor="bottom")
        )

        return fig
