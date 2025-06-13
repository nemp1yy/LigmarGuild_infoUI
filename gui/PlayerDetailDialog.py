from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlQuery

from utils.database import DatabaseManager
from utils.ui_helpers import MessageHelper


class PlayerDetailDialog(QDialog):
    def __init__(self, player_id=None, parent=None):
        super().__init__(parent)
        from utils.resource_helper import get_ui_path
        uic.loadUi(get_ui_path("about_player.ui"), self)

        self.player_id = player_id
        self.is_new_player = player_id is None
        self.db = DatabaseManager.connect()

        # Настройка UI
        self._setup_ui()

        if self.is_new_player:
            # Режим добавления нового игрока
            self._setup_new_player_mode()
        else:
            # Режим редактирования существующего игрока
            self._load_player_data()
            self._load_history_data()

        # Подключение событий
        self.buttonBox.accepted.connect(self._save_changes)

    def _setup_ui(self):
        """Настройка интерфейса"""
        # Настройка даты
        self.joinedDateEdit.setDate(QDate.currentDate())

        # Загрузка классов в комбобокс
        self._load_classes()

        # Настройка таблицы истории
        self.historyTableView.setAlternatingRowColors(True)
        self.historyTableView.setSelectionBehavior(self.historyTableView.SelectionBehavior.SelectRows)

    def _load_classes(self):
        """Загрузка классов в комбобокс"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("SELECT id, name FROM Classes ORDER BY name")

            if query.exec():
                self.classComboBox.clear()
                while query.next():
                    class_id = query.value(0)
                    class_name = query.value(1)
                    self.classComboBox.addItem(class_name, class_id)
        except Exception as e:
            print(f"Ошибка загрузки классов: {e}")

    def _setup_new_player_mode(self):
        """Настройка диалога для добавления нового игрока"""
        # Изменяем заголовки
        self.setWindowTitle("Добавить нового игрока")

        # Устанавливаем значения по умолчанию
        self.nicknameEdit.setText("Новый игрок")
        self.tagEdit.setText("@newuser")
        self.levelSpinBox.setValue(1)
        self.joinedDateEdit.setDate(QDate.currentDate())
        self.statusComboBox.setCurrentText("Активен")

        # Устанавливаем первый класс по умолчанию
        if self.classComboBox.count() > 0:
            self.classComboBox.setCurrentIndex(0)

        # Активность по умолчанию
        self.weeklyDamageSpinBox.setValue(0)
        self.raidParticipationSpinBox.setValue(0)

        # Вклад по умолчанию
        self.leadershipComboBox.setCurrentText("Участник")
        self.resourcesSpinBox.setValue(0)

        # Скрываем группу истории для новых игроков
        self.historyGroup.setVisible(False)

        # Фокус на поле никнейма
        self.nicknameEdit.setFocus()
        self.nicknameEdit.selectAll()

    def _load_player_data(self):
        """Загрузка данных игрока"""
        try:
            # Основные данные игрока
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT 
                    p.nickname,
                    p.tag,
                    p.class_id,
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
                WHERE p.id = ?
            """)
            query.addBindValue(self.player_id)

            if query.exec() and query.next():
                # Заполняем основную информацию
                self.nicknameEdit.setText(query.value("nickname") or "")
                self.tagEdit.setText(query.value("tag") or "")

                # Устанавливаем класс
                class_id = query.value("class_id")
                if class_id:
                    index = self.classComboBox.findData(class_id)
                    if index >= 0:
                        self.classComboBox.setCurrentIndex(index)

                self.levelSpinBox.setValue(query.value("level") or 1)

                # Устанавливаем дату
                joined_date = query.value("joined_date")
                if joined_date:
                    self.joinedDateEdit.setDate(QDate.fromString(joined_date, Qt.DateFormat.ISODate))

                # Устанавливаем статус
                status = query.value("guild_status") or "Активен"
                index = self.statusComboBox.findText(status)
                if index >= 0:
                    self.statusComboBox.setCurrentIndex(index)

                # Заполняем активность
                self.weeklyDamageSpinBox.setValue(query.value("weekly_damage") or 0)
                self.raidParticipationSpinBox.setValue(query.value("raid_participation") or 0)

                # Заполняем вклад в гильдию
                leadership = query.value("leadership_rank") or "Участник"
                index = self.leadershipComboBox.findText(leadership)
                if index >= 0:
                    self.leadershipComboBox.setCurrentIndex(index)

                self.resourcesSpinBox.setValue(query.value("resources_contributed") or 0)

                # Обновляем заголовок
                nickname = query.value("nickname") or "Неизвестный игрок"
                self.setWindowTitle(f"Детали игрока - {nickname}")

            else:
                MessageHelper.show_error(self, "Ошибка", "Не удалось загрузить данные игрока")
                self.reject()

        except Exception as e:
            MessageHelper.show_error(self, "Ошибка", f"Ошибка загрузки данных: {e}")
            print(f"Ошибка в _load_player_data: {e}")

    def _load_history_data(self):
        """Загрузка истории событий"""
        try:
            # Создаем модель для истории событий
            query_text = """
                SELECT 
                    ep.event_date as "Дата",
                    ep.event_type as "Тип события",
                    ep.description as "Описание",
                    ep.reward as "Награда"
                FROM EventParticipation ep
                WHERE ep.player_id = ?
                ORDER BY ep.event_date DESC
                LIMIT 10
            """

            model = DatabaseManager.create_query_model(self.db, query_text)
            if model:
                # Привязываем параметр
                query = QSqlQuery(self.db)
                query.prepare(query_text)
                query.addBindValue(self.player_id)
                model.setQuery(query)

                # Устанавливаем модель в таблицу
                self.historyTableView.setModel(model)
                self.historyTableView.resizeColumnsToContents()

                # Скрываем вертикальные заголовки
                self.historyTableView.verticalHeader().setVisible(False)

        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")

    def _save_changes(self):
        """Сохранение изменений"""
        try:
            # Валидация данных
            if not self._validate_data():
                return

            self.db.transaction()

            if self.is_new_player:
                # Создаем нового игрока
                self.player_id = self._create_new_player()
            else:
                # Обновляем существующего игрока
                self._update_existing_player()

            # Обновляем или создаем запись в Activity
            self._save_activity_data()

            # Обновляем или создаем запись в GuildContribution
            self._save_contribution_data()

            self.db.commit()

            success_message = "Новый игрок успешно добавлен" if self.is_new_player else "Данные игрока успешно обновлены"
            MessageHelper.show_info(self, "Успех", success_message)
            self.accept()

        except Exception as e:
            self.db.rollback()
            error_message = f"Не удалось {'добавить игрока' if self.is_new_player else 'сохранить изменения'}: {e}"
            MessageHelper.show_error(self, "Ошибка", error_message)
            print(f"Ошибка сохранения: {e}")

    def _validate_data(self):
        """Валидация введенных данных"""
        # Проверяем обязательные поля
        if not self.nicknameEdit.text().strip():
            MessageHelper.show_error(self, "Ошибка валидации", "Никнейм не может быть пустым")
            self.nicknameEdit.setFocus()
            return False

        if not self.tagEdit.text().strip():
            MessageHelper.show_error(self, "Ошибка валидации", "Тег не может быть пустым")
            self.tagEdit.setFocus()
            return False

        if self.classComboBox.currentData() is None:
            MessageHelper.show_error(self, "Ошибка валидации", "Необходимо выбрать класс")
            self.classComboBox.setFocus()
            return False

        # Проверяем уникальность никнейма для нового игрока
        if self.is_new_player:
            query = QSqlQuery(self.db)
            query.prepare("SELECT COUNT(*) FROM Players WHERE nickname = ?")
            query.addBindValue(self.nicknameEdit.text().strip())

            if query.exec() and query.next() and query.value(0) > 0:
                MessageHelper.show_error(self, "Ошибка валидации",
                                         "Игрок с таким никнеймом уже существует")
                self.nicknameEdit.setFocus()
                return False

        return True

    def _create_new_player(self):
        """Создание нового игрока"""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO Players (nickname, tag, class_id, level, joined_date, guild_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """)

        query.addBindValue(self.nicknameEdit.text().strip())
        query.addBindValue(self.tagEdit.text().strip())
        query.addBindValue(self.classComboBox.currentData())
        query.addBindValue(self.levelSpinBox.value())
        query.addBindValue(self.joinedDateEdit.date().toString(Qt.DateFormat.ISODate))
        query.addBindValue(self.statusComboBox.currentText())

        if not query.exec():
            raise Exception(f"Ошибка создания игрока: {query.lastError().text()}")

        # Получаем ID созданного игрока
        return query.lastInsertId()

    def _update_existing_player(self):
        """Обновление существующего игрока"""
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE Players 
            SET nickname = ?, tag = ?, class_id = ?, level = ?, 
                joined_date = ?, guild_status = ?
            WHERE id = ?
        """)

        query.addBindValue(self.nicknameEdit.text().strip())
        query.addBindValue(self.tagEdit.text().strip())
        query.addBindValue(self.classComboBox.currentData())
        query.addBindValue(self.levelSpinBox.value())
        query.addBindValue(self.joinedDateEdit.date().toString(Qt.DateFormat.ISODate))
        query.addBindValue(self.statusComboBox.currentText())
        query.addBindValue(self.player_id)

        if not query.exec():
            raise Exception(f"Ошибка обновления игрока: {query.lastError().text()}")

    def _save_activity_data(self):
        """Сохранение данных активности"""
        query = QSqlQuery(self.db)

        # Проверяем, есть ли уже запись
        query.prepare("SELECT COUNT(*) FROM Activity WHERE player_id = ?")
        query.addBindValue(self.player_id)

        if query.exec() and query.next() and query.value(0) > 0:
            # Обновляем существующую запись
            query.prepare("""
                UPDATE Activity 
                SET weekly_damage = ?, raid_participation = ?
                WHERE player_id = ?
            """)
            query.addBindValue(self.weeklyDamageSpinBox.value())
            query.addBindValue(self.raidParticipationSpinBox.value())
            query.addBindValue(self.player_id)
        else:
            # Создаем новую запись
            query.prepare("""
                INSERT INTO Activity (player_id, weekly_damage, raid_participation)
                VALUES (?, ?, ?)
            """)
            query.addBindValue(self.player_id)
            query.addBindValue(self.weeklyDamageSpinBox.value())
            query.addBindValue(self.raidParticipationSpinBox.value())

        if not query.exec():
            raise Exception(f"Ошибка обновления активности: {query.lastError().text()}")

    def _save_contribution_data(self):
        """Сохранение данных вклада в гильдию"""
        query = QSqlQuery(self.db)

        # Проверяем, есть ли уже запись
        query.prepare("SELECT COUNT(*) FROM GuildContribution WHERE player_id = ?")
        query.addBindValue(self.player_id)

        if query.exec() and query.next() and query.value(0) > 0:
            # Обновляем существующую запись
            query.prepare("""
                UPDATE GuildContribution 
                SET leadership_rank = ?, resources_contributed = ?
                WHERE player_id = ?
            """)
            query.addBindValue(self.leadershipComboBox.currentText())
            query.addBindValue(self.resourcesSpinBox.value())
            query.addBindValue(self.player_id)
        else:
            # Создаем новую запись
            query.prepare("""
                INSERT INTO GuildContribution (player_id, leadership_rank, resources_contributed)
                VALUES (?, ?, ?)
            """)
            query.addBindValue(self.player_id)
            query.addBindValue(self.leadershipComboBox.currentText())
            query.addBindValue(self.resourcesSpinBox.value())

        if not query.exec():
            raise Exception(f"Ошибка обновления вклада: {query.lastError().text()}")

    def get_player_id(self):
        """Получение ID игрока"""
        return self.player_id