"""
Test TwinCAT HMI Application
Demonstrates the application with simulated PLC data
"""

import sys
import random
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Import mock ADS client for testing
class MockADSClient:
    """Mock ADS client for testing without real PLC"""
    
    def __init__(self, ams_net_id, ams_port):
        self.ams_net_id = ams_net_id
        self.ams_port = ams_port
        self.connected = False
        self.symbols = {}
        
        # Create test symbols
        self._create_test_symbols()
    
    def _create_test_symbols(self):
        """Create test symbol data"""
        self.symbols = {
            'GVL.TemperaturSetpunkt': {
                'name': 'GVL.TemperaturSetpunkt',
                'data_type': 'REAL',
                'comment': "{attribute 'HMI_SP'}{attribute 'Unit' := '°C'}{attribute 'Min' := '0'}{attribute 'Max' := '100'}{attribute 'AlarmHighHigh' := '95'}{attribute 'AlarmHigh' := '85'}",
                'attributes': {
                    'HMI_SP': 'true',
                    'Unit': '°C',
                    'Min': '0',
                    'Max': '100',
                    'AlarmHighHigh': '95',
                    'AlarmHigh': '85'
                },
                'value': 25.0
            },
            'GVL.Temperatur_1': {
                'name': 'GVL.Temperatur_1',
                'data_type': 'REAL',
                'comment': "{attribute 'HMI_PV'}{attribute 'Unit' := '°C'}{attribute 'AlarmHighHigh' := '98'}{attribute 'AlarmHigh' := '90'}{attribute 'AlarmLow' := '5'}{attribute 'AlarmLowLow' := '2'}",
                'attributes': {
                    'HMI_PV': 'true',
                    'Unit': '°C',
                    'AlarmHighHigh': '98',
                    'AlarmHigh': '90',
                    'AlarmLow': '5',
                    'AlarmLowLow': '2'
                },
                'value': 23.5
            },
            'GVL.Tryk_1': {
                'name': 'GVL.Tryk_1',
                'data_type': 'REAL',
                'comment': "{attribute 'HMI_PV'}{attribute 'Unit' := 'bar'}{attribute 'AlarmHigh' := '9.5'}",
                'attributes': {
                    'HMI_PV': 'true',
                    'Unit': 'bar',
                    'AlarmHigh': '9.5'
                },
                'value': 5.0
            },
            'GVL.DriftMode': {
                'name': 'GVL.DriftMode',
                'data_type': 'INT',
                'comment': "{attribute 'HMI_SWITCH'}{attribute 'Pos0' := 'Stop'}{attribute 'Pos1' := 'Auto'}{attribute 'Pos2' := 'Manuel'}",
                'attributes': {
                    'HMI_SWITCH': 'true',
                    'Pos0': 'Stop',
                    'Pos1': 'Auto',
                    'Pos2': 'Manuel'
                },
                'value': 1
            },
            'GVL.Motor1Fejl': {
                'name': 'GVL.Motor1Fejl',
                'data_type': 'BOOL',
                'comment': "{attribute 'HMI_ALARM'}{attribute 'AlarmText' := 'Motor 1 Fejl'}{attribute 'AlarmPriority' := '1'}",
                'attributes': {
                    'HMI_ALARM': 'true',
                    'AlarmText': 'Motor 1 Fejl',
                    'AlarmPriority': '1'
                },
                'value': False
            }
        }
    
    def connect(self):
        """Simulate connection"""
        self.connected = True
        print("Mock: Connected to PLC")
        return True
    
    def disconnect(self):
        """Simulate disconnect"""
        self.connected = False
        print("Mock: Disconnected from PLC")
    
    def read_symbol(self, symbol_name):
        """Read simulated symbol value"""
        if symbol_name in self.symbols:
            value = self.symbols[symbol_name]['value']
            
            # Add some random variation for realism
            if self.symbols[symbol_name]['data_type'] == 'REAL':
                value += random.uniform(-0.5, 0.5)
                self.symbols[symbol_name]['value'] = value
            
            return value
        return None
    
    def write_symbol(self, symbol_name, value):
        """Write to simulated symbol"""
        if symbol_name in self.symbols:
            self.symbols[symbol_name]['value'] = value
            print(f"Mock: Wrote {value} to {symbol_name}")
            return True
        return False
    
    def read_multiple_symbols(self, symbol_names):
        """Read multiple symbols"""
        results = {}
        for name in symbol_names:
            value = self.read_symbol(name)
            if value is not None:
                results[name] = value
        return results
    
    def get_symbol_info(self, symbol_name):
        """Get symbol info"""
        return self.symbols.get(symbol_name)
    
    def discover_symbols(self, patterns=None):
        """Discover symbols"""
        discovered = {}
        
        for name, info in self.symbols.items():
            if patterns:
                # Check if any pattern matches
                for pattern in patterns:
                    if any(pattern in str(v) for v in info['attributes'].values()):
                        discovered[name] = info
                        break
            else:
                discovered[name] = info
        
        print(f"Mock: Discovered {len(discovered)} symbols")
        return discovered
    
    def get_connection_status(self):
        """Get connection status"""
        return {
            'connected': self.connected,
            'ams_net_id': self.ams_net_id,
            'ams_port': self.ams_port
        }


def test_application():
    """Run application with mock data"""
    
    # Set logging to DEBUG
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Replace real ADS client with mock
    import ads_client
    ads_client.ADSClient = MockADSClient
    
    # Import and run main application
    from main import TwinCATHMI
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TwinCATHMI()
    window.show()
    
    # Auto-simulate alarm conditions after 5 seconds
    def simulate_alarm():
        if hasattr(window, 'ads_client') and window.ads_client:
            # Trigger high temperature alarm
            window.ads_client.symbols['GVL.Temperatur_1']['value'] = 92.0
            print("Mock: Triggering temperature alarm...")
    
    def simulate_critical_alarm():
        if hasattr(window, 'ads_client') and window.ads_client:
            # Trigger critical alarm
            window.ads_client.symbols['GVL.Temperatur_1']['value'] = 99.0
            print("Mock: Triggering CRITICAL temperature alarm...")
    
    # Setup timers for alarm simulation
    alarm_timer = QTimer()
    alarm_timer.setSingleShot(True)
    alarm_timer.timeout.connect(simulate_alarm)
    alarm_timer.start(10000)  # 10 seconds
    
    critical_timer = QTimer()
    critical_timer.setSingleShot(True)
    critical_timer.timeout.connect(simulate_critical_alarm)
    critical_timer.start(20000)  # 20 seconds
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    print("=" * 50)
    print("TwinCAT HMI - TEST MODE")
    print("=" * 50)
    print("Running with simulated PLC data")
    print("Alarm simulation will trigger after 10 seconds")
    print("=" * 50)
    print()
    
    test_application()
