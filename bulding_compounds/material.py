from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid

# Матеріал
import uuid
from dataclasses import dataclass, field


@dataclass
class Material:
    name: str = "Default material"
    thickness: float = 1.0  # м
    conductivity: float = 1.0  # Вт/(м·К)
    density: float = 1.0  # кг/м³
    specific_heat: float = 1.0  # Дж/(кг·К)
    color: str = "#888888"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        """Перевірка фізичних параметрів на адекватність."""
        if not self.name:
            raise ValueError("Material name cannot be empty")
        # Товщина не може бути 0 або менше
        if self.thickness <= 0:
            raise ValueError(f"Thickness must be > 0. Got: {self.thickness}")
        # Теплопровідність має бути додатною
        if self.conductivity <= 0:
            raise ValueError(f"Conductivity must be > 0. Got: {self.conductivity}")
        # Щільність та теплоємність для розрахунку інерції
        if self.density <= 0:
            raise ValueError(f"Density must be > 0. Got: {self.density}")
        if self.specific_heat <= 0:
            raise ValueError(f"Specific heat must be > 0. Got: {self.specific_heat}")

    @property
    def U(self) -> float:
        """
        Розрахунок коефіцієнта теплопередачі U (W/m²K).
        R = thickness / conductivity
        U = 1 / (R + 0.17)
        """
        # Тут ділення на 0 вже неможливе завдяки post_init
        r_value = self.thickness / self.conductivity
        return round(1 / (r_value + 0.17), 3)

    @property
    def thermal_mass(self) -> float:
        """
        Теплоємність 1 м² стіни (Дж/К).
        """
        return self.density * self.thickness * self.specific_heat


