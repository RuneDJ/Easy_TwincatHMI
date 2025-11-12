"""
Test: Get all HMI variables from TMC file
Scans all program variables in their full depth and saves to text file
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any


def parse_tmc_file(tmc_path: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse TMC file and extract all symbols and data types with full depth
    
    Args:
        tmc_path: Path to TMC file
        
    Returns:
        Tuple of (symbols list, datatypes list)
    """
    print(f"Parsing TMC file: {tmc_path}")
    
    tree = ET.parse(tmc_path)
    root = tree.getroot()
    
    all_symbols = []
    all_datatypes = []
    
    # Find all DataType elements
    for datatype_elem in root.findall('.//DataTypes/DataType'):
        datatype = parse_datatype_element(datatype_elem)
        if datatype:
            all_datatypes.append(datatype)
    
    # Create lookup dictionary for datatypes
    datatype_lookup = {dt['name']: dt for dt in all_datatypes}
    
    # Find all Symbol elements in DataAreas
    for symbol_elem in root.findall('.//DataArea/Symbol'):
        symbol = parse_symbol_element(symbol_elem)
        if symbol:
            # Filter: only MAIN and GVL symbols
            if symbol['name'].startswith('MAIN.') or symbol['name'].startswith('GVL.'):
                # Expand symbol with datatype structure
                expand_symbol_with_datatype(symbol, datatype_lookup)
                all_symbols.append(symbol)
    
    return all_symbols, all_datatypes


def expand_symbol_with_datatype(symbol: Dict[str, Any], datatype_lookup: Dict[str, Dict[str, Any]], depth: int = 0, max_depth: int = 10):
    """
    Recursively expand a symbol with its datatype structure
    
    Args:
        symbol: Symbol dictionary to expand
        datatype_lookup: Dictionary of datatype name -> datatype definition
        depth: Current recursion depth
        max_depth: Maximum recursion depth
    """
    if depth >= max_depth:
        return
    
    # Get the base type of this symbol
    base_type = symbol.get('base_type', symbol.get('type', ''))
    
    # Look up the datatype definition
    if base_type in datatype_lookup:
        datatype = datatype_lookup[base_type]
        
        # Copy sub_items from datatype to symbol
        if datatype.get('sub_items') and not symbol.get('sub_items'):
            symbol['sub_items'] = []
            
            for dt_subitem in datatype['sub_items']:
                # Create a copy of the subitem with full path
                expanded_subitem = {
                    'name': dt_subitem['name'],
                    'full_path': f"{symbol.get('full_path', symbol['name'])}.{dt_subitem['name']}",
                    'type': dt_subitem['type'],
                    'bit_size': dt_subitem.get('bit_size', 0),
                    'bit_offset': dt_subitem.get('bit_offset', 0),
                    'comment': dt_subitem.get('comment', ''),
                    'default_value': dt_subitem.get('default_value', ''),
                    'properties': dt_subitem.get('properties', {}),
                    'sub_items': []
                }
                
                # Recursively expand nested types
                expand_symbol_with_datatype(expanded_subitem, datatype_lookup, depth + 1, max_depth)
                
                symbol['sub_items'].append(expanded_subitem)
    
    # Also recursively expand any existing sub_items
    for subitem in symbol.get('sub_items', []):
        expand_symbol_with_datatype(subitem, datatype_lookup, depth + 1, max_depth)


def parse_datatype_element(datatype_elem: ET.Element) -> Dict[str, Any]:
    """
    Parse a DataType XML element
    
    Args:
        datatype_elem: XML Element representing a DataType
        
    Returns:
        Dictionary with datatype information
    """
    # Get name
    name_elem = datatype_elem.find('Name')
    if name_elem is None or not name_elem.text:
        return None
    
    name = name_elem.text
    
    # Get BitSize
    bit_size_elem = datatype_elem.find('BitSize')
    bit_size = int(bit_size_elem.text) if bit_size_elem is not None and bit_size_elem.text else 0
    
    # Get Comment
    comment_elem = datatype_elem.find('Comment')
    comment = comment_elem.text if comment_elem is not None and comment_elem.text else ""
    
    datatype = {
        'name': name,
        'bit_size': bit_size,
        'comment': comment,
        'sub_items': []
    }
    
    # Check for SubItems
    for subitem_elem in datatype_elem.findall('SubItem'):
        subitem = parse_subitem_element(subitem_elem, name)
        if subitem:
            datatype['sub_items'].append(subitem)
    
    return datatype


