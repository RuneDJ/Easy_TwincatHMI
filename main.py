"""
TwinCAT HMI Main Application
Main window with ADS communication and alarm system integration
"""

import sys
import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QGroupBox, QTextEdit, QSplitter, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from ads_client import ADSClient
from ads_symbol_parser import SymbolParser
from alarm_manager import AlarmManager
from alarm_logger import AlarmLogger
from alarm_banner import AlarmBanner
from alarm_history_window import AlarmHistoryWindow
from gui_panels import SetpointPanel, ProcessValuePanel, SwitchPanel
from symbol_auto_config import SymbolAutoConfig

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TwinCATHMI(QMainWindow):
    """Main HMI application window"""
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.ads_client = None
        self.symbol_parser = SymbolParser()
        self.alarm_manager = AlarmManager(self.config)
        self.alarm_logger = AlarmLogger()
        
        # Register alarm callback for logging
        self.alarm_manager.register_callback(self.on_alarm_change)
        
        # UI state
        self.connected = False
        self.symbol_configs = []
        self.current_values = {}
        
        # Setup UI
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plc_data)
        
        logger.info("TwinCAT HMI Application started")
    
    def load_config(self) -> dict:
        """Load configuration from config.json"""
        config_file = Path('config.json')
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info("Configuration loaded")
                return config
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            'ads': {
                'ams_net_id': '127.0.0.1.1.1',
                'ams_port': 851,
                'update_interval': 1.0
            },
            'alarms': {
                'enabled': True,
                'sound_enabled': True,
                'blink_interval': 500,
                'auto_acknowledge': False,
                'log_to_csv': True
            },
            'symbol_search': {
                'enabled': True,
                'search_patterns': ['HMI_SP', 'HMI_PV', 'HMI_SWITCH', 'HMI_ALARM']
            },
            'gui': {
                'window_title': 'TwinCAT HMI',
                'window_width': 1200,
                'window_height': 800
            }
        }
    
    def setup_ui(self):
        """Setup main window UI"""
        # Window properties
        gui_config = self.config.get('gui', {})
        self.setWindowTitle(gui_config.get('window_title', 'TwinCAT HMI'))
        self.setGeometry(100, 100, 
                        gui_config.get('window_width', 1200), 
                        gui_config.get('window_height', 800))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Connection panel
        connection_panel = self.create_connection_panel()
        main_layout.addWidget(connection_panel)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Setpoint panel
        self.setpoint_panel = SetpointPanel()
        self.setpoint_panel.value_changed.connect(self.on_setpoint_changed)
        left_layout.addWidget(self.setpoint_panel)
        
        # Switch panel
        self.switch_panel = SwitchPanel()
        self.switch_panel.value_changed.connect(self.on_switch_changed)
        left_layout.addWidget(self.switch_panel)
        
        splitter.addWidget(left_widget)
        
        # Right side - Process values
        self.pv_panel = ProcessValuePanel()
        self.pv_panel.value_clicked.connect(self.show_trend)
        splitter.addWidget(self.pv_panel)
        
        # Set initial sizes
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter, stretch=1)
        
        # Information panel
        info_panel = self.create_info_panel()
        main_layout.addWidget(info_panel)
        
        # Alarm banner
        self.alarm_banner = AlarmBanner(self.alarm_manager, max_visible=5)
        self.alarm_banner.acknowledge_all_clicked.connect(self.acknowledge_all_alarms)
        self.alarm_banner.show_history_clicked.connect(self.show_alarm_history)
        self.alarm_banner.alarm_clicked.connect(self.show_trend)
        main_layout.addWidget(self.alarm_banner)
        
        # Status bar
        self.statusBar().showMessage('Ikke forbundet')
    
    def create_connection_panel(self) -> QGroupBox:
        """Create connection control panel"""
        panel = QGroupBox('Forbindelse')
        panel.setFont(QFont('Segoe UI', 11, QFont.Bold))
        
        layout = QHBoxLayout()
        
        # AMS Net ID input
        layout.addWidget(QLabel('AMS Net ID:'))
        self.ams_net_id_input = QLineEdit()
        self.ams_net_id_input.setText(self.config['ads']['ams_net_id'])
        self.ams_net_id_input.setMaximumWidth(150)
        layout.addWidget(self.ams_net_id_input)
        
        # AMS Port input
        layout.addWidget(QLabel('Port:'))
        self.ams_port_input = QLineEdit()
        self.ams_port_input.setText(str(self.config['ads']['ams_port']))
        self.ams_port_input.setMaximumWidth(80)
        layout.addWidget(self.ams_port_input)
        
        # Connect button
        self.connect_button = QPushButton('Forbind')
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setMinimumWidth(100)
        layout.addWidget(self.connect_button)
        
        # Status indicator
        self.status_label = QLabel('●')
        self.status_label.setFont(QFont('Segoe UI', 16))
        self.status_label.setStyleSheet('color: red;')
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Sound toggle
        self.sound_button = QPushButton('🔊 Lyd')
        self.sound_button.setCheckable(True)
        self.sound_button.setChecked(self.config['alarms']['sound_enabled'])
        self.sound_button.clicked.connect(self.toggle_sound)
        layout.addWidget(self.sound_button)
        
        # Scan PLC button
        scan_button = QPushButton('🔍 Scan PLC')
        scan_button.clicked.connect(self.scan_plc_symbols)
        layout.addWidget(scan_button)
        
        # Help button
        help_button = QPushButton('❓ Hjælp')
        help_button.clicked.connect(self.show_help)
        layout.addWidget(help_button)
        
        panel.setLayout(layout)
        return panel
    
    def create_info_panel(self) -> QGroupBox:
        """Create information panel"""
        panel = QGroupBox('Information')
        panel.setFont(QFont('Segoe UI', 10, QFont.Bold))
        panel.setMaximumHeight(120)
        
        layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(80)
        self.info_text.setFont(QFont('Courier New', 9))
        self.info_text.setText('Velkommen til TwinCAT HMI\nTryk "Forbind" for at starte...')
        
        layout.addWidget(self.info_text)
        panel.setLayout(layout)
        
        return panel
    
    def toggle_connection(self):
        """Toggle ADS connection"""
        if not self.connected:
            self.connect_to_plc()
        else:
            self.disconnect_from_plc()
    
    def connect_to_plc(self):
        """Connect to TwinCAT PLC"""
        try:
            # Get connection parameters
            ams_net_id = self.ams_net_id_input.text()
            ams_port = int(self.ams_port_input.text())
            
            # Create and connect client
            self.ads_client = ADSClient(ams_net_id, ams_port)
            
            if self.ads_client.connect():
                self.connected = True
                self.update_connection_ui(True)
                
                # Discover symbols
                self.discover_symbols()
                
                # Start update timer
                update_interval = int(self.config['ads']['update_interval'] * 1000)
                self.update_timer.start(update_interval)
                
                self.add_info_message('Forbundet til PLC')
                self.statusBar().showMessage('Forbundet')
                
            else:
                raise Exception('Connection failed')
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            QMessageBox.critical(self, 'Forbindelsesfejl', 
                               f'Kunne ikke forbinde til PLC:\n{e}')
            self.connected = False
            self.update_connection_ui(False)
    
    def disconnect_from_plc(self):
        """Disconnect from PLC"""
        try:
            # Stop timer
            self.update_timer.stop()
            
            # Disconnect
            if self.ads_client:
                self.ads_client.disconnect()
            
            self.connected = False
            self.update_connection_ui(False)
            
            self.add_info_message('Afbrudt fra PLC')
            self.statusBar().showMessage('Ikke forbundet')
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    def update_connection_ui(self, connected: bool):
        """Update UI based on connection state"""
        if connected:
            self.connect_button.setText('Afbryd')
            self.status_label.setStyleSheet('color: green;')
            self.ams_net_id_input.setEnabled(False)
            self.ams_port_input.setEnabled(False)
        else:
            self.connect_button.setText('Forbind')
            self.status_label.setStyleSheet('color: red;')
            self.ams_net_id_input.setEnabled(True)
            self.ams_port_input.setEnabled(True)
    
    def discover_symbols(self):
        """Discover and parse PLC symbols"""
        try:
            self.add_info_message('Søger efter symboler...')
            
            # Check if manual configuration exists and is not auto-discovered
            manual_symbols = self.config.get('manual_symbols', {})
            has_manual = manual_symbols.get('enabled', False) and manual_symbols.get('symbols')
            is_auto = manual_symbols.get('auto_discovered', False)
            
            # If no manual symbols or only auto-discovered, try auto-scan
            if not has_manual or (is_auto and self.config.get('auto_scan_on_start', True)):
                logger.info("No manual symbols or auto-scan enabled, running PLC scan...")
                self.add_info_message('Ingen manuel konfiguration, scanner PLC...')
                if self.scan_plc_symbols(silent=True):
                    # Reload config after scan
                    self.config = self.load_config()
                    manual_symbols = self.config.get('manual_symbols', {})
            
            # Check if manual configuration is enabled
            if manual_symbols.get('enabled', False):
                logger.info("Using manual symbol configuration")
                self.add_info_message('Bruger manuel symbol konfiguration...')
                self.load_manual_symbols()
                return
            
            # Get search patterns
            patterns = self.config['symbol_search']['search_patterns']
            
            # Discover symbols
            symbols = self.ads_client.discover_symbols(patterns)
            
            if not symbols:
                # Try without patterns (get all symbols)
                logger.warning("No symbols found with patterns, trying to get all symbols")
                self.add_info_message('Ingen symboler fundet med HMI tags, prøver manuel...')
                
                # Fallback to manual configuration if available
                if 'manual_symbols' in self.config and self.config['manual_symbols'].get('symbols'):
                    logger.info("Falling back to manual symbol configuration")
                    self.add_info_message('Skifter til manuel konfiguration...')
                    self.load_manual_symbols()
                    return
                else:
                    self.add_info_message('Ingen symboler fundet - tilføj manual_symbols til config.json')
                    logger.warning("No symbols found and no manual configuration available")
                    return
            
            # Parse symbols
            categorized = self.symbol_parser.parse_symbols(symbols)
            
            # Create UI elements
            self.create_symbol_widgets(categorized)
            
            # Store symbols with alarms
            self.symbol_configs = self.symbol_parser.get_symbols_with_alarms()
            
            info_msg = (f"Fundet {len(symbols)} symboler:\n"
                       f"  Setpunkter: {len(categorized['setpoint'])}\n"
                       f"  Procesværdier: {len(categorized['process_value'])}\n"
                       f"  Switches: {len(categorized['switch'])}\n"
                       f"  Alarmer: {len(categorized['alarm'])}")
            self.add_info_message(info_msg)
            
        except Exception as e:
            logger.error(f"Symbol discovery error: {e}", exc_info=True)
            self.add_info_message(f'Fejl ved symbol søgning: {e}')
    
    def load_manual_symbols(self):
        """Load symbols from manual configuration"""
        try:
            manual_config = self.config.get('manual_symbols', {}).get('symbols', {})
            
            if not manual_config:
                logger.error("No manual symbols configured")
                return
            
            # Build symbol dict in expected format
            symbols = {}
            for symbol_name, config in manual_config.items():
                # Verify symbol exists in PLC
                try:
                    value = self.ads_client.read_symbol(symbol_name)
                    if value is None:
                        logger.warning(f"Symbol {symbol_name} not found in PLC, skipping")
                        continue
                except:
                    logger.warning(f"Could not read {symbol_name}, skipping")
                    continue
                
                # Build symbol info
                symbols[symbol_name] = {
                    'name': symbol_name,
                    'data_type': 'REAL',  # Will be determined from PLC
                    'comment': f"Manual config: {config.get('category', 'unknown')}",
                    'attributes': self._build_attributes_from_config(config)
                }
            
            logger.info(f"Loaded {len(symbols)} manual symbols")
            
            # Parse symbols
            categorized = self.symbol_parser.parse_symbols(symbols)
            
            # Create UI elements
            self.create_symbol_widgets(categorized)
            
            # Store symbols with alarms
            self.symbol_configs = self.symbol_parser.get_symbols_with_alarms()
            
            info_msg = (f"Indlæst {len(symbols)} manuelle symboler:\n"
                       f"  Setpunkter: {len(categorized['setpoint'])}\n"
                       f"  Procesværdier: {len(categorized['process_value'])}\n"
                       f"  Switches: {len(categorized['switch'])}\n"
                       f"  Alarmer: {len(categorized['alarm'])}")
            self.add_info_message(info_msg)
            
        except Exception as e:
            logger.error(f"Error loading manual symbols: {e}", exc_info=True)
            self.add_info_message(f'Fejl ved indlæsning af symboler: {e}')
    
    def _build_attributes_from_config(self, config: dict) -> dict:
        """Build attributes dict from manual config"""
        attributes = {}
        
        category = config.get('category', '')
        
        # Add category tag
        if category == 'setpoint':
            attributes['HMI_SP'] = 'true'
        elif category == 'process_value':
            attributes['HMI_PV'] = 'true'
        elif category == 'switch':
            attributes['HMI_SWITCH'] = 'true'
        elif category == 'alarm':
            attributes['HMI_ALARM'] = 'true'
        
        # Add common attributes
        if 'unit' in config:
            attributes['Unit'] = config['unit']
        if 'min' in config:
            attributes['Min'] = str(config['min'])
        if 'max' in config:
            attributes['Max'] = str(config['max'])
        if 'decimals' in config:
            attributes['Decimals'] = str(config['decimals'])
        if 'step' in config:
            attributes['Step'] = str(config['step'])
        
        # Add alarm limits
        if 'alarm_high_high' in config:
            attributes['AlarmHighHigh'] = str(config['alarm_high_high'])
        if 'alarm_high' in config:
            attributes['AlarmHigh'] = str(config['alarm_high'])
        if 'alarm_low' in config:
            attributes['AlarmLow'] = str(config['alarm_low'])
        if 'alarm_low_low' in config:
            attributes['AlarmLowLow'] = str(config['alarm_low_low'])
        if 'alarm_priority' in config:
            attributes['AlarmPriority'] = str(config['alarm_priority'])
        if 'alarm_text' in config:
            attributes['AlarmText'] = config['alarm_text']
        
        # Add switch positions
        if 'positions' in config:
            for pos, label in config['positions'].items():
                attributes[f'Pos{pos}'] = label
        
        return attributes
    
    def create_symbol_widgets(self, categorized: dict):
        """Create UI widgets for discovered symbols"""
        # Add setpoints
        for symbol in categorized['setpoint']:
            self.setpoint_panel.add_setpoint(symbol)
        
        # Add process values
        for symbol in categorized['process_value']:
            self.pv_panel.add_process_value(symbol)
        
        # Add switches
        for symbol in categorized['switch']:
            self.switch_panel.add_switch(symbol)
    
    def update_plc_data(self):
        """Update data from PLC"""
        if not self.connected or not self.ads_client:
            return
        
        try:
            # Get all symbol names
            all_symbols = []
            
            for category in self.symbol_parser.categorized_symbols.values():
                all_symbols.extend([s['name'] for s in category])
            
            if not all_symbols:
                return
            
            # Read values
            values = self.ads_client.read_multiple_symbols(all_symbols)
            self.current_values = values
            
            # Update UI
            for symbol_name, value in values.items():
                symbol_config = self.symbol_parser.get_symbol_config(symbol_name)
                
                if not symbol_config:
                    continue
                
                category = symbol_config['category']
                
                if category == 'setpoint':
                    self.setpoint_panel.update_value(symbol_name, value)
                elif category == 'process_value':
                    self.pv_panel.update_value(symbol_name, value)
                elif category == 'switch':
                    self.switch_panel.update_value(symbol_name, value)
            
            # Check alarms
            self.alarm_manager.check_alarms(values, self.symbol_configs)
            
            # Update alarm indicators
            self.update_alarm_indicators()
            
        except Exception as e:
            logger.error(f"Update error: {e}")
            self.add_info_message(f'Fejl ved opdatering: {e}')
    
    def update_alarm_indicators(self):
        """Update alarm indicators on widgets"""
        active_alarms = self.alarm_manager.get_active_alarms()
        alarm_symbols = {a.symbol_name for a in active_alarms}
        
        # Update all symbols
        for symbol_name in self.current_values.keys():
            has_alarm = symbol_name in alarm_symbols
            
            self.setpoint_panel.set_alarm_state(symbol_name, has_alarm)
            self.pv_panel.set_alarm_state(symbol_name, has_alarm)
    
    def on_setpoint_changed(self, symbol_name: str, value: float):
        """Handle setpoint value change"""
        if not self.connected:
            return
        
        try:
            success = self.ads_client.write_symbol(symbol_name, value)
            if success:
                self.add_info_message(f'Skrev {value} til {symbol_name}')
            else:
                self.add_info_message(f'Fejl ved skrivning til {symbol_name}')
        except Exception as e:
            logger.error(f"Write error: {e}")
            self.add_info_message(f'Fejl: {e}')
    
    def on_switch_changed(self, symbol_name: str, position: int):
        """Handle switch position change"""
        if not self.connected:
            return
        
        try:
            success = self.ads_client.write_symbol(symbol_name, position)
            if success:
                self.add_info_message(f'Skiftede {symbol_name} til position {position}')
        except Exception as e:
            logger.error(f"Write error: {e}")
    
    def on_alarm_change(self, alarms):
        """Handle alarm changes (callback from alarm manager)"""
        # Log new alarms
        if self.config['alarms']['log_to_csv']:
            for alarm in alarms:
                if alarm.state.value == 'ACTIVE' and alarm not in self.alarm_logger:
                    self.alarm_logger.log_alarm(alarm)
    
    def acknowledge_all_alarms(self):
        """Acknowledge all active alarms"""
        self.alarm_manager.acknowledge_all()
        self.add_info_message('Alle alarmer kvitteret')
    
    def show_alarm_history(self):
        """Show alarm history window"""
        history_window = AlarmHistoryWindow(self.alarm_manager, self.alarm_logger, self)
        history_window.exec_()
    
    def show_trend(self, symbol_name: str):
        """Show trend for symbol (placeholder)"""
        self.add_info_message(f'Trend for {symbol_name} (ikke implementeret endnu)')
        # TODO: Implement trend visualization
    
    def toggle_sound(self, checked: bool):
        """Toggle alarm sound"""
        self.alarm_manager.set_sound_enabled(checked)
        status = 'aktiveret' if checked else 'deaktiveret'
        self.add_info_message(f'Alarm lyd {status}')
    
    def scan_plc_symbols(self, silent: bool = False) -> bool:
        """
        Scan PLC and auto-generate symbol configuration
        
        Args:
            silent: If True, don't show message boxes
            
        Returns:
            True if successful
        """
        if not self.connected or not self.ads_client:
            if not silent:
                QMessageBox.warning(self, 'Ikke forbundet', 
                                  'Du skal først forbinde til PLC\'en før scanning.')
            return False
        
        try:
            self.add_info_message('Scanner PLC for symboler...')
            
            # Create auto-config scanner
            scanner = SymbolAutoConfig(self.ads_client)
            
            # Scan and generate config
            success = scanner.scan_and_generate_config()
            
            if success:
                self.add_info_message('PLC scan komplet - config opdateret!')
                
                if not silent:
                    QMessageBox.information(
                        self, 
                        'Scan komplet',
                        'PLC symboler er scannet og config.json er opdateret.\n\n'
                        'Klik OK for at genindlæse symbolerne.'
                    )
                
                return True
            else:
                self.add_info_message('PLC scan fejlede - se log')
                if not silent:
                    QMessageBox.warning(self, 'Scan fejlet', 
                                      'Kunne ikke scanne PLC. Se log for detaljer.')
                return False
                
        except Exception as e:
            logger.error(f"PLC scan error: {e}", exc_info=True)
            self.add_info_message(f'Scan fejl: {e}')
            if not silent:
                QMessageBox.critical(self, 'Scan fejl', f'Fejl under scanning:\n{e}')
            return False
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        <h2>TwinCAT HMI Hjælp</h2>
        
        <h3>Forbindelse</h3>
        <p>Indtast AMS Net ID og Port for din TwinCAT PLC og tryk "Forbind".</p>
        
        <h3>Scan PLC</h3>
        <p>Tryk "Scan PLC" for automatisk at finde og konfigurere alle symboler i PLC'en.
        Dette opdaterer config.json automatisk.</p>
        
        <h3>Setpunkter</h3>
        <p>Indtast værdier og tryk "Skriv" for at sende til PLC.</p>
        
        <h3>Alarmer</h3>
        <p>
        - Alarmer vises automatisk når grænser overskrides<br>
        - Tryk "Kvitter" for at kvittere individuelle alarmer<br>
        - Tryk "Kvitter Alle" for at kvittere alle alarmer<br>
        - Tryk "Historik" for at se alarm log
        </p>
        
        <h3>Alarm Prioriteter</h3>
        <p>
        ⛔ Kritisk (Rød)<br>
        ⚠️ Høj (Orange)<br>
        ⚡ Medium (Gul)<br>
        ℹ️ Lav (Blå)
        </p>
        """
        
        QMessageBox.information(self, 'Hjælp', help_text)
    
    def add_info_message(self, message: str):
        """Add message to info panel"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        current_text = self.info_text.toPlainText()
        
        # Keep only last 4 lines
        lines = current_text.split('\n')
        if len(lines) >= 4:
            lines = lines[-3:]
        
        lines.append(f'[{timestamp}] {message}')
        self.info_text.setText('\n'.join(lines))
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.connected:
            self.disconnect_from_plc()
        
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TwinCATHMI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
