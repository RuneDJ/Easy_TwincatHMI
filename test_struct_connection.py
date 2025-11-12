"""
Test script for STRUCT-based HMI connection
Run this to verify the STRUCT implementation works
"""

import pyads
import json
from struct_reader import StructReader

def test_struct_connection():
    """Test connection and STRUCT reading"""
    
    print("=" * 60)
    print("STRUCT Connection Test")
    print("=" * 60)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✓ Config loaded")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Get connection details
    ams_net_id = config['plc']['ams_net_id']
    ams_port = config['plc']['port']
    base_path = config.get('hmi_struct_path', 'MAIN.HMI')
    
    print(f"  AMS Net ID: {ams_net_id}")
    print(f"  AMS Port: {ams_port}")
    print(f"  HMI Path: {base_path}")
    print()
    
    # Connect to PLC
    print("Connecting to PLC...")
    try:
        plc = pyads.Connection(ams_net_id, ams_port)
        plc.open()
        print("✓ Connected to PLC")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    
    try:
        # Initialize StructReader
        reader = StructReader(plc)
        print("✓ StructReader initialized")
        print()
        
        # Test reading setpoint
        print("-" * 60)
        print("TEST 1: Reading Setpoint (TemperaturSetpunkt)")
        print("-" * 60)
        try:
            sp_path = f"{base_path}.TemperaturSetpunkt"
            sp_data = reader.read_setpoint(sp_path)
            
            if sp_data:
                print(f"✓ Successfully read setpoint")
                print(f"  Value: {sp_data['value']} {sp_data['config']['unit']}")
                print(f"  Range: {sp_data['config']['min']} - {sp_data['config']['max']}")
                print(f"  Display: {sp_data['display']['name']}")
                print(f"  Decimals: {sp_data['config']['decimals']}")
                print(f"  Alarm High: {sp_data['alarm_limits']['high']} {sp_data['config']['unit']}")
            else:
                print(f"✗ Failed to read setpoint")
        except Exception as e:
            print(f"✗ Error reading setpoint: {e}")
        
        print()
        
        # Test reading process value
        print("-" * 60)
        print("TEST 2: Reading Process Value (Temperatur_1)")
        print("-" * 60)
        try:
            pv_path = f"{base_path}.Temperatur_1"
            pv_data = reader.read_process_value(pv_path)
            
            if pv_data:
                print(f"✓ Successfully read process value")
                print(f"  Value: {pv_data['value']} {pv_data['config']['unit']}")
                print(f"  Display: {pv_data['display']['name']}")
                print(f"  Quality: {pv_data['quality']}")
                print(f"  Sensor Fault: {pv_data['sensor_fault']}")
            else:
                print(f"✗ Failed to read process value")
        except Exception as e:
            print(f"✗ Error reading process value: {e}")
        
        print()
        
        # Test reading switch
        print("-" * 60)
        print("TEST 3: Reading Switch (DriftMode)")
        print("-" * 60)
        try:
            sw_path = f"{base_path}.DriftMode"
            sw_data = reader.read_switch(sw_path)
            
            if sw_data:
                print(f"✓ Successfully read switch")
                print(f"  Position: {sw_data['position']}")
                print(f"  Display: {sw_data['display']['name']}")
                print(f"  Labels: {', '.join(sw_data['config']['labels'])}")
                print(f"  Current: {sw_data['config']['labels'][sw_data['position']]}")
            else:
                print(f"✗ Failed to read switch")
        except Exception as e:
            print(f"✗ Error reading switch: {e}")
        
        print()
        
        # Test reading alarm
        print("-" * 60)
        print("TEST 4: Reading Alarm (Motor1Fejl)")
        print("-" * 60)
        try:
            al_path = f"{base_path}.Motor1Fejl"
            al_data = reader.read_alarm(al_path)
            
            if al_data:
                print(f"✓ Successfully read alarm")
                print(f"  Active: {al_data['active']}")
                print(f"  Text: {al_data['text']}")
                print(f"  Priority: {al_data['priority']}")
                print(f"  Acknowledged: {al_data['acknowledged']}")
            else:
                print(f"✗ Failed to read alarm")
        except Exception as e:
            print(f"✗ Error reading alarm: {e}")
        
        print()
        
        # Test reading all symbols
        print("-" * 60)
        print("TEST 5: Reading All Symbols")
        print("-" * 60)
        try:
            struct_config = config.get('struct_symbols', {})
            all_symbols = reader.read_all_symbols(struct_config, base_path)
            
            print(f"✓ Successfully read {len(all_symbols)} symbols")
            print(f"  Setpoints: {len([s for s in all_symbols.values() if s['type'] == 'setpoint'])}")
            print(f"  Process Values: {len([s for s in all_symbols.values() if s['type'] == 'process_value'])}")
            print(f"  Switches: {len([s for s in all_symbols.values() if s['type'] == 'switch'])}")
            print(f"  Alarms: {len([s for s in all_symbols.values() if s['type'] == 'alarm'])}")
        except Exception as e:
            print(f"✗ Error reading all symbols: {e}")
        
        print()
        
        # Test writing setpoint
        print("-" * 60)
        print("TEST 6: Writing Setpoint Value")
        print("-" * 60)
        try:
            sp_path = f"{base_path}.TemperaturSetpunkt"
            
            # Read current value
            current = plc.read_by_name(f"{sp_path}.Value", pyads.PLCTYPE_REAL)
            print(f"  Current value: {current}")
            
            # Write new value (same as current + 0.1)
            new_value = current + 0.1
            success = reader.write_setpoint_value(sp_path, new_value)
            
            if success:
                # Read back
                readback = plc.read_by_name(f"{sp_path}.Value", pyads.PLCTYPE_REAL)
                print(f"✓ Write successful")
                print(f"  New value: {readback}")
                
                # Write back original
                reader.write_setpoint_value(sp_path, current)
                print(f"  Restored original value: {current}")
            else:
                print(f"✗ Write failed")
        except Exception as e:
            print(f"✗ Error writing setpoint: {e}")
        
        print()
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
        return True
        
    finally:
        # Close connection
        plc.close()
        print("Connection closed")


if __name__ == '__main__':
    test_struct_connection()