def parse_symbol_element(symbol_elem: ET.Element, parent_path: str = "") -> Dict[str, Any]:
    """
    Parse a symbol XML element with full depth
    
    Args:
        symbol_elem: XML Element representing a Symbol
        parent_path: Parent path for nested symbols
        
    Returns:
        Dictionary with symbol information
    """
    # Get name
    name_elem = symbol_elem.find('Name')
    if name_elem is None or not name_elem.text:
        return None
    
    name = name_elem.text
    full_path = f"{parent_path}.{name}" if parent_path else name
    
    # Get BaseType
    base_type_elem = symbol_elem.find('BaseType')
    base_type = base_type_elem.text if base_type_elem is not None and base_type_elem.text else "Unknown"
    
    # Get BitSize
    bit_size_elem = symbol_elem.find('BitSize')
    bit_size = int(bit_size_elem.text) if bit_size_elem is not None and bit_size_elem.text else 0
    
    # Get Comment
    comment_elem = symbol_elem.find('Comment')
    comment = comment_elem.text if comment_elem is not None and comment_elem.text else ""
    
    # Get Default value
    default_elem = symbol_elem.find('Default/Value')
    default_value = default_elem.text if default_elem is not None and default_elem.text else ""
    
    # Get BitOffs (offset)
    bit_offs_elem = symbol_elem.find('BitOffs')
    bit_offs = int(bit_offs_elem.text) if bit_offs_elem is not None and bit_offs_elem.text else 0
    
    # Parse Properties/Attributes
    properties = {}
    properties_elem = symbol_elem.find('Properties')
    if properties_elem is not None:
        for prop_elem in properties_elem.findall('Property'):
            prop_name_elem = prop_elem.find('Name')
            prop_value_elem = prop_elem.find('Value')
            
            if prop_name_elem is not None and prop_name_elem.text:
                prop_name = prop_name_elem.text
                prop_value = prop_value_elem.text if prop_value_elem is not None and prop_value_elem.text else "True"
                properties[prop_name] = prop_value
    
    # Create symbol dict
    symbol = {
        'name': name,
        'full_path': full_path,
        'base_type': base_type,
        'bit_size': bit_size,
        'bit_offset': bit_offs,
        'comment': comment,
        'default_value': default_value,
        'properties': properties,
        'sub_items': []
    }
    
    # Check for SubItems (nested structure members)
    for subitem_elem in symbol_elem.findall('SubItem'):
        subitem = parse_subitem_element(subitem_elem, full_path)
        if subitem:
            symbol['sub_items'].append(subitem)
    
    return symbol


def parse_subitem_element(subitem_elem: ET.Element, parent_path: str) -> Dict[str, Any]:
    """
    Parse a SubItem XML element (member of a structure)
    
    Args:
        subitem_elem: XML Element representing a SubItem
        parent_path: Parent symbol path
        
    Returns:
        Dictionary with subitem information
    """
    # Get name
    name_elem = subitem_elem.find('Name')
    if name_elem is None or not name_elem.text:
        return None
    
    name = name_elem.text
    full_path = f"{parent_path}.{name}"
    
    # Get Type
    type_elem = subitem_elem.find('Type')
    item_type = type_elem.text if type_elem is not None and type_elem.text else "Unknown"
    
    # Get BitSize
    bit_size_elem = subitem_elem.find('BitSize')
    bit_size = int(bit_size_elem.text) if bit_size_elem is not None and bit_size_elem.text else 0
    
    # Get BitOffs
    bit_offs_elem = subitem_elem.find('BitOffs')
    bit_offs = int(bit_offs_elem.text) if bit_offs_elem is not None and bit_offs_elem.text else 0
    
    # Get Comment
    comment_elem = subitem_elem.find('Comment')
    comment = comment_elem.text if comment_elem is not None and comment_elem.text else ""
    
    # Get Default value
    default_elem = subitem_elem.find('Default/Value')
    default_value = default_elem.text if default_elem is not None and default_elem.text else ""
    
    # Parse Properties/Attributes
    properties = {}
    properties_elem = subitem_elem.find('Properties')
    if properties_elem is not None:
        for prop_elem in properties_elem.findall('Property'):
            prop_name_elem = prop_elem.find('Name')
            prop_value_elem = prop_elem.find('Value')
            
            if prop_name_elem is not None and prop_name_elem.text:
                prop_name = prop_name_elem.text
                prop_value = prop_value_elem.text if prop_value_elem is not None and prop_value_elem.text else "True"
                properties[prop_name] = prop_value
    
    # Create subitem dict
    subitem = {
        'name': name,
        'full_path': full_path,
        'type': item_type,
        'bit_size': bit_size,
        'bit_offset': bit_offs,
        'comment': comment,
        'default_value': default_value,
        'properties': properties,
        'sub_items': []
    }
    
    # Recursively parse nested SubItems
    for nested_elem in subitem_elem.findall('SubItem'):
        nested_item = parse_subitem_element(nested_elem, full_path)
        if nested_item:
            subitem['sub_items'].append(nested_item)
    
    return subitem