MATERIALS = {
    # =========================================================================
    # 1. КЛАСИЧНА ЦЕГЛА (Masonry)
    # Висока інерція, погана ізоляція без утеплення
    # =========================================================================
    "Brick_Red_120": Material(
        name="Цегла червона (перегородка) 120мм",
        thickness=0.12,
        conductivity=0.70,  # Типова λ для кладки
        density=1800,
        specific_heat=880,
        color="#B22222"
    ),
    "Brick_Red_250": Material(
        name="Цегла червона повнотіла 250мм (в 1 цеглу)",
        thickness=0.25,
        conductivity=0.70,
        density=1800,
        specific_heat=880,
        color="#8B0000"
    ),
    "Brick_Red_380": Material(
        name="Цегла червона повнотіла 380мм (в 1.5 цегли)",
        thickness=0.38,
        conductivity=0.70,
        density=1800,
        specific_heat=880,
        color="#A52A2A"
    ),
    "Brick_Red_510": Material(
        name="Цегла червона повнотіла 510мм (в 2 цегли)",
        thickness=0.51,
        conductivity=0.70,
        density=1800,
        specific_heat=880,
        color="#800000"
    ),
    "Brick_Silicate_250": Material(
        name="Цегла силікатна (біла) 250мм",
        thickness=0.25,
        conductivity=0.85,  # Холодніша за червону
        density=1900,
        specific_heat=840,
        color="#D3D3D3"
    ),
    "Brick_Hollow_380": Material(
        name="Цегла пустотіла (ефективна) 380мм",
        thickness=0.38,
        conductivity=0.50,  # Краща ізоляція завдяки повітрю
        density=1400,
        specific_heat=880,
        color="#CD5C5C"
    ),

    # =========================================================================
    # 2. ГАЗОБЕТОН ТА ПІНОБЕТОН (Aerated Concrete)
    # Найпопулярніший сучасний матеріал. Легкий, теплий.
    # =========================================================================
    "Aeroc_D300_300": Material(
        name="Газобетон D300 300мм (Super Plus)",
        thickness=0.30,
        conductivity=0.08,  # Дуже теплий
        density=300,
        specific_heat=1000,
        color="#F0F8FF"
    ),
    "Aeroc_D300_375": Material(
        name="Газобетон D300 375мм (Енергоефективний)",
        thickness=0.375,
        conductivity=0.08,
        density=300,
        specific_heat=1000,
        color="#F0FFFF"
    ),
    "Aeroc_D400_300": Material(
        name="Газобетон D400 300мм (Стандарт)",
        thickness=0.30,
        conductivity=0.11,
        density=400,
        specific_heat=1000,
        color="#E6E6FA"
    ),
    "Aeroc_D400_400": Material(
        name="Газобетон D400 400мм",
        thickness=0.40,
        conductivity=0.11,
        density=400,
        specific_heat=1000,
        color="#DCDCDC"
    ),
    "Aeroc_D500_300": Material(
        name="Газобетон D500 300мм (Конструкційний)",
        thickness=0.30,
        conductivity=0.13,
        density=500,
        specific_heat=1000,
        color="#C0C0C0"
    ),

    # =========================================================================
    # 3. КЕРАМІЧНІ БЛОКИ (Ceramic Blocks / Porotherm)
    # Екологічні, теплі, пустотілі.
    # =========================================================================
    "Keramoblock_380": Material(
        name="Керамоблок 380мм (Porotherm 38)",
        thickness=0.38,
        conductivity=0.14,
        density=800,
        specific_heat=920,
        color="#E9967A"
    ),
    "Keramoblock_440": Material(
        name="Керамоблок 440мм (Porotherm 44)",
        thickness=0.44,
        conductivity=0.13,
        density=750,
        specific_heat=920,
        color="#FFA07A"
    ),

    # =========================================================================
    # 4. БЕТОН (Concrete)
    # Важкий, холодний, величезна інерція.
    # =========================================================================
    "Concrete_Reinforced_200": Material(
        name="Залізобетонна стіна 200мм",
        thickness=0.20,
        conductivity=2.04,  # Дуже висока провідність
        density=2500,
        specific_heat=840,
        color="#708090"
    ),
    "Concrete_Panel_160": Material(
        name="Бетонна панель (Хрущовка/Панелька) 160мм",
        thickness=0.16,
        conductivity=1.80,
        density=2400,
        specific_heat=840,
        color="#808080"
    ),

    # =========================================================================
    # 5. КОМПОЗИТНІ / УТЕПЛЕНІ СТІНИ (Insulated / Composite)
    # Тут використано "Ефективну провідність" (Effective Conductivity).
    # Розраховано так, щоб при заданій товщині U було правильним.
    # =========================================================================
    "Brick_Retrofit_EPS": Material(
        name="Цегла 250мм + Пінопласт 100мм",
        thickness=0.35,  # 0.25 + 0.10
        conductivity=0.12,  # Ефективна λ сендвіча
        density=1300,  # Усереднена щільність
        specific_heat=950,
        color="#CD5C5C"
    ),
    "Brick_Retrofit_Wool": Material(
        name="Цегла 380мм + Мінвата 120мм",
        thickness=0.50,
        conductivity=0.15,
        density=1400,
        specific_heat=900,
        color="#A52A2A"
    ),
    "Concrete_Insulated": Material(
        name="Моноліт 200мм + Вата 150мм (Новобудова)",
        thickness=0.35,
        conductivity=0.09,  # Бетон не працює як ізолятор, працює вата
        density=1500,  # Важкий бетон + легка вата
        specific_heat=840,  # Інерція визначається бетоном
        color="#778899"
    ),

    # =========================================================================
    # 6. КАРКАСНІ ТА ДЕРЕВ'ЯНІ БУДИНКИ (Timber & Frame)
    # =========================================================================
    "Pine_Log_200": Material(
        name="Зруб сосновий 200мм",
        thickness=0.20,
        conductivity=0.15,
        density=500,
        specific_heat=2300,  # Дерево довго тримає тепло
        color="#D2691E"
    ),
    "Glued_Timber_200": Material(
        name="Клеєний брус 200мм",
        thickness=0.20,
        conductivity=0.13,  # Щільніше прилягання, менше втрат
        density=600,
        specific_heat=2300,
        color="#DAA520"
    ),
    "SIP_Panel_170": Material(
        name="СІП-панель 170мм (OSB+EPS+OSB)",
        thickness=0.17,
        conductivity=0.045,  # Практично чистий пінопласт за властивостями
        density=50,  # Дуже легка
        specific_heat=1400,
        color="#FFE4B5"
    ),
    "Frame_Wall_200": Material(
        name="Каркасна стіна 200мм (Мінвата в стійках)",
        thickness=0.20,
        conductivity=0.045,  # Дуже низька (тепла)
        density=80,  # Майже невагома (вата)
        specific_heat=1000,
        color="#FFFACD"
    ),

    # =========================================================================
    # 7. ЕКО / ПРИРОДНІ МАТЕРІАЛИ (Natural)
    # =========================================================================
    "Adobe_600": Material(
        name="Саманна стіна (глина+солома) 600мм",
        thickness=0.60,
        conductivity=0.50,
        density=1200,
        specific_heat=1300,  # Величезна теплоємність (прохолодно влітку)
        color="#8B4513"
    ),
    "Straw_Bale_450": Material(
        name="Пресована солома 450мм",
        thickness=0.45,
        conductivity=0.06,  # Дуже тепла
        density=100,
        specific_heat=1300,
        color="#EEE8AA"
    ),
    "Limestone_400": Material(
        name="Ракушняк (Одеський камінь) 400мм",
        thickness=0.40,
        conductivity=0.60,  # Залежить від пористості
        density=1400,
        specific_heat=920,
        color="#F5DEB3"
    ),

    # =========================================================================
    # 8. ПЕРЕГОРОДКИ (Internal Partitions)
    # Внутрішні стіни, не для зовнішнього периметра, але мають масу
    # =========================================================================
    "Gypsum_Drywall_100": Material(
        name="Гіпсокартонна перегородка 100мм",
        thickness=0.10,
        conductivity=0.15,  # За рахунок вати всередині
        density=300,  # Легка
        specific_heat=1000,
        color="#FFFAFA"
    ),
    "Gypsum_Block_80": Material(
        name="Пазогребнева гіпсова плита 80мм",
        thickness=0.08,
        conductivity=0.40,
        density=1000,
        specific_heat=1000,
        color="#FFFFFF"
    ),
    "Glass_Block_80": Material(
        name="Склоблок 80мм",
        thickness=0.08,
        conductivity=0.50,  # Трохи краще ніж скло за рахунок вакууму
        density=2000,
        specific_heat=750,
        color="#E0FFFF"
    )
}

