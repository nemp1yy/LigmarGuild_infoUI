from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt, QTimer

from gui.ReferenceWindow import ReferenceWindow
from gui.SearchWindow import SearchWindow

from utils.database import DatabaseManager
from utils.ui_helpers import TableManager, MessageHelper, MultiFieldFilterProxyModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/design/main.ui", self)

        # Подключение к БД и создание модели
        self.db = DatabaseManager.connect()
        self.current_view_mode = "simple"  # "simple" или "detailed"

        # Создание моделей для разных режимов
        self.simple_model = self._create_simple_model()
        self.detailed_model = self._create_detailed_model()

        # Создание прокси-модели для фильтрации
        self.filter_model = MultiFieldFilterProxyModel()
        self.filter_model.setSourceModel(self.simple_model)

        # Настройка таблицы
        self.tableView.setModel(self.filter_model)
        TableManager.setup_table_view(self.tableView, self.filter_model)

        # Настройка поиска в реальном времени
        self._setup_realtime_search()

        # Подключение событий
        self._connect_buttons()
        self._connect_menu()
        self.tableView.doubleClicked.connect(self._edit_row)

        # Обновление статус-бара
        self._update_status_bar()

    def _create_simple_model(self):
        """Создание простой модели (менее информативной)"""
        model = DatabaseManager.create_table_model(self.db, "Players")

        # Настройка заголовков для простого режима
        headers = {
            1: "Никнейм",
            2: "Тег",
            4: "Уровень",
            5: "Дата вступления",
            6: "Статус"
        }

        for column, header in headers.items():
            model.setHeaderData(column, Qt.Orientation.Horizontal, header)

        return model

    def _create_detailed_model(self):
        """Создание детальной модели с JOIN"""
        query = """
        SELECT 
            p.id,
            p.nickname,
            p.tag,
            c.name as class_name,
            p.level,
            p.joined_date,
            p.guild_status,
            COALESCE(a.weekly_damage, 0) as weekly_damage,
            COALESCE(a.raid_participation, 0) as raid_participation,
            COALESCE(gc.leadership_rank, 'Участник') as leadership_rank,
            COALESCE(gc.resources_contributed, 0) as resources_contributed
        FROM Players p
        LEFT JOIN Classes c ON p.class_id = c.id
        LEFT JOIN Activity a ON p.id = a.player_id
        LEFT JOIN GuildContribution gc ON p.id = gc.player_id
        ORDER BY p.nickname
        """

        model = DatabaseManager.create_query_model(self.db, query)

        # Настройка заголовков для детального режима
        headers = [
            "ID", "Никнейм", "Тег", "Класс", "Уровень", "Дата вступления",
            "Статус", "Урон за неделю", "Участие в рейдах", "Роль", "Взносы"
        ]

        for i, header in enumerate(headers):
            model.setHeaderData(i, Qt.Orientation.Horizontal, header)

        return model

    def _setup_realtime_search(self):
        """Настройка поиска в реальном времени"""
        # Создаем таймер для задержки поиска
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        # Подключаем изменение текста к таймеру
        self.lineEdit.textChanged.connect(self._on_search_text_changed)

    def _on_search_text_changed(self):
        """Обработчик изменения текста поиска"""
        # Перезапускаем таймер при каждом изменении текста
        self.search_timer.stop()
        self.search_timer.start(300)  # Задержка 300ms

    def _perform_search(self):
        """Выполнение поиска"""
        search_text = self.lineEdit.text().strip()

        if not search_text:
            # Если поиск пустой, убираем все фильтры
            self.filter_model.clear_filters()
        else:
            # Определяем колонки для поиска в зависимости от режима
            if self.current_view_mode == "simple":
                # Поиск по никнейму, тегу и статусу
                search_filters = {
                    1: search_text,  # nickname
                    2: search_text,  # tag
                    6: search_text  # guild_status
                }
            else:
                # Поиск по всем видимым колонкам в детальном режиме
                search_filters = {
                    1: search_text,  # nickname
                    2: search_text,  # tag
                    3: search_text,  # class_name
                    6: search_text,  # guild_status
                    9: search_text  # leadership_rank
                }

            self.filter_model.set_filters(search_filters)

        self._update_status_bar()

    def _connect_buttons(self):
        """Подключение кнопок к методам"""
        self.add_button.clicked.connect(self._add_row)
        self.delete_button.clicked.connect(self._delete_row)
        self.refresh_button.clicked.connect(self._refresh)
        # Убираем старую кнопку поиска, так как теперь поиск в реальном времени

    def _connect_menu(self):
        """Подключение меню к методам"""
        if hasattr(self, 'action_3'):  # "Простой вид"
            self.action_3.triggered.connect(self._switch_to_simple_view)
        if hasattr(self, 'action_4'):  # "Детальный вид"
            self.action_4.triggered.connect(self._switch_to_detailed_view)

        menu_actions = {
            self.actionActivity: "Activity",
            self.actionClasses: "Classes",
            self.actionGuild: "GuildContribution",
            self.actionEvents: "EventParticipation"
        }
        for action, table in menu_actions.items():
            action.triggered.connect(lambda checked, t=table: ReferenceWindow(t, self).exec())

    def _switch_to_simple_view(self):
        """Переключение на простой вид"""
        if self.current_view_mode != "simple":
            self.current_view_mode = "simple"
            self.filter_model.setSourceModel(self.simple_model)

            # Скрываем лишние колонки в простом режиме
            self.tableView.setColumnHidden(0, True)  # ID
            self.tableView.setColumnHidden(3, True)  # class_id (скрываем, показываем только в детальном)

            self.tableView.resizeColumnsToContents()
            self._update_status_bar("Переключено на простой вид")

            # Очищаем поиск и выполняем заново
            self._perform_search()

    def _switch_to_detailed_view(self):
        """Переключение на детальный вид"""
        if self.current_view_mode != "detailed":
            self.current_view_mode = "detailed"
            self.filter_model.setSourceModel(self.detailed_model)

            # В детальном режиме показываем все колонки кроме ID
            self.tableView.setColumnHidden(0, True)  # ID
            for i in range(1, self.detailed_model.columnCount()):
                self.tableView.setColumnHidden(i, False)

            self.tableView.resizeColumnsToContents()
            self._update_status_bar("Переключено на детальный вид")

            # Очищаем поиск и выполняем заново
            self._perform_search()

    def _add_row(self):
        """Добавление новой записи"""
        # Добавление работает только с основной таблицей Players
        if self.current_view_mode == "detailed":
            MessageHelper.show_info(self, "Информация",
                                    "Для добавления записей переключитесь на простой вид")
            return

        try:
            row = self.simple_model.rowCount()
            self.simple_model.insertRow(row)

            # Устанавливаем значения по умолчанию
            default_values = {
                1: "Новый игрок",  # nickname
                2: "@newuser",  # tag
                3: 1,  # class_id
                4: 1,  # level
                5: "2024-01-01",  # joined_date
                6: "Активен"  # guild_status
            }

            for column, value in default_values.items():
                self.simple_model.setData(self.simple_model.index(row, column), value)

            if self.simple_model.submitAll():
                self._update_status_bar("Запись добавлена")
                # Обновляем детальную модель
                self.detailed_model.setQuery(self.detailed_model.query().lastQuery())
            else:
                MessageHelper.show_error(self, "Ошибка",
                                         f"Не удалось добавить запись: {self.simple_model.lastError().text()}")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Ошибка добавления: {e}")

    def _edit_row(self):
        """Редактирование выбранной записи через двойной клик"""
        if self.current_view_mode == "detailed":
            MessageHelper.show_info(self, "Информация",
                                    "Для редактирования записей переключитесь на простой вид")
            return

        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка для редактирования")
            return

        # Получаем индекс в исходной модели
        source_index = self.filter_model.mapToSource(index)
        self.tableView.edit(source_index)

    def _delete_row(self):
        """Удаление выбранной записи"""
        if self.current_view_mode == "detailed":
            MessageHelper.show_info(self, "Информация",
                                    "Для удаления записей переключитесь на простой вид")
            return

        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка для удаления")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите удалить выбранную запись?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Получаем индекс в исходной модели
            source_index = self.filter_model.mapToSource(index)

            if self.simple_model.removeRow(source_index.row()):
                if self.simple_model.submitAll():
                    self._update_status_bar("Запись удалена")
                    # Обновляем детальную модель
                    self.detailed_model.setQuery(self.detailed_model.query().lastQuery())
                else:
                    MessageHelper.show_error(self, "Ошибка",
                                             f"Не удалось удалить запись: {self.simple_model.lastError().text()}")
            else:
                MessageHelper.show_error(self, "Ошибка", "Не удалось удалить строку")

    def _refresh(self):
        """Обновление данных"""
        if self.current_view_mode == "simple":
            self.simple_model.select()
        else:
            # Для детальной модели перевыполняем запрос
            self.detailed_model.setQuery(self.detailed_model.query().lastQuery())

        self.filter_model.clear_filters()
        self.lineEdit.clear()
        self._update_status_bar("Обновлено")

    def _update_status_bar(self, message=""):
        """Обновление статус-бара"""
        if hasattr(self, 'statusbar'):
            current_model = self.simple_model if self.current_view_mode == "simple" else self.detailed_model
            total_records = current_model.rowCount()
            visible_records = self.filter_model.rowCount()

            if message:
                if visible_records != total_records:
                    self.statusbar.showMessage(f"{message}. Показано: {visible_records} из {total_records}")
                else:
                    self.statusbar.showMessage(f"{message}. Всего записей: {total_records}")
            else:
                if visible_records != total_records:
                    self.statusbar.showMessage(f"Показано: {visible_records} из {total_records}")
                else:
                    self.statusbar.showMessage(f"Всего записей: {total_records}")