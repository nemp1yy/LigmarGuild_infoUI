from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation, \
    QSqlRelationalDelegate
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
import sys
import os
from pathlib import Path


def get_database_path():
    """Получение пути к базе данных"""
    if hasattr(sys, '_MEIPASS'):
        # Запуск из exe
        app_data = os.path.join(os.path.expanduser("~"), "GuildManager")
        return os.path.join(app_data, "ligma.db")
    else:
        # Обычный запуск
        return 'data/ligma.db'


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    @staticmethod
    def connect(db_path=None):
        """Подключение к базе данных"""
        if db_path is None:
            db_path = get_database_path()

        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(db_path)

        if not db.open():
            error_msg = f"Не удалось подключиться к базе данных: {db_path}\n{db.lastError().text()}"
            QMessageBox.critical(None, "Ошибка БД", error_msg)
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
    def create_table_model(db, table_name, where_condition=None):
        """Создание модели таблицы с опциональным WHERE условием"""
        from PyQt6.QtSql import QSqlTableModel
        from PyQt6.QtCore import Qt

        model = QSqlTableModel(db=db)
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)

        # Применяем фильтр если он задан
        if where_condition:
            model.setFilter(where_condition)

        model.select()
        return model

    @staticmethod
    def create_query_model(db, query):
        """Создание модели на основе SQL запроса"""
        from PyQt6.QtSql import QSqlQueryModel

        model = QSqlQueryModel()
        model.setQuery(query, db)
        return model