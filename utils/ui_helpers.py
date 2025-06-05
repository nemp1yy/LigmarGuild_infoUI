from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from datetime import datetime


class TableManager:
    """Менеджер для работы с таблицами"""

    @staticmethod
    def setup_table_view(table_view, model, hide_id=True):
        """Стандартная настройка TableView"""
        table_view.setModel(model)
        table_view.resizeColumnsToContents()
        table_view.setSortingEnabled(True)
        if hide_id:
            table_view.setColumnHidden(0, True)


class MessageHelper:
    """Помощник для показа сообщений"""

    @staticmethod
    def show_error(parent, title, message):
        """Показ сообщения об ошибке"""
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_critical(parent, title, message):
        """Показ критического сообщения"""
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_info(parent, title, message):
        """Показ информационного сообщения"""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_question(parent, title, message, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        """Показ диалога с вопросом"""
        return QMessageBox.question(parent, title, message, buttons)


class ModelHelper:
    """Помощник для работы с моделями данных"""

    @staticmethod
    def set_model_headers(model, headers_dict):
        """Установка заголовков модели

        Args:
            model: Модель данных
            headers_dict: Словарь {column_index: header_name}
        """
        for column, header in headers_dict.items():
            model.setHeaderData(column, Qt.Orientation.Horizontal, header)

    @staticmethod
    def add_row_with_defaults(model, defaults_dict):
        """Добавление строки со значениями по умолчанию

        Args:
            model: Модель данных
            defaults_dict: Словарь {column_index: default_value}

        Returns:
            int: Индекс добавленной строки или -1 при ошибке
        """
        try:
            row = model.rowCount()
            if model.insertRow(row):
                for column, value in defaults_dict.items():
                    model.setData(model.index(row, column), value)
                return row
            return -1
        except Exception:
            return -1


class FormUtils:
    """Утилиты для работы с формами"""

    @staticmethod
    def clear_line_edits(parent):
        """Очистка всех QLineEdit в родительском виджете"""
        for line_edit in parent.findChildren(QtWidgets.QLineEdit):
            line_edit.clear()

    @staticmethod
    def reset_datetime_edits(parent):
        """Сброс всех QDateTimeEdit к текущему времени"""
        current_datetime = QtCore.QDateTime.currentDateTime()
        for date_edit in parent.findChildren(QtWidgets.QDateTimeEdit):
            date_edit.setDateTime(current_datetime)

    @staticmethod
    def reset_combo_boxes(parent):
        """Сброс всех QComboBox к первому элементу"""
        for combo in parent.findChildren(QtWidgets.QComboBox):
            combo.setCurrentIndex(0)

    @staticmethod
    def get_line_edit_values(parent, field_names):
        """Получение значений из QLineEdit по именам полей

        Args:
            parent: Родительский виджет
            field_names (list): Список имен полей

        Returns:
            dict: Словарь {field_name: value}
        """
        values = {}
        for field_name in field_names:
            line_edit = parent.findChild(QtWidgets.QLineEdit, f"lineEdit_{field_name}")
            if line_edit:
                values[field_name] = line_edit.text().strip()
        return values

    @staticmethod
    def get_datetime_range(start_edit, end_edit, default_check_value="2000-01-01 00:00"):
        """Получение временного диапазона из QDateTimeEdit

        Args:
            start_edit: QDateTimeEdit для начального времени
            end_edit: QDateTimeEdit для конечного времени
            default_check_value: Значение для проверки на дефолт

        Returns:
            tuple или None: (start_time, end_time) или None если дефолтные значения
        """
        start_time = start_edit.dateTime().toString("yyyy-MM-dd hh:mm")
        end_time = end_edit.dateTime().toString("yyyy-MM-dd hh:mm")

        if start_time != default_check_value or end_time != default_check_value:
            return (start_time, end_time)
        return None


class SearchConditionBuilder:
    """Построитель условий поиска для SQL запросов"""

    @staticmethod
    def add_like_condition(conditions, params, value, field):
        """Добавление LIKE условия"""
        if value:
            conditions.append(f"{field} LIKE ?")
            params.append(f"%{value}%")

    @staticmethod
    def add_multi_like_condition(conditions, params, value, fields):
        """Добавление множественного LIKE условия"""
        if value:
            condition = " OR ".join([f"{field} LIKE ?" for field in fields])
            conditions.append(f"({condition})")  # Заключаем в скобки для корректности
            params.extend([f"%{value}%"] * len(fields))

    @staticmethod
    def add_time_range_condition(conditions, params, start_time, end_time, field):
        """Добавление условия временного диапазона"""
        if start_time and end_time:
            conditions.append(f"{field} BETWEEN ? AND ?")
            params.extend([start_time, end_time])
        elif start_time:
            conditions.append(f"{field} >= ?")
            params.append(start_time)
        elif end_time:
            conditions.append(f"{field} <= ?")
            params.append(end_time)


class FilterHelper:
    """Помощник для работы с фильтрами таблиц"""

    @staticmethod
    def create_flight_filter_model(source_model, parent=None):
        """Создание модели фильтрации для рейсов

        Args:
            source_model: Исходная модель данных
            parent: Родительский объект

        Returns:
            FlightFilterProxyModel: Настроенная модель фильтрации
        """
        filter_model = FlightFilterProxyModel(parent)
        filter_model.setSourceModel(source_model)

        # Стандартное соответствие колонок для рейсов
        # Адаптируйте под вашу структуру данных
        default_mapping = {
            'flight': 1,  # Номер рейса
            'airline': 2,  # Авиакомпания
            'aircraft_type': 3,  # Тип самолета
            'departure_from': 4,  # Аэропорт отправления
            'destination': 5,  # Аэропорт назначения
            'departure_time': 6,  # Время отправления
            'arrival_time': 7,  # Время прибытия
            'status': 8,  # Статус
            'gate': 9  # Гейт
        }

        filter_model.set_column_mapping(default_mapping)
        return filter_model

    @staticmethod
    def setup_filtered_table(table_view, source_model, parent=None):
        """Настройка таблицы с фильтрацией

        Args:
            table_view: QTableView для отображения данных
            source_model: Исходная модель данных
            parent: Родительский объект

        Returns:
            FlightFilterProxyModel: Настроенная модель фильтрации
        """
        filter_model = FilterHelper.create_flight_filter_model(source_model, parent)

        # Настраиваем таблицу
        table_view.setModel(filter_model)
        table_view.setSortingEnabled(True)
        table_view.resizeColumnsToContents()

        # Скрываем ID колонку если она есть
        if filter_model.columnCount() > 0:
            table_view.setColumnHidden(0, True)

        return filter_model


class MultiFieldFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}  # ключ: номер колонки, значение: фильтр (строка)

    def set_filters(self, filters: dict):
        """Установка фильтров для множественных колонок

        Args:
            filters: Словарь {column_index: search_text}
        """
        self.filters = {k: v for k, v in filters.items() if v.strip()}
        self.invalidateFilter()

    def clear_filters(self):
        """Очистка всех фильтров"""
        self.filters = {}
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Проверка соответствия строки фильтрам"""
        if not self.filters:
            return True

        model = self.sourceModel()

        # Проверяем, содержит ли хотя бы одна из указанных колонок искомый текст
        for column, pattern in self.filters.items():
            if not pattern:
                continue

            index = model.index(source_row, column, source_parent)
            if not index.isValid():
                continue

            data = str(model.data(index, Qt.ItemDataRole.DisplayRole) or "").lower()
            if pattern.lower() in data:
                return True  # Найдено совпадение в одной из колонок

        return False  # Не найдено совпадений ни в одной колонке