"""
Alarm History Window for TwinCAT HMI
Displays historical alarms with filtering and export
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                             QLineEdit, QHeaderView, QFileDialog, QDateEdit,
                             QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmHistoryWindow(QDialog):
    """Window for displaying alarm history"""
    
    # Priority colors (same as AlarmWidget)
    PRIORITY_COLORS = {
        1: QColor('#DC143C'),  # Critical
        2: QColor('#FF8C00'),  # High
        3: QColor('#FFD700'),  # Medium
        4: QColor('#4169E1')   # Low
    }
    
    def __init__(self, alarm_manager, alarm_logger, parent=None):
        super().__init__(parent)
        self.alarm_manager = alarm_manager
        self.alarm_logger = alarm_logger
        
        self.setup_ui()
        self.load_alarms()
    
    def setup_ui(self):
        """Setup history window UI"""
        self.setWindowTitle('Alarm Historik')
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout()
        
        # Filter section
        filter_group = QGroupBox('Filtre')
        filter_layout = QHBoxLayout()
        
        # Priority filter
        filter_layout.addWidget(QLabel('Prioritet:'))
        self.priority_combo = QComboBox()
        self.priority_combo.addItem('Alle', None)
        self.priority_combo.addItem('⛔ Kritisk', 1)
        self.priority_combo.addItem('⚠️ Høj', 2)
        self.priority_combo.addItem('⚡ Medium', 3)
        self.priority_combo.addItem('ℹ️ Lav', 4)
        self.priority_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_combo)
        
        # State filter
        filter_layout.addWidget(QLabel('Status:'))
        self.state_combo = QComboBox()
        self.state_combo.addItem('Alle', None)
        self.state_combo.addItem('Aktiv', 'ACTIVE')
        self.state_combo.addItem('Kvitteret', 'ACKNOWLEDGED')
        self.state_combo.addItem('Clearet', 'CLEARED')
        self.state_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.state_combo)
        
        # Date filter
        filter_layout.addWidget(QLabel('Fra:'))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel('Til:'))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.end_date)
        
        # Search box
        filter_layout.addWidget(QLabel('Søg:'))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Symbol eller besked...')
        self.search_box.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_box)
        
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Tidspunkt', 'Symbol', 'Værdi', 'Type', 'Prioritet', 
            'Status', 'Besked', 'Kvitteret af', 'Kvitteret tidspunkt'
        ])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton('Opdater')
        self.refresh_button.clicked.connect(self.load_alarms)
        button_layout.addWidget(self.refresh_button)
        
        self.export_button = QPushButton('Eksporter til CSV')
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)
        
        self.clear_history_button = QPushButton('Ryd Historik')
        self.clear_history_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_history_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton('Luk')
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setFont(QFont('Segoe UI', 9))
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_alarms(self):
        """Load alarms from alarm manager history"""
        # Get alarms from manager
        alarms = self.alarm_manager.get_alarm_history(limit=1000)
        
        self.all_alarms = alarms
        self.apply_filters()
    
    def apply_filters(self):
        """Apply filters to alarm list"""
        filtered_alarms = self.all_alarms.copy()
        
        # Priority filter
        priority = self.priority_combo.currentData()
        if priority is not None:
            filtered_alarms = [a for a in filtered_alarms if a.priority.value == priority]
        
        # State filter
        state = self.state_combo.currentData()
        if state is not None:
            filtered_alarms = [a for a in filtered_alarms if a.state.value == state]
        
        # Date filter
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        filtered_alarms = [
            a for a in filtered_alarms 
            if start_date <= a.timestamp.date() <= end_date
        ]
        
        # Search filter
        search_text = self.search_box.text().lower()
        if search_text:
            filtered_alarms = [
                a for a in filtered_alarms 
                if search_text in a.symbol_name.lower() or 
                   search_text in a.message.lower()
            ]
        
        self.display_alarms(filtered_alarms)
    
    def display_alarms(self, alarms):
        """Display alarms in table"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(alarms))
        
        for row, alarm in enumerate(alarms):
            # Timestamp
            time_item = QTableWidgetItem(alarm.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            self.table.setItem(row, 0, time_item)
            
            # Symbol
            symbol_item = QTableWidgetItem(alarm.symbol_name)
            self.table.setItem(row, 1, symbol_item)
            
            # Value
            value_item = QTableWidgetItem(f"{alarm.value:.2f}")
            self.table.setItem(row, 2, value_item)
            
            # Type
            type_item = QTableWidgetItem(alarm.alarm_type.value)
            self.table.setItem(row, 3, type_item)
            
            # Priority
            priority_icons = {1: '⛔', 2: '⚠️', 3: '⚡', 4: 'ℹ️'}
            priority_names = {1: 'Kritisk', 2: 'Høj', 3: 'Medium', 4: 'Lav'}
            priority_text = f"{priority_icons.get(alarm.priority.value, '')} {priority_names.get(alarm.priority.value, '')}"
            priority_item = QTableWidgetItem(priority_text)
            
            # Color code by priority
            color = self.PRIORITY_COLORS.get(alarm.priority.value, QColor('#CCCCCC'))
            priority_item.setBackground(color)
            if alarm.priority.value in [1, 2, 4]:  # Dark backgrounds
                priority_item.setForeground(QColor('#FFFFFF'))
            
            self.table.setItem(row, 4, priority_item)
            
            # State
            state_item = QTableWidgetItem(alarm.state.value)
            self.table.setItem(row, 5, state_item)
            
            # Message
            message_item = QTableWidgetItem(alarm.message)
            self.table.setItem(row, 6, message_item)
            
            # Acknowledged by
            ack_by = alarm.acknowledged_by if alarm.acknowledged_by else ''
            ack_by_item = QTableWidgetItem(ack_by)
            self.table.setItem(row, 7, ack_by_item)
            
            # Acknowledged time
            ack_time = alarm.acknowledged_time.strftime('%H:%M:%S') if alarm.acknowledged_time else ''
            ack_time_item = QTableWidgetItem(ack_time)
            self.table.setItem(row, 8, ack_time_item)
        
        self.table.setSortingEnabled(True)
        
        # Update status
        self.status_label.setText(f'Viser {len(alarms)} alarmer')
    
    def export_to_csv(self):
        """Export filtered alarms to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Eksporter Alarmer',
            f'alarm_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'CSV filer (*.csv)'
        )
        
        if filename:
            try:
                import csv
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Headers
                    headers = [
                        'Tidspunkt', 'Symbol', 'Værdi', 'Type', 'Prioritet',
                        'Status', 'Besked', 'Kvitteret af', 'Kvitteret tidspunkt'
                    ]
                    writer.writerow(headers)
                    
                    # Data
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else '')
                        writer.writerow(row_data)
                
                self.status_label.setText(f'Eksporteret til {filename}')
                logger.info(f"Exported alarms to {filename}")
                
            except Exception as e:
                logger.error(f"Failed to export alarms: {e}")
                self.status_label.setText(f'Fejl ved eksport: {e}')
    
    def clear_history(self):
        """Clear alarm history"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Bekræft',
            'Er du sikker på at du vil rydde alarm historikken?\n'
            'Dette vil fjerne alle clearede alarmer.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.alarm_manager.clear_alarm_history()
            self.load_alarms()
            self.status_label.setText('Historik ryddet')
