from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
import sys


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    @staticmethod
    def connect(db_path='data/ligma.db'):
        """Подключение к базе данных"""
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(db_path)
        if not db.open():
            QMessageBox.critical(None, "Ошибка БД", "Не удалось подключиться к базе данных")
            sys.exit(1)
        return db

    @staticmethod
    def execute_query(db, query_text, params=None):
        """Выполнение SQL-запроса с параметрами"""
        query = QSqlQuery(db)
        if params:
            query.prepare(query_text)
            for param in params:
                query.addBindValue(param)
            return query.exec()
        return query.exec(query_text)

    @staticmethod
    def create_query_model(db, query_text, params=None):
        """Создание модели запроса"""
        model = QSqlQueryModel()
        query = QSqlQuery(db)

        if params:
            query.prepare(query_text)
            for param in params:
                query.addBindValue(param)
            query.exec()
        else:
            query.exec(query_text)

        model.setQuery(query)
        return model

    @staticmethod
    def create_flights_relational_model(db):
        """Создание реляционной модели с поддержкой фильтрации"""
        model = QSqlRelationalTableModel(db=db)
        model.setTable("flights")

        # Настройка связей (замените индексы на ваши реальные)
        model.setRelation(2, QSqlRelation("airlines", "id", "name"))
        model.setRelation(3, QSqlRelation("aircraft_types", "id", "model"))
        model.setRelation(4, QSqlRelation("airports", "id", "name"))
        model.setRelation(5, QSqlRelation("airports", "id", "name"))
        model.setRelation(8, QSqlRelation("statuses", "id", "name"))
        # Заголовки
        model.setHeaderData(1, Qt.Orientation.Horizontal, "Номер рейса")
        model.setHeaderData(2, Qt.Orientation.Horizontal, "Авиакомпания")
        model.setHeaderData(3, Qt.Orientation.Horizontal, "Самолёт")
        model.setHeaderData(4, Qt.Orientation.Horizontal, "Откуда")
        model.setHeaderData(5, Qt.Orientation.Horizontal, "Куда")
        model.setHeaderData(6, Qt.Orientation.Horizontal, "Время вылета")
        model.setHeaderData(7, Qt.Orientation.Horizontal, "Время прибытия")
        model.setHeaderData(8, Qt.Orientation.Horizontal, "Статус")
        model.setHeaderData(9, Qt.Orientation.Horizontal, "Гейт")

        model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        model.select()

        return model

    @staticmethod
    def create_table_model(db, table_name):
        """Создание простой табличной модели"""
        model = QSqlTableModel(db=db)
        model.setTable(table_name)
        model.select()
        return model


class SQLQueries:
    """Константы SQL-запросов"""

    FLIGHTS_BASE = '''
        SELECT f.id, f.flight_number, al.name AS airline, ac.model AS aircraft,
               dap.{airport_field} AS departure, aap.{airport_field} AS arrival,
               f.departure_time, f.arrival_time, st.name AS status, f.gate
        FROM flights f
        LEFT JOIN airlines al ON f.airline_id = al.id
        LEFT JOIN aircraft_types ac ON f.aircraft_type_id = ac.id
        LEFT JOIN airports dap ON f.departure_airport_id = dap.id
        LEFT JOIN airports aap ON f.arrival_airport_id = aap.id
        LEFT JOIN statuses st ON f.status_id = st.id
    '''

    @classmethod
    def flights_query(cls, airport_field='code'):
        return cls.FLIGHTS_BASE.format(airport_field=airport_field)

    @classmethod
    def search_query(cls):
        return cls.flights_query('name') + " WHERE 1=1"