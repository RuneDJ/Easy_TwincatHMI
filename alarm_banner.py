"""
Alarm Banner Widget for TwinCAT HMI
Displays active alarms with color coding and acknowledgment buttons
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QFrame, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmWidget(QFrame):
    """Individual alarm display widget"""
    
    acknowledge_clicked = pyqtSignal(str)  # Emits alarm ID
    alarm_clicked = pyqtSignal(str)  # Emits symbol name for trend
    
    # Priority colors
    PRIORITY_COLORS = {
        1: {'bg': '#DC143C', 'fg': '#FFFFFF', 'icon': '⛔'},  # Critical - Red
        2: {'bg': '#FF8C00', 'fg': '#FFFFFF', 'icon': '⚠️'},  # High - Orange
        3: {'bg': '#FFD700', 'fg': '#000000', 'icon': '⚡'},  # Medium - Yellow
        4: {'bg': '#4169E1', 'fg': '#FFFFFF', 'icon': 'ℹ️'}   # Low - Blue
    }
    
    def __init__(self, alarm, parent=None):
        super().__init__(parent)
        self.alarm = alarm
        self.blink_state = False
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup alarm widget UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Priority icon
        self.icon_label = QLabel()
        self.icon_label.setFont(QFont('Segoe UI', 14))
        layout.addWidget(self.icon_label)
        
        # Alarm message
        self.message_label = QLabel()
        self.message_label.setFont(QFont('Segoe UI', 10))
        self.message_label.setWordWrap(False)
        self.message_label.setCursor(Qt.PointingHandCursor)
        self.message_label.mousePressEvent = lambda e: self.alarm_clicked.emit(self.alarm.symbol_name)
        layout.addWidget(self.message_label, stretch=1)
        
        # Timestamp
        self.time_label = QLabel()
        self.time_label.setFont(QFont('Segoe UI', 8))
        layout.addWidget(self.time_label)
        
        # Acknowledge button
        self.ack_button = QPushButton('Kvitter')
        self.ack_button.setMaximumWidth(80)
        self.ack_button.clicked.connect(lambda: self.acknowledge_clicked.emit(self.alarm.id))
        layout.addWidget(self.ack_button)
        
        self.setLayout(layout)
        
        # Make clickable
        self.setCursor(Qt.PointingHandCursor)
    
    def update_display(self):
        """Update alarm display"""
        # Get color scheme
        colors = self.PRIORITY_COLORS.get(self.alarm.priority.value, 
                                         self.PRIORITY_COLORS[2])
        
        # Set icon
        self.icon_label.setText(colors['icon'])
        
        # Set message
        self.message_label.setText(self.alarm.message)
        
        # Set timestamp
        time_str = self.alarm.timestamp.strftime('%H:%M:%S')
        self.time_label.setText(time_str)
        
        # Set colors based on state
        if self.alarm.state.value == 'ACTIVE':
            bg_color = colors['bg']
            fg_color = colors['fg']
            self.ack_button.setVisible(True)
        elif self.alarm.state.value == 'ACKNOWLEDGED':
            # Dimmed colors for acknowledged
            bg_color = self._dim_color(colors['bg'])
            fg_color = colors['fg']
            self.ack_button.setVisible(False)
        else:
            bg_color = '#CCCCCC'
            fg_color = '#000000'
            self.ack_button.setVisible(False)
        
        # Apply style
        self.setStyleSheet(f"""
            AlarmWidget {{
                background-color: {bg_color};
                border: 2px solid {self._darken_color(bg_color)};
                border-radius: 5px;
            }}
        """)
        
        self.message_label.setStyleSheet(f"color: {fg_color};")
        self.time_label.setStyleSheet(f"color: {fg_color};")
        self.icon_label.setStyleSheet(f"color: {fg_color};")
    
    def set_blink(self, blink: bool):
        """Set blinking state"""
        self.blink_state = blink
        if blink:
            if self.alarm.state.value == 'ACTIVE':
                self.setVisible(not self.isVisible())
        else:
            self.setVisible(True)
    
    def _dim_color(self, color: str) -> str:
        """Dim a color by mixing with gray"""
        # Simple dimming by blending with gray
        qcolor = QColor(color)
        r = int((qcolor.red() + 128) / 2)
        g = int((qcolor.green() + 128) / 2)
        b = int((qcolor.blue() + 128) / 2)
        return f'#{r:02X}{g:02X}{b:02X}'
    
    def _darken_color(self, color: str) -> str:
        """Darken a color"""
        qcolor = QColor(color)
        return qcolor.darker(120).name()


class AlarmBanner(QWidget):
    """Alarm banner widget with scrolling list"""
    
    acknowledge_all_clicked = pyqtSignal()
    show_history_clicked = pyqtSignal()
    alarm_clicked = pyqtSignal(str)  # Emits symbol name
    
    def __init__(self, alarm_manager, max_visible: int = 5, parent=None):
        super().__init__(parent)
        self.alarm_manager = alarm_manager
        self.max_visible = max_visible
        self.alarm_widgets = {}
        self.blink_timer = None
        
        self.setup_ui()
        
        # Register callback with alarm manager
        self.alarm_manager.register_callback(self.update_alarms)
        
        # Start blink timer
        self.start_blink_timer()
    
    def setup_ui(self):
        """Setup banner UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel('🔔 AKTIVE ALARMER (0)')
        self.title_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Acknowledge all button
        self.ack_all_button = QPushButton('Kvitter Alle')
        self.ack_all_button.clicked.connect(self.acknowledge_all_clicked.emit)
        header_layout.addWidget(self.ack_all_button)
        
        # History button
        self.history_button = QPushButton('Historik')
        self.history_button.clicked.connect(self.show_history_clicked.emit)
        header_layout.addWidget(self.history_button)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for alarms
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container for alarm widgets
        self.alarm_container = QWidget()
        self.alarm_layout = QVBoxLayout()
        self.alarm_layout.setSpacing(3)
        self.alarm_layout.addStretch()
        self.alarm_container.setLayout(self.alarm_layout)
        
        scroll_area.setWidget(self.alarm_container)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
        # Style
        self.setStyleSheet("""
            AlarmBanner {
                background-color: #F0F0F0;
                border: 2px solid #888888;
                border-radius: 5px;
            }
        """)
        
        # Initially hidden
        self.setVisible(False)
    
    def update_alarms(self, alarms):
        """
        Update alarm display
        
        Args:
            alarms: List of Alarm objects
        """
        # Clear existing widgets
        for widget in self.alarm_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self.alarm_widgets.clear()
        
        # Update title
        alarm_count = len(alarms)
        self.title_label.setText(f'🔔 AKTIVE ALARMER ({alarm_count})')
        
        # Show/hide banner
        if alarm_count > 0:
            self.setVisible(True)
        else:
            self.setVisible(False)
            return
        
        # Add new alarm widgets
        for alarm in alarms:
            widget = AlarmWidget(alarm)
            widget.acknowledge_clicked.connect(self._on_acknowledge)
            widget.alarm_clicked.connect(self.alarm_clicked.emit)
            
            # Insert before stretch
            self.alarm_layout.insertWidget(self.alarm_layout.count() - 1, widget)
            self.alarm_widgets[alarm.id] = widget
        
        # Adjust height based on number of alarms
        widget_height = 50  # Approximate height per alarm widget
        max_height = min(alarm_count, self.max_visible) * widget_height + 80
        self.setMaximumHeight(max_height)
    
    def _on_acknowledge(self, alarm_id: str):
        """Handle acknowledge button click"""
        self.alarm_manager.acknowledge_alarm(alarm_id)
    
    def start_blink_timer(self):
        """Start blinking timer for unacknowledged alarms"""
        if self.blink_timer is None:
            self.blink_timer = QTimer()
            self.blink_timer.timeout.connect(self._toggle_blink)
            self.blink_timer.start(500)  # 500ms blink interval
    
    def stop_blink_timer(self):
        """Stop blinking timer"""
        if self.blink_timer:
            self.blink_timer.stop()
            self.blink_timer = None
    
    def _toggle_blink(self):
        """Toggle blinking state for unacknowledged alarms"""
        for alarm_id, widget in self.alarm_widgets.items():
            if widget.alarm.state.value == 'ACTIVE':
                widget.set_blink(True)
            else:
                widget.set_blink(False)
    
    def set_expanded(self, expanded: bool):
        """Expand or collapse banner"""
        if expanded:
            self.alarm_container.setVisible(True)
        else:
            self.alarm_container.setVisible(False)
