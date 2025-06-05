from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtSql import QSqlTableModel
from PyQt6.QtCore import Qt

from utils.database import DatabaseManager
from utils.ui_helpers import TableManager, MessageHelper


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/design/main.ui", self)

        self.db = DatabaseManager.connect()
        self.model = QSqlTableModel(db=self.db)
        self.model.setTable("Players")

        # Настройка заголовков
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Никнейм")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Тег")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Класс")
        self.model.setHeaderData(4, Qt.Orientation.Horizontal, "Уровень")
        self.model.setHeaderData(5, Qt.Orientation.Horizontal, "Дата вступления")
        self.model.setHeaderData(6, Qt.Orientation.Horizontal, "Статус")

        self.model.select()

        self.tableView.setModel(self.model)
        TableManager.setup_table_view(self.tableView, self.model)

        self._connect_buttons()
        self._connect_menu()
        self.tableView.doubleClicked.connect(self._edit_row)

        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage(f"Всего записей: {self.model.rowCount()}")

    def _connect_buttons(self):
        self.add_button.clicked.connect(self._add_row)
        self.delete_button.clicked.connect(self._delete_row)
        self.refresh_button.clicked.connect(self._refresh)
        self.search_button.clicked.connect(self._show_search)

    def _connect_menu(self):
        if hasattr(self, 'action_3'):  # "Показывать"
            self.action_3.triggered.connect(self._show_all)
        if hasattr(self, 'action_4'):  # "Скрыть"
            self.action_4.triggered.connect(self._hide_inactive)

    def _add_row(self):
        """Добавление новой записи"""
        try:
            row = self.model.rowCount()
            self.model.insertRow(row)

            # Устанавливаем значения по умолчанию
            self.model.setData(self.model.index(row, 1), "Новый игрок")  # nickname
            self.model.setData(self.model.index(row, 2), "@newuser")  # tag
            self.model.setData(self.model.index(row, 3), 1)  # class_id
            self.model.setData(self.model.index(row, 4), 1)  # level
            self.model.setData(self.model.index(row, 5), "2024-01-01")  # joined_date
            self.model.setData(self.model.index(row, 6), "Активен")  # guild_status

            if self.model.submitAll():
                if hasattr(self, 'statusbar'):
                    self.statusbar.showMessage(f"Запись добавлена. Всего записей: {self.model.rowCount()}")
            else:
                MessageHelper.show_error(self, "Ошибка",
                                         f"Не удалось добавить запись: {self.model.lastError().text()}")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Ошибка добавления: {e}")

    def _edit_row(self):
        """Редактирование выбранной записи через двойной клик"""
        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка для редактирования")
            return

        # Включаем режим редактирования
        self.tableView.edit(index)

    def _delete_row(self):
        """Удаление выбранной записи"""
        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка для удаления")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите удалить выбранную запись?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.model.removeRow(index.row()):
                if self.model.submitAll():
                    if hasattr(self, 'statusbar'):
                        self.statusbar.showMessage(f"Запись удалена. Всего записей: {self.model.rowCount()}")
                else:
                    MessageHelper.show_error(self, "Ошибка",
                                             f"Не удалось удалить запись: {self.model.lastError().text()}")
            else:
                MessageHelper.show_error(self, "Ошибка", "Не удалось удалить строку")

    def _refresh(self):
        """Обновление данных"""
        self.model.setFilter("")
        self.model.select()
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage(f"Обновлено. Всего записей: {self.model.rowCount()}")

    def _show_search(self):
        """Показ поиска по введенному тексту"""
        search_text = self.lineEdit.text().strip()
        if search_text and search_text != "Введите игрока для поиска":
            filter_text = f"nickname LIKE '%{search_text}%' OR tag LIKE '%{search_text}%'"
            self.model.setFilter(filter_text)
            self.model.select()
            if hasattr(self, 'statusbar'):
                self.statusbar.showMessage(f"Найдено: {self.model.rowCount()} записей")
        else:
            self._refresh()

    def _show_all(self):
        """Показать все записи"""
        self.model.setFilter("")
        self.model.select()
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage(f"Показаны все записи: {self.model.rowCount()}")

    def _hide_inactive(self):
        """Скрыть неактивных игроков"""
        self.model.setFilter("guild_status = 'Активен'")
        self.model.select()
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage(f"Показаны только активные: {self.model.rowCount()}")