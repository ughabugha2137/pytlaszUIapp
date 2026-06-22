#!/usr/bin/env python3
"""
PYTLASZ Flight Computer UI
- Connect to STM32 flight computer via serial
- Export flight data to CSV files
- Control and configure the flight computer
- Auto-update from https://github.com/ughabugha2137/pytlaszUIapp
"""

import sys
import os
import subprocess
import serial
import serial.tools.list_ports
import csv
import threading
import time
import json
import tempfile
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTabWidget, QGroupBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QScrollArea, QFormLayout,
    QStatusBar, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QSettings
from PyQt5.QtGui import QFont, QColor

# ════════════════════════════════════════════════════════
# VERSION
# ════════════════════════════════════════════════════════
APP_VERSION = "1.0.0"
GITHUB_REPO = "ughabugha2137/pytlaszUIapp"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

# ════════════════════════════════════════════════════════
# TRANSLATIONS
# ════════════════════════════════════════════════════════
TRANSLATIONS = {
    'en': {
        'app_title': 'PYTLASZ Flight Computer Control',
        'connection': 'Connection',
        'port': 'Port',
        'refresh': '⟳ Refresh',
        'connect': 'Connect',
        'disconnect': 'Disconnect',
        'disconnected': 'Disconnected',
        'status': 'Status',
        'commands': 'Commands',
        'config': 'Configuration',
        'data': 'Flight Data',
        'flight_status': 'Flight Status',
        'refresh_status': 'Refresh Status',
        'flight_mode': 'Flight Mode',
        'bench_mode': 'Bench Mode',
        'flight_mode_btn': 'Flight Mode',
        'data_management': 'Data Management',
        'export_all': 'Export All Flights',
        'delete_flash': 'Delete Flash',
        'utilities': 'Utilities',
        'reset_mcu': 'Reset MCU',
        'clear_errors': 'Clear Errors',
        'ignore_battery': 'Ignore Battery',
        'output': 'Output:',
        'read_config': 'Read Current Config',
        'apply_config': 'Apply Configuration',
        'export_folder': 'Export Folder:',
        'change_folder': 'Change Export Folder...',
        'available_flights': 'Available Flights:',
        'open_folder': 'Open Export Folder',
        'settings': 'Settings',
        'language': 'Language',
        'theme': 'Theme',
        'select_language': 'Select language:',
        'dark_mode': 'Dark Mode',
        'enable_dark_mode': 'Enable Dark Mode',
        'apply': 'Apply',
        'close': 'Close',
        'flight_data_export': 'Flight Data Export:',
        'no_port': 'No Port',
        'select_port': 'Please select a valid COM port.',
        'connected_to': 'Connected to',
        'no_com_ports': 'No COM ports found',
        'found_stm32': 'Found',
        'stm32_devices': 'STM32 device(s)',
        'no_stm32_detected': 'No STM32 detected - showing all ports',
        'launch_accel': 'Launch Acceleration (m/s²):',
        'coast_accel': 'Coast Acceleration (m/s²):',
        'apogee_time': 'Apogee Lockout Time (ms):',
        'apogee_alt': 'Apogee Lockout Altitude (m):',
        'main_deploy_alt': 'Main Deploy Altitude (m):',
        'backup_drogue': 'Backup Drogue Velocity (m/s):',
        'backup_main': 'Backup Main Velocity (m/s):',
        'landed_vel': 'Landing Velocity (m/s):',
        'landed_alt': 'Landing Altitude (m):',
        'landed_confirm': 'Landing Confirm Time (ms):',
        'post_land_log': 'Post-Land Logging Duration (ms):',
        'pyro_fire': 'Pyro Fire Time (ms):',
        'bat_min': 'Minimum Battery Voltage (V):',
        'arm_threshold': 'Arm Pin Threshold (V):',
        'kf_q_alt': 'KF Process Noise (Alt):',
        'kf_q_vel': 'KF Process Noise (Vel):',
        'kf_r_baro': 'KF Baro Measurement Noise:',
        'kf_r_accel': 'KF Accel Measurement Noise:',
        'kf_baro_vel': 'KF Baro Velocity Scale:',
        'kf_baro_min': 'KF Baro Min Trust:',
        'idle_hz': 'Idle Sample Rate (Hz):',
        'flight_hz': 'Flight Sample Rate (Hz):',
        'battery_check': 'Battery Check:',
        'buzzer': 'Buzzer:',
        'enable_buzzer': 'Enable Buzzer',
        'delete_confirm_title': 'Delete Flash Memory',
        'delete_confirm_msg': 'This will erase all flight data on the STM32.\nAre you sure?',
        'export_complete': 'Export Complete',
        'export_success': 'Exported',
        'flights_to': 'flights to',
        'not_connected': 'Not Connected',
        'connect_first': 'Please connect to the flight computer first.',
        'flight_detection': '=== FLIGHT DETECTION ===',
        'apogee_detection': '=== APOGEE DETECTION ===',
        'deployment': '=== DEPLOYMENT ===',
        'landing_detection': '=== LANDING DETECTION ===',
        'hardware': '=== HARDWARE ===',
        'kalman_filter': '=== KALMAN FILTER ===',
        'system': '=== SYSTEM ===',
        'flight_num': 'Flight #',
        'records': 'Records',
    }
}

