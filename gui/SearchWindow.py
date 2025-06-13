from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QDialog
from PyQt6.QtSql import QSqlQuery
from utils.database import DatabaseManager
from utils.ui_helpers import FormUtils
import sqlite3
from utils.resource_helper import get_ui_path


class AdvancedSearchWindow(QDialog):
    search_requested = QtCore.pyqtSignal(dict)

    def __init__(self, search_mode="simple", parent=None):
        super().__init__(parent)

        # Определяем какой UI файл загружать в зависимости от режима
        if search_mode == "simple":
            uic.loadUi(get_ui_path("minimalistical_search.ui"), self)
            self.setWindowTitle("Поиск - Простой режим")
        else:
            uic.loadUi(get_ui_path("improoved_search.ui"), self)
            self.setWindowTitle("Поиск - Детальный режим")

        self.search_mode = search_mode
        self.db = DatabaseManager.connect()

        # Инициализация формы
        self._init_form()

        # Подключение событий
        self._connect_events()

    def _init_form(self):
        """Инициализация формы в зависимости от режима"""
        # Загружаем классы в comboBox_4 если он есть
        if hasattr(self, 'comboBox_4'):
            self._load_classes()

        # Устанавливаем значения по умолчанию
        FormUtils.reset_datetime_edits(self)

        # Устанавливаем разумные диапазоны для спинбоксов
        self._set_spinbox_ranges()

    def _load_classes(self):
        """Загрузка классов в comboBox"""
        try:
            # DatabaseManager возвращает QSqlDatabase
            if self.db.isOpen():
                query = QSqlQuery(self.db)
                if query.exec("SELECT name FROM Classes ORDER BY name"):
                    self.comboBox_4.addItem("Все классы")
                    while query.next():
                        class_name = query.value(0)
                        if class_name:  # Проверяем что значение не пустое
                            self.comboBox_4.addItem(class_name)
                else:
                    print(f"Ошибка выполнения запроса: {query.lastError().text()}")
                    self.comboBox_4.addItem("Все классы")
            else:
                print("База данных не открыта")
                self.comboBox_4.addItem("Все классы")

        except Exception as e:
            print(f"Ошибка загрузки классов: {e}")
            # Добавляем базовые значения в случае ошибки
            self.comboBox_4.addItem("Все классы")
            self.comboBox_4.addItem("Ошибка загрузки")

    def _set_spinbox_ranges(self):
        """Установка диапазонов для SpinBox элементов"""
        spinbox_configs = {
            # Уровень
            'spinBox': (1, 100),  # от 1 до 100 уровня
            'spinBox_2': (1, 100),
            # Взносы
            'spinBox_3': (0, 1000000),  # взносы могут быть большими
            'spinBox_4': (0, 1000000),
            # Урон
            'spinBox_5': (0, 10000000),  # урон может быть очень большим
            'spinBox_6': (0, 10000000),
            # Рейды (проценты)
            'spinBox_7': (0, 100),
            'spinBox_8': (0, 100),
            # Если есть дополнительные спинбоксы в детальном режиме
            'spinBox_9': (1, 100),
            'spinBox_10': (1, 100)
        }

        for spinbox_name, (min_val, max_val) in spinbox_configs.items():
            if hasattr(self, spinbox_name):
                spinbox = getattr(self, spinbox_name)
                spinbox.setMinimum(min_val)
                spinbox.setMaximum(max_val)

    def _connect_events(self):
        """Подключение событий кнопок"""
        # Кнопки должны быть в том же порядке что и в UI
        self.pushButton_2.clicked.connect(self._perform_search)  # Найти
        self.pushButton.clicked.connect(self._clear_form)  # Очистить
        self.pushButton_3.clicked.connect(self.reject)  # Отменить

    def _perform_search(self):
        """Выполнение поиска и передача параметров в главное окно"""
        search_params = self._collect_search_params()
        self.search_requested.emit(search_params)
        self.accept()

    def _collect_search_params(self):
        """Сбор параметров поиска в зависимости от режима"""
        params = {
            'mode': self.search_mode,
            'date_range': self._get_date_range(),
            'level_range': self._get_level_range(),
            'status': self._get_status(),
            'role': self._get_role()
        }

        # Дополнительные параметры для детального режима
        if self.search_mode == "detailed":
            params.update({
                'contribution_range': self._get_contribution_range(),
                'damage_range': self._get_damage_range(),
                'raid_range': self._get_raid_range(),
                'class_name': self._get_class()
            })

        return params

    def _get_date_range(self):
        """Получение диапазона дат вступления"""
        if hasattr(self, 'dateEdit') and hasattr(self, 'dateEdit_2'):
            start_date = self.dateEdit.date().toString("yyyy-MM-dd")
            end_date = self.dateEdit_2.date().toString("yyyy-MM-dd")
            return (start_date, end_date)
        return None

    def _get_level_range(self):
        """Получение диапазона уровней"""
        if hasattr(self, 'spinBox') and hasattr(self, 'spinBox_2'):
            min_level = self.spinBox.value()
            max_level = self.spinBox_2.value()
            if min_level > 0 or max_level > 0:
                return (min_level, max_level if max_level > 0 else 100)
        return None

    def _get_contribution_range(self):
        """Получение диапазона взносов (только для детального режима)"""
        if hasattr(self, 'spinBox_3') and hasattr(self, 'spinBox_4'):
            min_contrib = self.spinBox_3.value()
            max_contrib = self.spinBox_4.value()
            if min_contrib > 0 or max_contrib > 0:
                return (min_contrib, max_contrib if max_contrib > 0 else 1000000)
        return None

    def _get_damage_range(self):
        """Получение диапазона урона (только для детального режима)"""
        if hasattr(self, 'spinBox_5') and hasattr(self, 'spinBox_6'):
            min_damage = self.spinBox_5.value()
            max_damage = self.spinBox_6.value()
            if min_damage > 0 or max_damage > 0:
                return (min_damage, max_damage if max_damage > 0 else 10000000)
        return None

    def _get_raid_range(self):
        """Получение диапазона участия в рейдах (только для детального режима)"""
        if hasattr(self, 'spinBox_7') and hasattr(self, 'spinBox_8'):
            min_raid = self.spinBox_7.value()
            max_raid = self.spinBox_8.value()
            if min_raid > 0 or max_raid > 0:
                return (min_raid, max_raid if max_raid > 0 else 100)
        return None

    def _get_status(self):
        """Получение выбранного статуса"""
        if hasattr(self, 'comboBox_2'):
            status = self.comboBox_2.currentText()
            return status if status != "Все статусы" else None
        return None

    def _get_role(self):
        """Получение выбранной роли"""
        if hasattr(self, 'comboBox_3'):
            role = self.comboBox_3.currentText()
            return role if role != "Все роли" else None
        return None

    def _get_class(self):
        """Получение выбранного класса (только для детального режима)"""
        if hasattr(self, 'comboBox_4'):
            class_name = self.comboBox_4.currentText()
            return class_name if class_name != "Все классы" else None
        return None

    def _clear_form(self):
        """Очистка формы"""
        # Сброс дат к значениям по умолчанию
        if hasattr(self, 'dateEdit'):
            self.dateEdit.setDate(self.dateEdit.minimumDate())
        if hasattr(self, 'dateEdit_2'):
            self.dateEdit_2.setDate(self.dateEdit_2.maximumDate())

        # Сброс всех SpinBox к 0
        for i in range(1, 11):
            spinbox_name = f'spinBox_{i}' if i > 1 else 'spinBox'
            if hasattr(self, spinbox_name):
                getattr(self, spinbox_name).setValue(0)

        # Сброс ComboBox к первому элементу
        for combo_name in ['comboBox_2', 'comboBox_3', 'comboBox_4']:
            if hasattr(self, combo_name):
                getattr(self, combo_name).setCurrentIndex(0)