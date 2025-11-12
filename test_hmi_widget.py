"""
Test: Verificer GUI opdatering med mock data
"""

from hmi_symbol_widget import HMISymbolWidget
from PyQt5.QtWidgets import QApplication
import sys

def test_hmi_widget():
    """Test HMI widget med test data"""
    app = QApplication(sys.argv)
    
    # Test data for setpoint
    setpoint_data = {
        'name': 'MAIN.Motor01.HMI.SpeedSetpoint',
        'category': 'setpoint',
        'display_name': 'Motor Speed Setpoint',
        'value': 50.5,
        'unit': 'RPM',
        'min': 0.0,
        'max': 100.0,
        'decimals': 1,
        'step': 5.0,
        'alarm_limits': {
            'high_high': 95.0,
            'high': 85.0,
            'low': 10.0,
            'low_low': 5.0
        },
        'description': 'Motor hastighed setpunkt',
        'visible': True,
        'readonly': False
    }
    
    # Create widget
    widget = HMISymbolWidget('MAIN.Motor01.HMI.SpeedSetpoint', setpoint_data)
    widget.show()
    
    # Update value
    widget.update_value(75.3)
    
    print("✓ Widget created successfully")
    print(f"  Display name: {setpoint_data['display_name']}")
    print(f"  Initial value: {setpoint_data['value']}")
    print(f"  Unit: {setpoint_data['unit']}")
    print(f"  Range: {setpoint_data['min']} - {setpoint_data['max']}")
    
    # Test process value
    pv_data = {
        'name': 'MAIN.Motor01.HMI.CurrentSpeed',
        'category': 'process_value',
        'display_name': 'Current Speed',
        'value': 45.2,
        'unit': 'RPM',
        'decimals': 1,
        'alarm_limits': {},
        'description': 'Aktuel motor hastighed',
        'visible': True,
        'readonly': True
    }
    
    pv_widget = HMISymbolWidget('MAIN.Motor01.HMI.CurrentSpeed', pv_data)
    pv_widget.show()
    pv_widget.move(400, 0)
    
    print("\n✓ Process value widget created")
    print(f"  Display name: {pv_data['display_name']}")
    print(f"  Value: {pv_data['value']}")
    
    # Test switch
    switch_data = {
        'name': 'MAIN.Motor01.HMI.Mode',
        'category': 'switch',
        'display_name': 'Mode',
        'position': 1,
        'positions': ['Stop', 'Auto', 'Manual'],
        'description': 'Motor drift mode',
        'visible': True,
        'readonly': False
    }
    
    switch_widget = HMISymbolWidget('MAIN.Motor01.HMI.Mode', switch_data)
    switch_widget.show()
    switch_widget.move(800, 0)
    
    print("\n✓ Switch widget created")
    print(f"  Display name: {switch_data['display_name']}")
    print(f"  Positions: {switch_data['positions']}")
    print(f"  Current: {switch_data['position']}")
    
    # Test alarm
    alarm_data = {
        'name': 'MAIN.Motor01.HMI.Fault',
        'category': 'alarm',
        'display_name': 'Motor Fault',
        'active': False,
        'alarm_text': 'Motor overheat detected',
        'priority': 1,
        'acknowledged': False,
        'description': 'Motor fejl alarm',
        'visible': True,
        'readonly': True
    }
    
    alarm_widget = HMISymbolWidget('MAIN.Motor01.HMI.Fault', alarm_data)
    alarm_widget.show()
    alarm_widget.move(0, 300)
    
    print("\n✓ Alarm widget created")
    print(f"  Display name: {alarm_data['display_name']}")
    print(f"  Active: {alarm_data['active']}")
    print(f"  Text: {alarm_data['alarm_text']}")
    
    print("\n" + "="*60)
    print("All widgets created successfully!")
    print("Close windows to exit...")
    print("="*60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_hmi_widget()
