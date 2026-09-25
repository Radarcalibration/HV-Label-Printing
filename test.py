import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import QDateTime, QTimer


class BatteryPackWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Battery Pack Integration")
        self.resize(1000, 700)

        # White Theme
        self.setStyleSheet("""
        QWidget {
            background-color: white;
            color: black;
            font-size: 11pt;
        }

        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
            background-color: white;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QLineEdit, QComboBox {
            background-color: white;
            border: 1px solid #b0b0b0;
            padding: 4px;
            min-height: 25px;
        }

        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #b0b0b0;
            padding: 6px;
            min-height: 30px;
        }

        QPushButton:hover {
            background-color: #e0e0e0;
        }

        QTableWidget {
            background-color: white;
            gridline-color: #d0d0d0;
        }

        QHeaderView::section {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 5px;
            font-weight: bold;
        }
        """)

        self.build_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()

    def build_ui(self):
        main_layout = QVBoxLayout()

        # CONFIGURATION
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()

        self.plant = QComboBox()
        self.plant.addItems(["Jigani", "Domlur"])

        self.line = QComboBox()
        self.line.addItems(["1", "2", "3"])

        self.variant = QComboBox()
        self.variant.addItems(["HV75", "HV100", "HV150"])

        self.shift = QComboBox()
        self.shift.addItems(["A", "B", "C"])

        self.serial = QLineEdit("000001")

        config_layout.addWidget(QLabel("Plant"), 0, 0)
        config_layout.addWidget(self.plant, 0, 1)

        config_layout.addWidget(QLabel("Line"), 0, 2)
        config_layout.addWidget(self.line, 0, 3)

        config_layout.addWidget(QLabel("Variant"), 1, 0)
        config_layout.addWidget(self.variant, 1, 1)

        config_layout.addWidget(QLabel("Shift"), 1, 2)
        config_layout.addWidget(self.shift, 1, 3)

        config_layout.addWidget(QLabel("Serial"), 2, 0)
        config_layout.addWidget(self.serial, 2, 1)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # MODULES
        module_group = QGroupBox("Modules")
        module_layout = QGridLayout()

        self.m1 = QLabel("-")
        self.m2 = QLabel("-")
        self.m3 = QLabel("-")
        self.m4 = QLabel("-")

        module_layout.addWidget(QLabel("M1"), 0, 0)
        module_layout.addWidget(self.m1, 0, 1)

        module_layout.addWidget(QLabel("M2"), 1, 0)
        module_layout.addWidget(self.m2, 1, 1)

        module_layout.addWidget(QLabel("M3"), 2, 0)
        module_layout.addWidget(self.m3, 2, 1)

        module_layout.addWidget(QLabel("M4"), 3, 0)
        module_layout.addWidget(self.m4, 3, 1)

        module_group.setLayout(module_layout)
        main_layout.addWidget(module_group)

        # SCANNER
        scan_group = QGroupBox("Scanner")
        scan_layout = QHBoxLayout()

        self.scan_box = QLineEdit()
        self.scan_box.setPlaceholderText("Scan module QR here")

        self.scan_btn = QPushButton("Add")

        scan_layout.addWidget(self.scan_box)
        scan_layout.addWidget(self.scan_btn)

        scan_group.setLayout(scan_layout)
        main_layout.addWidget(scan_group)

        # STATUS
        status_group = QGroupBox("Integration Status")
        status_layout = QGridLayout()

        self.status_label = QLabel("Waiting")
        self.qr_preview = QLabel("No QR Generated")
        self.time_label = QLabel()

        status_layout.addWidget(QLabel("Status"), 0, 0)
        status_layout.addWidget(self.status_label, 0, 1)

        status_layout.addWidget(QLabel("Pack QR"), 1, 0)
        status_layout.addWidget(self.qr_preview, 1, 1)

        status_layout.addWidget(QLabel("Current Time"), 2, 0)
        status_layout.addWidget(self.time_label, 2, 1)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # TABLE
        history_group = QGroupBox("Scan History")
        history_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Module", "Variant", "Timestamp"]
        )

        history_layout.addWidget(self.table)

        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group)

        # BUTTONS
        row = QHBoxLayout()

        self.print_btn = QPushButton("Print")
        self.clear_btn = QPushButton("Clear")

        row.addWidget(self.print_btn)
        row.addWidget(self.clear_btn)

        main_layout.addLayout(row)

        self.setLayout(main_layout)

        # EVENTS
        self.scan_btn.clicked.connect(self.add_scan)
        self.scan_box.returnPressed.connect(self.add_scan)
        self.clear_btn.clicked.connect(self.clear_all)

    def update_time(self):
        self.time_label.setText(
            QDateTime.currentDateTime().toString(
                "dd-MM-yyyy hh:mm:ss"
            )
        )

    def add_scan(self):
        text = self.scan_box.text().strip()

        if not text:
            return

        if self.m1.text() == "-":
            self.m1.setText(text)

        elif self.m2.text() == "-":
            self.m2.setText(text)

        elif self.m3.text() == "-":
            self.m3.setText(text)

        elif self.m4.text() == "-":
            self.m4.setText(text)

            self.status_label.setText("✅ INTEGRATION OK")

            self.qr_preview.setText(
                f"{self.variant.currentText()}-PACK-{self.serial.text()}"
            )

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(text))
        self.table.setItem(
            row, 1, QTableWidgetItem(self.variant.currentText())
        )
        self.table.setItem(
            row,
            2,
            QTableWidgetItem(
                QDateTime.currentDateTime().toString("hh:mm:ss")
            ),
        )

        self.scan_box.clear()

    def clear_all(self):
        self.m1.setText("-")
        self.m2.setText("-")
        self.m3.setText("-")
        self.m4.setText("-")

        self.status_label.setText("Waiting")
        self.qr_preview.setText("No QR Generated")

        self.table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BatteryPackWindow()
    window.show()

    sys.exit(app.exec())