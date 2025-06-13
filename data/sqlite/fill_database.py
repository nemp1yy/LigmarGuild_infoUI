import sqlite3
import random
from datetime import datetime, timedelta

def fill_db(cursor):
    classes = [
        ("Воин", "Фронтовой танк с высокой выживаемостью."),
        ("Лучник", "Атакует с дальнего расстояния, наносит большой урон."),
        ("Маг", "Использует заклинания, эффективен против групп врагов."),
        ("Хиллер", "Поддерживает союзников лечением."),
        ("Разбойник", "Быстрый и ловкий, наносит критические удары.")
    ]
    cursor.executemany("INSERT INTO Classes (name, description) VALUES (?, ?)", classes)
    cursor.execute("SELECT id FROM Classes")
    class_ids = [row[0] for row in cursor.fetchall()]

    statuses = ["Активен", "Неактивен", "В отпуске"]
    players = []
    for i in range(50):
        nickname = f"Игрок{i+1}"
        tag = f"@user{i+1:03}"
        class_id = random.choice(class_ids)
        level = random.randint(10, 70)
        joined_date = (datetime.today() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        players.append((nickname, tag, class_id, level, joined_date, status))
    cursor.executemany("""
        INSERT INTO Players (nickname, tag, class_id, level, joined_date, guild_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, players)

    cursor.execute("SELECT id FROM Players")
    player_ids = [row[0] for row in cursor.fetchall()]

    event_data = []
    for player_id in player_ids:
        for i in range(3):
            date = (datetime.today() - timedelta(days=i*7)).strftime("%Y-%m-%d")
            participated = random.choice([0, 1])
            event_data.append((player_id, date, participated))
    cursor.executemany("""
        INSERT INTO EventParticipation (player_id, event_date, participated)
        VALUES (?, ?, ?)
    """, event_data)

    activity_data = []
    for player_id in player_ids:
        activity_data.append((
            player_id,
            random.randint(5000, 50000),
            random.randint(0, 5),
            random.randint(0, 20)
        ))
    cursor.executemany("""
        INSERT INTO Activity (player_id, weekly_damage, raid_participation, weekly_crafts)
        VALUES (?, ?, ?, ?)
    """, activity_data)

    ranks = ["Участник", "Офицер", "Заместитель", "Лидер", "Новичок"]
    contribution_data = []
    for player_id in player_ids:
        contribution_data.append((
            player_id,
            random.randint(0, 10000),
            random.randint(0, 50),
            random.choice(ranks)
        ))
        
    cursor.executemany("""
        INSERT INTO GuildContribution (player_id, resources_contributed, help_count, leadership_rank)
        VALUES (?, ?, ?, ?)
    """, contribution_data)
