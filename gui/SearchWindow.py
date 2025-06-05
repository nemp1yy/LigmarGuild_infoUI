from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QDialog
from utils.database import DatabaseManager
from utils.ui_helpers import FormUtils


class SearchWindow(QDialog):
    search_requested = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("gui/design/search.ui", self)

        self.db = DatabaseManager.connect()
        FormUtils.reset_datetime_edits(self)

        self.pushButton.clicked.connect(self._emit_filter)
        self.pushButton_2.clicked.connect(self._clear_form)
        self.pushButton_3.clicked.connect(self.close)

    def _emit_filter(self):
        params = self._get_form_data()
        filter_text = self._build_filter(params)
        self.search_requested.emit(filter_text)
        self.close()

    def _get_form_data(self):
        return {
            'flight': self.lineEdit_flight.text().strip(),
            'airline': self.lineEdit_airline.text().strip(),
            'departure_from': self.lineEdit_departure_from.text().strip(),
            'destination': self.lineEdit_destination.text().strip(),
            'gate': self.lineEdit_gate.text().strip(),
            'status': self.comboBox_status.currentText(),
            'aircraft_type': self.lineEdit_aircraft_type.text().strip(),
            'departure_range': (
                self.dateTimeEdit_departure_time_range1.dateTime().toString("yyyy-MM-dd hh:mm"),
                self.dateTimeEdit_departure_time_range2.dateTime().toString("yyyy-MM-dd hh:mm")
            ),
            'arrival_range': (
                self.dateTimeEdit_arrival_time_range1.dateTime().toString("yyyy-MM-dd hh:mm"),
                self.dateTimeEdit_arrival_time_range2.dateTime().toString("yyyy-MM-dd hh:mm")
            )
        }

    def _build_filter(self, params):
        conditions = []

        if params['flight']:
            conditions.append(f"flight_number LIKE '%{params['flight']}%'")
        if params['airline']:
            conditions.append(f"airline_id IN (SELECT id FROM airlines WHERE name LIKE '%{params['airline']}%')")
        if params['aircraft_type']:
            conditions.append(
                f"aircraft_type_id IN (SELECT id FROM aircraft_types WHERE model LIKE '%{params['aircraft_type']}%')")
        if params['departure_from']:
            conditions.append(
                f"departure_airport_id IN (SELECT id FROM airports WHERE name LIKE '%{params['departure_from']}%')")
        if params['destination']:
            conditions.append(
                f"arrival_airport_id IN (SELECT id FROM airports WHERE name LIKE '%{params['destination']}%')")
        if params['gate']:
            conditions.append(f"gate LIKE '%{params['gate']}%'")

        if params['status'] and params['status'] != "Все статусы":
            conditions.append(f"status_id IN (SELECT id FROM statuses WHERE name = '{params['status']}')")

        # Временные диапазоны
        if params['departure_range'][0] and params['departure_range'][1]:
            conditions.append(
                f"departure_time BETWEEN '{params['departure_range'][0]}' AND '{params['departure_range'][1]}'")
        if params['arrival_range'][0] and params['arrival_range'][1]:
            conditions.append(f"arrival_time BETWEEN '{params['arrival_range'][0]}' AND '{params['arrival_range'][1]}'")

        return " AND ".join(conditions) if conditions else ""

    def _clear_form(self):
        FormUtils.clear_line_edits(self)
        FormUtils.reset_datetime_edits(self)
        FormUtils.reset_combo_boxes(self)

    # def _cancel_search(self):
