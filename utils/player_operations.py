from PyQt6.QtSql import QSqlQuery


class PlayerOperations:
    """Класс для операций с игроками"""

    def __init__(self, db):
        self.db = db

    def delete_player_with_relations(self, player_id):
        """Удаление игрока со всеми связанными данными"""
        try:
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

    def get_player_info(self, player_id):
        """Получение информации о игроке"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT p.*, c.name as class_name 
                FROM Players p 
                LEFT JOIN Classes c ON p.class_id = c.id 
                WHERE p.id = ?
            """)
            query.addBindValue(player_id)

            if query.exec() and query.next():
                player_info = {}
                record = query.record()
                for i in range(record.count()):
                    field_name = record.fieldName(i)
                    player_info[field_name] = query.value(i)
                return player_info
            return None

        except Exception as e:
            print(f"Ошибка получения информации о игроке: {e}")
            return None

    def update_player(self, player_id, player_data):
        """Обновление данных игрока"""
        try:
            query = QSqlQuery(self.db)

            # Строим запрос динамически на основе переданных данных
            fields = []
            values = []

            for field, value in player_data.items():
                if field != 'id':  # Исключаем ID из обновления
                    fields.append(f"{field} = ?")
                    values.append(value)

            if not fields:
                return False

            sql = f"UPDATE Players SET {', '.join(fields)} WHERE id = ?"
            values.append(player_id)

            query.prepare(sql)
            for value in values:
                query.addBindValue(value)

            return query.exec()

        except Exception as e:
            print(f"Ошибка обновления игрока: {e}")
            return False

    def create_player(self, player_data):
        """Создание нового игрока"""
        try:
            query = QSqlQuery(self.db)

            # Исключаем ID из вставки (он автоинкрементный)
            fields = [field for field in player_data.keys() if field != 'id']
            placeholders = ['?' for _ in fields]
            values = [player_data[field] for field in fields]

            sql = f"INSERT INTO Players ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

            query.prepare(sql)
            for value in values:
                query.addBindValue(value)

            if query.exec():
                # Возвращаем ID созданного игрока
                return query.lastInsertId()
            return None

        except Exception as e:
            print(f"Ошибка создания игрока: {e}")
            return None

    def get_player_activity(self, player_id):
        """Получение активности игрока"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("SELECT * FROM Activity WHERE player_id = ?")
            query.addBindValue(player_id)

            if query.exec() and query.next():
                activity_info = {}
                record = query.record()
                for i in range(record.count()):
                    field_name = record.fieldName(i)
                    activity_info[field_name] = query.value(i)
                return activity_info
            return None

        except Exception as e:
            print(f"Ошибка получения активности игрока: {e}")
            return None

    def get_player_contribution(self, player_id):
        """Получение вклада игрока в гильдию"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("SELECT * FROM GuildContribution WHERE player_id = ?")
            query.addBindValue(player_id)

            if query.exec() and query.next():
                contribution_info = {}
                record = query.record()
                for i in range(record.count()):
                    field_name = record.fieldName(i)
                    contribution_info[field_name] = query.value(i)
                return contribution_info
            return None

        except Exception as e:
            print(f"Ошибка получения вклада игрока: {e}")
            return None

    def update_player_activity(self, player_id, activity_data):
        """Обновление/создание активности игрока"""
        try:
            query = QSqlQuery(self.db)

            # Проверяем, есть ли уже запись активности
            query.prepare("SELECT id FROM Activity WHERE player_id = ?")
            query.addBindValue(player_id)

            if query.exec() and query.next():
                # Обновляем существующую запись
                fields = []
                values = []

                for field, value in activity_data.items():
                    if field not in ['id', 'player_id']:
                        fields.append(f"{field} = ?")
                        values.append(value)

                if fields:
                    sql = f"UPDATE Activity SET {', '.join(fields)} WHERE player_id = ?"
                    values.append(player_id)

                    query.prepare(sql)
                    for value in values:
                        query.addBindValue(value)

                    return query.exec()
            else:
                # Создаем новую запись
                activity_data['player_id'] = player_id
                fields = list(activity_data.keys())
                placeholders = ['?' for _ in fields]
                values = [activity_data[field] for field in fields]

                sql = f"INSERT INTO Activity ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

                query.prepare(sql)
                for value in values:
                    query.addBindValue(value)

                return query.exec()

            return False

        except Exception as e:
            print(f"Ошибка обновления активности игрока: {e}")
            return False

    def update_player_contribution(self, player_id, contribution_data):
        """Обновление/создание вклада игрока в гильдию"""
        try:
            query = QSqlQuery(self.db)

            # Проверяем, есть ли уже запись вклада
            query.prepare("SELECT id FROM GuildContribution WHERE player_id = ?")
            query.addBindValue(player_id)

            if query.exec() and query.next():
                # Обновляем существующую запись
                fields = []
                values = []

                for field, value in contribution_data.items():
                    if field not in ['id', 'player_id']:
                        fields.append(f"{field} = ?")
                        values.append(value)

                if fields:
                    sql = f"UPDATE GuildContribution SET {', '.join(fields)} WHERE player_id = ?"
                    values.append(player_id)

                    query.prepare(sql)
                    for value in values:
                        query.addBindValue(value)

                    return query.exec()
            else:
                # Создаем новую запись
                contribution_data['player_id'] = player_id
                fields = list(contribution_data.keys())
                placeholders = ['?' for _ in fields]
                values = [contribution_data[field] for field in fields]

                sql = f"INSERT INTO GuildContribution ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

                query.prepare(sql)
                for value in values:
                    query.addBindValue(value)

                return query.exec()

            return False

        except Exception as e:
            print(f"Ошибка обновления вклада игрока: {e}")
            return False