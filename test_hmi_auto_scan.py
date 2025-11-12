"""
Test script for HMI Auto-Scan functionality
Tests the HMIAttributeScanner and StructReader integration
"""

import pyads
import logging
from hmi_attribute_scanner import HMIAttributeScanner, SymbolInfo
from struct_reader import StructReader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_auto_scan_with_struct_reader():
    """Test complete auto-scan with struct reading"""
    
    # Connection parameters - update these to match your PLC
    AMS_NET_ID = "5.112.50.143.1.1"
    AMS_PORT = 851
    
    print("=" * 70)
    print("HMI AUTO-SCAN + STRUCT READER TEST")
    print("=" * 70)
    
    try:
        # 1. Connect to PLC
        print(f"\n1. Connecting to PLC at {AMS_NET_ID}:{AMS_PORT}...")
        plc = pyads.Connection(AMS_NET_ID, AMS_PORT)
        plc.open()
        print("   ✓ Connected successfully")
        
        # 2. Create scanner and struct reader
        print("\n2. Creating HMI Attribute Scanner and StructReader...")
        scanner = HMIAttributeScanner(plc)
        struct_reader = StructReader(plc)
        print("   ✓ Scanner and reader created")
        
        # 3. Scan for {attribute 'HMI'} markers
        print("\n3. Scanning for {attribute 'HMI'} markers...")
        hmi_base_paths = scanner.scan_for_hmi_attributes()
        print(f"   ✓ Found {len(hmi_base_paths)} HMI base structures:")
        for path in hmi_base_paths:
            print(f"     - {path}")
        
        if len(hmi_base_paths) == 0:
            print("\n⚠️ No HMI structures found!")
            print("   Make sure your PLC has symbols marked with {attribute 'HMI'}")
            print("\n   Example PLC code:")
            print("   VAR_GLOBAL")
            print("       {attribute 'HMI'}")
            print("       Motor : ARRAY[1..3] OF ST_Motor;")
            print("   END_VAR")
            plc.close()
            return False
        
        # 4. Analyze each HMI structure
        print("\n4. Analyzing HMI structures and reading data...")
        all_symbols = {}
        all_data = {
            'setpoints': {},
            'process_values': {},
            'switches': {},
            'alarms': {}
        }
        
        for base_path in hmi_base_paths:
            print(f"\n   Analyzing: {base_path}")
            symbols = scanner.analyze_hmi_struct(base_path)
            all_symbols.update(symbols)
            
            # Read actual data for each symbol
            for symbol_path, symbol_info in symbols.items():
                print(f"     - {symbol_info.display_name} ({symbol_info.category})")
                
                try:
                    if symbol_info.category == 'setpoint':
                        data = struct_reader.read_setpoint(symbol_path)
                        if data:
                            all_data['setpoints'][symbol_path] = data
                            print(f"       Value: {data['value']} {data['config']['unit']}")
                            print(f"       Range: {data['config']['min']}-{data['config']['max']}")
                    
                    elif symbol_info.category == 'process_value':
                        data = struct_reader.read_process_value(symbol_path)
                        if data:
                            all_data['process_values'][symbol_path] = data
                            print(f"       Value: {data['value']} {data['config']['unit']}")
                            print(f"       Quality: {data.get('quality', 'Unknown')}")
                    
                    elif symbol_info.category == 'switch':
                        data = struct_reader.read_switch(symbol_path)
                        if data:
                            all_data['switches'][symbol_path] = data
                            print(f"       Position: {data['position']}")
                            print(f"       Labels: {', '.join(data['config']['labels'])}")
                    
                    elif symbol_info.category == 'alarm':
                        data = struct_reader.read_alarm(symbol_path)
                        if data:
                            all_data['alarms'][symbol_path] = data
                            status = "ACTIVE" if data['active'] else "Inactive"
                            print(f"       Status: {status}")
                            print(f"       Text: {data['text']}")
                
                except Exception as e:
                    print(f"       ❌ Failed to read: {e}")
        
        # 5. Test write operations
        print("\n5. Testing write operations...")
        if len(all_data['setpoints']) > 0:
            # Test setpoint write
            test_sp_path = list(all_data['setpoints'].keys())[0]
            test_sp_data = all_data['setpoints'][test_sp_path]
            original_value = test_sp_data['value']
            test_value = (test_sp_data['config']['min'] + test_sp_data['config']['max']) / 2
            
            print(f"   Testing setpoint write to {test_sp_path}")
            print(f"   Original value: {original_value}")
            print(f"   Writing test value: {test_value}")
            
            if struct_reader.write_setpoint_value(test_sp_path, test_value):
                print("   ✓ Write successful")
                
                # Read back
                import time
                time.sleep(0.5)
                verify_data = struct_reader.read_setpoint(test_sp_path)
                if verify_data:
                    print(f"   Readback value: {verify_data['value']}")
                    if abs(verify_data['value'] - test_value) < 0.01:
                        print("   ✓ Verification successful")
                    else:
                        print("   ⚠️ Readback value doesn't match")
            else:
                print("   ❌ Write failed")
        
        if len(all_data['switches']) > 0:
            # Test switch write
            test_sw_path = list(all_data['switches'].keys())[0]
            test_sw_data = all_data['switches'][test_sw_path]
            original_pos = test_sw_data['position']
            test_pos = 0 if original_pos != 0 else 1
            
            print(f"\n   Testing switch write to {test_sw_path}")
            print(f"   Original position: {original_pos}")
            print(f"   Writing test position: {test_pos}")
            
            if struct_reader.write_switch_position(test_sw_path, test_pos):
                print("   ✓ Write successful")
        
        # 6. Summary
        print("\n" + "=" * 70)
        print("TEST RESULTS:")
        print(f"  Total HMI base structures: {len(hmi_base_paths)}")
        print(f"  Total HMI symbols found: {len(all_symbols)}")
        print(f"  Setpoints: {len(all_data['setpoints'])}")
        print(f"  Process Values: {len(all_data['process_values'])}")
        print(f"  Switches: {len(all_data['switches'])}")
        print(f"  Alarms: {len(all_data['alarms'])}")
        print("=" * 70)
        
        if len(all_symbols) > 0 and len(all_data['setpoints']) + len(all_data['process_values']) > 0:
            print("\n✅ AUTO-SCAN + STRUCT READER TEST PASSED!")
            print("   System is ready for use with auto-scan enabled.")
        else:
            print("\n⚠️ WARNING: Symbols found but data reading failed")
            print("   Check PLC STRUCT definitions match ST_HMI_* format")
        
        # Close connection
        plc.close()
        print("\n✓ Disconnected from PLC")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test error")
        return False


if __name__ == "__main__":
    success = test_auto_scan_with_struct_reader()
    
    if success:
        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("1. Update config.json: Set \"auto_scan\": {\"enabled\": true}")
        print("2. Start main HMI application")
        print("3. Click 'Forbind' to connect to PLC")
        print("4. Auto-scan will discover all HMI symbols automatically!")
        print("=" * 70)
