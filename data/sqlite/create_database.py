import sqlite3
from pathlib import Path
from random import choice
from data.sqlite.fill_database import fill_db


class create_db:
    def __init__(self):
        self.path_file = Path("data/ligma.db")
        self.create()

    def create(self):
        if self.path_file.exists():
            print("База данных уже существует.")
        else:
            print("Создаем базу данных...")
            self.conn = sqlite3.connect(self.path_file)
            self.cursor = self.conn.cursor()

            self.create_classes()
            self.create_players()
            self.create_events()
            self.create_activities()
            self.create_guild_contribution()

            choice = int(input("Необходимо ли заполнить базу данных? \n1 - да \n0 - нет \nОтвет: "))
            if choice == 1:
                fill_db(self.cursor)
            else:
                print("База данных не будет заполнена.")

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



