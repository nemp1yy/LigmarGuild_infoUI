from PyQt6.QtWidgets import QApplication
from gui.MainWindow import MainWindow
from data.sqlite.create_database import create_db
from config.cfg import Config
import sys

create_db()
app = QApplication(sys.argv)
window = MainWindow()
window.show()
print("Запуск приложения")
sys.exit(app.exec())