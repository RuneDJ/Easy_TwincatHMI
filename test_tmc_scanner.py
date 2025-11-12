"""
Test TMC-based HMI scanning
"""

import pyads
import logging
from hmi_attribute_scanner import HMIAttributeScanner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_tmc_scanner():
    """Test TMC-based HMI symbol scanning"""
    
    print("=" * 80)
    print("TESTING TMC-BASED HMI SCANNER")
    print("=" * 80)
    
    # Connect to PLC
    try:
        plc = pyads.Connection('5.112.50.143.1.1', 851)
        plc.open()
        print("✓ Connected to PLC")
    except Exception as e:
        print(f"❌ Failed to connect to PLC: {e}")
        return
    
    try:
        # TMC file path
        tmc_path = r"C:\Users\Rune\Documents\TcXaeShell\Easy_TwincatHMI\Easy_TwincatHMI\PLC\PLC.tmc"
        
        # Create scanner
        print(f"\n📁 Using TMC file: {tmc_path}")
        scanner = HMIAttributeScanner(plc, tmc_path=tmc_path)
        
        # Scan for HMI attributes
        print("\n🔍 Scanning for HMI symbols...")
        hmi_paths = scanner.scan_for_hmi_attributes()
        
        print(f"\n✅ Found {len(hmi_paths)} HMI symbols:")
        for path in hmi_paths:
            print(f"  - {path}")
        
        # Analyze each symbol
        print("\n📊 Analyzing symbols...")
        for path in hmi_paths:
            print(f"\n--- {path} ---")
            
            # Get attributes
            attributes = scanner.get_symbol_attributes(path)
            print(f"Attributes:")
            for key, value in attributes.items():
                print(f"  {key}: {value}")
            
            # Analyze symbol
            symbol_info = scanner.analyze_hmi_symbol(path)
            if symbol_info:
                for full_path, info in symbol_info.items():
                    print(f"Symbol Info:")
                    print(f"  Category: {info.category}")
                    print(f"  Type: {info.struct_type}")
                    print(f"  Display Name: {info.display_name}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        categorized = scanner.get_all_discovered_symbols()
        print(f"Setpoints: {len(categorized['setpoints'])}")
        print(f"Process Values: {len(categorized['process_values'])}")
        print(f"Switches: {len(categorized['switches'])}")
        print(f"Alarms: {len(categorized['alarms'])}")
        
    finally:
        plc.close()
        print("\n✓ Disconnected from PLC")


if __name__ == "__main__":
    test_tmc_scanner()
