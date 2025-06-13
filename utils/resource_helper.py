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
    return get_resource_path(fr"gui\design\{ui_filename}")


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


def get_resource_path(relative_path):
    """Получает абсолютный путь к ресурсу, работает как в разработке, так и в exe"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # В режиме разработки используем директорию скрипта
        base_path = Path(__file__).parent.parent

    return os.path.join(base_path, relative_path)


def get_ui_path(ui_file):
    """Получает путь к UI файлу"""
    return get_resource_path(fr"gui\ui\{ui_file}")


def get_icon_path(icon_file):
    """Получает путь к иконке"""
    return get_resource_path(fr"gui\icons\{icon_file}")


def get_image_path(image_file):
    """Получает путь к изображению"""
    return get_resource_path(fr"gui\images\{image_file}")


def setup_window_icon(self):
    """Установка иконки окна"""
    try:
        from PyQt6.QtGui import QIcon

        icon_path = get_icon_path("app_icon.ico")  # или .png
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"Не удалось загрузить иконку окна: {e}")


def setup_button_icons(self):
    """Установка иконок для кнопок"""
    try:
        from PyQt6.QtGui import QIcon

        # Словарь кнопка: файл_иконки
        button_icons = {
            'add_button': 'add.png',
            'delete_button': 'delete.png',
            'refresh_button': 'refresh.png',
            'advanced_search_button': 'search.png'
        }

        for button_name, icon_file in button_icons.items():
            if hasattr(self, button_name):
                icon_path = get_icon_path(icon_file)
                if os.path.exists(icon_path):
                    button = getattr(self, button_name)
                    button.setIcon(QIcon(icon_path))
                else:
                    print(f"Иконка не найдена: {icon_path}")

    except Exception as e:
        print(f"Ошибка при установке иконок кнопок: {e}")
