import os
import sys
import pytest
from building import Building
from bulding_compounds.material import MATERIALS


tests_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(tests_dir, "../.."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def app_path():
    """Повертає абсолютний шлях до main.py в корені проєкту"""
    path = os.path.join(project_root, "main.py")

    # Додаткова перевірка, щоб точно знати, що файл існує
    if not os.path.exists(path):
        raise FileNotFoundError(f"main.py не знайдено за шляхом: {path}")

    return path
