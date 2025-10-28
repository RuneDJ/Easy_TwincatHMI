"""
Test program to display all attributes of first HMI symbol in PLC
"""
import pyads
import sys
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_hmi_attributes():
    """Connect to PLC and display all info about first HMI symbol"""
    
    print("="*80)
    print("HMI SYMBOL ATTRIBUTE TEST")
    print("="*80)
    print()
    
    # Connect to PLC
    plc = pyads.Connection('5.112.50.143.1.1', 851)
    
    try:
        plc.open()
        print("✓ Connected to PLC")
        print()
        
        # Get all symbols
        all_symbols = plc.get_all_symbols()
        print(f"Found {len(all_symbols)} total symbols")
        print()
        
        # Find first HMI symbol
        hmi_symbol = None
        hmi_markers = ['HMI_SP', 'HMI_PV', 'HMI_SWITCH', 'HMI_ALARM', 'HMI']
        
        for symbol in all_symbols:
            comment = symbol.comment if hasattr(symbol, 'comment') and symbol.comment else ''
            
            # Check if any HMI marker is in comment
            if any(marker in comment for marker in hmi_markers):
                hmi_symbol = symbol
                break
        
        if not hmi_symbol:
            print("❌ No HMI symbols found!")
            print("\nSearched for markers:", hmi_markers)
            return
        
        print("="*80)
        print("FIRST HMI SYMBOL FOUND")
        print("="*80)
        print()
        
        # Display all available attributes
        print(f"Symbol Name: {hmi_symbol.name}")
        print(f"Full Path: {hmi_symbol.name}")
        print()
        
        print("OBJECT ATTRIBUTES:")
        print("-"*80)
        for attr_name in dir(hmi_symbol):
            if not attr_name.startswith('_'):  # Skip private attributes
                try:
                    attr_value = getattr(hmi_symbol, attr_name)
                    # Skip methods
                    if not callable(attr_value):
                        print(f"  {attr_name:20s} = {attr_value}")
                except Exception as e:
                    print(f"  {attr_name:20s} = <Error: {e}>")
        
        print()
        print("DATA TYPE:")
        print("-"*80)
        try:
            print(f"  Type: {type(hmi_symbol.plc_type)}")
            print(f"  Value: {hmi_symbol.plc_type}")
            print(f"  String: {str(hmi_symbol.plc_type)}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
        print("COMMENT:")
        print("-"*80)
        if hasattr(hmi_symbol, 'comment') and hmi_symbol.comment:
            print(f"  Length: {len(hmi_symbol.comment)} characters")
            print(f"  Content:")
            print()
            print(hmi_symbol.comment)
        else:
            print("  No comment available")
        
        print()
        print("="*80)
        print("CURRENT VALUE:")
        print("="*80)
        try:
            value = plc.read_by_name(hmi_symbol.name)
            print(f"  Value: {value}")
            print(f"  Type: {type(value)}")
        except Exception as e:
            print(f"  Error reading value: {e}")
        
        print()
        print("="*80)
        print("SYMBOL HANDLE INFO:")
        print("="*80)
        try:
            handle = plc.get_handle(hmi_symbol.name)
            print(f"  Handle: {handle}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
        print("="*80)
        print("ALL AVAILABLE METHODS:")
        print("="*80)
        for attr_name in dir(hmi_symbol):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(hmi_symbol, attr_name)
                    if callable(attr_value):
                        print(f"  {attr_name}()")
                except:
                    pass
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        plc.close()
        print()
        print("="*80)
        print("Test completed")
        print("="*80)

if __name__ == '__main__':
    test_hmi_attributes()
    input("\nPress Enter to exit...")
