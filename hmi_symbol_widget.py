"""
HMI Symbol Widget - Expandable widget for HMI symbols
Shows HMI symbol with collapsible submenu for all sub-variables
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QDoubleSpinBox, QComboBox,
                             QCheckBox, QGroupBox, QScrollArea, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class HMISymbolWidget(QFrame):
    """
    Expandable widget for a single HMI symbol (ST_HMI_Setpoint, ST_HMI_ProcessValue, etc.)
    Shows main value with expand button to show all sub-variables
    """
    
    value_changed = pyqtSignal(str, object)  # symbol_path, new_value
    
    def __init__(self, symbol_name: str, symbol_data: dict, parent=None):
        super().__init__(parent)
        self.symbol_name = symbol_name
        self.symbol_data = symbol_data
        self.expanded = False
        self.has_alarm = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI for HMI symbol"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(5)
        
        # Header (always visible)
        header_layout = QHBoxLayout()
        
        # Expand/collapse button
        self.expand_button = QPushButton("▶")
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.clicked.connect(self.toggle_expand)
        self.expand_button.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        header_layout.addWidget(self.expand_button)
        
        # Symbol name and type
        name_label = QLabel(f"<b>{self.symbol_data.get('display_name', self.symbol_name)}</b>")
        name_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        header_layout.addWidget(name_label)
        
        # Type indicator
        hmi_type = self.get_hmi_type()
        type_label = QLabel(f"({hmi_type})")
        type_label.setStyleSheet("color: #666;")
        header_layout.addWidget(type_label)
        
        header_layout.addStretch()
        
        # Main value display (for quick view)
        self.main_value_label = QLabel("--")
        self.main_value_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.main_value_label.setStyleSheet("color: #2C5AA0;")
        header_layout.addWidget(self.main_value_label)
        
        # Unit
        unit = self.symbol_data.get('unit', '')
        if unit:
            unit_label = QLabel(unit)
            unit_label.setFont(QFont('Segoe UI', 10))
            header_layout.addWidget(unit_label)
        
        main_layout.addLayout(header_layout)
        
        # Full path (small text)
        path_label = QLabel(f"<i>{self.symbol_name}</i>")
        path_label.setFont(QFont('Segoe UI', 8))
        path_label.setStyleSheet("color: #888;")
        main_layout.addWidget(path_label)
        
        # Details panel (expandable)
        self.details_panel = QFrame()
        self.details_panel.setFrameStyle(QFrame.StyledPanel)
        self.details_panel.setVisible(False)
        
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(8)
        
        # Add sub-variable widgets based on HMI type
        self.create_details_widgets(details_layout)
        
        self.details_panel.setLayout(details_layout)
        main_layout.addWidget(self.details_panel)
        
        self.setLayout(main_layout)
        
        # Default styling
        self.update_style()
    
    def get_hmi_type(self) -> str:
        """Get HMI type label"""
        category = self.symbol_data.get('category', '')
        if category == 'setpoint':
            return 'Setpoint'
        elif category == 'process_value':
            return 'Procesværdi'
        elif category == 'switch':
            return 'Switch'
        elif category == 'alarm':
            return 'Alarm'
        return 'Unknown'
    
    def create_details_widgets(self, layout: QVBoxLayout):
        """Create detail widgets based on HMI type"""
        category = self.symbol_data.get('category', '')
        
        if category == 'setpoint':
            self.create_setpoint_details(layout)
        elif category == 'process_value':
            self.create_process_value_details(layout)
        elif category == 'switch':
            self.create_switch_details(layout)
        elif category == 'alarm':
            self.create_alarm_details(layout)
    
    def create_setpoint_details(self, layout: QVBoxLayout):
        """Create details for ST_HMI_Setpoint"""
        # Value control
        value_group = QGroupBox("Værdi")
        value_layout = QHBoxLayout()
        
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setMinimum(self.symbol_data.get('min', 0))
        self.value_spinbox.setMaximum(self.symbol_data.get('max', 100))
        self.value_spinbox.setDecimals(self.symbol_data.get('decimals', 2))
        self.value_spinbox.setSingleStep(self.symbol_data.get('step', 1))
        self.value_spinbox.setMinimumWidth(120)
        value_layout.addWidget(self.value_spinbox)
        
        write_btn = QPushButton("Skriv")
        write_btn.clicked.connect(self.on_write_setpoint)
        write_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        value_layout.addWidget(write_btn)
        value_layout.addStretch()
        
        value_group.setLayout(value_layout)
        layout.addWidget(value_group)
        
        # Config section
        config_group = QGroupBox("Konfiguration")
        config_layout = QVBoxLayout()
        
        config_layout.addWidget(QLabel(f"Unit: {self.symbol_data.get('unit', '-')}"))
        config_layout.addWidget(QLabel(f"Range: {self.symbol_data.get('min', 0)} - {self.symbol_data.get('max', 100)}"))
        config_layout.addWidget(QLabel(f"Decimaler: {self.symbol_data.get('decimals', 2)}"))
        config_layout.addWidget(QLabel(f"Step: {self.symbol_data.get('step', 1)}"))
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Alarm limits (if present)
        if self.symbol_data.get('alarm_limits'):
            self.create_alarm_limits_display(layout, self.symbol_data['alarm_limits'])
        
        # Display config
        self.create_display_config(layout)
    
    def create_process_value_details(self, layout: QVBoxLayout):
        """Create details for ST_HMI_ProcessValue"""
        # Current value (read-only)
        value_group = QGroupBox("Aktuel Værdi")
        value_layout = QHBoxLayout()
        
        self.value_display = QLabel("--")
        self.value_display.setFont(QFont('Segoe UI', 14, QFont.Bold))
        self.value_display.setStyleSheet("color: #2C5AA0;")
        value_layout.addWidget(self.value_display)
        
        unit = self.symbol_data.get('unit', '')
        if unit:
            value_layout.addWidget(QLabel(unit))
        
        value_layout.addStretch()
        value_group.setLayout(value_layout)
        layout.addWidget(value_group)
        
        # Config
        config_group = QGroupBox("Konfiguration")
        config_layout = QVBoxLayout()
        
        config_layout.addWidget(QLabel(f"Unit: {self.symbol_data.get('unit', '-')}"))
        config_layout.addWidget(QLabel(f"Decimaler: {self.symbol_data.get('decimals', 2)}"))
        
        # Quality indicator
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_indicator = QLabel("● Good")
        self.quality_indicator.setStyleSheet("color: green;")
        quality_layout.addWidget(self.quality_indicator)
        quality_layout.addStretch()
        config_layout.addLayout(quality_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Alarm limits
        if self.symbol_data.get('alarm_limits'):
            self.create_alarm_limits_display(layout, self.symbol_data['alarm_limits'])
        
        # Display config
        self.create_display_config(layout)
    
    def create_switch_details(self, layout: QVBoxLayout):
        """Create details for ST_HMI_Switch"""
        # Position selector
        switch_group = QGroupBox("Position")
        switch_layout = QVBoxLayout()
        
        self.position_combo = QComboBox()
        positions = self.symbol_data.get('positions', [])
        
        # Handle both list and dict formats
        if isinstance(positions, dict):
            for pos_idx, label in sorted(positions.items()):
                self.position_combo.addItem(f"{pos_idx}: {label}", int(pos_idx))
        elif isinstance(positions, list):
            for i, label in enumerate(positions):
                self.position_combo.addItem(f"{i}: {label}", i)
        
        self.position_combo.currentIndexChanged.connect(self.on_position_changed)
        switch_layout.addWidget(self.position_combo)
        
        switch_group.setLayout(switch_layout)
        layout.addWidget(switch_group)
        
        # Display config
        self.create_display_config(layout)
    
    def create_alarm_details(self, layout: QVBoxLayout):
        """Create details for ST_HMI_Alarm"""
        # Alarm status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.alarm_status_label = QLabel("● Inaktiv")
        self.alarm_status_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.alarm_status_label.setStyleSheet("color: green;")
        status_layout.addWidget(self.alarm_status_label)
        
        self.alarm_text_label = QLabel("")
        status_layout.addWidget(self.alarm_text_label)
        
        # Acknowledge button
        self.ack_button = QPushButton("Kvitter")
        self.ack_button.clicked.connect(self.on_acknowledge_alarm)
        self.ack_button.setEnabled(False)
        status_layout.addWidget(self.ack_button)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Priority
        priority_label = QLabel(f"Prioritet: {self.symbol_data.get('priority', 3)}")
        layout.addWidget(priority_label)
        
        # Display config
        self.create_display_config(layout)
    
    def create_alarm_limits_display(self, layout: QVBoxLayout, limits: dict):
        """Create alarm limits display"""
        alarm_group = QGroupBox("Alarm Grænser")
        alarm_layout = QVBoxLayout()
        
        if 'high_high' in limits:
            alarm_layout.addWidget(QLabel(f"⛔ Høj-Høj: {limits['high_high']}"))
        if 'high' in limits:
            alarm_layout.addWidget(QLabel(f"⚠️ Høj: {limits['high']}"))
        if 'low' in limits:
            alarm_layout.addWidget(QLabel(f"⚠️ Lav: {limits['low']}"))
        if 'low_low' in limits:
            alarm_layout.addWidget(QLabel(f"⛔ Lav-Lav: {limits['low_low']}"))
        
        alarm_group.setLayout(alarm_layout)
        layout.addWidget(alarm_group)
    
    def create_display_config(self, layout: QVBoxLayout):
        """Create display configuration section"""
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        display_name = self.symbol_data.get('display_name', self.symbol_name)
        display_layout.addWidget(QLabel(f"Navn: {display_name}"))
        
        description = self.symbol_data.get('description', '')
        if description:
            desc_label = QLabel(f"Beskrivelse: {description}")
            desc_label.setWordWrap(True)
            display_layout.addWidget(desc_label)
        
        visible = self.symbol_data.get('visible', True)
        readonly = self.symbol_data.get('readonly', False)
        
        display_layout.addWidget(QLabel(f"Synlig: {'Ja' if visible else 'Nej'}"))
        display_layout.addWidget(QLabel(f"Læs-kun: {'Ja' if readonly else 'Nej'}"))
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
    
    def toggle_expand(self):
        """Toggle expansion of details panel"""
        self.expanded = not self.expanded
        self.details_panel.setVisible(self.expanded)
        
        # Update button icon
        self.expand_button.setText("▼" if self.expanded else "▶")
        
        # Animate size change (optional)
        self.adjustSize()
    
    def on_write_setpoint(self):
        """Handle write setpoint button"""
        if hasattr(self, 'value_spinbox'):
            value = self.value_spinbox.value()
            # Emit with .Value path
            value_path = f"{self.symbol_name}.Value"
            self.value_changed.emit(value_path, value)
            logger.info(f"Writing {value} to {value_path}")
    
    def on_position_changed(self, index):
        """Handle switch position change"""
        if hasattr(self, 'position_combo'):
            position = self.position_combo.itemData(index)
            # Emit with .Position path
            position_path = f"{self.symbol_name}.Position"
            self.value_changed.emit(position_path, position)
            logger.info(f"Switching {position_path} to position {position}")
    
    def on_acknowledge_alarm(self):
        """Handle alarm acknowledgment"""
        # Emit acknowledge signal with .Acknowledged path
        ack_path = f"{self.symbol_name}.Acknowledged"
        self.value_changed.emit(ack_path, True)
        logger.info(f"Acknowledging alarm {ack_path}")
    
    def update_value(self, value):
        """Update main value display"""
        category = self.symbol_data.get('category', '')
        decimals = self.symbol_data.get('decimals', 2)
        unit = self.symbol_data.get('unit', '')
        
        if category in ['setpoint', 'process_value']:
            if isinstance(value, (int, float)):
                formatted = f"{value:.{decimals}f}"
                self.main_value_label.setText(f"{formatted} {unit}")
                
                if hasattr(self, 'value_spinbox'):
                    self.value_spinbox.blockSignals(True)
                    self.value_spinbox.setValue(value)
                    self.value_spinbox.blockSignals(False)
                
                if hasattr(self, 'value_display'):
                    self.value_display.setText(formatted)
        
        elif category == 'switch':
            if isinstance(value, int):
                self.main_value_label.setText(f"Pos {value}")
                
                if hasattr(self, 'position_combo'):
                    self.position_combo.blockSignals(True)
                    self.position_combo.setCurrentIndex(value)
                    self.position_combo.blockSignals(False)
        
        elif category == 'alarm':
            if isinstance(value, bool):
                if value:
                    self.main_value_label.setText("🔴 AKTIV")
                    self.main_value_label.setStyleSheet("color: red;")
                    if hasattr(self, 'alarm_status_label'):
                        self.alarm_status_label.setText("🔴 Aktiv")
                        self.alarm_status_label.setStyleSheet("color: red;")
                    if hasattr(self, 'ack_button'):
                        self.ack_button.setEnabled(True)
                else:
                    self.main_value_label.setText("🟢 OK")
                    self.main_value_label.setStyleSheet("color: green;")
                    if hasattr(self, 'alarm_status_label'):
                        self.alarm_status_label.setText("🟢 Inaktiv")
                        self.alarm_status_label.setStyleSheet("color: green;")
                    if hasattr(self, 'ack_button'):
                        self.ack_button.setEnabled(False)
    
    def set_alarm_state(self, has_alarm: bool):
        """Set alarm indication for the widget"""
        self.has_alarm = has_alarm
        self.update_style()
    
    def update_style(self):
        """Update widget style based on state"""
        if self.has_alarm:
            self.setStyleSheet("""
                HMISymbolWidget {
                    background-color: #FFE6E6;
                    border: 3px solid #FF0000;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                HMISymbolWidget {
                    background-color: #F8F9FA;
                    border: 2px solid #DEE2E6;
                    border-radius: 8px;
                }
            """)


class HMISymbolPanel(QScrollArea):
    """
    Panel containing multiple HMI symbol widgets
    Organized by category (Setpoints, Process Values, Switches, Alarms)
    """
    
    value_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets = {}  # symbol_name -> HMISymbolWidget
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup panel UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Main widget
        main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Category sections
        self.setpoint_layout = QVBoxLayout()
        self.pv_layout = QVBoxLayout()
        self.switch_layout = QVBoxLayout()
        self.alarm_layout = QVBoxLayout()
        
        # Add category headers and layouts
        self.add_category_section("Setpoints", self.setpoint_layout)
        self.add_category_section("Procesværdier", self.pv_layout)
        self.add_category_section("Switches", self.switch_layout)
        self.add_category_section("Alarmer", self.alarm_layout)
        
        self.main_layout.addStretch()
        
        main_widget.setLayout(self.main_layout)
        self.setWidget(main_widget)
    
    def add_category_section(self, title: str, layout: QVBoxLayout):
        """Add a category section with header"""
        header = QLabel(f"<b>{title}</b>")
        header.setFont(QFont('Segoe UI', 12, QFont.Bold))
        header.setStyleSheet("color: #2C5AA0; padding: 5px;")
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #CCC;")
        
        self.main_layout.addWidget(header)
        self.main_layout.addWidget(separator)
        self.main_layout.addLayout(layout)
    
    def add_hmi_symbol(self, symbol_name: str, symbol_data: dict):
        """Add HMI symbol widget"""
        widget = HMISymbolWidget(symbol_name, symbol_data)
        widget.value_changed.connect(self.value_changed.emit)
        
        self.widgets[symbol_name] = widget
        
        # Add to appropriate category layout
        category = symbol_data.get('category', '')
        if category == 'setpoint':
            self.setpoint_layout.addWidget(widget)
        elif category == 'process_value':
            self.pv_layout.addWidget(widget)
        elif category == 'switch':
            self.switch_layout.addWidget(widget)
        elif category == 'alarm':
            self.alarm_layout.addWidget(widget)
        
        logger.info(f"Added HMI symbol widget: {symbol_name} ({category})")
    
    def update_value(self, symbol_name: str, value):
        """Update symbol value"""
        # Handle both full path and base path
        # E.g., both "MAIN.Motor01.HMI.SpeedSetpoint" and "MAIN.Motor01.HMI.SpeedSetpoint.Value"
        base_symbol = symbol_name.split('.Value')[0].split('.Position')[0].split('.Active')[0]
        
        if base_symbol in self.widgets:
            self.widgets[base_symbol].update_value(value)
    
    def set_alarm_state(self, symbol_name: str, has_alarm: bool):
        """Set alarm state for symbol"""
        if symbol_name in self.widgets:
            self.widgets[symbol_name].set_alarm_state(has_alarm)
    
    def clear(self):
        """Clear all widgets"""
        for widget in self.widgets.values():
            widget.deleteLater()
        
        self.widgets.clear()