# Dark mode stylesheet
DARK_MODE_STYLESHEET = """
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QGroupBox {
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 3px;
    }
    QPushButton {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #4d4d4d;
    }
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 5px;
    }
    QTableWidget::item {
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
    }
    QTabWidget::pane {
        border: 1px solid #3d3d3d;
    }
    QTabBar::tab {
        background-color: #2d2d2d;
        color: #ffffff;
        padding: 5px 15px;
        border: 1px solid #3d3d3d;
    }
    QTabBar::tab:selected {
        background-color: #404040;
    }
    QScrollBar:vertical {
        background-color: #2d2d2d;
        width: 12px;
    }
    QScrollBar::handle:vertical {
        background-color: #555555;
        border-radius: 6px;
    }
"""


# ════════════════════════════════════════════════════════
# AUTO-UPDATER
# ════════════════════════════════════════════════════════
def _version_tuple(v):
    """Convert 'v1.2.3' or '1.2.3' to (1, 2, 3) for comparison."""
    v = v.lstrip('vV').strip()
    try:
        return tuple(int(x) for x in v.split('.'))
    except ValueError:
        return (0, 0, 0)


class UpdateChecker(QObject):
    """Worker that hits the GitHub releases API on a background thread."""
    update_available = pyqtSignal(str, str, str) # tag, release_name, html_url
    up_to_date = pyqtSignal(str) # latest tag
    check_failed = pyqtSignal(str) # error message

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": f"pytlasz-ui/{APP_VERSION}"},
            )
            # Use certifi CA bundle when available to avoid system SSL issues
            try:
                import ssl, certifi
                context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                context = None

            try:
                if context is not None:
                    with urllib.request.urlopen(req, timeout=8, context=context) as resp:
                        data = json.loads(resp.read().decode())
                else:
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode())
            except urllib.error.HTTPError as he:
                # GitHub returns 404 for repos with no releases; treat as 'no updates'
                if he.code == 404:
                    self.up_to_date.emit(APP_VERSION)
                    return
                raise

            tag = data.get("tag_name", "")
            release_name = data.get("name", tag)
            html_url = data.get("html_url", GITHUB_RELEASE_URL)

            if _version_tuple(tag) > _version_tuple(APP_VERSION):
                self.update_available.emit(tag, release_name, html_url)
            else:
                self.up_to_date.emit(tag)

        except urllib.error.URLError as e:
            self.check_failed.emit(f"Network error: {e.reason}")
        except Exception as e:
            self.check_failed.emit(str(e))


