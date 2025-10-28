"""
TMC File Parser - Reads TwinCAT metadata directly from .tmc XML file
Requires access to TwinCAT project folder
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List


class TMCParser:
    """Parse TwinCAT TMC (Type Management Component) XML files"""
    
    def __init__(self, tmc_file_path: str):
        """
        Initialize TMC parser
        
        Args:
            tmc_file_path: Path to .tmc file (e.g., "C:/TwinCAT/Projects/MyProject/MyProject.tmc")
        """
        self.tmc_path = Path(tmc_file_path)
        if not self.tmc_path.exists():
            raise FileNotFoundError(f"TMC file not found: {tmc_file_path}")
        
        self.tree = ET.parse(self.tmc_path)
        self.root = self.tree.getroot()
        
    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """
        Extract all symbols with their attributes from TMC file
        
        Returns:
            List of symbol dictionaries with name, type, attributes, etc.
        """
        symbols = []
        
        # TMC structure: TcModuleClass -> Modules -> Module -> DataAreas -> DataArea -> Symbol
        for symbol_elem in self.root.findall(".//Symbol"):
            symbol_info = self._parse_symbol(symbol_elem)
            if symbol_info:
                symbols.append(symbol_info)
        
        return symbols
    
    def _parse_symbol(self, symbol_elem) -> Dict[str, Any]:
        """Parse a single Symbol element from TMC DataArea"""
        name_elem = symbol_elem.find("Name")
        if name_elem is None:
            return None
        
        symbol = {
            'name': name_elem.text,
            'type': None,
            'attributes': {},
            'comment': None,
            'bit_size': None,
            'bit_offset': None,
            'default_value': None
        }
        
        # Get base type
        basetype = symbol_elem.find("BaseType")
        if basetype is not None:
            symbol['type'] = basetype.text
        
        # Get bit size
        bitsize = symbol_elem.find("BitSize")
        if bitsize is not None:
            symbol['bit_size'] = int(bitsize.text)
        
        # Get bit offset
        bitoffs = symbol_elem.find("BitOffs")
        if bitoffs is not None:
            symbol['bit_offset'] = int(bitoffs.text)
        
        # Get comment/description
        comment = symbol_elem.find("Comment")
        if comment is not None:
            symbol['comment'] = comment.text
        
        # Get default value
        default = symbol_elem.find("Default")
        if default is not None:
            value_elem = default.find("Value")
            if value_elem is not None:
                symbol['default_value'] = value_elem.text
        
        # Get attributes from Properties
        properties = symbol_elem.find("Properties")
        if properties is not None:
            for prop in properties.findall("Property"):
                name_prop = prop.find("Name")
                value_prop = prop.find("Value")
                
                if name_prop is not None:
                    attr_name = name_prop.text
                    if value_prop is not None:
                        # Attribute with value
                        symbol['attributes'][attr_name] = value_prop.text
                    else:
                        # Attribute without value (flag)
                        symbol['attributes'][attr_name] = True
        
        return symbol
    
    def _parse_datatype(self, datatype_elem) -> Dict[str, Any]:
        """Parse a single DataType element"""
        name_elem = datatype_elem.find("Name")
        if name_elem is None:
            return None
        
        symbol = {
            'name': name_elem.text,
            'type': None,
            'attributes': {},
            'comment': None,
            'subItems': []
        }
        
        # Get base type
        basetype = datatype_elem.find(".//BaseType")
        if basetype is not None:
            symbol['type'] = basetype.text
        
        # Get comment/description
        comment = datatype_elem.find(".//Comment")
        if comment is not None:
            symbol['comment'] = comment.text
        
        # Get attributes (pragmas)
        for prop in datatype_elem.findall(".//Property"):
            name = prop.find("Name")
            value = prop.find("Value")
            if name is not None and value is not None:
                symbol['attributes'][name.text] = value.text
        
        # Get attributes from pragmas
        for pragma in datatype_elem.findall(".//Attribute"):
            attr_name = pragma.get('Name')
            attr_value = pragma.get('Value')
            if attr_name and attr_value:
                symbol['attributes'][attr_name] = attr_value
        
        # Get structure members (SubItems)
        for subitem in datatype_elem.findall(".//SubItem"):
            member = self._parse_subitem(subitem)
            if member:
                symbol['subItems'].append(member)
        
        return symbol
    
    def _parse_subitem(self, subitem_elem) -> Dict[str, Any]:
        """Parse a SubItem (structure member) element"""
        name_elem = subitem_elem.find("Name")
        if name_elem is None:
            return None
        
        member = {
            'name': name_elem.text,
            'type': None,
            'attributes': {},
            'comment': None
        }
        
        # Get type
        type_elem = subitem_elem.find("Type")
        if type_elem is not None:
            member['type'] = type_elem.text
        
        # Get comment
        comment_elem = subitem_elem.find("Comment")
        if comment_elem is not None:
            member['comment'] = comment_elem.text
        
        # Get attributes
        for pragma in subitem_elem.findall(".//Attribute"):
            attr_name = pragma.get('Name')
            attr_value = pragma.get('Value')
            if attr_name and attr_value:
                member['attributes'][attr_name] = attr_value
        
        return member
    
    def find_hmi_symbols(self) -> List[Dict[str, Any]]:
        """
        Find all symbols with HMI-related attributes
        
        Returns:
            List of HMI symbols with their complete attribute sets
        """
        all_symbols = self.get_all_symbols()
        hmi_symbols = []
        
        for symbol in all_symbols:
            # Check if symbol has HMI attributes
            has_hmi = any(
                key.startswith(('HMI_', 'Unit', 'Min', 'Max', 'Decimals', 'Pos', 'Alarm', 'Step'))
                for key in symbol['attributes'].keys()
            )
            
            if has_hmi:
                hmi_symbols.append(symbol)
        
        return hmi_symbols
    
    def print_symbol_details(self, symbol: Dict[str, Any], indent: int = 0):
        """Pretty print symbol information"""
        prefix = "  " * indent
        print(f"{prefix}Symbol: {symbol['name']}")
        if symbol['type']:
            print(f"{prefix}  Type: {symbol['type']}")
        if symbol.get('bit_size'):
            print(f"{prefix}  Size: {symbol['bit_size']} bits")
        if symbol.get('default_value'):
            print(f"{prefix}  Default: {symbol['default_value']}")
        if symbol['comment']:
            # Show first line only
            comment_lines = symbol['comment'].split('\n')
            print(f"{prefix}  Comment: {comment_lines[0][:80]}...")
        if symbol['attributes']:
            print(f"{prefix}  Attributes:")
            for key, value in symbol['attributes'].items():
                if value is True:
                    print(f"{prefix}    {key}")
                else:
                    print(f"{prefix}    {key} = {value}")
        print()


def main():
    """Test TMC parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py tmc_parser.py <path_to_tmc_file>")
        print("\nExample:")
        print("  py tmc_parser.py C:/TwinCAT/Projects/MyProject/MyProject.tmc")
        print("  py tmc_parser.py //5.112.50.143/SharedFolder/Project.tmc")
        return
    
    tmc_file = sys.argv[1]
    
    try:
        print(f"Parsing TMC file: {tmc_file}\n")
        parser = TMCParser(tmc_file)
        
        print("=" * 80)
        print("HMI SYMBOLS WITH ATTRIBUTES")
        print("=" * 80)
        
        hmi_symbols = parser.find_hmi_symbols()
        print(f"\nFound {len(hmi_symbols)} HMI symbols\n")
        
        for symbol in hmi_symbols:
            parser.print_symbol_details(symbol)
            print("-" * 80)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTMC file not found. Make sure:")
        print("1. Path is correct")
        print("2. You have network access if using UNC path")
        print("3. TwinCAT project is compiled (generates TMC file)")
    except Exception as e:
        print(f"Error parsing TMC: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
