import mariadb

from config.cfg import Config



class Database:
    def __init__(self):

        cfg = Config("config.json")

        host, user, password, database = cfg.get_connection()

        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

        self.connect()

        if self.connection is None:
            print("Error connecting to the database.")
        else:
            print("Connected to the database.")
            self.cursor = self.connection.cursor()
            self.create_tables()
            self.create_main_table()
            self.add_demonstration_data()
            self.add_test_flight()


    def connect(self):
        try:
            self.connection = mariadb.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Connected to the database.")

        except mariadb.Error as e:

            print(f"Error connecting to the database: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("Disconnected from the database.")

            def create_tables(self):
                # Создание справочных таблиц
                self.cursor.executescript("""
                CREATE TABLE airlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    country TEXT
                );


                CREATE TABLE aircraft_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL UNIQUE,
                    manufacturer TEXT,
                    capacity INTEGER
                );

                CREATE TABLE airports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    city TEXT,
                    country TEXT,
                    code TEXT UNIQUE
                );

                CREATE TABLE statuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );
                """)

            # Создание основной таблицы

            def create_main_table(self):
                self.cursor.execute("""
                CREATE TABLE flights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flight_number TEXT NOT NULL,
                    airline_id INTEGER,
                    aircraft_type_id INTEGER,
                    departure_airport_id INTEGER,
                    arrival_airport_id INTEGER,
                    departure_time DATETIME,
                    arrival_time DATETIME,
                    status_id INTEGER,
                    gate TEXT,
                    FOREIGN KEY (airline_id) REFERENCES airlines(id),
                    FOREIGN KEY (aircraft_type_id) REFERENCES aircraft_types(id),
                    FOREIGN KEY (departure_airport_id) REFERENCES airports(id),
                    FOREIGN KEY (arrival_airport_id) REFERENCES airports(id),
                    FOREIGN KEY (status_id) REFERENCES statuses(id)
                );
                """)

            def add_demonstration_data(self):
                # Вставка демонстрационных данных
                self.cursor.executescript("""
                INSERT INTO airlines (name, country) VALUES
                ('Aeroflot', 'Russia'),
                ('Lufthansa', 'Germany');

                INSERT INTO aircraft_types (model, manufacturer, capacity) VALUES
                ('A320', 'Airbus', 180),
                ('B737', 'Boeing', 160);

                INSERT INTO airports (name, city, country, code) VALUES
                ('Sheremetyevo International Airport', 'Moscow', 'Russia', 'SVO'),
                ('Frankfurt Airport', 'Frankfurt', 'Germany', 'FRA');

                INSERT INTO statuses (name) VALUES
                ('On Time'),
                ('Delayed'),
                ('Cancelled');
                """)

                # Вставка тестового рейса

            def add_test_flight(self):
                self.cursor.execute("""
                INSERT INTO flights (
                    flight_number, airline_id, aircraft_type_id,
                    departure_airport_id, arrival_airport_id,
                    departure_time, arrival_time, status_id, gate
                )
                VALUES (
                    'SU123', 1, 1, 1, 2,
                    '2025-06-01 08:00', '2025-06-01 11:00', 1, 'A12'
                );
                """)