class UpdateDialog(QDialog):
    """Shown when a new release is found."""

    def __init__(self, parent, tag, release_name, html_url):
        super().__init__(parent)
        self.html_url = html_url
        self.setWindowTitle("Update Available")
        self.setFixedWidth(420)

        layout = QVBoxLayout()

        title = QLabel(f"A new version of PYTLASZ UI is available!")
        title.setWordWrap(True)
        layout.addWidget(title)

        layout.addWidget(QLabel(f"Current version: {APP_VERSION}"))
        layout.addWidget(QLabel(f"Latest version: {tag}"))
        if release_name and release_name != tag:
            layout.addWidget(QLabel(f"Release name: {release_name}"))

        layout.addSpacing(8)
        note = QLabel(
            "Click Download to open the GitHub releases page in your browser, "
            "then download the latest file and replace this script."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addSpacing(8)
        btns = QHBoxLayout()
        dl_btn = QPushButton("⬇ Download")
        dl_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        dl_btn.clicked.connect(self._open_download)

        skip_btn = QPushButton("Skip this time")
        skip_btn.clicked.connect(self.reject)

        btns.addWidget(dl_btn)
        btns.addWidget(skip_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _open_download(self):
        import webbrowser
        webbrowser.open(self.html_url)
        self.accept()


# ════════════════════════════════════════════════════════
# SETTINGS DIALOG
# ════════════════════════════════════════════════════════
class SettingsDialog(QDialog):
    """Settings dialog for dark mode and update checking."""
    settings_applied = pyqtSignal(bool)

    def __init__(self, parent, dark_mode):
        super().__init__(parent)
        self.setWindowTitle(self.parent().tr_str('settings'))
        self.setGeometry(200, 200, 420, 230)
        self.dark_mode = dark_mode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Dark mode
        theme_group = QGroupBox(self.parent().tr_str('theme'))
        theme_layout = QHBoxLayout()
        self.dark_mode_check = QCheckBox(self.parent().tr_str('enable_dark_mode'))
        self.dark_mode_check.setChecked(self.dark_mode)
        theme_layout.addWidget(self.dark_mode_check)
        theme_layout.addStretch()
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Updates
        update_group = QGroupBox("Updates")
        update_layout = QHBoxLayout()
        check_now_btn = QPushButton("Check for updates now")
        check_now_btn.clicked.connect(lambda: self.parent().check_for_updates(silent=False))
        version_lbl = QLabel(f"Current version: {APP_VERSION}")
        gh_lbl = QLabel(f'GitHub releases ↗')
        gh_lbl.setOpenExternalLinks(True)
        update_layout.addWidget(version_lbl)
        update_layout.addWidget(gh_lbl)
        update_layout.addStretch()
        update_layout.addWidget(check_now_btn)
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        apply_btn = QPushButton(self.parent().tr_str('apply'))
        apply_btn.clicked.connect(self.apply_settings)
        close_btn = QPushButton(self.parent().tr_str('close'))
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_settings(self):
        self.dark_mode = self.dark_mode_check.isChecked()
        self.settings_applied.emit(self.dark_mode)


class SerialThread(QObject):
    """Thread for handling serial communication"""
    data_received = pyqtSignal(str)
    connected = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False
        self.port = None
        self.baudrate = 115200
        self.read_thread = None

    def connect(self, port):
        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=0.5)
            time.sleep(0.5)
            self.port = port
            self.running = True
            self.connected.emit(True)
            self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
            self.read_thread.start()
        except serial.SerialException as e:
            self.error.emit(f"Cannot open port {port}: {str(e)}")
            self.connected.emit(False)
            self.ser = None
        except Exception as e:
            self.error.emit(f"Connection error: {str(e)}")
            self.connected.emit(False)
            self.ser = None

    def read_loop(self):
        while self.running and self.ser:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.data_received.emit(line)
                time.sleep(0.01)
            except Exception as e:
                if self.running:
                    self.error.emit(f"Read error: {str(e)}")
                break

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + '\n').encode())
                self.ser.flush()
            except Exception as e:
                self.error.emit(f"Send error: {str(e)}")

    def disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass
        self.ser = None
        self.connected.emit(False)


class FlightComputerUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("PYTLASZ", "FlightComputerUI")
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)

        self.setWindowTitle(f"{self.tr_str('app_title')} v{APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)

        self.serial_thread = None
        self.export_folder = str(Path.home() / "pytlasz_flights")
        Path(self.export_folder).mkdir(exist_ok=True)

        self.config = {}
        self.flight_data = []
        self.detected_stm32_ports = []

        self._update_thread = None
        self._update_worker = None

        self.init_ui()
        self.setup_serial()
        self.detect_stm32_ports()

        if self.dark_mode:
            self.apply_dark_mode()

        # Auto-check for updates 2 s after startup (silent — no "up to date" popup)
        QTimer.singleShot(2000, lambda: self.check_for_updates(silent=True))

    # ──────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────
    def tr_str(self, key):
        return TRANSLATIONS['en'].get(key, key)

    # ──────────────────────────────────────────────────
    # AUTO-UPDATE
    # ──────────────────────────────────────────────────
    def check_for_updates(self, silent=True):
        """Spawn a background thread that checks the GitHub releases API."""
        # Avoid launching multiple simultaneous checks
        if self._update_thread and self._update_thread.isRunning():
            return

        self._update_worker = UpdateChecker()
        self._update_thread = QThread(self)
        self._update_worker.moveToThread(self._update_thread)

        self._update_thread.started.connect(self._update_worker.run)
        self._update_worker.update_available.connect(
            lambda tag, name, url: self._on_update_available(tag, name, url))
        self._update_worker.up_to_date.connect(
            lambda tag: self._on_up_to_date(tag, silent))
        self._update_worker.check_failed.connect(
            lambda msg: self._on_update_failed(msg, silent))

        # Clean up after the worker finishes
        self._update_worker.update_available.connect(self._update_thread.quit)
        self._update_worker.up_to_date.connect(self._update_thread.quit)
        self._update_worker.check_failed.connect(self._update_thread.quit)

        self._update_thread.start()
        self.statusBar().showMessage("Checking for updates…")

    def _on_update_available(self, tag, release_name, html_url):
        self.statusBar().showMessage(f"Update available: {tag}")
        dlg = UpdateDialog(self, tag, release_name, html_url)
        dlg.exec_()

    def _on_up_to_date(self, tag, silent):
        self.statusBar().showMessage(f"Up to date (v{APP_VERSION})", 4000)
        if not silent:
            QMessageBox.information(self, "No updates",
                f"You are running the latest version ({APP_VERSION}).")

    def _on_update_failed(self, msg, silent):
        self.statusBar().showMessage("Update check failed", 4000)
        if not silent:
            QMessageBox.warning(self, "Update check failed",
                f"Could not reach GitHub:\n{msg}")

    # ──────────────────────────────────────────────────
    # UI INIT
    # ──────────────────────────────────────────────────
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Connection panel
        conn_group = QGroupBox(self.tr_str('connection'))
        conn_inner_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton(self.tr_str('refresh'))
        self.refresh_ports_btn.setMaximumWidth(80)
        self.refresh_ports_btn.clicked.connect(self.detect_stm32_ports)

        self.settings_btn = QPushButton(f"⚙ {self.tr_str('settings')}")
        self.settings_btn.setMaximumWidth(110)
        self.settings_btn.clicked.connect(self.open_settings)

        self.connect_btn = QPushButton(self.tr_str('connect'))
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.status_label = QLabel(self.tr_str('disconnected'))
        self.status_label.setStyleSheet("color: red;")

        conn_inner_layout.addWidget(QLabel(self.tr_str('port')))
        conn_inner_layout.addWidget(self.port_combo, 1)
        conn_inner_layout.addWidget(self.refresh_ports_btn)
        conn_inner_layout.addWidget(self.settings_btn)
        conn_inner_layout.addWidget(self.connect_btn)
        conn_inner_layout.addWidget(self.status_label, 1)

        conn_group.setLayout(conn_inner_layout)
        main_layout.addWidget(conn_group)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_status_tab(), self.tr_str('status'))
        tabs.addTab(self.create_commands_tab(), self.tr_str('commands'))
        tabs.addTab(self.create_config_tab(), self.tr_str('config'))
        tabs.addTab(self.create_data_tab(), self.tr_str('data'))
        main_layout.addWidget(tabs)

        central_widget.setLayout(main_layout)
        self.setStatusBar(QStatusBar())

    # ──────────────────────────────────────────────────
    # TAB BUILDERS
    # ──────────────────────────────────────────────────
    def create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Courier", 10))
        layout.addWidget(QLabel(self.tr_str('flight_status')))
        layout.addWidget(self.status_text)
        refresh_btn = QPushButton(self.tr_str('refresh_status'))
        refresh_btn.clicked.connect(lambda: self.send_command("status"))
        layout.addWidget(refresh_btn)
        widget.setLayout(layout)
        return widget

    def create_commands_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        mode_group = QGroupBox(self.tr_str('flight_mode'))
        mode_layout = QHBoxLayout()
        bench_btn = QPushButton(self.tr_str('bench_mode'))
        bench_btn.clicked.connect(lambda: self.send_command("bench"))
        bench_btn.setStyleSheet("background-color: #FFC107; color: black;")
        fly_btn = QPushButton(self.tr_str('flight_mode_btn'))
        fly_btn.clicked.connect(lambda: self.send_command("fly"))
        fly_btn.setStyleSheet("background-color: #2196F3; color: white;")
        mode_layout.addWidget(bench_btn)
        mode_layout.addWidget(fly_btn)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        data_group = QGroupBox(self.tr_str('data_management'))
        data_layout = QHBoxLayout()
        export_btn = QPushButton(self.tr_str('export_all'))
        export_btn.clicked.connect(self.export_flights)
        export_btn.setStyleSheet("background-color: #9C27B0; color: white;")
        delete_btn = QPushButton(self.tr_str('delete_flash'))
        delete_btn.setStyleSheet("background-color: #F44336; color: white;")
        delete_btn.clicked.connect(self.confirm_delete_flash)
        data_layout.addWidget(export_btn)
        data_layout.addWidget(delete_btn)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        util_group = QGroupBox(self.tr_str('utilities'))
        util_layout = QHBoxLayout()
        reset_btn = QPushButton(self.tr_str('reset_mcu'))
        reset_btn.clicked.connect(lambda: self.send_command("reset"))
        reset_btn.setStyleSheet("background-color: #FF5722; color: white;")
        ignore_err_btn = QPushButton(self.tr_str('clear_errors'))
        ignore_err_btn.clicked.connect(lambda: self.send_command("ignore_errors"))
        ignore_bat_btn = QPushButton(self.tr_str('ignore_battery'))
        ignore_bat_btn.clicked.connect(lambda: self.send_command("ignore_battery"))
        util_layout.addWidget(reset_btn)
        util_layout.addWidget(ignore_err_btn)
        util_layout.addWidget(ignore_bat_btn)
        util_group.setLayout(util_layout)
        layout.addWidget(util_group)

        self.command_output = QTextEdit()
        self.command_output.setReadOnly(True)
        self.command_output.setFont(QFont("Courier", 9))
        layout.addWidget(QLabel(self.tr_str('output')))
        layout.addWidget(self.command_output)

        widget.setLayout(layout)
        return widget

    def create_config_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout()

        self.config_fields = {}

        def add_section(key):
            form_layout.addRow(QLabel(self.tr_str(key)), QLabel(""))

        def add_double(key, label_key, lo, hi, default, step):
            spin = QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setValue(default)
            spin.setSingleStep(step)
            self.config_fields[key] = spin
            form_layout.addRow(self.tr_str(label_key), spin)

        def add_int(key, label_key, lo, hi, default):
            spin = QSpinBox()
            spin.setRange(lo, hi)
            spin.setValue(default)
            self.config_fields[key] = spin
            form_layout.addRow(self.tr_str(label_key), spin)

        def add_check(key, label_key, check_label, default):
            cb = QCheckBox(self.tr_str(check_label))
            cb.setChecked(default)
            self.config_fields[key] = cb
            form_layout.addRow(self.tr_str(label_key), cb)

        add_section('flight_detection')
        add_double('launch_accel_mss', 'launch_accel', 0, 100, 29.4, 0.1)
        add_double('coast_accel_mss', 'coast_accel', 0, 100, 2.94, 0.1)

        add_section('apogee_detection')
        add_double('apogee_lockout_time_ms', 'apogee_time', 0, 10000,2000.0, 100)
        add_double('apogee_lockout_alt_m', 'apogee_alt', 0, 10000, 50.0, 1)

        add_section('deployment')
        add_double('main_deploy_alt_m', 'main_deploy_alt',0, 10000, 150.0, 1)
        add_double('backup_drogue_vel_ms', 'backup_drogue', -100, 0, -15.0, 0.1)
        add_double('backup_main_vel_ms', 'backup_main', -100, 0, -20.0, 0.1)

        add_section('landing_detection')
        add_double('landed_vel_ms', 'landed_vel', 0, 100, 2.0, 0.1)
        add_double('landed_alt_m', 'landed_alt', 0, 10000, 10.0, 1)
        add_double('landed_confirm_ms', 'landed_confirm', 0, 10000,3000.0, 100)
        add_double('post_land_log_ms', 'post_land_log', 0, 60000,5000.0, 100)

        add_section('hardware')
        add_double('pyro_fire_ms', 'pyro_fire', 0, 10000, 500.0, 10)
        add_double('bat_min_v', 'bat_min', 0, 20, 7.0, 0.1)
        add_double('arm_pin_threshold_v', 'arm_threshold', 0, 5, 2.0, 0.1)

        add_section('kalman_filter')
        add_double('kf_q_alt', 'kf_q_alt', 0, 1, 0.05, 0.01)
        add_double('kf_q_vel', 'kf_q_vel', 0, 10, 0.5, 0.05)
        add_double('kf_r_baro', 'kf_r_baro', 0, 5, 0.8, 0.05)
        add_double('kf_r_accel', 'kf_r_accel', 0, 5, 0.3, 0.05)
        add_double('kf_baro_vel_scale', 'kf_baro_vel',0, 100, 30.0, 1.0)
        add_double('kf_baro_min_trust', 'kf_baro_min',0, 1, 0.25, 0.05)

        add_section('system')
        add_int('idle_hz', 'idle_hz', 1, 1000, 10)
        add_int('flight_hz', 'flight_hz', 1, 1000, 200)
        add_check('ignore_battery', 'battery_check', 'ignore_battery', False)
        add_check('buzzer_enable', 'buzzer', 'enable_buzzer', True)

        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        read_btn = QPushButton(self.tr_str('read_config'))
        read_btn.clicked.connect(lambda: self.send_command("config"))
        apply_btn = QPushButton(self.tr_str('apply_config'))
        apply_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        apply_btn.clicked.connect(self.apply_config)
        button_layout.addWidget(read_btn)
        button_layout.addWidget(apply_btn)
        main_layout.addLayout(button_layout)

        widget.setLayout(main_layout)
        return widget

    def create_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        folder_layout = QHBoxLayout()
        self.export_folder_label = QLabel(self.export_folder)
        folder_btn = QPushButton(self.tr_str('change_folder'))
        folder_btn.clicked.connect(self.choose_export_folder)
        folder_layout.addWidget(QLabel(self.tr_str('export_folder')))
        folder_layout.addWidget(self.export_folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)

        self.flight_table = QTableWidget()
        self.flight_table.setColumnCount(2)
        self.flight_table.setHorizontalHeaderLabels(
            [self.tr_str('flight_num'), self.tr_str('records')])
        self.update_flight_table_style()
        layout.addWidget(QLabel(self.tr_str('available_flights')))
        layout.addWidget(self.flight_table)

        layout.addWidget(QLabel(self.tr_str('flight_data_export')))

        export_layout = QHBoxLayout()
        export_all_btn = QPushButton(self.tr_str('export_all'))
        export_all_btn.clicked.connect(self.export_flights)
        export_all_btn.setStyleSheet("background-color: #9C27B0; color: white;")
        open_folder_btn = QPushButton(self.tr_str('open_folder'))
        open_folder_btn.clicked.connect(lambda: os.startfile(self.export_folder))
        export_layout.addWidget(export_all_btn)
        export_layout.addWidget(open_folder_btn)
        layout.addLayout(export_layout)

        widget.setLayout(layout)
        return widget

    # ──────────────────────────────────────────────────
    # SERIAL
    # ──────────────────────────────────────────────────
    def setup_serial(self):
        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.on_data_received)
        self.serial_thread.connected.connect(self.on_connection_changed)
        self.serial_thread.error.connect(self.on_serial_error)

        thread = QThread()
        self.serial_thread.moveToThread(thread)
        thread.start()
        self.serial_thread_obj = thread

    def toggle_connection(self):
        if self.serial_thread.ser and self.serial_thread.ser.is_open:
            self.serial_thread.disconnect()
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        else:
            port = self.port_combo.currentData()
            if not port:
                port = self.port_combo.currentText()
            if port and port != "No COM ports found":
                self.connect_btn.setEnabled(False)
                self.connect_btn.setText("Connecting…")
                self.serial_thread.connect(port)
                QTimer.singleShot(1000, lambda: self.connect_btn.setEnabled(True))
            else:
                QMessageBox.warning(self, "No Port", "Please select a valid COM port.")

    def detect_stm32_ports(self):
        self.port_combo.clear()
        self.detected_stm32_ports = []

        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("No COM ports found")
            self.status_label.setText("No COM ports available")
            self.status_label.setStyleSheet("color: orange;")
            return

        for port in ports:
            if self.is_stm32_port(port.device):
                self.detected_stm32_ports.append(port.device)
                self.port_combo.addItem(f"{port.device} (STM32 Detected)", port.device)

        if not self.detected_stm32_ports:
            for port in ports:
                self.port_combo.addItem(port.device, port.device)
            self.status_label.setText("No STM32 detected - showing all ports")
            self.status_label.setStyleSheet("color: orange;")
        else:
            self.status_label.setText(f"Found {len(self.detected_stm32_ports)} STM32 device(s)")
            self.status_label.setStyleSheet("color: blue;")

    def is_stm32_port(self, port):
        try:
            ser = serial.Serial(port, 115200, timeout=0.5)
            time.sleep(0.3)
            ser.write(b"status\n")
            time.sleep(0.5)
            response = ""
            while ser.in_waiting:
                response += ser.read().decode('utf-8', errors='ignore')
            ser.close()
            return "state:" in response or "PYTLASZ" in response or "alt_m:" in response
        except:
            return False

    def on_connection_changed(self, connected):
        if connected:
            self.status_label.setText(f"Connected to {self.serial_thread.port}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.statusBar().showMessage(f"Connected to {self.serial_thread.port}")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
            self.refresh_ports_btn.setEnabled(False)
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red;")
            self.statusBar().showMessage("Disconnected")
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.port_combo.setEnabled(True)
            self.refresh_ports_btn.setEnabled(True)

    def on_data_received(self, data):
        self.command_output.append(data)
        self.status_text.append(data)

    def on_serial_error(self, error):
        self.connect_btn.setEnabled(True)
        self.port_combo.setEnabled(True)
        self.refresh_ports_btn.setEnabled(True)
        self.status_label.setText("Connection Error")
        self.status_label.setStyleSheet("color: red;")
        QMessageBox.warning(self, "Serial Error", error)

    def send_command(self, cmd):
        if self.serial_thread.ser and self.serial_thread.ser.is_open:
            self.serial_thread.send_command(cmd)
        else:
            QMessageBox.warning(self, "Not Connected",
                "Please connect to the flight computer first.")

    # ──────────────────────────────────────────────────
    # CONFIG / EXPORT / MISC
    # ──────────────────────────────────────────────────
    def apply_config(self):
        if not (self.serial_thread.ser and self.serial_thread.ser.is_open):
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        for key, widget in self.config_fields.items():
            value = "1" if (isinstance(widget, QCheckBox) and widget.isChecked()) else \
                    "0" if isinstance(widget, QCheckBox) else str(widget.value())
            self.send_command(f"set {key} {value}")
            time.sleep(0.1)

    def export_flights(self):
        if not (self.serial_thread.ser and self.serial_thread.ser.is_open):
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        self.command_output.append("\n>>> Starting export...")
        self.send_command("export")
        QTimer.singleShot(2000, self.save_flight_data)

    def save_flight_data(self):
        if not self.flight_data:
            QMessageBox.information(self, "Export", "No flight data to export.")
            return
        for i, flight_csv in enumerate(self.flight_data, 1):
            filename = self.get_next_filename(f"flight{i}.csv")
            with open(os.path.join(self.export_folder, filename), 'w', newline='') as f:
                f.write(flight_csv)
        QMessageBox.information(self, "Export Complete",
            f"Exported {len(self.flight_data)} flights to {self.export_folder}")
        self.flight_data = []

    def get_next_filename(self, base_name):
        if not os.path.exists(os.path.join(self.export_folder, base_name)):
            return base_name
        name, ext = os.path.splitext(base_name)
        counter = 2
        while os.path.exists(os.path.join(self.export_folder, f"{name}{counter}{ext}")):
            counter += 1
        return f"{name}{counter}{ext}"

    def choose_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder", self.export_folder)
        if folder:
            self.export_folder = folder
            self.export_folder_label.setText(folder)
            Path(folder).mkdir(parents=True, exist_ok=True)

    def confirm_delete_flash(self):
        reply = QMessageBox.warning(self, "Delete Flash Memory",
            "This will erase all flight data on the STM32.\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.send_command("delete_flash")

    def cleanup_serial(self):
        if self.serial_thread and self.serial_thread.ser and self.serial_thread.ser.is_open:
            self.serial_thread.disconnect()
        if hasattr(self, 'serial_thread_obj') and self.serial_thread_obj.isRunning():
            self.serial_thread_obj.quit()
            self.serial_thread_obj.wait(1000)

    def closeEvent(self, event):
        self.cleanup_serial()
        event.accept()

    # ──────────────────────────────────────────────────
    # SETTINGS / THEME
    # ──────────────────────────────────────────────────
    def apply_settings_from_dialog(self, dark_mode):
        self.settings.setValue("dark_mode", dark_mode)
        self.settings.sync()
        self.dark_mode = dark_mode
        if self.dark_mode:
            self.apply_dark_mode()
        else:
            self.apply_light_mode()

    def open_settings(self):
        dialog = SettingsDialog(self, self.dark_mode)
        dialog.settings_applied.connect(self.apply_settings_from_dialog)
        dialog.exec_()

    def apply_dark_mode(self):
        self.setStyleSheet(DARK_MODE_STYLESHEET)
        self.update_flight_table_style()

    def apply_light_mode(self):
        self.setStyleSheet("")
        self.update_flight_table_style()

    def update_flight_table_style(self):
        if not hasattr(self, 'flight_table') or self.flight_table is None:
            return
        if self.dark_mode:
            self.flight_table.setStyleSheet("QTableWidget { background-color: #2d2d2d; color: #ffffff; }")
            self.flight_table.horizontalHeader().setStyleSheet(
                "QHeaderView::section { background-color: #2d2d2d; color: #ffffff; }")
        else:
            self.flight_table.setStyleSheet("QTableWidget { background-color: #ffffff; color: #000000; }")
            self.flight_table.horizontalHeader().setStyleSheet(
                "QHeaderView::section { background-color: #f0f0f0; color: #000000; }")


# ════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    window = FlightComputerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Allow forcing no re-exec via environment for debugging
    no_reexec = os.environ.get('PYTLASZ_NO_REEXEC', '') == '1'
    # Don't re-exec when packaged by PyInstaller (frozen)
    frozen = getattr(sys, 'frozen', False)
    if not no_reexec and not frozen and sys.platform == 'win32' and sys.executable.lower().endswith('python.exe'):
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw] + sys.argv[1:], close_fds=True)
            sys.exit(0)
    main()
