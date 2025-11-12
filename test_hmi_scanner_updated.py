"""
Test: Verificer at opdateret HMI scanner finder symboler
"""

import logging
from hmi_attribute_scanner import HMIAttributeScanner

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_hmi_scanner():
    """Test HMI scanner med TMC fil"""
    print("=" * 80)
    print("TEST: HMI Scanner med TMC Expansion")
    print("=" * 80)
    
    # TMC path
    tmc_path = r"C:\Users\Rune\Documents\TcXaeShell\Easy_TwincatHMI\Easy_TwincatHMI\PLC\PLC.tmc"
    
    # Create scanner uden PLC connection (vi bruger kun TMC)
    scanner = HMIAttributeScanner(plc_connection=None, tmc_path=tmc_path)
    
    # Scan for HMI symbols
    print("\n1. Scanning for HMI symbols...")
    hmi_paths = scanner.scan_for_hmi_attributes()
    
    print(f"\n✓ Found {len(hmi_paths)} HMI symbols:")
    for path in hmi_paths:
        print(f"  - {path}")
    
    # Analyze each symbol
    print("\n2. Analyzing each HMI symbol...")
    all_analyzed = {}
    for path in hmi_paths:
        symbols = scanner.analyze_hmi_symbol(path)
        all_analyzed.update(symbols)
    
    print(f"\n✓ Analyzed {len(all_analyzed)} symbols:")
    for path, info in all_analyzed.items():
        print(f"  - {path}")
        print(f"    Category: {info.category}")
        print(f"    Type: {info.struct_type}")
        print(f"    Display: {info.display_name}")
    
    # Categorize
    print("\n3. Categorized symbols:")
    categorized = scanner.get_all_discovered_symbols()
    for category, symbols in categorized.items():
        print(f"\n  {category}: {len(symbols)}")
        for sym in symbols:
            print(f"    - {sym.full_path}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    if len(hmi_paths) == 0:
        print("\n⚠️ WARNING: No HMI symbols found!")
        print("Check that TMC file contains ST_HMI_* structures")
    else:
        print(f"\n✓ SUCCESS: Found {len(hmi_paths)} HMI symbols")


if __name__ == "__main__":
    test_hmi_scanner()
