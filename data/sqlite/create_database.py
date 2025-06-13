import sqlite3
import sys
import os
from pathlib import Path
from random import choice

def get_app_data_path():
    """Получение пути для данных приложения"""
    if hasattr(sys, '_MEIPASS'):
        # Запуск из exe - используем временную папку пользователя
        app_data = os.path.join(os.path.expanduser("~"), "GuildManager")
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Обычный запуск - создаем папку data если её нет
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        return str(data_dir)


class create_db:
    def __init__(self):
        # Получаем корректный путь для базы данных
        app_path = get_app_data_path()
        self.path_file = Path(app_path) / "ligma.db"
        print(f"База данных будет создана по пути: {self.path_file}")
        self.create()

    def create(self):
        if self.path_file.exists():
            print("База данных уже существует.")
        else:
            print("Создаем базу данных...")

            # Убеждаемся, что родительская папка существует
            self.path_file.parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.path_file)
            self.cursor = self.conn.cursor()

            self.create_classes()
            self.create_players()
            self.create_events()
            self.create_activities()
            self.create_guild_contribution()

            self.conn.commit()
            self.conn.close()
            print("База данных создана.")

    def drop_tables(self):
        self.cursor.executescript('''
        DROP TABLE IF EXISTS GuildContribution;
        DROP TABLE IF EXISTS Activity;
        DROP TABLE IF EXISTS EventParticipation;
        DROP TABLE IF EXISTS Players;
        DROP TABLE IF EXISTS Classes;
        ''')

    def create_classes(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
        ''')

    def create_players(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            tag TEXT NOT NULL,
            class_id INTEGER,
            level INTEGER,
            joined_date TEXT,
            guild_status TEXT,
            FOREIGN KEY (class_id) REFERENCES Classes(id)
    )
    ''')

    def create_events(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS EventParticipation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            event_date TEXT,
            participated INTEGER CHECK(participated IN (0, 1)),
            FOREIGN KEY (player_id) REFERENCES Players(id)
        )
        ''')

    def create_activities(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            weekly_damage INTEGER,
            raid_participation INTEGER,
            weekly_crafts INTEGER,
            FOREIGN KEY (player_id) REFERENCES Players(id)
        )
        ''')

    def create_guild_contribution(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS GuildContribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            resources_contributed INTEGER,
            help_count INTEGER,
            leadership_rank TEXT,
            FOREIGN KEY (player_id) REFERENCES Players(id)
        )
        ''')