def filter_hmi_symbols(symbol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively filter a symbol to only include items with 'HMI' in their path
    
    Args:
        symbol: Symbol dictionary to filter
        
    Returns:
        Filtered symbol dictionary or None if no HMI items found
    """
    # Check if current symbol has HMI in path
    full_path = symbol.get('full_path', symbol.get('name', ''))
    has_hmi_in_path = '.HMI' in full_path or full_path.endswith('HMI')
    
    # Filter sub_items recursively
    filtered_subitems = []
    for subitem in symbol.get('sub_items', []):
        filtered_sub = filter_hmi_symbols(subitem)
        if filtered_sub:
            filtered_subitems.append(filtered_sub)
    
    # If this symbol or any subitem has HMI, keep it
    if has_hmi_in_path or filtered_subitems:
        # Create a copy with filtered sub_items
        filtered_symbol = symbol.copy()
        filtered_symbol['sub_items'] = filtered_subitems
        return filtered_symbol
    
    return None


def write_hmi_symbols_only(symbols: List[Dict[str, Any]], output_path: str):
    """
    Write only HMI symbols to a text file in tree format
    
    Args:
        symbols: List of symbol dictionaries
        output_path: Path to output text file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TMC FILE - HMI SYMBOLS ONLY\n")
        f.write("=" * 80 + "\n\n")
        
        # Filter symbols to only include HMI-related items
        hmi_symbols = []
        for symbol in symbols:
            filtered = filter_hmi_symbols(symbol)
            if filtered:
                hmi_symbols.append(filtered)
        
        f.write(f"Total HMI symbols found: {len(hmi_symbols)}\n\n")
        f.write("=" * 80 + "\n")
        f.write("HMI SYMBOLS:\n")
        f.write("=" * 80 + "\n\n")
        
        for i, symbol in enumerate(hmi_symbols, 1):
            write_symbol_details(f, symbol, level=0, index=i)
            f.write("\n")


def write_symbols_to_file(symbols: List[Dict[str, Any]], datatypes: List[Dict[str, Any]], output_path: str):
    """
    Write all symbols and datatypes to a text file with full depth
    
    Args:
        symbols: List of symbol dictionaries
        datatypes: List of datatype dictionaries
        output_path: Path to output text file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TMC FILE - ALL PROGRAM VARIABLES AND DATA TYPES\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total symbols: {len(symbols)}\n")
        f.write(f"Total data types: {len(datatypes)}\n\n")
        
        # Count HMI datatypes and symbols
        hmi_datatypes = [dt for dt in datatypes if 'ST_HMI_' in dt.get('name', '')]
        
        hmi_count = {
            'HMI_SP': 0,
            'HMI_PV': 0,
            'HMI_SWITCH': 0,
            'HMI_ALARM': 0,
            'HMI attribute': 0
        }
        
        # Count HMI properties in symbols
        def count_hmi_in_symbol(sym, counts):
            props = sym.get('properties', {})
            if 'HMI' in props or any(k.startswith('HMI_') for k in props):
                counts['HMI attribute'] += 1
            for attr in ['HMI_SP', 'HMI_PV', 'HMI_SWITCH', 'HMI_ALARM']:
                if attr in props:
                    counts[attr] += 1
            # Recursively check sub-items
            for subitem in sym.get('sub_items', []):
                count_hmi_in_symbol(subitem, counts)
        
        for symbol in symbols:
            count_hmi_in_symbol(symbol, hmi_count)
        
        f.write("HMI Data Types:\n")
        f.write(f"  Total HMI types (ST_HMI_*): {len(hmi_datatypes)}\n")
        for dt in hmi_datatypes:
            f.write(f"    - {dt['name']}\n")
        f.write("\n")
        
        f.write("HMI Symbols/Attributes:\n")
        f.write(f"  HMI_SP (Setpoints): {hmi_count['HMI_SP']}\n")
        f.write(f"  HMI_PV (Process Values): {hmi_count['HMI_PV']}\n")
        f.write(f"  HMI_SWITCH (Switches): {hmi_count['HMI_SWITCH']}\n")
        f.write(f"  HMI_ALARM (Alarms): {hmi_count['HMI_ALARM']}\n")
        f.write(f"  HMI attribute marker: {hmi_count['HMI attribute']}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Write DataTypes first
        f.write("DATA TYPES:\n")
        f.write("=" * 80 + "\n\n")
        for i, datatype in enumerate(datatypes, 1):
            write_symbol_details(f, datatype, level=0, index=i)
            f.write("\n")
        
        # Write Symbols
        f.write("\n" + "=" * 80 + "\n")
        f.write("SYMBOLS:\n")
        f.write("=" * 80 + "\n\n")
        for i, symbol in enumerate(symbols, 1):
            write_symbol_details(f, symbol, level=0, index=i)
            f.write("\n")


def write_symbol_details(file, symbol: Dict[str, Any], level: int = 0, index: int = None):
    """
    Write symbol details to file in tree format with full paths
    
    Args:
        file: File handle
        symbol: Symbol dictionary
        level: Nesting level for indentation
        index: Symbol index number
    """
    # Tree characters
    if level == 0:
        prefix = ""
        connector = ""
    else:
        prefix = "     " * (level - 1)
        connector = "└── " if level > 0 else ""
    
    # Get type info
    symbol_type = symbol.get('base_type', symbol.get('type', ''))
    type_display = f" ({symbol_type})" if symbol_type and symbol_type != "Unknown" else ""
    
    # Get full path
    full_path = symbol.get('full_path', symbol.get('name', 'Unknown'))
    
    # Write header with index for top-level symbols
    if index and level == 0:
        file.write(f"\n{full_path}{type_display}\n")
    else:
        # Get just the name part for display
        name = symbol.get('name', 'Unknown')
        file.write(f"{prefix}{connector}{name}{type_display} → {full_path}\n")
    
    # Write sub-items recursively
    sub_items = symbol.get('sub_items', [])
    if sub_items:
        for i, subitem in enumerate(sub_items):
            # Determine if this is the last item
            is_last = (i == len(sub_items) - 1)
            write_symbol_details(file, subitem, level + 1)


def test_get_all_hmi_variables_in_tmc():
    """
    Main test function:
    1. Load TMC file
    2. Scan all program variables in full depth
    3. Create text file with all variables found
    """
    print("=" * 80)
    print("TEST: Get All HMI Variables in TMC")
    print("=" * 80)
    
    # 1. TMC file path
    tmc_path = r"C:\Users\Rune\Documents\TcXaeShell\Easy_TwincatHMI\Easy_TwincatHMI\PLC\PLC.tmc"
    
    if not Path(tmc_path).exists():
        print(f"❌ TMC file not found: {tmc_path}")
        return
    
    print(f"✓ TMC file found: {tmc_path}")
    
    # 2. Parse TMC file
    print("\nScanning all program variables and data types in full depth...")
    symbols, datatypes = parse_tmc_file(tmc_path)
    print(f"✓ Found {len(symbols)} total symbols")
    print(f"✓ Found {len(datatypes)} total data types")
    
    # Count HMI data types
    hmi_datatypes = [dt for dt in datatypes if 'ST_HMI_' in dt.get('name', '')]
    print(f"\nHMI Data Types (ST_HMI_*): {len(hmi_datatypes)}")
    for dt in hmi_datatypes:
        print(f"  - {dt['name']}")
    
    # Find symbols with HMI attribute or containing HMI structures
    def find_hmi_in_symbol(sym, hmi_list, path_prefix=""):
        props = sym.get('properties', {})
        current_path = f"{path_prefix}.{sym['name']}" if path_prefix else sym.get('full_path', sym['name'])
        
        if 'HMI' in props:
            hmi_list.append(current_path)
        
        for subitem in sym.get('sub_items', []):
            find_hmi_in_symbol(subitem, hmi_list, current_path)
    
    hmi_symbol_paths = []
    for symbol in symbols:
        find_hmi_in_symbol(symbol, hmi_symbol_paths)
    
    print(f"\nSymbols with {{attribute 'HMI'}} marker: {len(hmi_symbol_paths)}")
    for path in hmi_symbol_paths[:10]:  # Show first 10
        print(f"  - {path}")
    if len(hmi_symbol_paths) > 10:
        print(f"  ... and {len(hmi_symbol_paths) - 10} more")
    
    # 3. Write to text file
    output_path = r"C:\Users\Rune\VSCodeIns\Easy_TwincatHMI\PLC output.txt"
    print(f"\nWriting all variables to: {output_path}")
    write_symbols_to_file(symbols, datatypes, output_path)
    print(f"✓ File created successfully")
    
    # 4. Write HMI-only symbols to separate file
    hmi_output_path = r"C:\Users\Rune\VSCodeIns\Easy_TwincatHMI\PLC output hmi symbols only.txt"
    print(f"\nWriting HMI symbols only to: {hmi_output_path}")
    write_hmi_symbols_only(symbols, hmi_output_path)
    print(f"✓ HMI-only file created successfully")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"\nCheck output files:")
    print(f"  - All variables: {output_path}")
    print(f"  - HMI symbols only: {hmi_output_path}")


if __name__ == "__main__":
    test_get_all_hmi_variables_in_tmc()
