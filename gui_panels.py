"""
GUI Panels for TwinCAT HMI
Setpoint, Switch, and Process Value widgets
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
                             QComboBox, QGroupBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDoubleValidator, QIntValidator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SetpointWidget(QFrame):
    """Widget for a single setpoint"""
    
    value_changed = pyqtSignal(str, float)  # symbol_name, new_value
    
    def __init__(self, symbol_config, parent=None):
        super().__init__(parent)
        self.symbol_config = symbol_config
        self.has_alarm = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup setpoint UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel(self.symbol_config['display_name'])
        label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        layout.addWidget(label)
        
        # Value input
        input_layout = QHBoxLayout()
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self.symbol_config.get('min', 0))
        self.spinbox.setMaximum(self.symbol_config.get('max', 100))
        self.spinbox.setDecimals(self.symbol_config.get('decimals', 1))
        self.spinbox.setSingleStep(self.symbol_config.get('step', 1))
        self.spinbox.setMinimumWidth(100)
        self.spinbox.valueChanged.connect(self._on_value_changed)
        input_layout.addWidget(self.spinbox)
        
        # Unit
        unit = self.symbol_config.get('unit', '')
        if unit:
            unit_label = QLabel(unit)
            unit_label.setFont(QFont('Segoe UI', 10))
            input_layout.addWidget(unit_label)
        
        input_layout.addStretch()
        
        # Write button
        self.write_button = QPushButton('Skriv')
        self.write_button.clicked.connect(self._on_write_clicked)
        input_layout.addWidget(self.write_button)
        
        layout.addLayout(input_layout)
        
        # Info label (range)
        info_text = f"Range: {self.symbol_config.get('min', 0)} - {self.symbol_config.get('max', 100)}"
        info_label = QLabel(info_text)
        info_label.setFont(QFont('Segoe UI', 8))
        info_label.setStyleSheet("color: #666666;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # Normal style
        self.setStyleSheet("""
            SetpointWidget {
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
            }
        """)
    
    def _on_value_changed(self, value):
        """Handle spinbox value change"""
        # Just update the spinbox, don't write yet
        pass
    
    def _on_write_clicked(self):
        """Handle write button click"""
        value = self.spinbox.value()
        self.value_changed.emit(self.symbol_config['name'], value)
    
    def set_value(self, value: float):
        """Update displayed value"""
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
    
    def set_alarm_state(self, has_alarm: bool):
        """Set alarm indication"""
        self.has_alarm = has_alarm
        
        if has_alarm:
            self.setStyleSheet("""
                SetpointWidget {
                    background-color: #FFCCCC;
                    border: 3px solid #FF0000;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                SetpointWidget {
                    background-color: #FFFFFF;
                    border: 2px solid #CCCCCC;
                    border-radius: 5px;
                }
            """)


class ProcessValueWidget(QFrame):
    """Widget for displaying process value"""
    
    clicked = pyqtSignal(str)  # Emits symbol name when clicked
    
    def __init__(self, symbol_config, parent=None):
        super().__init__(parent)
        self.symbol_config = symbol_config
        self.has_alarm = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup process value UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel(self.symbol_config['display_name'])
        label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        layout.addWidget(label)
        
        # Value display
        value_layout = QHBoxLayout()
        
        self.value_label = QLabel('---')
        self.value_label.setFont(QFont('Segoe UI', 16, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        value_layout.addWidget(self.value_label)
        
        # Unit
        unit = self.symbol_config.get('unit', '')
        if unit:
            unit_label = QLabel(unit)
            unit_label.setFont(QFont('Segoe UI', 12))
            value_layout.addWidget(unit_label)
        
        value_layout.addStretch()
        
        layout.addLayout(value_layout)
        
        # Alarm limits info (if present)
        alarm_config = self.symbol_config.get('alarm_config', {})
        if alarm_config.get('enabled', False):
            limits = alarm_config.get('limits', {})
            info_parts = []
            
            if 'high_high' in limits:
                info_parts.append(f"HH: {limits['high_high']}")
            if 'high' in limits:
                info_parts.append(f"H: {limits['high']}")
            if 'low' in limits:
                info_parts.append(f"L: {limits['low']}")
            if 'low_low' in limits:
                info_parts.append(f"LL: {limits['low_low']}")
            
            if info_parts:
                info_label = QLabel(' | '.join(info_parts))
                info_label.setFont(QFont('Segoe UI', 8))
                info_label.setStyleSheet("color: #666666;")
                layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # Make clickable for trend
        self.mousePressEvent = lambda e: self.clicked.emit(self.symbol_config['name'])
        
        # Normal style
        self._update_style()
    
    def set_value(self, value: float):
        """Update displayed value"""
        decimals = self.symbol_config.get('decimals', 2)
        format_str = self.symbol_config.get('format', f'{{:.{decimals}f}}')
        
        try:
            value_str = format_str.format(value)
        except:
            value_str = f"{value:.{decimals}f}"
        
        self.value_label.setText(value_str)
    
    def set_alarm_state(self, has_alarm: bool):
        """Set alarm indication"""
        self.has_alarm = has_alarm
        self._update_style()
    
    def _update_style(self):
        """Update widget style"""
        if self.has_alarm:
            self.setStyleSheet("""
                ProcessValueWidget {
                    background-color: #FFCCCC;
                    border: 3px solid #FF0000;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                ProcessValueWidget {
                    background-color: #E8F4F8;
                    border: 2px solid #4682B4;
                    border-radius: 5px;
                }
            """)


class SwitchWidget(QFrame):
    """Widget for switch/selector"""
    
    value_changed = pyqtSignal(str, int)  # symbol_name, position
    
    def __init__(self, symbol_config, parent=None):
        super().__init__(parent)
        self.symbol_config = symbol_config
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup switch UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel(self.symbol_config['display_name'])
        label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        layout.addWidget(label)
        
        # Combo box
        self.combo = QComboBox()
        self.combo.setFont(QFont('Segoe UI', 10))
        
        # Add positions
        positions = self.symbol_config.get('positions', {})
        for pos_num in sorted(positions.keys()):
            self.combo.addItem(positions[pos_num], pos_num)
        
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.combo)
        
        self.setLayout(layout)
        
        self.setStyleSheet("""
            SwitchWidget {
                background-color: #FFF8DC;
                border: 2px solid #DAA520;
                border-radius: 5px;
            }
        """)
    
    def _on_selection_changed(self, index):
        """Handle selection change"""
        pos_num = self.combo.itemData(index)
        self.value_changed.emit(self.symbol_config['name'], pos_num)
    
    def set_value(self, value: int):
        """Update selected value"""
        # Find index for this position value
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == value:
                self.combo.blockSignals(True)
                self.combo.setCurrentIndex(i)
                self.combo.blockSignals(False)
                break


class SetpointPanel(QGroupBox):
    """Panel containing all setpoints"""
    
    value_changed = pyqtSignal(str, float)
    
    def __init__(self, parent=None):
        super().__init__("Setpunkter", parent)
        self.setFont(QFont('Segoe UI', 11, QFont.Bold))
        
        self.widgets = {}
        self.layout = QVBoxLayout()
        self.layout.addStretch()
        self.setLayout(self.layout)
    
    def add_setpoint(self, symbol_config):
        """Add a setpoint widget"""
        widget = SetpointWidget(symbol_config)
        widget.value_changed.connect(self.value_changed.emit)
        
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, widget)
        self.widgets[symbol_config['name']] = widget
    
    def update_value(self, symbol_name: str, value: float):
        """Update setpoint value"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_value(value)
    
    def set_alarm_state(self, symbol_name: str, has_alarm: bool):
        """Set alarm state for setpoint"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_alarm_state(has_alarm)


class ProcessValuePanel(QGroupBox):
    """Panel containing all process values"""
    
    value_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("Procesværdier", parent)
        self.setFont(QFont('Segoe UI', 11, QFont.Bold))
        
        self.widgets = {}
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
        self.next_row = 0
        self.next_col = 0
        self.max_cols = 2
    
    def add_process_value(self, symbol_config):
        """Add a process value widget"""
        widget = ProcessValueWidget(symbol_config)
        widget.clicked.connect(self.value_clicked.emit)
        
        self.layout.addWidget(widget, self.next_row, self.next_col)
        self.widgets[symbol_config['name']] = widget
        
        # Update grid position
        self.next_col += 1
        if self.next_col >= self.max_cols:
            self.next_col = 0
            self.next_row += 1
    
    def update_value(self, symbol_name: str, value: float):
        """Update process value"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_value(value)
    
    def set_alarm_state(self, symbol_name: str, has_alarm: bool):
        """Set alarm state for process value"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_alarm_state(has_alarm)


class SwitchPanel(QGroupBox):
    """Panel containing all switches"""
    
    value_changed = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__("Switches", parent)
        self.setFont(QFont('Segoe UI', 11, QFont.Bold))
        
        self.widgets = {}
        self.layout = QVBoxLayout()
        self.layout.addStretch()
        self.setLayout(self.layout)
    
    def add_switch(self, symbol_config):
        """Add a switch widget"""
        widget = SwitchWidget(symbol_config)
        widget.value_changed.connect(self.value_changed.emit)
        
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, widget)
        self.widgets[symbol_config['name']] = widget
    
    def update_value(self, symbol_name: str, value: int):
        """Update switch value"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_value(value)
