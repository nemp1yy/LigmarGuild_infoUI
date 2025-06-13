from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QMainWindow, QDialog
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtSql import QSqlQuery

from gui.ReferenceWindow import ReferenceWindow
from gui.SearchWindow import AdvancedSearchWindow
from gui.PlayerDetailDialog import PlayerDetailDialog

from utils.database import DatabaseManager
from utils.ui_helpers import TableManager, MessageHelper, MultiFieldFilterProxyModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        from utils.resource_helper import get_ui_path
        uic.loadUi(get_ui_path("main.ui"), self)

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
            3: "Класс",
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
        try:
            """Подключение кнопок к методам"""
            self.add_button.clicked.connect(self._add_row)
            self.delete_button.clicked.connect(self._delete_row)
            self.refresh_button.clicked.connect(self._refresh)

            # Добавляем кнопку расширенного поиска
            if hasattr(self, 'advanced_search_button'):
                self.advanced_search_button.clicked.connect(self._open_advanced_search)

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", "Не удалось обновить таблицу")
            print(f"Ошибка при обновлении таблицы: {e}")

    def _connect_menu(self):
        """Подключение меню к методам"""
        if hasattr(self, 'action_3'):  # "Простой вид"
            self.action_3.triggered.connect(self._switch_to_simple_view)
        if hasattr(self, 'action_4'):  # "Детальный вид"
            self.action_4.triggered.connect(self._switch_to_detailed_view)

        # Добавляем пункт меню для расширенного поиска
        if hasattr(self, 'action_advanced_search'):
            self.action_advanced_search.triggered.connect(self._open_advanced_search)

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
        """Добавление нового игрока через диалог"""
        try:
            # Открываем диалог для нового игрока (без player_id)
            dialog = PlayerDetailDialog(None, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Если игрок был добавлен, обновляем таблицу
                self._refresh()
                self._update_status_bar("Новый игрок добавлен")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Не удалось добавить игрока: {e}")
            print(f"Ошибка в _add_row: {e}")

    def _edit_row(self):
        """Открытие детального просмотра игрока через двойной клик"""
        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка")
            return

        try:
            # Получаем индекс в исходной модели
            source_index = self.filter_model.mapToSource(index)

            # Получаем ID игрока (всегда в колонке 0)
            if self.current_view_mode == "simple":
                player_id = self.simple_model.data(self.simple_model.index(source_index.row(), 0))
            else:
                player_id = self.detailed_model.data(self.detailed_model.index(source_index.row(), 0))

            if not player_id:
                MessageHelper.show_error(self, "Ошибка", "Не удалось получить ID игрока")
                return

            # Открываем диалог детального просмотра
            dialog = PlayerDetailDialog(player_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Если данные были сохранены, обновляем таблицу
                self._refresh()
                self._update_status_bar("Данные игрока обновлены")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Не удалось открыть детали игрока: {e}")
            print(f"Ошибка в _edit_row: {e}")

    def _refresh(self):
        """Обновление данных"""
        try:
            if self.current_view_mode == "simple":
                # Для простого режима - пересоздаем модель
                self.simple_model = self._create_simple_model()
                self.filter_model.setSourceModel(self.simple_model)
            else:
                # Для детального режима - пересоздаем модель
                self.detailed_model = self._create_detailed_model()
                self.filter_model.setSourceModel(self.detailed_model)

                # Настройка видимости колонок для детального режима
                self.tableView.setColumnHidden(0, True)  # ID
                for i in range(1, self.detailed_model.columnCount()):
                    self.tableView.setColumnHidden(i, False)

            # Очищаем фильтры и поисковую строку
            self.filter_model.clear_filters()
            self.lineEdit.clear()

            # Обновляем размеры колонок
            self.tableView.resizeColumnsToContents()

            self._update_status_bar("Обновлено")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Не удалось обновить таблицу: {e}")
            print(f"Ошибка при обновлении таблицы: {e}")

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

    def _open_advanced_search(self):
        search_window = AdvancedSearchWindow(self.current_view_mode, self)
        search_window.search_requested.connect(self._apply_advanced_search)
        search_window.exec()

    def _apply_advanced_search(self, search_params):
        """Применение параметров расширенного поиска"""
        try:
            # Очищаем предыдущие фильтры
            self.filter_model.clear_filters()

            # Строим WHERE условие на основе параметров
            where_conditions = self._build_search_conditions(search_params)

            if where_conditions:
                if search_params['mode'] == "simple":
                    # Для простого режима применяем фильтр к существующей модели
                    self._apply_simple_search_filter(where_conditions)
                else:
                    # Для детального режима модифицируем SQL запрос
                    self._apply_detailed_search_filter(where_conditions)

            self._update_status_bar("Применен расширенный поиск")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка поиска", f"Не удалось применить поиск: {e}")

    def _build_search_conditions(self, params):
        """Построение SQL условий на основе параметров поиска"""
        conditions = []

        # Диапазон дат вступления
        if params.get('date_range'):
            start_date, end_date = params['date_range']
            conditions.append(f"joined_date BETWEEN '{start_date}' AND '{end_date}'")

        # Диапазон уровней
        if params.get('level_range'):
            min_level, max_level = params['level_range']
            conditions.append(f"level BETWEEN {min_level} AND {max_level}")

        # Статус
        if params.get('status'):
            conditions.append(f"guild_status = '{params['status']}'")

        # Для детального режима добавляем дополнительные условия
        if params['mode'] == "detailed":
            # Диапазон взносов
            if params.get('contribution_range'):
                min_contrib, max_contrib = params['contribution_range']
                conditions.append(f"COALESCE(gc.resources_contributed, 0) BETWEEN {min_contrib} AND {max_contrib}")

            # Диапазон урона
            if params.get('damage_range'):
                min_damage, max_damage = params['damage_range']
                conditions.append(f"COALESCE(a.weekly_damage, 0) BETWEEN {min_damage} AND {max_damage}")

            # Диапазон участия в рейдах
            if params.get('raid_range'):
                min_raid, max_raid = params['raid_range']
                conditions.append(f"COALESCE(a.raid_participation, 0) BETWEEN {min_raid} AND {max_raid}")

            # Класс
            if params.get('class_name'):
                conditions.append(f"c.name = '{params['class_name']}'")

            # Роль
            if params.get('role'):
                conditions.append(f"COALESCE(gc.leadership_rank, 'Участник') = '{params['role']}'")

        return " AND ".join(conditions)

    def _apply_simple_search_filter(self, where_conditions):
        """Применение фильтра для простого режима"""
        # Создаем новую модель с фильтром
        model = DatabaseManager.create_table_model(self.db, "Players", where_conditions)

        # Настройка заголовков
        headers = {
            1: "Никнейм",
            2: "Тег",
            4: "Уровень",
            5: "Дата вступления",
            6: "Статус"
        }

        for column, header in headers.items():
            model.setHeaderData(column, Qt.Orientation.Horizontal, header)

        # Обновляем модель
        self.simple_model = model
        if self.current_view_mode == "simple":
            self.filter_model.setSourceModel(self.simple_model)

    def _apply_detailed_search_filter(self, where_conditions):
        """Применение фильтра для детального режима"""
        try:
            # Модифицируем базовый запрос добавив WHERE условие
            base_query = """
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
            WHERE {where_conditions}
            ORDER BY p.nickname
            """.format(where_conditions=where_conditions)

            # Создаем новую модель с модифицированным запросом
            model = DatabaseManager.create_query_model(self.db, base_query)

            # Проверяем, что модель создалась успешно
            if not model or model.lastError().isValid():
                error_text = model.lastError().text() if model else "Неизвестная ошибка"
                raise Exception(f"Ошибка создания модели: {error_text}")

            # Настройка заголовков
            headers = [
                "ID", "Никнейм", "Тег", "Класс", "Уровень", "Дата вступления",
                "Статус", "Урон за неделю", "Участие в рейдах", "Роль", "Взносы"
            ]

            for i, header in enumerate(headers):
                model.setHeaderData(i, Qt.Orientation.Horizontal, header)

            # Обновляем модель
            self.detailed_model = model
            if self.current_view_mode == "detailed":
                self.filter_model.setSourceModel(self.detailed_model)

        except Exception as e:
            print(f"Ошибка в _apply_detailed_search_filter: {e}")
            # В случае ошибки возвращаемся к исходной модели
            self.detailed_model = self._create_detailed_model()
            if self.current_view_mode == "detailed":
                self.filter_model.setSourceModel(self.detailed_model)
            raise e

    def _clear_advanced_search(self):
        """Очистка расширенного поиска и возврат к исходным данным"""
        try:
            # Используем тот же механизм что и в refresh
            self._refresh()
            self._update_status_bar("Поиск очищен")
        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Не удалось очистить поиск: {e}")
            print(f"Ошибка при очистке поиска: {e}")

    def _delete_row(self):
        """Удаление выбранной записи"""
        index = self.tableView.currentIndex()
        if not index.isValid():
            MessageHelper.show_error(self, "Ошибка", "Не выбрана строка для удаления")
            return

        try:
            # Получаем индекс в исходной модели
            source_index = self.filter_model.mapToSource(index)

            # Получаем ID игрока и никнейм для подтверждения
            if self.current_view_mode == "simple":
                player_id = self.simple_model.data(self.simple_model.index(source_index.row(), 0))
                nickname = self.simple_model.data(self.simple_model.index(source_index.row(), 1))
            else:
                player_id = self.detailed_model.data(self.detailed_model.index(source_index.row(), 0))
                nickname = self.detailed_model.data(self.detailed_model.index(source_index.row(), 1))

            if not player_id:
                MessageHelper.show_error(self, "Ошибка", "Не удалось получить ID игрока")
                return

            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить игрока '{nickname}'?\n\n"
                "Это действие также удалит все связанные данные:\n"
                "- Активность игрока\n"
                "- Вклад в гильдию\n"
                "- Участие в событиях\n\n"
                "Это действие нельзя отменить!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Выполняем удаление через DatabaseManager
                success = self._delete_player_with_relations(player_id)

                if success:
                    # Обновляем таблицу
                    self._refresh()
                    self._update_status_bar(f"Игрок '{nickname}' удален")
                    MessageHelper.show_info(self, "Успех", f"Игрок '{nickname}' успешно удален")
                else:
                    MessageHelper.show_error(self, "Ошибка", "Не удалось удалить игрока")

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Не удалось удалить игрока: {e}")
            print(f"Ошибка в _delete_row: {e}")

    def _delete_player_with_relations(self, player_id):
        """Удаление игрока со всеми связанными данными"""
        try:
            # Используем QSqlQuery для PyQt6
            query = QSqlQuery(self.db)

            # Начинаем транзакцию
            self.db.transaction()

            # Удаляем связанные данные в правильном порядке
            # (сначала зависимые таблицы, потом основную)

            # Удаляем участие в событиях
            query.prepare("DELETE FROM EventParticipation WHERE player_id = ?")
            query.addBindValue(player_id)
            if not query.exec():
                print(f"Ошибка удаления EventParticipation: {query.lastError().text()}")

            # Удаляем активность
            query.prepare("DELETE FROM Activity WHERE player_id = ?")
            query.addBindValue(player_id)
            if not query.exec():
                print(f"Ошибка удаления Activity: {query.lastError().text()}")

            # Удаляем вклад в гильдию
            query.prepare("DELETE FROM GuildContribution WHERE player_id = ?")
            query.addBindValue(player_id)
            if not query.exec():
                print(f"Ошибка удаления GuildContribution: {query.lastError().text()}")

            # Удаляем основную запись игрока
            query.prepare("DELETE FROM Players WHERE id = ?")
            query.addBindValue(player_id)
            if not query.exec():
                self.db.rollback()
                print(f"Ошибка удаления игрока: {query.lastError().text()}")
                return False

            # Проверяем, что игрок был удален
            if query.numRowsAffected() == 0:
                self.db.rollback()
                print(f"Игрок с ID {player_id} не найден")
                return False

            # Подтверждаем транзакцию
            self.db.commit()
            return True

        except Exception as e:
            # Откатываем транзакцию в случае ошибки
            self.db.rollback()
            print(f"Ошибка при удалении игрока: {e}")
            return False


