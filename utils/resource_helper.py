import sys
import os
from pathlib import Path


def get_resource_path(relative_path):
    """
    Получение корректного пути к ресурсу для PyInstaller

    Args:
        relative_path (str): Относительный путь к ресурсу

    Returns:
        str: Абсолютный путь к ресурсу
    """
    if hasattr(sys, '_MEIPASS'):
        # Запуск из exe файла (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Обычный запуск из исходного кода
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Поднимаемся на уровень выше, так как этот файл в utils/
        base_path = os.path.dirname(base_path)

    return os.path.join(base_path, relative_path)


def get_ui_path(ui_filename):
    """
    Получение пути к UI файлу

    Args:
        ui_filename (str): Имя UI файла (например, 'main.ui')

    Returns:
        str: Путь к UI файлу
    """
    return get_resource_path(f"gui/design/{ui_filename}")


def get_database_path():
    """Получение пути к базе данных для exe"""
    if hasattr(sys, '_MEIPASS'):
        # Для exe версии сохраняем БД в папке пользователя
        app_data = os.path.join(os.path.expanduser("~"), "GuildManager")
        os.makedirs(app_data, exist_ok=True)
        return os.path.join(app_data, "ligma.db")
    else:
        # Для обычного запуска
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "ligma.db")